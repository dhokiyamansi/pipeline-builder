# backend/main.py


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List
from collections import defaultdict, deque

app = FastAPI(title="VectorShift Pipeline API")

# ── CORS — allow the React dev server ────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request schema ────────────────────────────────────────────────────────────
class Pipeline(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


# ── DAG check using Kahn's algorithm (BFS topological sort) ──────────────────
def check_is_dag(nodes: List[Dict], edges: List[Dict]) -> bool:
    """
    Returns True iff the directed graph formed by nodes + edges is a DAG
    (Directed Acyclic Graph — i.e. has no cycles).

    Uses Kahn's algorithm:
      1. Compute in-degree for every node.
      2. Enqueue all nodes with in-degree 0.
      3. BFS: for each dequeued node, reduce neighbours' in-degree by 1;
         enqueue those that reach 0.
      4. If the number of visited nodes equals the total node count → DAG.
         Otherwise a cycle exists.
    """
    if not nodes:
        return True  # empty graph is trivially a DAG

    node_ids   = {n["id"] for n in nodes}
    adj        = defaultdict(list)   # source → [targets]
    in_degree  = defaultdict(int)    # node_id → in-degree count

    # Initialise in-degree to 0 for every node
    for nid in node_ids:
        in_degree[nid] = 0

    # Populate adjacency list + in-degree from edges
    for edge in edges:
        src = edge.get("source")
        tgt = edge.get("target")
        if src in node_ids and tgt in node_ids:
            adj[src].append(tgt)
            in_degree[tgt] += 1

    # BFS from all zero-in-degree nodes
    queue   = deque(nid for nid in node_ids if in_degree[nid] == 0)
    visited = 0

    while queue:
        nid = queue.popleft()
        visited += 1
        for neighbour in adj[nid]:
            in_degree[neighbour] -= 1
            if in_degree[neighbour] == 0:
                queue.append(neighbour)

    return visited == len(node_ids)


# ── Endpoint ──────────────────────────────────────────────────────────────────
@app.post("/pipelines/parse")
def parse_pipeline(pipeline: Pipeline):
    nodes = pipeline.nodes
    edges = pipeline.edges

    return {
        "num_nodes": len(nodes),
        "num_edges": len(edges),
        "is_dag":    check_is_dag(nodes, edges),
    }


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "message": "VectorShift Pipeline API is running."}