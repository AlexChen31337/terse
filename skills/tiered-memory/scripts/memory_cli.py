#!/usr/bin/env python3
"""
Tiered Memory CLI for OpenClaw agents.

Three-tier memory system:
  - Hot (core): 5KB max, living document (MEMORY.md), always in context
  - Warm (recent): 50KB max, scored facts with decay, local JSON
  - Cold (archive): Unlimited, Turso database

Usage:
  memory_cli.py store --text "..." --category "..." [--importance 0.7]
  memory_cli.py retrieve --query "..." [--limit 5]
  memory_cli.py consolidate
  memory_cli.py stats
  memory_cli.py tree [--show | --add PATH DESC | --remove PATH]
  memory_cli.py warm [--list | --evict | --search QUERY]
  memory_cli.py cold --store FILE | --query QUERY [--limit 10]
  memory_cli.py rebuild-hot --output MEMORY.md
"""

import argparse
import json
import os
import sys
import time
import math
import hashlib
import re
from datetime import datetime, timedelta
from pathlib import Path

# Paths
WORKSPACE = os.environ.get("WORKSPACE", os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
MEMORY_DIR = os.path.join(WORKSPACE, "memory")
WARM_FILE = os.path.join(MEMORY_DIR, "warm-memory.json")
TREE_FILE = os.path.join(MEMORY_DIR, "memory-tree.json")
HOT_STATE_FILE = os.path.join(MEMORY_DIR, "hot-memory-state.json")
MEMORY_MD = os.path.join(WORKSPACE, "MEMORY.md")

# Constraints
HOT_MAX_BYTES = 4096       # 4KB (~80% of old 5KB, leaves headroom)
WARM_MAX_KB = 50           # 50KB
WARM_MAX_BYTES = WARM_MAX_KB * 1024
WARM_RETENTION_DAYS = 30
COLD_ARCHIVE_DAYS = 2       # Archive facts older than 2 days to cold (keeps warm fresh)
HALF_LIFE_DAYS = 30.0
REINFORCEMENT_BOOST = 0.1
EVICTION_THRESHOLD = 0.3
TREE_MAX_NODES = 50
TREE_MAX_DEPTH = 4
TREE_MAX_CHILDREN = 10

# ─── Scoring ───

def recency_decay(age_days: float, half_life: float = HALF_LIFE_DAYS) -> float:
    """Exponential decay: score halves every half_life days."""
    return math.exp(-age_days / half_life)

def reinforcement_factor(access_count: int, boost: float = REINFORCEMENT_BOOST) -> float:
    """Diminishing returns reinforcement."""
    return 1.0 + boost * math.log(1 + access_count)

def calculate_score(importance: float, created_at: float, access_count: int = 0) -> float:
    """Full score: importance × recency × reinforcement."""
    age_days = (time.time() - created_at) / 86400
    decay = recency_decay(age_days)
    reinf = reinforcement_factor(access_count)
    return importance * decay * reinf

# ─── Tree Index ───

class MemoryTree:
    """Hierarchical index of memory categories (~2KB)."""
    
    def __init__(self):
        self.nodes = {}  # path -> {desc, warm_count, cold_count, last_access}
        self.load()
    
    def load(self):
        if os.path.exists(TREE_FILE):
            with open(TREE_FILE) as f:
                self.nodes = json.load(f)
        else:
            self.nodes = {
                "root": {"desc": "Memory root", "warm_count": 0, "cold_count": 0, "last_access": 0, "children": []}
            }
    
    def save(self):
        os.makedirs(os.path.dirname(TREE_FILE), exist_ok=True)
        with open(TREE_FILE, "w") as f:
            json.dump(self.nodes, f, indent=2)
    
    def add_node(self, path: str, desc: str) -> bool:
        if len(self.nodes) >= TREE_MAX_NODES:
            return False
        depth = path.count("/") + 1
        if depth > TREE_MAX_DEPTH:
            return False
        
        # Ensure parent exists
        if "/" in path:
            parent = path.rsplit("/", 1)[0]
            if parent not in self.nodes:
                self.add_node(parent, parent.split("/")[-1].title())
        
        parent_path = path.rsplit("/", 1)[0] if "/" in path else "root"
        parent = self.nodes.get(parent_path, {})
        children = parent.get("children", [])
        if len(children) >= TREE_MAX_CHILDREN:
            return False
        
        if path not in self.nodes:
            self.nodes[path] = {
                "desc": desc,
                "warm_count": 0,
                "cold_count": 0,
                "last_access": 0,
                "children": []
            }
            if parent_path in self.nodes:
                if path not in self.nodes[parent_path].get("children", []):
                    self.nodes[parent_path].setdefault("children", []).append(path)
        
        self.save()
        return True
    
    def remove_node(self, path: str) -> bool:
        if path not in self.nodes or path == "root":
            return False
        node = self.nodes[path]
        if node.get("warm_count", 0) > 0 or node.get("cold_count", 0) > 0:
            return False  # Don't remove nodes with data
        
        # Remove from parent's children
        parent_path = path.rsplit("/", 1)[0] if "/" in path else "root"
        if parent_path in self.nodes:
            children = self.nodes[parent_path].get("children", [])
            if path in children:
                children.remove(path)
        
        # Remove children recursively
        for child in list(node.get("children", [])):
            self.remove_node(child)
        
        del self.nodes[path]
        self.save()
        return True
    
    def update_counts(self, path: str, warm_delta: int = 0, cold_delta: int = 0):
        if path in self.nodes:
            self.nodes[path]["warm_count"] = max(0, self.nodes[path].get("warm_count", 0) + warm_delta)
            self.nodes[path]["cold_count"] = max(0, self.nodes[path].get("cold_count", 0) + cold_delta)
            self.nodes[path]["last_access"] = time.time()
            self.save()
    
    def search(self, query: str, top_k: int = 5) -> list:
        """Keyword-based search over tree nodes."""
        query_words = set(query.lower().split())
        results = []
        
        for path, node in self.nodes.items():
            if path == "root":
                continue
            # Score by keyword overlap
            path_words = set(re.split(r'[/_\-\s]', path.lower()))
            desc_words = set(node.get("desc", "").lower().split())
            all_words = path_words | desc_words
            overlap = len(query_words & all_words)
            if overlap > 0:
                score = overlap / max(len(query_words), 1)
                # Boost by recency
                if node.get("last_access", 0) > 0:
                    age_days = (time.time() - node["last_access"]) / 86400
                    score *= (1 + recency_decay(age_days, 7))  # 7-day half-life for tree
                results.append({"path": path, "score": score, "desc": node.get("desc", "")})
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    
    def show(self) -> str:
        """Pretty-print the tree."""
        lines = ["Memory Tree Index", "=" * 40]
        
        def _show(path, indent=0):
            node = self.nodes.get(path, {})
            prefix = "  " * indent
            warm = node.get("warm_count", 0)
            cold = node.get("cold_count", 0)
            desc = node.get("desc", "")
            lines.append(f"{prefix}📁 {path} — {desc} (warm:{warm}, cold:{cold})")
            for child in sorted(node.get("children", [])):
                _show(child, indent + 1)
        
        _show("root")
        lines.append(f"\nTotal nodes: {len(self.nodes)}/{TREE_MAX_NODES}")
        lines.append(f"Size: {len(json.dumps(self.nodes))} bytes")
        return "\n".join(lines)


# ─── Warm Memory ───

class WarmMemory:
    """Scored recent facts with eviction (50KB max, 30-day retention)."""
    
    def __init__(self):
        self.facts = []  # [{id, text, category, importance, created_at, access_count, score}]
        self.load()
    
    def load(self):
        if os.path.exists(WARM_FILE):
            with open(WARM_FILE) as f:
                self.facts = json.load(f)
        else:
            self.facts = []
    
    def save(self):
        os.makedirs(os.path.dirname(WARM_FILE), exist_ok=True)
        with open(WARM_FILE, "w") as f:
            json.dump(self.facts, f, indent=2)
    
    def add(self, text: str, category: str, importance: float = 0.5) -> str:
        fact_id = hashlib.md5(f"{text}{time.time()}".encode()).hexdigest()[:12]
        fact = {
            "id": fact_id,
            "text": text,
            "category": category,
            "importance": importance,
            "created_at": time.time(),
            "access_count": 0,
            "score": importance
        }
        self.facts.append(fact)
        self._enforce_limits()
        self.save()
        return fact_id
    
    def search(self, query: str, limit: int = 5) -> list:
        """Search warm facts by keyword overlap."""
        query_words = set(query.lower().split())
        results = []
        
        for fact in self.facts:
            fact_words = set(fact["text"].lower().split())
            cat_words = set(re.split(r'[/_\-]', fact.get("category", "").lower()))
            all_words = fact_words | cat_words
            overlap = len(query_words & all_words)
            
            if overlap > 0:
                # Recalculate score
                score = calculate_score(fact["importance"], fact["created_at"], fact["access_count"])
                relevance = (overlap / max(len(query_words), 1)) * score
                fact["access_count"] += 1
                results.append({**fact, "relevance": relevance})
        
        results.sort(key=lambda x: x["relevance"], reverse=True)
        self.save()  # Save updated access counts
        return results[:limit]
    
    def get_by_category(self, category: str, limit: int = 10) -> list:
        matches = [f for f in self.facts if f.get("category", "").startswith(category)]
        # Recalculate scores
        for f in matches:
            f["score"] = calculate_score(f["importance"], f["created_at"], f["access_count"])
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:limit]
    
    def get_recent(self, limit: int = 10) -> list:
        sorted_facts = sorted(self.facts, key=lambda x: x["created_at"], reverse=True)
        return sorted_facts[:limit]
    
    def evict_expired(self, archive_old: bool = True) -> list:
        """Remove expired facts AND archive older facts to cold. Returns evicted facts.
        
        Two eviction paths:
        1. Hard evict: facts older than WARM_RETENTION_DAYS with low scores (removed from warm)
        2. Age archive: facts older than COLD_ARCHIVE_DAYS (copied to cold, kept in warm until hard evict)
        
        When archive_old=True, returns facts older than COLD_ARCHIVE_DAYS for cold archival
        even if they stay in warm (dual-residence until they age out).
        """
        hard_cutoff = time.time() - (WARM_RETENTION_DAYS * 86400)
        archive_cutoff = time.time() - (COLD_ARCHIVE_DAYS * 86400)
        
        keep = []
        evicted = []       # Hard evicted (removed from warm)
        to_archive = []    # Old enough for cold archival (may stay in warm)
        
        for fact in self.facts:
            score = calculate_score(fact["importance"], fact["created_at"], fact["access_count"])
            fact["score"] = score
            
            if fact["created_at"] < hard_cutoff and score < EVICTION_THRESHOLD:
                # Hard evict — too old + low score
                evicted.append(fact)
            else:
                keep.append(fact)
                # Also flag for cold archival if old enough
                if archive_old and fact["created_at"] < archive_cutoff and not fact.get("_archived"):
                    to_archive.append(fact)
        
        # Mark archived facts so we don't re-archive
        for fact in to_archive:
            fact["_archived"] = True
        
        self.facts = keep
        self.save()
        
        # Return both hard-evicted and to-archive facts
        return evicted + to_archive
    
    def _enforce_limits(self):
        """Evict lowest-scored facts if over size limit."""
        while self._size() > WARM_MAX_BYTES and len(self.facts) > 1:
            # Recalculate all scores
            for f in self.facts:
                f["score"] = calculate_score(f["importance"], f["created_at"], f["access_count"])
            self.facts.sort(key=lambda x: x["score"])
            self.facts.pop(0)  # Remove lowest scored
    
    def _size(self) -> int:
        return len(json.dumps(self.facts).encode())
    
    def stats(self) -> dict:
        if not self.facts:
            return {"count": 0, "size_bytes": 2, "categories": {}}
        
        categories = {}
        for f in self.facts:
            cat = f.get("category", "uncategorized")
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "count": len(self.facts),
            "size_bytes": self._size(),
            "size_kb": round(self._size() / 1024, 1),
            "max_kb": WARM_MAX_KB,
            "oldest": datetime.fromtimestamp(min(f["created_at"] for f in self.facts)).isoformat(),
            "newest": datetime.fromtimestamp(max(f["created_at"] for f in self.facts)).isoformat(),
            "categories": categories,
        }


