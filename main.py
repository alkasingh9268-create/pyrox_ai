import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

API_KEY = os.environ.get("GROQ_API_KEY") or ""

class ChatRequest(BaseModel):
    message: str

@app.get("/api/check-model")
async def check_model():
    """Groq API se puchta hai ki kaun sa Llama model active hai"""
    if not API_KEY:
        return {"active_model": "API Key Missing!"}
    try:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        res = requests.get("https://api.groq.com/openai/v1/models", headers=headers, timeout=5)
        if res.status_code == 200:
            models = res.json().get("data", [])
            for m in models:
                mid = m.get("id", "")
                if "llama" in mid.lower():
                    return {"active_model": mid}
            if models:
                return {"active_model": models[0]["id"]}
    except Exception as e:
        print("Model fetch error:", e)
    return {"active_model": "llama-3.1-70b-versatile"}

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    if not API_KEY:
        raise HTTPException(status_code=400, detail="Groq API Key missing!")
    
    model_data = await check_model()
    active_model = model_data.get("active_model", "llama-3.1-70b-versatile")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": active_model,
        "messages": [
            {"role": "system", "content": "You are Pyrox, an advanced Gen-Z AI assistant for India. Talk in natural Hinglish with cool emojis ✨."},
            {"role": "user", "content": req.message}
        ],
        "temperature": 0.7,
        "max_tokens": 512
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            res_json = response.json()
            reply = res_json['choices'][0]['message']['content']
            return {"reply": reply, "audio_url": None}
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
async def read_index():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "index.html missing!"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
