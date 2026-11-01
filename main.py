import os
import asyncio
import requests
import edge_tts
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
    """Groq API से खुद चेक करेगा कि इस समय कौन सा Llama मॉडल एक्टिव है"""
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

async def generate_edge_audio(text, filename="static/response.mp3"):
    try:
        clean_t = (
            text.replace("*", "")
            .replace("#", "")
            .replace("`", "")
            .replace("✨", "")
            .replace("👋", "")
            .replace("🚀", "")
            .replace("💻", "")
            .replace("😎", "")
            .replace("💡", "")
            .replace("🎯", "")
        )
        communicate = edge_tts.Communicate(clean_t, "hi-IN-MadhurNeural")
        await communicate.save(filename)
        return True
    except Exception as e:
        print("TTS Error:", e)
        return False

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    if not API_KEY:
        raise HTTPException(status_code=400, detail="Groq API Key missing!")
    
    # ऑटोमैटिक वर्किंग मॉडल उठाएगा
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
            {
                "role": "system",
                "content": "You are Pyrox, an advanced Gen-Z AI assistant created for users in India (specifically Delhi context). Talk in a smooth mix of natural Hindi and English (Hinglish) with cool emojis ✨."
            },
            {
                "role": "user",
                "content": req.message
            }
        ],
        "temperature": 0.7,
        "max_tokens": 512
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            res_json = response.json()
            reply = res_json['choices'][0]['message']['content']
            
            audio_path = "static/response.mp3"
            success = await generate_edge_audio(reply, audio_path)
            
            return {
                "reply": reply,