# ─── Cold Memory (Turso) ───

def _normalize_db_url(db_url: str) -> str:
    """Convert libsql:// URLs to https:// for HTTP API access."""
    if db_url.startswith("libsql://"):
        return db_url.replace("libsql://", "https://", 1)
    return db_url


def cold_store(text: str, category: str, importance: float, db_url: str, auth_token: str) -> bool:
    """Store a fact in Turso cold storage."""
    import urllib.request
    db_url = _normalize_db_url(db_url)
    
    fact_id = hashlib.md5(f"{text}{time.time()}".encode()).hexdigest()[:16]
    
    payload = {
        "requests": [
            {
                "type": "execute",
                "stmt": {
                    "sql": """INSERT INTO cold_memories (id, text, category, importance, created_at, access_count)
                              VALUES (?, ?, ?, ?, ?, 0)""",
                    "args": [
                        {"type": "text", "value": fact_id},
                        {"type": "text", "value": text},
                        {"type": "text", "value": category},
                        {"type": "float", "value": importance},
                        {"type": "integer", "value": str(int(time.time()))}
                    ]
                }
            },
            {"type": "close"}
        ]
    }
    
    req = urllib.request.Request(
        f"{db_url}/v2/pipeline",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"Cold store error: {e}", file=sys.stderr)
        return False


