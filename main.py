import os
import json
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

app = FastAPI()

# Render ke Environment Variable se secure tarike se API Key uthayega
API_KEY = os.environ.get("GROQ_API_KEY")

@app.get("/", response_class=HTMLResponse)
async def serve_home():
    # index.html file ko padhkar browser ko dikhayega
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"<h3>Error loading index.html: {str(e)}</h3>"

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    user_prompt = data.get("message", "")
    
    if not API_KEY:
        return {"reply": "⚠️ Groq API Key missing in Render Environment Variables!"}
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": "You are Pyrox, an advanced, highly intelligent, and Gen-Z friendly AI assistant. Talk in a smooth mix of natural Hindi and English (Hinglish) with cool emojis ✨. Give crisp, highly accurate, and engaging answers."
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 512
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        if response.status_code == 200:
            res_json = response.json()
            reply = res_json['choices'][0]['message']['content']
            return {"reply": reply}
        else:
            return {"reply": f"⚠️ API Error ({response.status_code}): {response.text}"}
    except Exception as e:
        return {"reply": f"⚠️ Network Exception: {str(e)}"}
