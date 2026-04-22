#!/usr/bin/env python3
"""
ArxivToCode Pipeline
Discovers top ML/AI papers from arXiv, generates code scaffolds, and creates GitHub repos.
Usage:
    uv run python scripts/arxiv_to_code_pipeline.py           # full run (max 2 repos)
    uv run python scripts/arxiv_to_code_pipeline.py --dry-run # discover + scaffold, no push/repo
    uv run python scripts/arxiv_to_code_pipeline.py --limit 1 # cap repos for this run
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
WORKSPACE = Path("/home/bowen/.openclaw/workspace")
STATE_FILE = WORKSPACE / "memory" / "arxiv-to-code-state.json"
MAX_REPOS_PER_RUN = 2

# arXiv categories to monitor
ARXIV_CATEGORIES = ["cs.AI", "cs.LG", "cs.CL"]

# Keywords for relevance scoring (higher weight = more relevant to our focus)
HIGH_VALUE_KEYWORDS = [
    "agent", "agents", "multi-agent", "autonomous",
    "llm", "language model", "large language",
    "blockchain", "decentralized", "federated",
    "reasoning", "planning", "tool use",
    "rag", "retrieval", "knowledge graph",
    "reinforcement learning", "rlhf", "reward",
    "transformer", "attention", "architecture",
    "inference", "efficiency", "optimization",
    "fine-tuning", "lora", "quantization",
    "vision", "multimodal", "embodied",
    "code generation", "program synthesis",
]

MEDIUM_VALUE_KEYWORDS = [
    "benchmark", "evaluation", "dataset",
    "safety", "alignment", "constitutional",
    "memory", "context", "long-context",
    "chain-of-thought", "prompt", "few-shot",
    "diffusion", "generation", "synthesis",
]

GIT_USER_EMAIL = "alex.chen31337@gmail.com"
GIT_USER_NAME = "Alex Chen"
GH_ORG = "Arxiv-to-code"
SSH_KEY = Path.home() / ".ssh" / "id_ed25519_alexchen"


# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"processed_ids": [], "repos_created": [], "last_run": None}


def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ---------------------------------------------------------------------------
# arXiv discovery
# ---------------------------------------------------------------------------

def fetch_arxiv_papers(categories: list[str], hours_back: int = 24, max_results: int = 50) -> list[dict]:
    """Query arXiv API for recent papers across given categories."""
    since = (datetime.now(timezone.utc) - timedelta(hours=hours_back)).strftime("%Y%m%d%H%M%S")
    
    cat_query = " OR ".join(f"cat:{c}" for c in categories)
    query = urllib.parse.quote(f"({cat_query})")
    
    url = (
        f"https://export.arxiv.org/api/query?"
        f"search_query={query}"
        f"&sortBy=submittedDate&sortOrder=descending"
        f"&start=0&max_results={max_results}"
    )
    
    print(f"[arxiv] Fetching from: {url}")
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ArxivToCode/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            xml_data = resp.read()
    except Exception as e:
        print(f"[arxiv] ERROR fetching papers: {e}")
        return []
    
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }
    
    root = ET.fromstring(xml_data)
    papers = []
    
    for entry in root.findall("atom:entry", ns):
        arxiv_id_raw = entry.findtext("atom:id", "", ns)
        # Extract clean ID like "2504.01234" from "http://arxiv.org/abs/2504.01234v1"
        m = re.search(r"abs/(\d{4}\.\d{4,5})(v\d+)?", arxiv_id_raw)
        if not m:
            continue
        arxiv_id = m.group(1)
        
        title = (entry.findtext("atom:title", "", ns) or "").strip().replace("\n", " ")
        abstract = (entry.findtext("atom:summary", "", ns) or "").strip().replace("\n", " ")
        published = entry.findtext("atom:published", "", ns)
        
        authors = []
        for author in entry.findall("atom:author", ns):
            name = author.findtext("atom:name", "", ns)
            if name:
                authors.append(name)
        
        cats = [c.get("term", "") for c in entry.findall("atom:category", ns)]
        
        papers.append({
            "id": arxiv_id,
            "title": title,
            "abstract": abstract,
            "authors": authors[:5],  # cap at 5
            "published": published,
            "categories": cats,
            "url": f"https://arxiv.org/abs/{arxiv_id}",
        })
    
    print(f"[arxiv] Found {len(papers)} papers")
    return papers


def score_paper(paper: dict) -> float:
    """Score paper by relevance to our focus areas."""
    text = (paper["title"] + " " + paper["abstract"]).lower()
    score = 0.0
    
    for kw in HIGH_VALUE_KEYWORDS:
        if kw.lower() in text:
            score += 2.0
    
    for kw in MEDIUM_VALUE_KEYWORDS:
        if kw.lower() in text:
            score += 1.0
    
    # Slight bonus for primary ML categories
    primary_cats = [c for c in paper.get("categories", []) if c in ARXIV_CATEGORIES]
    score += len(primary_cats) * 0.5
    
    # Penalty for very short abstracts (likely withdrawn/placeholder)
    if len(paper.get("abstract", "")) < 100:
        score -= 5.0
    
    return score


def filter_and_rank(papers: list[dict], processed_ids: set) -> list[dict]:
    """Remove already-processed papers, score, and rank."""
    fresh = [p for p in papers if p["id"] not in processed_ids]
    print(f"[filter] {len(fresh)} unprocessed papers (of {len(papers)} total)")
    
    for p in fresh:
        p["score"] = score_paper(p)
    
    ranked = sorted(fresh, key=lambda x: x["score"], reverse=True)
    return ranked


# ---------------------------------------------------------------------------
# Slug utilities
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    """Convert title to a safe repo-name slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    text = text.strip("-")
    # Cap length and append arXiv-style uniqueness
    return text[:60].rstrip("-")