def cold_query(query: str, limit: int, db_url: str, auth_token: str) -> list:
    """Search cold storage by keyword (simple LIKE query)."""
    import urllib.request
    db_url = _normalize_db_url(db_url)
    
    words = query.split()[:3]  # Top 3 keywords
    conditions = " OR ".join([f"text LIKE '%{w}%'" for w in words])
    
    payload = {
        "requests": [
            {
                "type": "execute",
                "stmt": {
                    "sql": f"SELECT id, text, category, importance, created_at FROM cold_memories WHERE {conditions} ORDER BY importance DESC, created_at DESC LIMIT ?",
                    "args": [{"type": "integer", "value": str(limit)}]
                }
            },
            {"type": "close"}
        ]
    }
    
    req = urllib.request.Request(
        f"{db_url}/v2/pipeline",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)
            rows = data.get("results", [{}])[0].get("response", {}).get("result", {}).get("rows", [])
            results = []
            for row in rows:
                results.append({
                    "id": row[0]["value"],
                    "text": row[1]["value"],
                    "category": row[2]["value"],
                    "importance": float(row[3]["value"]),
                    "created_at": int(row[4]["value"]),
                    "tier": "cold"
                })
            return results
    except Exception as e:
        print(f"Cold query error: {e}", file=sys.stderr)
        return []


