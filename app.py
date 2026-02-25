from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

import httpx  # async HTTP client — does NOT block the event loop

app = FastAPI()

# Trust proxy headers (e.g. X-Forwarded-Proto: https) from the reverse proxy.
# This ensures url_for() generates https:// URLs — fixes Mixed Content errors.
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# CORS — allow frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files & templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Request body model
class ChatRequest(BaseModel):
    query: str

# n8n webhook URL — matches the Webhook node path in the workflow
WEBHOOK = "https://n8n.n8nautomations.me/webhook/51b66e9e-15d3-4418-a304-030d357e35a2"


def extract_answer(result) -> str:
    """
    Safely extract a plain-text answer from the n8n response.

    n8n can return any of:
      - str              → use as-is
      - {"output": "…"} → extract "output"
      - [{"output":"…"}]→ extract first item's "output"
      - anything else   → stringify it
    """
    if isinstance(result, str):
        return result

    if isinstance(result, list):
        # Some n8n versions wrap the response in a list
        result = result[0] if result else {}

    if isinstance(result, dict):
        # Primary key returned by the "Respond to Webhook" node
        answer = result.get("output") or result.get("answer") or result.get("text", "")
        return str(answer) if answer else str(result)

    return str(result)


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/chat")
async def chat(body: ChatRequest):
    query = body.query.strip()

    if not query:
        raise HTTPException(status_code=400, detail="Empty query")

    # ── Payload ──────────────────────────────────────────────────────────────
    # The n8n Rag Question node accesses: {{ $json.body.query }}
    # The n8n AI Agent prompt accesses:   {{ $json.body }}
    # Both are satisfied by sending: {"query": "<user question>"}
    payload = {"query": query}

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(WEBHOOK, json=payload)

        print(f"[n8n] status={resp.status_code}  body={resp.text[:300]}")

        # Surface n8n errors clearly instead of silently swallowing them
        if resp.status_code not in (200, 201):
            raise HTTPException(
                status_code=502,
                detail=f"n8n webhook returned HTTP {resp.status_code}: {resp.text[:200]}"
            )

        try:
            result = resp.json()
        except Exception:
            # n8n returned plain text (rare, but possible)
            result = resp.text

        answer = extract_answer(result)
        return {"answer": answer}

    except httpx.TimeoutException:
        print("ERROR: n8n webhook timed out")
        raise HTTPException(status_code=504, detail="The AI backend took too long to respond. Please try again.")

    except HTTPException:
        raise  # re-raise our own 502/504

    except Exception as e:
        print(f"ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)