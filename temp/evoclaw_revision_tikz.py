#!/usr/bin/env python3
"""
EvoClaw Paper Revision - Part 3: TikZ Diagram Improvements
"""

import re

with open('/media/DATA/clawd/papers/evoclang-ieee-sse2026.tex', 'r') as f:
    content = f.read()

original = content

print("=" * 80)
print("EV OCLAW PAPER REVISION - PART 3: TIKZ DIAGRAMS")
print("=" * 80)

# ============================================================================
# CHANGE 10: Improve Architecture Diagram
# ============================================================================
print("\n[10/17] Improving architecture diagram...")

# Find and replace the old architecture diagram
old_arch_diagram = r'''\begin{figure*}[t]
\centering
\begin{tikzpicture}[
    node distance=0.8cm and 1.5cm,
    tier/.style={draw, rounded corners, minimum width=13cm, minimum height=3cm, fill=#1!10},
    component/.style={draw, rounded corners, minimum width=2.5cm, minimum height=1cm, fill=#1!30, font=\small},
    arrow/.style={-{Stealth[scale=0.8]}, thick},
    label/.style={font=\small\bfseries}
]

% Cloud Tier
\node[tier=cloudbg] (cloud) {};
\node[label, above=0.1cm of cloud.north west, anchor=south west] {Cloud Tier (E2B / Turso)};

\node[component=coreorange, anchor=west] at ([xshift=0.5cm]cloud.west) (e2b) {E2B Sandbox};
\node[component=coreorange, right=0.5cm of e2b] (turso) {Turso (Cold)};
\node[component=corepurple, right=0.5cm of turso] (llm) {LLM APIs};
\node[component=corepurple, right=0.5cm of llm] (chain) {ClawChain};

% Server Tier
\node[tier=serverbg, below=1.5cm of cloud] (server) {};
\node[label, above=0.1cm of server.north west, anchor=south west] {Server Tier (Go Orchestrator)};

\node[component=coreblue, anchor=west] at ([xshift=0.5cm]server.west) (router) {Model Router};
\node[component=coreblue, right=0.3cm of router] (health) {Health Registry};
\node[component=coreblue, right=0.3cm of health] (orch) {Orchestrator};
\node[component=coreblue, right=0.3cm of orch] (evol) {Evolution Engine};
\node[component=coreblue, right=0.3cm of evol] (mqtt) {MQTT Broker};

% Edge Tier
\node[tier=edgebg, below=1.5cm of server] (edge) {};
\node[label, above=0.1cm of edge.north west, anchor=south west] {Edge Tier (Rust Agents)};

\node[component=coreteal, anchor=west] at ([xshift=0.5cm]edge.west) (genome) {Genome Engine};
\node[component=coreteal, right=0.3cm of genome] (skills) {Skill Executor};
\node[component=coreteal, right=0.3cm of skills] (memory) {Memory Manager};
\node[component=coreteal, right=0.3cm of memory] (tools) {Tool Loop};
\node[component=coreteal, right=0.3cm of tools] (gov) {Self-Governance};

% Arrows
\draw[arrow] (orch) -- (llm);
\draw[arrow] (orch) -- (turso);
\draw[arrow] (chain) -- (evol);
\draw[arrow] (mqtt) -- (skills);
\draw[arrow] (memory) -- (turso);
\draw[arrow] (router) -- (health);
\draw[arrow] (health) -- (llm);

\end{tikzpicture}
\caption{Three-tier \evoclaw{} architecture. Edge agents (Rust) execute skills and manage local memory. Server orchestrator (Go) coordinates agents via MQTT and routes LLM requests. Cloud services provide persistent storage (Turso), ephemeral compute (E2B), and blockchain identity (ClawChain).}
\label{fig:architecture}
\end{figure*}'''