def cold_sync_hot_state(state: dict, db_url: str, auth_token: str) -> bool:
    """Sync hot-state JSON to Turso (cloud-first: critical sync)."""
    import urllib.request
    db_url = _normalize_db_url(db_url)

    payload = {
        "requests": [
            {
                "type": "execute",
                "stmt": {
                    "sql": """INSERT OR REPLACE INTO hot_state (id, data, updated_at)
                              VALUES ('current', ?, ?)""",
                    "args": [
                        {"type": "text", "value": json.dumps(state)},
                        {"type": "integer", "value": str(int(time.time()))}
                    ]
                }
            },
            {"type": "close"}
        ]
    }

    req = urllib.request.Request(
        f"{db_url}/v2/pipeline",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"Hot state cloud sync error: {e}", file=sys.stderr)
        return False


def cold_restore_hot_state(db_url: str, auth_token: str) -> dict:
    """Restore hot-state from Turso (disaster recovery)."""
    import urllib.request
    db_url = _normalize_db_url(db_url)

    payload = {
        "requests": [
            {
                "type": "execute",
                "stmt": {"sql": "SELECT data FROM hot_state WHERE id = 'current'"}
            },
            {"type": "close"}
        ]
    }

    req = urllib.request.Request(
        f"{db_url}/v2/pipeline",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read())
            rows = body.get("results", [{}])[0].get("response", {}).get("result", {}).get("rows", [])
            if rows:
                return json.loads(rows[0][0]["value"])
    except Exception as e:
        print(f"Hot state restore error: {e}", file=sys.stderr)
    return {}


