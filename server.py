import os, uuid
from fastapi import FastAPI, Header
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Kimi-Coze Mailbox")

TOKEN = os.getenv("BOX_TOKEN", "demo-token-change-me")
messages = []

class Msg(BaseModel):
    from_who: str
    to_who: str
    text: str
    img: str = None

@app.post("/drop")
def drop(m: Msg, x_token: str = Header(None)):
    if x_token != TOKEN:
        return {"err": "bad token"}
    entry = {"id": str(uuid.uuid4())[:8], **m.dict(), "status": "new"}
    messages.append(entry)
    if len(messages) > 50:
        messages.pop(0)
    return {"ok": True, "id": entry["id"]}

@app.get("/pick")
def pick(who: str, x_token: str = Header(None)):
    if x_token != TOKEN:
        return {"err": "bad token"}
    for i in range(len(messages) - 1, -1, -1):
        if messages[i]["to_who"] == who and messages[i]["status"] == "new":
            messages[i]["status"] = "read"
            return {"found": True, "msg": messages[i]}
    return {"found": False}

@app.get("/pick_batch")
def pick_batch(who: str, x_token: str = Header(None)):
    """批量取走所有 pending 信件（方案2优化）"""
    if x_token != TOKEN:
        return {"err": "bad token"}
    collected = []
    for msg in messages:
        if msg["to_who"] == who and msg["status"] == "new":
            msg["status"] = "read"
            collected.append(msg)
    return {
        "found": len(collected) > 0,
        "count": len(collected),
        "msgs": collected
    }

@app.get("/peek")
def peek(who: str, x_token: str = Header(None)):
    if x_token != TOKEN:
        return {"err": "bad token"}
    for i in range(len(messages) - 1, -1, -1):
        if messages[i]["to_who"] == who and messages[i]["status"] == "new":
            return {"found": True, "msg": messages[i]}
    return {"found": False}

@app.get("/health")
def health():
    pending_kimi = len([m for m in messages if m["to_who"] == "kimi" and m["status"] == "new"])
    pending_coze = len([m for m in messages if m["to_who"] == "coze" and m["status"] == "new"])
    return {"alive": True, "pending_kimi": pending_kimi, "pending_coze": pending_coze}

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