def make_repo_name(paper: dict) -> str:
    slug = slugify(paper["title"])
    arxiv_short = paper["id"].replace(".", "")
    return f"arxiv-{arxiv_short}-{slug}"[:80]


# ---------------------------------------------------------------------------
# Code scaffold generation
# ---------------------------------------------------------------------------

MAIN_PY_TEMPLATE = '''\
"""
Implementation scaffold for: {title}
arXiv: {arxiv_url}

This is a structured scaffold. Key algorithms are stubbed — see README for paper details.
"""

import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core model / algorithm stubs (fill in from paper)
# ---------------------------------------------------------------------------

class Model:
    """
    Main model class based on {title}.
    
    Reference: {arxiv_url}
    """

    def __init__(self, config: dict):
        self.config = config
        logger.info("Model initialised with config: %s", config)

    def forward(self, inputs):
        """
        Forward pass — implement according to paper methodology.
        
        Args:
            inputs: Model inputs (format depends on task)
        
        Returns:
            Model outputs
        """
        raise NotImplementedError("Implement forward() per paper Section 3")

    def train_step(self, batch):
        """Single training step."""
        raise NotImplementedError("Implement train_step() per paper Section 4")

    def evaluate(self, eval_data):
        """Evaluation loop."""
        raise NotImplementedError("Implement evaluate() per paper Section 5")


def load_data(data_path: Path):
    """Load and preprocess dataset. Adapt to paper's data format."""
    logger.info("Loading data from %s", data_path)
    raise NotImplementedError("Implement data loading per paper Section 4.1")


def train(config: dict):
    """Full training loop."""
    logger.info("Starting training run")
    model = Model(config)
    # TODO: load data, run epochs, log metrics
    raise NotImplementedError("Implement training loop")


def inference(model_path: Path, input_data):
    """Run inference with trained model."""
    logger.info("Running inference from %s", model_path)
    raise NotImplementedError("Implement inference")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(description="Run {title} implementation")
    parser.add_argument("--mode", choices=["train", "eval", "infer"], default="train")
    parser.add_argument("--config", type=Path, default=Path("config.yaml"),
                        help="Path to config file")
    parser.add_argument("--data", type=Path, default=Path("data/"),
                        help="Path to data directory")
    parser.add_argument("--output", type=Path, default=Path("outputs/"),
                        help="Output directory")
    parser.add_argument("--checkpoint", type=Path, default=None,
                        help="Path to model checkpoint")
    return parser.parse_args()


def main():
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    
    config = {{
        "mode": args.mode,
        "data_path": str(args.data),
        "output_dir": str(args.output),
    }}
    
    logger.info("Running in mode: %s", args.mode)
    
    if args.mode == "train":
        train(config)
    elif args.mode == "eval":
        logger.info("Evaluation mode not yet implemented")
    elif args.mode == "infer":
        inference(args.checkpoint, None)


if __name__ == "__main__":
    main()
'''