def cold_init_table(db_url: str, auth_token: str) -> bool:
    db_url = _normalize_db_url(db_url)
    """Create cold_memories and hot_state tables if not exists."""
    import urllib.request
    
    payload = {
        "requests": [
            {
                "type": "execute",
                "stmt": {
                    "sql": """CREATE TABLE IF NOT EXISTS cold_memories (
                        id TEXT PRIMARY KEY,
                        text TEXT NOT NULL,
                        category TEXT NOT NULL,
                        importance REAL DEFAULT 0.5,
                        created_at INTEGER NOT NULL,
                        access_count INTEGER DEFAULT 0
                    )"""
                }
            },
            {
                "type": "execute",
                "stmt": {"sql": "CREATE INDEX IF NOT EXISTS idx_cold_category ON cold_memories(category)"}
            },
            {
                "type": "execute",
                "stmt": {"sql": "CREATE INDEX IF NOT EXISTS idx_cold_created ON cold_memories(created_at)"}
            },
            {
                "type": "execute",
                "stmt": {
                    "sql": """CREATE TABLE IF NOT EXISTS hot_state (
                        id TEXT PRIMARY KEY,
                        data TEXT NOT NULL,
                        updated_at INTEGER NOT NULL
                    )"""
                }
            },
            {"type": "close"}
        ]
    }
    
    req = urllib.request.Request(
        f"{db_url}/v2/pipeline",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"Cold init error: {e}", file=sys.stderr)
        return False


# ─── Hot Memory (MEMORY.md rebuild) ───

def rebuild_hot(output_path: str = MEMORY_MD):
    """Rebuild MEMORY.md from hot state + warm tier top facts."""
    warm = WarmMemory()
    tree = MemoryTree()
    
    # Load hot state
    hot_state = {}
    if os.path.exists(HOT_STATE_FILE):
        with open(HOT_STATE_FILE) as f:
            hot_state = json.load(f)
    
    owner = hot_state.get("owner", {})
    agent = hot_state.get("agent", {})
    lessons = hot_state.get("lessons", [])
    projects = hot_state.get("projects", [])
    
    # Get top warm facts by score
    all_warm = warm.facts[:]
    for f in all_warm:
        f["score"] = calculate_score(f["importance"], f["created_at"], f["access_count"])
    all_warm.sort(key=lambda x: x["score"], reverse=True)
    top_facts = all_warm[:10]  # Top 10 recent distilled facts (keep hot well under 4KB)
    
    # Build MEMORY.md
    lines = [
        "# MEMORY.md - Long-Term Context",
        "",
        "*Curated memory - auto-generated from tiered memory system*",
        "",
        "---",
        ""
    ]
    
    # Owner section
    if owner:
        lines.append("## 🧑 About " + owner.get("name", "Owner"))
        lines.append("")
        for k, v in owner.items():
            if k != "name":
                lines.append(f"- **{k.title()}:** {v}")
        lines.append("")
    
    # Agent section
    if agent:
        lines.append("## 🤖 Agent Identity")
        lines.append("")
        for k, v in agent.items():
            lines.append(f"- **{k.title()}:** {v}")
        lines.append("")
    
    # Active projects
    if projects:
        lines.append("## 💼 Active Projects")
        lines.append("")
        for p in projects[:5]:
            lines.append(f"### {p.get('name', 'Project')}")
            if p.get("status"):
                lines.append(f"**Status:** {p['status']}")
            if p.get("description"):
                lines.append(p["description"])
            lines.append("")
    
    # Lessons
    if lessons:
        lines.append("## 🎯 Key Learnings")
        lines.append("")
        for lesson in lessons[-20:]:
            lines.append(f"- {lesson}")
        lines.append("")
    
    # Recent memory (from warm)
    if top_facts:
        lines.append("## 📝 Recent Context")
        lines.append("")
        # Group by category
        by_cat = {}
        for f in top_facts:
            cat = f.get("category", "general")
            by_cat.setdefault(cat, []).append(f)
        
        for cat, facts in by_cat.items():
            lines.append(f"### {cat}")
            for f in facts[:5]:
                date = datetime.fromtimestamp(f["created_at"]).strftime("%b %d")
                lines.append(f"- [{date}] {f['text']}")
            lines.append("")
    
    # Footer
    lines.append("---")
    lines.append(f"*Auto-generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Warm: {warm.stats()['count']} facts | Tree: {len(tree.nodes)} nodes*")
    lines.append("*Review frequency: Auto-rebuilt each session*")
    
    content = "\n".join(lines)
    
    # Enforce 5KB limit
    if len(content.encode()) > HOT_MAX_BYTES:
        # Truncate recent context section
        while len(content.encode()) > HOT_MAX_BYTES and "📝 Recent Context" in content:
            # Remove last fact line
            content_lines = content.split("\n")
            for i in range(len(content_lines) - 1, -1, -1):
                if content_lines[i].startswith("- ["):
                    content_lines.pop(i)
                    break
            content = "\n".join(content_lines)
    
    with open(output_path, "w") as f:
        f.write(content)
    
    return len(content.encode())


