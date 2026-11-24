# pipeline-builder (backend)

FastAPI backend for a node-based pipeline builder. The frontend sends the pipeline's nodes and edges, and the API returns how many there are and whether the graph is a **DAG** (has no cycles), so the editor can reject pipelines that would loop forever.

## API

`POST /pipelines/parse`

```json
// request
{
  "nodes": [{ "id": "input" }, { "id": "llm" }, { "id": "output" }],
  "edges": [
    { "source": "input", "target": "llm" },
    { "source": "llm", "target": "output" }
  ]
}

// response
{ "num_nodes": 3, "num_edges": 2, "is_dag": true }
```

`GET /` is a health check.

## The DAG check

`check_is_dag` in [`backend/main.py`](backend/main.py) uses **Kahn's algorithm** (a BFS topological sort):

1. Count each node's in-degree (its incoming edges).
2. Put every node with in-degree 0 in a queue.
3. Take nodes off the queue one at a time. For each outgoing edge, lower the target's in-degree by 1, and queue the target when it reaches 0.
4. If every node was visited, the graph is a DAG. If some never reached in-degree 0, they're part of a cycle.

This runs in O(V + E). Edges that point to unknown node IDs are ignored, and an empty pipeline counts as a valid DAG.

## Run it

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload       # http://localhost:8000, docs at /docs
```

Try it:

```bash
curl -X POST http://localhost:8000/pipelines/parse \
  -H "Content-Type: application/json" \
  -d '{"nodes":[{"id":"a"},{"id":"b"}],"edges":[{"source":"a","target":"b"},{"source":"b","target":"a"}]}'
# {"num_nodes":2,"num_edges":2,"is_dag":false}
```

CORS is open to `http://localhost:3000` for a local React frontend.

## Stack
Python · FastAPI · Pydantic · Uvicorn
