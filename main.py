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

# Render Environment Variable से सुरक्षित तरीके से की उठाएगा
API_KEY = os.environ.get("GROQ_API_KEY", "").strip()

class ChatRequest(BaseModel):
    message: str

@app.get("/api/check-model")
async def check_model():
    """Groq API से चेक करेगा कि कौन सा जेनरेटिव Llama मॉडल एक्टिव है"""
    if not API_KEY:
        return {"active_model": "API Key Missing in Render Environment!"}
    try:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        res = requests.get("https://api.groq.com/openai/v1/models", headers=headers, timeout=5)
        if res.status_code == 200:
            models = res.json().get("data", [])
            # क्लासिफायर/गार्ड मॉडल को छोड़कर सही चैट मॉडल पकड़ेगा
            for m in models:
                mid = m.get("id", "")
                if "llama" in mid.lower() and "guard" not in mid.lower() and ("70b" in mid.lower() or "8b" in mid.lower()):
                    return {"active_model": mid}
            for m in models:
                mid = m.get("id", "")
                if "llama" in mid.lower() and "guard" not in mid.lower():
                    return {"active_model": mid}
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
        raise HTTPException(status_code=400, detail="Groq API Key missing in environment variables!")
    
    model_data = await check_model()
    active_model = model_data.get("active_model", "llama-3.1-70b-versatile")
    if "guard" in active_model.lower():
        active_model = "llama-3.1-70b-versatile"

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
                "audio_url": f"/{audio_path}" if success else None
            }
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
async def read_index():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "index.html file missing!"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