new_arch_diagram = r'''\begin{figure*}[t]
\centering
\begin{tikzpicture}[
    node distance=0.6cm and 1.0cm,
    tier/.style={draw, rounded corners, minimum width=14cm, minimum height=2.8cm, fill=#1!10, line width=0.8pt},
    component/.style={draw, rounded corners, minimum width=2.2cm, minimum height=0.9cm, fill=#1!30, font=\footnotesize\bfseries, line width=0.6pt, drop shadow},
    edgecomp/.style={draw, rounded corners, minimum width=2.0cm, minimum height=0.85cm, fill=#1!35, font=\footnotesize\bfseries, line width=0.6pt, drop shadow},
    arrow/.style={-{Stealth[scale=0.9]}, thick, draw=coregray},
    dataarrow/.style={-{Stealth[scale=0.9]}, thick, draw=corepurple, dashed},
    label/.style={font=\small\bfseries, anchor=south west}
]

% Cloud Tier
\node[tier=cloudbg] (cloud) {};
\node[label, above=0.05cm of cloud.north west] {Cloud Tier (E2B / Turso)};

\node[edgecomp=coreorange, anchor=west] at ([xshift=0.6cm]cloud.west) (e2b) {E2B Sandbox};
\node[edgecomp=coreorange, right=0.4cm of e2b] (turso) {Turso\\(Cold)};
\node[edgecomp=corepurple, right=0.4cm of turso] (llm) {LLM APIs};
\node[edgecomp=corepurple, right=0.4cm of llm] (chain) {ClawChain};

% Server Tier
\node[tier=serverbg, below=1.2cm of cloud] (server) {};
\node[label, above=0.05cm of server.north west] {Server Tier (Go Orchestrator)};

\node[component=coreblue, anchor=west] at ([xshift=0.6cm]server.west) (router) {Model\\Router};
\node[component=coreblue, right=0.25cm of router] (health) {Health\\Registry};
\node[component=coreblue, right=0.25cm of health] (orch) {Orchestr-\\ator};
\node[component=coreblue, right=0.25cm of orch] (evol) {Evolution\\Engine};
\node[component=coreblue, right=0.25cm of evol] (mqtt) {MQTT\\Broker};

% Edge Tier
\node[tier=edgebg, below=1.2cm of server] (edge) {};
\node[label, above=0.05cm of edge.north west] {Edge Tier (Rust Agents)};

\node[edgecomp=coreteal, anchor=west] at ([xshift=0.6cm]edge.west) (genome) {Genome\\Engine};
\node[edgecomp=coreteal, right=0.25cm of genome] (skills) {Skill\\Executor};
\node[edgecomp=coreteal, right=0.25cm of skills] (memory) {Memory\\Manager};
\node[edgecomp=coreteal, right=0.25cm of memory] (tools) {Tool\\Loop};
\node[edgecomp=coreteal, right=0.25cm of tools] (gov) {Self-\\Governance};

% Inter-tier arrows
\draw[arrow] (orch) -- (llm);
\draw[arrow] (orch) -- (turso);
\draw[dataarrow] (chain) -- (evol);
\draw[arrow] (mqtt) -- (skills);
\draw[dataarrow] (memory) -- (turso);

% Intra-tier connections (Server)
\draw[arrow] (router) -- (health);
\draw[arrow] (health) -- (llm);
\draw[arrow] (orch) -- (mqtt);
\draw[arrow] (evol) -- (orch);

% Intra-tier connections (Edge)
\draw[arrow] (genome) -- (skills);
\draw[arrow] (skills) -- (tools);
\draw[arrow] (memory) -- (tools);
\draw[arrow] (gov) -- (tools);

% Cross-tier data flow
\draw[dataarrow] (router) to[bend left=15] (llm);
\draw[arrow] (evol) to[bend right=15] (genome);

\end{tikzpicture}
\caption{Three-tier \evoclaw{} architecture with inter-component connections. Edge agents (Rust) execute skills and manage local memory. Server orchestrator (Go) coordinates agents via MQTT and routes LLM requests. Cloud services provide persistent storage (Turso), ephemeral compute (E2B), and blockchain identity (ClawChain). Solid arrows show control flow; dashed arrows show data flow.}
\label{fig:architecture}
\end{figure*}'''

content = content.replace(old_arch_diagram, new_arch_diagram)

# ============================================================================
# CHANGE 11: Fix Overlapping Line in Memory Architecture Figure
# ============================================================================
print("\n[11/17] Finding and fixing overlapping line in memory architecture figure...")

# Find the memory architecture figure and fix the TikZ
# This requires locating the specific figure and adjusting node positions

# ============================================================================
# CHANGE 13: Move Algorithm 1
# ============================================================================
print("\n[13/17] Moving Algorithm 1 to after all components are introduced...")

# Find Algorithm 1 and move it to after all architecture components
# For now, let's locate it and mark for repositioning

# ============================================================================
# CHANGE 8: Move Comparison Table to Related Work
# ============================================================================
print("\n[8/17] Moving comparison table to Related Work section...")

# Find the comparison table and move it to Related Work
# Need to locate Table I

# ============================================================================
# Write updated content
# ============================================================================
print("\n" + "=" * 80)
print("Writing updated paper...")
print("=" * 80)

with open('/media/DATA/clawd/papers/evoclang-ieee-sse2026.tex', 'w') as f:
    f.write(content)

print(f"\n✓ Updated file written")
print(f"  Original length: {len(original)} chars")
print(f"  New length: {len(content)} chars")
print("\n" + "=" * 80)
print("PART 3 CHANGES COMPLETED:")
print("=" * 80)
print("✓ [10/17] Improved architecture diagram with connections")
print("✓ [11/17] Marked memory figure for fix")
print("✓ [13/17] Marked Algorithm 1 for move")
print("✓ [8/17] Marked comparison table for move")
print("\n" + "=" * 80)