# ─── Consolidation ───

def consolidate(db_url: str = None, auth_token: str = None):
    """Run full consolidation: evict warm, archive to cold, prune tree."""
    warm = WarmMemory()
    tree = MemoryTree()
    
    # 1. Evict expired warm facts (now returns the actual evicted facts)
    evicted_facts = warm.evict_expired()
    evicted_count = len(evicted_facts)
    
    # 2. Archive evicted to cold (if Turso configured)
    archived = 0
    if db_url and auth_token and evicted_count > 0:
        for fact in evicted_facts:
            ok = cold_store(
                fact["text"],
                fact.get("category", "uncategorized"),
                fact.get("importance", 0.5),
                db_url,
                auth_token
            )
            if ok:
                archived += 1
    
    # 3. Recalculate tree counts
    for path in tree.nodes:
        if path == "root":
            continue
        warm_facts = warm.get_by_category(path, limit=1000)
        tree.nodes[path]["warm_count"] = len(warm_facts)
    tree.save()
    
    # 4. Rebuild hot
    hot_size = rebuild_hot()
    
    print(json.dumps({
        "evicted_warm": evicted_count,
        "archived_cold": archived,
        "tree_nodes": len(tree.nodes),
        "hot_size_bytes": hot_size,
        "hot_max_bytes": HOT_MAX_BYTES,
        "warm_facts": len(warm.facts),
        "warm_size_kb": round(warm._size() / 1024, 1),
    }, indent=2))


# ─── Retrieve (multi-tier) ───

def retrieve(query: str, limit: int = 5, db_url: str = None, auth_token: str = None) -> list:
    """Search across all tiers: tree → warm → cold."""
    tree = MemoryTree()
    warm = WarmMemory()
    
    results = []
    
    # 1. Tree search to find relevant categories
    tree_hits = tree.search(query, top_k=3)
    
    # 2. Search warm memory (both targeted and general)
    seen_ids = set()
    
    # Targeted by tree categories
    for hit in tree_hits:
        cat_facts = warm.get_by_category(hit["path"], limit=limit)
        for f in cat_facts:
            if f["id"] not in seen_ids:
                f["tier"] = "warm"
                f["tree_relevance"] = hit["score"]
                results.append(f)
                seen_ids.add(f["id"])
    
    # General warm search
    warm_hits = warm.search(query, limit=limit)
    for f in warm_hits:
        if f["id"] not in seen_ids:
            f["tier"] = "warm"
            results.append(f)
            seen_ids.add(f["id"])
    
    # 3. Cold search if not enough results and Turso available
    if len(results) < limit and db_url and auth_token:
        cold_hits = cold_query(query, limit - len(results), db_url, auth_token)
        for f in cold_hits:
            if f["id"] not in seen_ids:
                results.append(f)
                seen_ids.add(f["id"])
    
    # Sort by relevance/score
    results.sort(key=lambda x: x.get("relevance", x.get("score", x.get("importance", 0))), reverse=True)
    return results[:limit]


