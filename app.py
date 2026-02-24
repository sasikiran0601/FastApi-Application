from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests

app = FastAPI()

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

WEBHOOK = "https://n8n.n8nautomations.me/webhook/51b66e9e-15d3-4418-a304-030d357e35a2"

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
def chat(body: ChatRequest):
    query = body.query.strip()

    if not query:
        raise HTTPException(status_code=400, detail="Empty query")

    try:
        resp = requests.post(
            WEBHOOK,
            json={"chatInput": query},  # IMPORTANT: matches your n8n input field
            timeout=30
        )

        print("Webhook status:", resp.status_code)
        print("Webhook response:", resp.text)

        try:
            result = resp.json()
            answer = result if isinstance(result, str) else result.get("output", result)
        except Exception:
            answer = resp.text

        return {"answer": answer}

    except Exception as e:
        print("ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