REQUIREMENTS_TEMPLATE = """\
# Core dependencies — adjust versions to match paper's environment
torch>=2.0.0
numpy>=1.24.0
transformers>=4.36.0
datasets>=2.14.0
accelerate>=0.24.0
tqdm>=4.65.0
pyyaml>=6.0
wandb>=0.15.0  # optional: experiment tracking
"""

CONFIG_YAML_TEMPLATE = """\
# Configuration for {title}
# Reference: {arxiv_url}

model:
  # Model architecture params — fill in from paper
  hidden_dim: 512
  num_layers: 6
  num_heads: 8
  dropout: 0.1

training:
  batch_size: 32
  learning_rate: 1.0e-4
  num_epochs: 10
  warmup_steps: 1000
  gradient_clip: 1.0
  seed: 42

data:
  train_path: data/train
  eval_path: data/eval
  max_length: 512

output:
  checkpoint_dir: outputs/checkpoints
  log_dir: outputs/logs
"""

README_TEMPLATE = """\
# {title}

> Unofficial implementation scaffold — arXiv:{arxiv_id}

[![arXiv](https://img.shields.io/badge/arXiv-{arxiv_id}-b31b1b.svg)](https://arxiv.org/abs/{arxiv_id})
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()

## Paper

**{title}**  
{authors_line}  
[https://arxiv.org/abs/{arxiv_id}](https://arxiv.org/abs/{arxiv_id})

### Abstract

{abstract}

---

## Overview

This repository provides a structured implementation scaffold for the above paper.
The core algorithms are stubbed out — contributions to complete the implementation are welcome.

## Project Structure

```
.
├── main.py              # Entry point (train / eval / infer)
├── requirements.txt     # Python dependencies
├── config.yaml          # Hyperparameter config
├── data/                # Dataset directory (not included)
└── outputs/             # Training outputs
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Train (stub — implement main.py first)
python main.py --mode train --config config.yaml

# Eval
python main.py --mode eval --checkpoint outputs/checkpoints/best.pt
```

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Model architecture | 🚧 Stub | See `Model.forward()` in main.py |
| Training loop | 🚧 Stub | See `train()` in main.py |
| Data loading | 🚧 Stub | See `load_data()` in main.py |
| Evaluation | 🚧 Stub | See `Model.evaluate()` in main.py |

## Citation

```bibtex
@article{{{cite_key},
  title={{{title}}},
  author={{{authors_bib}}},
  journal={{arXiv preprint arXiv:{arxiv_id}}},
  year={{{year}}}
}}
```

## License

MIT
"""