# ─── Hot State Management ───

def update_hot_state(key: str, data: dict, db_url: str = None, auth_token: str = None):
    """Update hot memory state (owner profile, lessons, projects). Cloud-first: syncs to Turso."""
    state = {}
    if os.path.exists(HOT_STATE_FILE):
        with open(HOT_STATE_FILE) as f:
            state = json.load(f)
    
    if key == "lesson":
        state.setdefault("lessons", [])
        state["lessons"].append(data.get("text", ""))
        state["lessons"] = state["lessons"][-20:]  # Keep last 20
    elif key == "owner":
        state.setdefault("owner", {})
        state["owner"].update(data)
    elif key == "agent":
        state.setdefault("agent", {})
        state["agent"].update(data)
    elif key == "project":
        state.setdefault("projects", [])
        # Update or add
        existing = [p for p in state["projects"] if p.get("name") == data.get("name")]
        if existing:
            existing[0].update(data)
        else:
            state["projects"].append(data)
            state["projects"] = state["projects"][-5:]  # Max 5 active
    
    # Write local
    os.makedirs(os.path.dirname(HOT_STATE_FILE), exist_ok=True)
    with open(HOT_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
    
    # Cloud-first: critical sync to Turso
    cloud_synced = False
    if db_url and auth_token:
        cloud_synced = cold_sync_hot_state(state, db_url, auth_token)
    
    return cloud_synced


# ─── CLI ───

def main():
    parser = argparse.ArgumentParser(description="Tiered Memory CLI")
    sub = parser.add_subparsers(dest="command")
    
    # store
    p_store = sub.add_parser("store", help="Store a fact in warm memory")
    p_store.add_argument("--text", required=True)
    p_store.add_argument("--category", required=True)
    p_store.add_argument("--importance", type=float, default=0.5)
    p_store.add_argument("--db-url", default=None, help="Turso URL for cloud-first dual-write")
    p_store.add_argument("--auth-token", default=None, help="Turso auth token")
    
    # retrieve
    p_ret = sub.add_parser("retrieve", help="Search across all tiers")
    p_ret.add_argument("--query", required=True)
    p_ret.add_argument("--limit", type=int, default=5)
    p_ret.add_argument("--db-url", default=None)
    p_ret.add_argument("--auth-token", default=None)
    
    # consolidate
    p_con = sub.add_parser("consolidate", help="Run consolidation cycle")
    p_con.add_argument("--db-url", default=None)
    p_con.add_argument("--auth-token", default=None)
    
    # stats
    sub.add_parser("stats", help="Show memory system stats")
    
    # tree
    p_tree = sub.add_parser("tree", help="Manage tree index")
    p_tree.add_argument("--show", action="store_true")
    p_tree.add_argument("--add", nargs=2, metavar=("PATH", "DESC"))
    p_tree.add_argument("--remove")
    p_tree.add_argument("--search")
    
    # warm
    p_warm = sub.add_parser("warm", help="Manage warm memory")
    p_warm.add_argument("--list", action="store_true")
    p_warm.add_argument("--evict", action="store_true")
    p_warm.add_argument("--search")
    p_warm.add_argument("--recent", type=int, default=0)
    
    # cold
    p_cold = sub.add_parser("cold", help="Manage cold storage")
    p_cold.add_argument("--init", action="store_true")
    p_cold.add_argument("--store-text")
    p_cold.add_argument("--query")
    p_cold.add_argument("--category", default="general")
    p_cold.add_argument("--importance", type=float, default=0.5)
    p_cold.add_argument("--limit", type=int, default=10)
    p_cold.add_argument("--db-url", required=True)
    p_cold.add_argument("--auth-token", required=True)
    
    # rebuild-hot
    p_hot = sub.add_parser("rebuild-hot", help="Rebuild MEMORY.md from tiers")
    p_hot.add_argument("--output", default=MEMORY_MD)
    
    # hot-state
    p_hs = sub.add_parser("hot-state", help="Update hot memory state")
    p_hs.add_argument("--key", required=True, choices=["owner", "agent", "lesson", "project"])
    p_hs.add_argument("--data", required=True, help="JSON data")
    p_hs.add_argument("--db-url", default=None, help="Turso URL for cloud-first sync")
    p_hs.add_argument("--auth-token", default=None, help="Turso auth token")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "store":
        warm = WarmMemory()
        tree = MemoryTree()
        fact_id = warm.add(args.text, args.category, args.importance)
        # Ensure tree node exists
        tree.add_node(args.category, args.category.split("/")[-1].title())
        tree.update_counts(args.category, warm_delta=1)
        # Cloud-first: dual-write to cold storage
        cloud_synced = False
        if args.db_url and args.auth_token:
            cloud_synced = cold_store(args.text, args.category, args.importance, args.db_url, args.auth_token)
        print(json.dumps({"id": fact_id, "category": args.category, "status": "stored", "cloud_synced": cloud_synced}))
    
    elif args.command == "retrieve":
        results = retrieve(args.query, args.limit, args.db_url, args.auth_token)
        print(json.dumps(results, indent=2))
    
    elif args.command == "consolidate":
        consolidate(args.db_url, args.auth_token)
    
    elif args.command == "stats":
        warm = WarmMemory()
        tree = MemoryTree()
        hot_size = os.path.getsize(MEMORY_MD) if os.path.exists(MEMORY_MD) else 0
        
        print(json.dumps({
            "hot": {
                "file": MEMORY_MD,
                "size_bytes": hot_size,
                "max_bytes": HOT_MAX_BYTES,
                "pct_used": round(hot_size / HOT_MAX_BYTES * 100, 1)
            },
            "warm": warm.stats(),
            "tree": {
                "nodes": len(tree.nodes),
                "max_nodes": TREE_MAX_NODES,
                "size_bytes": len(json.dumps(tree.nodes).encode())
            }
        }, indent=2))
    
    elif args.command == "tree":
        tree = MemoryTree()
        if args.show:
            print(tree.show())
        elif args.add:
            ok = tree.add_node(args.add[0], args.add[1])
            print(json.dumps({"path": args.add[0], "added": ok}))
        elif args.remove:
            ok = tree.remove_node(args.remove)
            print(json.dumps({"path": args.remove, "removed": ok}))
        elif args.search:
            results = tree.search(args.search)
            print(json.dumps(results, indent=2))
        else:
            print(tree.show())
    
    elif args.command == "warm":
        warm = WarmMemory()
        if args.list:
            for f in warm.facts:
                f["score"] = calculate_score(f["importance"], f["created_at"], f["access_count"])
            print(json.dumps(warm.facts, indent=2))
        elif args.evict:
            count = warm.evict_expired()
            print(json.dumps({"evicted": count, "remaining": len(warm.facts)}))
        elif args.search:
            results = warm.search(args.search)
            print(json.dumps(results, indent=2))
        elif args.recent > 0:
            results = warm.get_recent(args.recent)
            print(json.dumps(results, indent=2))
        else:
            print(json.dumps(warm.stats(), indent=2))
    
    elif args.command == "cold":
        if args.init:
            ok = cold_init_table(args.db_url, args.auth_token)
            print(json.dumps({"initialized": ok}))
        elif args.store_text:
            ok = cold_store(args.store_text, args.category, args.importance, args.db_url, args.auth_token)
            print(json.dumps({"stored": ok}))
        elif args.query:
            results = cold_query(args.query, args.limit, args.db_url, args.auth_token)
            print(json.dumps(results, indent=2))
    
    elif args.command == "rebuild-hot":
        size = rebuild_hot(args.output)
        print(json.dumps({"output": args.output, "size_bytes": size, "max_bytes": HOT_MAX_BYTES}))
    
    elif args.command == "hot-state":
        data = json.loads(args.data)
        cloud_synced = update_hot_state(args.key, data, args.db_url, args.auth_token)
        print(json.dumps({"key": args.key, "updated": True, "cloud_synced": cloud_synced}))


if __name__ == "__main__":
    main()
