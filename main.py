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

API_KEY = os.environ.get("GROQ_API_KEY", "").strip()

class ChatRequest(BaseModel):
    message: str

@app.get("/api/check-model")
async def check_model():
    if not API_KEY:
        return {"active_model": "API Key Missing in Render Environment!"}
    try:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        res = requests.get("https://api.groq.com/openai/v1/models", headers=headers, timeout=5)
        if res.status_code == 200:
            models = res.json().get("data", [])
            for m in models:
                mid = m.get("id", "")
                if "llama-3.3" in mid.lower():
                    return {"active_model": mid}
            for m in models:
                mid = m.get("id", "")
                if "llama" in mid.lower() and "guard" not in mid.lower() and ("70b" in mid.lower() or "8b" in mid.lower()):
                    return {"active_model": mid}
    except Exception as e:
        print("Model fetch error:", e)
    
    return {"active_model": "llama-3.3-70b-versatile"}

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
    active_model = model_data.get("active_model", "llama-3.3-70b-versatile")
    
    if "guard" in active_model.lower() or "3.1-70b" in active_model.lower():
        active_model = "llama-3.3-70b-versatile"

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
                "audio_url": f"/{audio_path}?t={asyncio.get_event_loop().time()}" if success else None
            }
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
async def read_index():
    html_content = """<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pyrox Studio</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background-color: #000000; color: #ffffff; display: flex; height: 100vh; overflow: hidden; }
        .sidebar { width: 0px; background-color: #050505; border-right: none; display: flex; flex-direction: column; justify-content: space-between; padding: 0px; z-index: 20; overflow: hidden; transition: width 0.3s ease, padding 0.3s ease, border-right 0.3s ease; }
        .sidebar.expanded { width: 230px; padding: 12px 10px; border-right: 1px solid #141414; }
        .sidebar-logo-header { display: flex; align-items: center; gap: 12px; padding: 6px 6px; margin-bottom: 12px; }
        .sidebar-brand-name { font-size: 1.15rem; font-weight: 700; color: #ffffff; letter-spacing: 0.5px; }
        .menu-list { display: flex; flex-direction: column; gap: 4px; }
        .menu-btn { display: flex; align-items: center; gap: 12px; padding: 9px 10px; color: #aaaaaa; font-size: 13.5px; border-radius: 8px; cursor: pointer; transition: background 0.2s, color 0.2s; position: relative; white-space: nowrap; }
        .menu-btn:hover { background-color: #141414; color: #ffffff; }
        .main-container { flex: 1; display: flex; flex-direction: column; justify-content: space-between; align-items: center; height: 100vh; padding-top: 4px; padding-bottom: 8px; position: relative; }
        .top-navbar { width: 100%; display: flex; align-items: center; justify-content: space-between; padding: 6px 20px; position: relative; z-index: 10; }
        .hamburger-btn { background: transparent; border: none; color: #aaaaaa; cursor: pointer; padding: 6px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
        .center-landing-header { display: flex; flex-direction: column; align-items: center; text-align: center; gap: 6px; margin-top: 15px; }
        .brand-name-large { font-size: 2.2rem; font-weight: 800; color: #ffffff; }
        .greeting-subtext { font-size: 1.15rem; font-weight: 500; color: #888888; }
        .chat-container { width: 100%; max-width: 800px; flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; padding: 10px 15px; margin-top: 5px; }
        .message { display: flex; flex-direction: column; max-width: 82%; line-height: 1.5; font-size: 0.95rem; gap: 8px; }
        .user-message { align-self: flex-end; background-color: #1c1c1e; color: #ffffff; padding: 10px 16px; border-radius: 16px 16px 4px 16px; border: 1px solid #2d2d2d; }
        .ai-message { align-self: flex-start; background-color: #080808; color: #f0f0f0; padding: 14px 18px; border-radius: 16px 16px 16px 4px; border: 1px solid #1a1a1a; display: flex; flex-direction: column; gap: 8px; width: 100%; max-width: 100%; }
        audio { width: 100%; height: 32px; margin-top: 6px; filter: invert(100%) hue-rotate(180deg); }
        .input-wrapper { width: 100%; max-width: 800px; display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 0 15px; }
        .input-box { width: 100%; background-color: #080808; border: 1px solid #222222; border-radius: 26px; padding: 8px 16px; display: flex; align-items: center; gap: 10px; position: relative; }
        .chat-input-field { flex: 1; background: transparent; border: none; outline: none; color: #ffffff; font-size: 0.95rem; padding: 4px 0; }
        .chat-input-field::placeholder { color: #555555; }
        .arrow-submit-btn { width: 32px; height: 32px; background-color: #ffffff; color: #000000; border: none; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; }
        .footer-disclaimer { font-size: 10.5px; color: #444444; text-align: center; }
    </style>
</head>
<body>
    <div class="sidebar" id="sidebar">
        <div>
            <div class="sidebar-logo-header"><span class="sidebar-brand-name">Pyrox</span></div>
            <div class="menu-list"><div class="menu-btn" onclick="clearChat()"><span>New Chat</span></div></div>
        </div>
    </div>
    <div class="main-container">
        <div class="top-navbar"><button type="button" class="hamburger-btn" onclick="toggleSidebar()">☰</button></div>
        <div class="center-landing-header" id="landingHeader">
            <span class="brand-name-large">Pyrox</span>
            <div class="greeting-subtext">Hi, how can I help you today?</div>
        </div>
        <div class="chat-container" id="chatContainer"></div>
        <div class="input-wrapper">
            <div class="input-box" id="inputBox">
                <input type="text" id="chatInput" class="chat-input-field" placeholder="Ask Pyrox anything..." onkeypress="if(event.key==='Enter'){ event.preventDefault(); triggerSend(); }" />
                <button type="button" class="arrow-submit-btn" onclick="triggerSend(event)">→</button>
            </div>
            <div class="footer-disclaimer">Pyrox is AI and can make mistakes</div>
        </div>
    </div>
    <script>
        function toggleSidebar() { document.getElementById('sidebar').classList.toggle('expanded'); }
        async function triggerSend(e) {
            if(e) e.preventDefault();
            const inputField = document.getElementById('chatInput');
            const text = inputField.value.trim();
            if(!text) return;
            inputField.value = '';
            document.getElementById('landingHeader').style.display = 'none';
            appendMsg('user', text);
            const aiDiv = appendMsg('ai', '⚡ Pyrox सोच रहा है...');
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                const data = await response.json();
                if(response.ok) {
                    let htmlContent = `<div>${data.reply}</div>`;
                    if(data.audio_url) {
                        htmlContent += `<audio controls autoplay><source src="${data.audio_url}?t=${new Date().getTime()}" type="audio/mp3"></audio>`;
                    }
                    aiDiv.innerHTML = htmlContent;
                } else {
                    aiDiv.innerText = "⚠️ Error: " + (data.detail || "Something went wrong");
                }
            } catch(e) {
                aiDiv.innerText = "⚠️ Network Exception: " + e.message;
            }
        }
        function appendMsg(role, content) {
            const container = document.getElementById('chatContainer');
            const div = document.createElement('div');
            div.className = 'message ' + (role === 'user' ? 'user-message' : 'ai-message');
            div.innerText = content;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
            return div;
        }
        function clearChat() {
            document.getElementById('chatContainer').innerHTML = '';
            document.getElementById('landingHeader').style.display = 'flex';
        }
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content, status_code=200)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