def generate_scaffold(paper: dict, target_dir: Path):
    """Write all scaffold files into target_dir."""
    target_dir.mkdir(parents=True, exist_ok=True)
    
    arxiv_id = paper["id"]
    title = paper["title"]
    abstract = textwrap.fill(paper["abstract"], width=90)
    authors = paper.get("authors", [])
    authors_line = ", ".join(authors) if authors else "Authors listed on arXiv"
    authors_bib = " and ".join(authors) if authors else "et al."
    year = paper.get("published", "2024")[:4]
    cite_key = slugify(title.split()[0]) + year
    arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"
    
    # main.py
    (target_dir / "main.py").write_text(
        MAIN_PY_TEMPLATE.format(title=title, arxiv_url=arxiv_url)
    )
    
    # requirements.txt
    (target_dir / "requirements.txt").write_text(REQUIREMENTS_TEMPLATE)
    
    # config.yaml
    (target_dir / "config.yaml").write_text(
        CONFIG_YAML_TEMPLATE.format(title=title, arxiv_url=arxiv_url)
    )
    
    # README.md
    (target_dir / "README.md").write_text(
        README_TEMPLATE.format(
            title=title,
            arxiv_id=arxiv_id,
            authors_line=authors_line,
            authors_bib=authors_bib,
            abstract=abstract,
            cite_key=cite_key,
            year=year,
        )
    )
    
    # .gitignore
    (target_dir / ".gitignore").write_text(
        "__pycache__/\n*.py[cod]\n*.egg-info/\ndist/\nbuild/\n"
        ".env\n*.env\nvenv/\n.venv/\noutputs/\ndata/\n*.pt\n*.ckpt\n"
        "wandb/\n.DS_Store\n"
    )
    
    # data/ and outputs/ placeholders
    (target_dir / "data").mkdir(exist_ok=True)
    (target_dir / "data" / ".gitkeep").touch()
    (target_dir / "outputs").mkdir(exist_ok=True)
    (target_dir / "outputs" / ".gitkeep").touch()
    
    print(f"[scaffold] Generated scaffold in {target_dir}")


# ---------------------------------------------------------------------------
# Secret scan
# ---------------------------------------------------------------------------

def secret_scan(directory: Path) -> bool:
    """Return True if clean (no secrets found)."""
    result = subprocess.run(
        ["grep", "-rn", r"token\|secret\|password\|api_key", str(directory)],
        capture_output=True, text=True
    )
    if result.stdout.strip():
        print(f"[security] ⚠️  Potential secrets found in {directory}:")
        print(result.stdout[:500])
        return False
    print(f"[security] ✅ No secrets found in {directory}")
    return True


# ---------------------------------------------------------------------------
# GitHub repo creation & push
# ---------------------------------------------------------------------------

def create_github_repo(repo_name: str, description: str, dry_run: bool = False) -> bool:
    """Create a public GitHub repo under GH_ORG."""
    cmd = [
        "gh", "repo", "create",
        f"{GH_ORG}/{repo_name}",
        "--public",
        f"--description={description}",
    ]
    print(f"[github] {'[DRY-RUN] ' if dry_run else ''}Creating repo: {GH_ORG}/{repo_name}")
    if dry_run:
        return True
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[github] ERROR: {result.stderr}")
        return False
    print(f"[github] ✅ Created: {result.stdout.strip()}")
    return True


