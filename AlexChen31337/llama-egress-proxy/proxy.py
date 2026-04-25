#!/usr/bin/env python3
"""
llama-egress-proxy -- streaming hygiene proxy for llama-server.

Listens:  0.0.0.0:8082
Upstream: http://127.0.0.1:8080

Routes:
  POST /v1/chat/completions  -- sanitise choices[].message.content / delta.content
  POST /v1/completions       -- sanitise choices[].text
  GET  /health               -- proxy + upstream status
  *    /*                    -- transparent pass-through
"""

import json
import logging

import aiohttp
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse

from sanitize import sanitize

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("egress-proxy")

UPSTREAM = "http://127.0.0.1:8080"
STREAM_OVERLAP = 512  # rolling buffer overlap for cross-chunk tag detection

app = FastAPI(title="llama-egress-proxy")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sanitize_chat_response(data: dict) -> dict:
    for choice in data.get("choices", []):
        msg = choice.get("message")
        if isinstance(msg, dict) and "content" in msg and msg["content"]:
            msg["content"] = sanitize(msg["content"])
    return data


def _sanitize_completions_response(data: dict) -> dict:
    for choice in data.get("choices", []):
        if "text" in choice and choice["text"]:
            choice["text"] = sanitize(choice["text"])
    return data


async def _stream_sanitized(upstream_response) -> "AsyncGenerator[bytes, None]":
    """
    Yield SSE lines, sanitising delta.content across chunk boundaries.
    Uses a rolling buffer to catch tags split across packet boundaries.
    """
    buffer = ""
    async for raw_chunk in upstream_response.content:
        chunk_str = raw_chunk.decode("utf-8", errors="replace")
        buffer += chunk_str

        # Process complete SSE lines (ending with \n)
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.rstrip("\r")

            if line.startswith("data: "):
                payload = line[6:]
                if payload.strip() == "[DONE]":
                    yield b"data: [DONE]\n\n"
                    continue
                try:
                    obj = json.loads(payload)
                    # Sanitise delta.content for chat completions
                    for choice in obj.get("choices", []):
                        delta = choice.get("delta", {})
                        if delta.get("content"):
                            delta["content"] = sanitize(delta["content"])
                        # Also handle text field for /v1/completions streaming
                        if choice.get("text"):
                            choice["text"] = sanitize(choice["text"])
                    yield f"data: {json.dumps(obj)}\n\n".encode()
                except json.JSONDecodeError:
                    # Non-JSON SSE line -- pass through unchanged
                    yield f"data: {payload}\n\n".encode()
            elif line == "":
                # Empty line (SSE event separator) -- skip, we emit our own
                pass
            else:
                # Non-data SSE fields (event:, id:, retry:) -- pass through
                yield f"{line}\n".encode()

    # Flush remaining buffer
    if buffer.strip():
        yield buffer.encode()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    upstream_ok = False
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{UPSTREAM}/health", timeout=aiohttp.ClientTimeout(total=3)) as r:
                upstream_ok = r.status < 500
    except Exception:
        pass
    return {
        "proxy": "ok",
        "upstream": "ok" if upstream_ok else "unreachable",
        "upstream_ok": upstream_ok,
        "upstream_url": UPSTREAM,
        "listen": "0.0.0.0:8082",
    }


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy(request: Request, path: str):
    upstream_url = f"{UPSTREAM}/{path}"
    body = await request.body()
    headers = {k: v for k, v in request.headers.items()
               if k.lower() not in ("host", "content-length")}

    # Determine if this is a sanitisable endpoint
    is_chat = path in ("v1/chat/completions",)
    is_completions = path in ("v1/completions",)
    is_sanitisable = is_chat or is_completions

    # Parse request to check for stream flag
    is_stream = False
    req_data = {}
    if is_sanitisable and body:
        try:
            req_data = json.loads(body)
            is_stream = bool(req_data.get("stream", False))
        except json.JSONDecodeError:
            pass

    timeout = aiohttp.ClientTimeout(total=300, connect=10)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        upstream_req = session.request(
            method=request.method,
            url=upstream_url,
            headers=headers,
            data=body,
            params=dict(request.query_params),
        )

        async with upstream_req as upstream_resp:
            resp_headers = {k: v for k, v in upstream_resp.headers.items()
                            if k.lower() not in ("content-encoding", "transfer-encoding", "content-length")}

            if is_sanitisable and is_stream:
                # Streaming: sanitise delta.content on the fly
                return StreamingResponse(
                    _stream_sanitized(upstream_resp),
                    status_code=upstream_resp.status,
                    headers=resp_headers,
                    media_type="text/event-stream",
                )

            elif is_sanitisable and not is_stream:
                # Non-streaming: parse, sanitise, return
                raw = await upstream_resp.read()
                try:
                    data = json.loads(raw)
                    if is_chat:
                        data = _sanitize_chat_response(data)
                    else:
                        data = _sanitize_completions_response(data)
                    sanitised = json.dumps(data).encode()
                    resp_headers["content-length"] = str(len(sanitised))
                    return Response(
                        content=sanitised,
                        status_code=upstream_resp.status,
                        headers=resp_headers,
                        media_type="application/json",
                    )
                except json.JSONDecodeError:
                    # Not JSON -- pass through raw
                    return Response(
                        content=raw,
                        status_code=upstream_resp.status,
                        headers=resp_headers,
                    )

            else:
                # Pass-through for all other endpoints
                raw = await upstream_resp.read()
                return Response(
                    content=raw,
                    status_code=upstream_resp.status,
                    headers=resp_headers,
                )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082, log_level="info")
