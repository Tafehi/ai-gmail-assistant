from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.llm.agent import (
    PROVIDERS,
    check_provider_credentials,
    create_agent,
    load_skills_as_system_prompt,
)

app = FastAPI(title="AI Gmail Assistant")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

agents_cache: dict[str, object] = {}


class ChatRequest(BaseModel):
    message: str
    provider: str
    model: str
    history: list[dict] = []


@app.get("/")
async def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/api/providers")
async def get_providers():
    return PROVIDERS


@app.get("/api/status")
async def get_status():
    token_exists = Path("token.json").exists()
    return {
        "gmail_authenticated": token_exists,
    }


@app.post("/api/chat")
async def chat(req: ChatRequest):
    cred_error = check_provider_credentials(req.provider)
    if cred_error:
        return {"error": cred_error}

    if not Path("token.json").exists():
        return {"error": "Gmail not authenticated. Run 'gmail-cleaner auth' first."}

    cache_key = f"{req.provider}:{req.model}"
    if cache_key not in agents_cache:
        agent = create_agent(req.provider, req.model)
        if agent is None:
            return {"error": f"Could not create agent for {req.provider}"}
        agents_cache[cache_key] = agent

    agent = agents_cache[cache_key]

    try:
        from langchain_core.messages import AIMessage, HumanMessage

        messages = []
        for m in req.history:
            if m["role"] == "user":
                messages.append(HumanMessage(content=m["content"]))
            elif m["role"] == "assistant":
                messages.append(AIMessage(content=m["content"]))
        messages.append(HumanMessage(content=req.message))

        result = agent.invoke({"messages": messages}, config={"recursion_limit": 50})

        # Extract the final AI response (skip tool messages)
        response = ""
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and msg.content:
                if isinstance(msg.content, list):
                    # Handle structured content blocks
                    text_parts = [b["text"] for b in msg.content if isinstance(b, dict) and b.get("type") == "text"]
                    if text_parts:
                        response = "\n".join(text_parts)
                        break
                elif isinstance(msg.content, str) and msg.content.strip():
                    response = msg.content
                    break

        if not response:
            response = "Action completed but no summary was provided by the model."

        return {"response": response}
    except Exception as e:
        import traceback
        error_msg = str(e) or repr(e)
        traceback.print_exc()
        return {"error": f"{type(e).__name__}: {error_msg}"}


@app.post("/api/auth")
async def authenticate():
    try:
        from src.gmail.auth import get_credentials
        from src.gmail.config import load_config

        config = load_config()
        get_credentials(config.credentials_path, config.token_path)
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
