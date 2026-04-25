# llama-egress-proxy

A lightweight FastAPI + aiohttp proxy that strips OpenClaw internal-context wrapper tags from llama-server output.

## Architecture

```
OpenClaw (dev box)
    |  HTTP -> 10.0.0.30:8082
    v
llama-egress-proxy  (0.0.0.0:8082)   <- this service
    |  forward to 127.0.0.1:8080
    v
llama-server        (127.0.0.1:8080)
    |  model: Qwen3.6-35B-A3B-Q6_K_P.gguf
```

## Deploy (from dev box when GPU server is reachable)

```bash
cd AlexChen31337/llama-egress-proxy
bash deploy.sh
# Then update OpenClaw:
openclaw config patch models.providers.gpu-server-35b.baseUrl http://10.0.0.30:8082
```

## What it strips

Applied to choices[].message.content (non-streaming) and choices[].delta.content (streaming SSE).
A rolling buffer handles tags split across SSE chunk boundaries.

| # | Pattern |
|---|---------|
| 1 | system-reminder tags |
| 2 | BEGIN_OPENCLAW_INTERNAL_CONTEXT wrappers |
| 3 | EXTERNAL_UNTRUSTED_CONTENT wrappers |
| 4 | tool_result blobs |
| 5 | Conversation info (untrusted metadata) + JSON block |
| 6 | Sender (untrusted metadata) + JSON block |
| 7 | Inter-session message lines |
| 8 | function= orphan XML |
| 9 | parameter= orphan XML |

## Endpoints

- `POST /v1/chat/completions` -- sanitised (stream and non-stream)
- `POST /v1/completions` -- sanitised (stream and non-stream)
- `GET /health` -- proxy + upstream status
- All other paths -- transparent pass-through

## Manage on GPU server

```bash
journalctl --user -u llama-egress-proxy -f    # live logs
systemctl --user restart llama-egress-proxy   # restart
curl http://127.0.0.1:8082/health             # health check
```