def push_to_github(local_dir: Path, repo_name: str, dry_run: bool = False) -> bool:
    """Init git, commit, and push to GitHub repo."""
    remote_url = f"git@github.com:{GH_ORG}/{repo_name}.git"
    
    env = os.environ.copy()
    env["GIT_SSH_COMMAND"] = f"ssh -i {SSH_KEY} -o StrictHostKeyChecking=no"
    
    cmds = [
        ["git", "init"],
        ["git", "config", "user.email", GIT_USER_EMAIL],
        ["git", "config", "user.name", GIT_USER_NAME],
        ["git", "add", "."],
        ["git", "commit", "-m", "Initial scaffold: generated by ArxivToCode pipeline"],
        ["git", "branch", "-M", "main"],
        ["git", "remote", "add", "origin", remote_url],
        ["git", "push", "-u", "origin", "main"],
    ]
    
    if dry_run:
        print(f"[git] [DRY-RUN] Would push {local_dir} → {remote_url}")
        return True
    
    for cmd in cmds:
        print(f"[git] {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=local_dir, capture_output=True, text=True, env=env)
        if result.returncode != 0:
            print(f"[git] ERROR running {cmd[0]}: {result.stderr}")
            return False
    
    print(f"[git] ✅ Pushed to {remote_url}")
    return True


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_pipeline(dry_run: bool = False, limit: int = MAX_REPOS_PER_RUN):
    print(f"\n{'='*60}")
    print(f"ArxivToCode Pipeline — {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"{'='*60}\n")
    
    state = load_state()
    processed_ids = set(state.get("processed_ids", []))
    print(f"[state] {len(processed_ids)} previously processed papers")
    
    # 1. Discover papers
    papers = fetch_arxiv_papers(ARXIV_CATEGORIES, hours_back=24, max_results=60)
    if not papers:
        print("[pipeline] No papers found — exiting")
        return
    
    # 2. Filter & rank
    ranked = filter_and_rank(papers, processed_ids)
    if not ranked:
        print("[pipeline] No new unprocessed papers — exiting")
        return
    
    print(f"\n[pipeline] Top {min(5, len(ranked))} candidates:")
    for i, p in enumerate(ranked[:5]):
        print(f"  {i+1}. [{p['score']:.1f}] {p['id']} — {p['title'][:70]}")
    
    # 3. Process top N papers
    to_process = ranked[:limit]
    created_count = 0
    
    with tempfile.TemporaryDirectory(prefix="arxiv2code_") as tmp_root:
        tmp_root = Path(tmp_root)
        
        for paper in to_process:
            if created_count >= limit:
                break
            
            arxiv_id = paper["id"]
            title = paper["title"]
            repo_name = make_repo_name(paper)
            description = (
                f"Implementation of {title} (arXiv:{arxiv_id}) "
                f"https://arxiv.org/abs/{arxiv_id}"
            )
            
            print(f"\n[pipeline] Processing: {arxiv_id} — {title[:60]}")
            print(f"[pipeline] Repo name: {repo_name}")
            print(f"[pipeline] Score: {paper['score']:.1f}")
            
            # Generate scaffold
            scaffold_dir = tmp_root / repo_name
            generate_scaffold(paper, scaffold_dir)
            
            # Secret scan
            if not secret_scan(scaffold_dir):
                print(f"[pipeline] ⚠️  Skipping {arxiv_id} — secret scan failed")
                continue
            
            if not dry_run:
                # Create GitHub repo
                if not create_github_repo(repo_name, description, dry_run=dry_run):
                    print(f"[pipeline] ⚠️  Failed to create repo for {arxiv_id}, skipping")
                    continue
                
                # Brief pause to avoid GH rate limits
                time.sleep(2)
                
                # Push code
                if not push_to_github(scaffold_dir, repo_name, dry_run=dry_run):
                    print(f"[pipeline] ⚠️  Failed to push {arxiv_id}")
                    continue
                
                # Update state
                processed_ids.add(arxiv_id)
                state["processed_ids"] = list(processed_ids)
                state["repos_created"].append({
                    "arxiv_id": arxiv_id,
                    "repo": f"{GH_ORG}/{repo_name}",
                    "title": title,
                    "description": description,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
                state["last_run"] = datetime.now(timezone.utc).isoformat()
                save_state(state)
                print(f"[state] ✅ Saved state for {arxiv_id}")
                
            else:
                print(f"[dry-run] ✅ Would create + push: {GH_ORG}/{repo_name}")
                print(f"[dry-run] Description: {description}")
                # Show scaffold preview
                for f in sorted(scaffold_dir.rglob("*")):
                    if f.is_file():
                        print(f"[dry-run]   {f.relative_to(scaffold_dir)}")
            
            created_count += 1
        
        if dry_run:
            # Update state.last_run even in dry-run for tracking
            state["last_run"] = datetime.now(timezone.utc).isoformat()
            save_state(state)
    
    print(f"\n[pipeline] Done. {'Would have created' if dry_run else 'Created'} {created_count} repos.")
    
    if not dry_run and created_count > 0:
        print("\n[pipeline] Run promote_arxiv_repos.py to push these to social media.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ArxivToCode Pipeline")
    parser.add_argument("--dry-run", action="store_true",
                        help="Discover and scaffold without pushing to GitHub")
    parser.add_argument("--limit", type=int, default=MAX_REPOS_PER_RUN,
                        help=f"Max repos to create per run (default: {MAX_REPOS_PER_RUN})")
    args = parser.parse_args()
    
    run_pipeline(dry_run=args.dry_run, limit=args.limit)
