import os
import asyncio
import requests
import edge_tts
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

# Static folder ensure karega ki audio aur assets sahi se load hon
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Render Environment Variable se API key secure tarike se uthayega
API_KEY = os.environ.get("GROQ_API_KEY", "").strip()

class ChatRequest(BaseModel):
    message: str

@app.get("/api/check-model")
async def check_model():
    """Groq API se live check karega ki is waqt teri key par kaun sa model active hai"""
    if not API_KEY:
        return {"active_model": "API Key Missing in Render Environment!"}
    try:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        res = requests.get("https://api.groq.com/openai/v1/models", headers=headers, timeout=5)
        if res.status_code == 200:
            models = res.json().get("data", [])
            # Jo bhi Llama chat model pehle mil jaye, use turant utha lo
            for m in models:
                mid = m.get("id", "")
                if "llama" in mid.lower() and "guard" not in mid.lower() and ("70b" in mid.lower() or "8b" in mid.lower() or "versatile" in mid.lower() or "instant" in mid.lower()):
                    return {"active_model": mid}
            for m in models:
                mid = m.get("id", "")
                if "llama" in mid.lower() and "guard" not in mid.lower():
                    return {"active_model": mid}
    except Exception as e:
        print("Model fetch error:", e)
    
    # Fallback agar API se list na mile toh koi bhi common model
    return {"active_model": "llama-3.1-8b-instant"}

async def generate_edge_audio(text, filename="static/response.mp3"):
    """Edge-TTS ke zariye Madhur Neural aawaz me audio banayega"""
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
    
    # Live check karega ki abhi kaun sa model chal raha hai
    model_data = await check_model()
    active_model = model_data.get("active_model", "llama-3.1-8b-instant")
    
    # Agar galti se koi decommissioned model aa jaye toh use bypass karo
    if "3.1-70b" in active_model.lower():
        active_model = "llama-3.1-8b-instant"

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
    """Tera pura original HTML, CSS, collapsible sidebar, star logo aur mic/waves ke sath"""
    html_content = """<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pyrox Studio</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background-color: #000000; color: #ffffff; display: flex; height: 100vh; overflow: hidden; }

        /* COLLAPSIBLE SIDEBAR */
        .sidebar {
            width: 0px; background-color: #050505; border-right: none;
            display: flex; flex-direction: column; justify-content: space-between;
            padding: 0px; z-index: 20; overflow: hidden;
            transition: width 0.3s ease, padding 0.3s ease, border-right 0.3s ease;
        }
        .sidebar.expanded { width: 230px; padding: 12px 10px; border-right: 1px solid #141414; }
        .sidebar-logo-header { display: flex; align-items: center; gap: 12px; padding: 6px 6px; margin-bottom: 12px; }
        .sidebar-brand-name { font-size: 1.15rem; font-weight: 700; color: #ffffff; letter-spacing: 0.5px; }
        .menu-list { display: flex; flex-direction: column; gap: 4px; }
        .menu-btn {
            display: flex; align-items: center; gap: 12px; padding: 9px 10px;
            color: #aaaaaa; font-size: 13.5px; border-radius: 8px; cursor: pointer;
            transition: background 0.2s, color 0.2s; white-space: nowrap;
        }
        .menu-btn:hover { background-color: #141414; color: #ffffff; }
        .menu-btn svg { width: 18px; height: 18px; stroke: currentColor; fill: none; stroke-width: 2; flex-shrink: 0; }
        .sidebar-bottom { border-top: 1px solid #141414; padding-top: 8px; }

        /* MAIN WORKSPACE */
        .main-container { flex: 1; display: flex; flex-direction: column; justify-content: space-between; align-items: center; height: 100vh; padding-top: 4px; padding-bottom: 8px; position: relative; }
        .top-navbar { width: 100%; display: flex; align-items: center; justify-content: space-between; padding: 6px 20px; position: relative; z-index: 10; }
        .hamburger-btn { background: transparent; border: none; color: #aaaaaa; cursor: pointer; padding: 6px; border-radius: 50%; display: flex; align-items: center; justify-content: center; transition: color 0.2s, background 0.2s; }
        .hamburger-btn:hover { color: #ffffff; background-color: #1a1a1a; }

        /* CENTER LANDING HEADER */
        .center-landing-header { display: flex; flex-direction: column; align-items: center; text-align: center; gap: 6px; margin-top: 15px; }
        .brand-title-box { display: flex; align-items: center; gap: 12px; }
        .brand-name-large { font-size: 2.2rem; font-weight: 800; color: #ffffff; letter-spacing: -0.5px; }
        .greeting-subtext { font-size: 1.15rem; font-weight: 500; color: #888888; }

        /* CHAT MESSAGES */
        .chat-container { width: 100%; max-width: 800px; flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; padding: 10px 15px; margin-top: 5px; }
        .message { display: flex; flex-direction: column; max-width: 82%; line-height: 1.5; font-size: 0.95rem; gap: 8px; }
        .user-message { align-self: flex-end; background-color: #1c1c1e; color: #ffffff; padding: 10px 16px; border-radius: 16px 16px 4px 16px; border: 1px solid #2d2d2d; }
        .ai-message { align-self: flex-start; background-color: #080808; color: #f0f0f0; padding: 14px 18px; border-radius: 16px 16px 16px 4px; border: 1px solid #1a1a1a; display: flex; flex-direction: column; gap: 8px; width: 100%; max-width: 100%; }
        audio { width: 100%; height: 32px; margin-top: 6px; filter: invert(100%) hue-rotate(180deg); }

        /* INPUT BAR */
        .input-wrapper { width: 100%; max-width: 800px; display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 0 15px; }
        .input-box {
            width: 100%; background-color: #080808; border: 1px solid #222222;
            border-radius: 26px; padding: 8px 16px; display: flex; align-items: center; gap: 10px; position: relative;
            transition: border-color 0.3s, box-shadow 0.3s;
        }
        .input-box.recording { border-color: #ef4444; box-shadow: 0 0 15px rgba(239, 68, 68, 0.25); }

        /* GEMINI WAVE BARS */
        .gemini-wave-container { display: flex; align-items: center; gap: 3.5px; height: 20px; width: 100px; display: none; }
        .gemini-wave-container.active { display: flex; }
        .wave-bar { flex: 1; background: linear-gradient(180deg, #888, #fff); border-radius: 3px; height: 20%; animation: waveMotion 0.6s infinite ease-in-out alternate; }
        .wave-bar:nth-child(1) { animation-delay: 0.1s; }
        .wave-bar:nth-child(2) { animation-delay: 0.3s; }
        .wave-bar:nth-child(3) { animation-delay: 0.2s; }
        .wave-bar:nth-child(4) { animation-delay: 0.5s; }
        .wave-bar:nth-child(5) { animation-delay: 0.15s; }
        @keyframes waveMotion { 0% { height: 15%; } 100% { height: 100%; } }

        .chat-input-field { flex: 1; background: transparent; border: none; outline: none; color: #ffffff; font-size: 0.95rem; padding: 4px 0; }
        .chat-input-field::placeholder { color: #555555; }

        .mic-btn { background: transparent; border: none; color: #aaaaaa; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: color 0.2s, transform 0.2s; }
        .mic-btn:hover { color: #ffffff; transform: scale(1.1); }
        .mic-btn.active { color: #ef4444; }

        .arrow-submit-btn {
            width: 32px; height: 32px; background-color: #ffffff; color: #000000;
            border: none; border-radius: 50%; display: flex; align-items: center; justify-content: center;
            cursor: pointer; transition: transform 0.2s, opacity 0.2s;
        }
        .arrow-submit-btn:hover { transform: scale(1.05); opacity: 0.9; }
        .footer-disclaimer { font-size: 10.5px; color: #444444; text-align: center; }
    </style>
</head>
<body>

    <!-- COLLAPSIBLE SIDEBAR -->
    <div class="sidebar" id="sidebar">
        <div>
            <div class="sidebar-logo-header">
                <svg width="28" height="28" viewBox="0 0 100 100" fill="none" stroke="#ffffff" stroke-width="4" stroke-linejoin="round">
                    <polygon points="50,5 63,35 95,38 71,60 78,92 50,75 22,92 29,60 5,38 37,35" stroke-width="5" opacity="1.0" />
                    <polygon points="50,22 59,42 80,44 64,59 69,80 50,68 31,80 36,59 20,44 41,42" stroke-width="3" opacity="0.65" />
                    <polygon points="50,34 55,47 68,48 58,58 61,71 50,63 39,71 42,58 32,48 45,47" stroke-width="2" opacity="0.35" fill="#ffffff" />
                </svg>
                <span class="sidebar-brand-name">Pyrox</span>
            </div>
            <div class="menu-list">
                <div class="menu-btn" onclick="clearChat()">
                    <svg viewBox="0 0 24 24"><path d="M12 4v16m8-8H4"></path></svg>
                    <span>New Chat</span>
                </div>
            </div>
        </div>
    </div>

    <!-- MAIN CONTAINER -->
    <div class="main-container">
        <div class="top-navbar">
            <button type="button" class="hamburger-btn" onclick="toggleSidebar()">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="3" y1="12" x2="21" y2="12"></line>
                    <line x1="3" y1="6" x2="21" y2="6"></line>
                    <line x1="3" y1="18" x2="21" y2="18"></line>
                </svg>
            </button>
        </div>

        <!-- CENTER LANDING HEADER WITH STAR LOGO -->
        <div class="center-landing-header" id="landingHeader">
            <div class="brand-title-box">
                <svg width="52" height="52" viewBox="0 0 100 100" fill="none" stroke="#ffffff" stroke-linejoin="round">
                    <polygon points="50,5 63,35 95,38 71,60 78,92 50,75 22,92 29,60 5,38 37,35" stroke-width="4.5" opacity="1.0" />
                    <polygon points="50,22 59,42 80,44 64,59 69,80 50,68 31,80 36,59 20,44 41,42" stroke-width="3" opacity="0.6" />
                    <polygon points="50,34 55,47 68,48 58,58 61,71 50,63 39,71 42,58 32,48 45,47" stroke-width="2" opacity="0.3" fill="#ffffff" />
                </svg>
                <span class="brand-name-large">Pyrox</span>
            </div>
            <div class="greeting-subtext">Hi, how can I help you today?</div>
        </div>

        <div class="chat-container" id="chatContainer"></div>

        <div class="input-wrapper">
            <div class="input-box" id="inputBox">
                <button type="button" id="micBtn" class="mic-btn" onclick="toggleVoice(event)">
                    <svg id="micIconSvg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                        <line x1="12" y1="19" x2="12" y2="23"></line>
                    </svg>
                </button>

                <div class="gemini-wave-container" id="waveBox">
                    <div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div>
                </div>

                <input type="text" id="chatInput" class="chat-input-field" placeholder="Ask Pyrox anything..." onkeypress="if(event.key==='Enter'){ event.preventDefault(); triggerSend(); }" />

                <button type="button" class="arrow-submit-btn" onclick="triggerSend(event)">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                        <line x1="5" y1="12" x2="19" y2="12"></line>
                        <polyline points="12 5 19 12 12 19"></polyline>
                    </svg>
                </button>
            </div>
            <div class="footer-disclaimer">Pyrox is AI and can make mistakes</div>
        </div>
    </div>

    <script>
        let isListening = false;
        let recognition = null;
        let accumulatedSpeech = "";

        function toggleSidebar() {
            document.getElementById('sidebar').classList.toggle('expanded');
        }

        function toggleVoice(e) {
            if(e) e.preventDefault();
            const micBtn = document.getElementById('micBtn');
            const micSvg = document.getElementById('micIconSvg');
            const inputBox = document.getElementById('inputBox');
            const waveBox = document.getElementById('waveBox');
            const inputField = document.getElementById('chatInput');

            if (isListening) {
                if (recognition) recognition.stop();
                stopVoiceUI();
                return;
            }

            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                alert("Speech recognition not supported in your browser.");
                return;
            }

            recognition = new SpeechRecognition();
            recognition.lang = 'hi-IN';
            recognition.continuous = true;
            recognition.interimResults = true;

            accumulatedSpeech = inputField.value ? inputField.value + " " : "";

            recognition.onstart = function() {
                isListening = true;
                micBtn.classList.add('active');
                inputBox.classList.add('recording');
                waveBox.classList.add('active');
                inputField.placeholder = "Listening continuously...";
                micSvg.innerHTML = `<rect x="6" y="4" width="4" height="16" fill="currentColor"/><rect x="14" y="4" width="4" height="16" fill="currentColor"/>`;
            };

            recognition.onresult = function(event) {
                let interim = '';
                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    if (event.results[i].isFinal) {
                        accumulatedSpeech += event.results[i][0].transcript + " ";
                    } else {
                        interim += event.results[i][0].transcript;
                    }
                }
                inputField.value = accumulatedSpeech + interim;
            };

            recognition.onend = function() {
                if (isListening) { try { recognition.start(); } catch(e) {} }
            };

            try { recognition.start(); } catch(e) {}
        }

        function stopVoiceUI() {
            isListening = false;
            const micBtn = document.getElementById('micBtn');
            const micSvg = document.getElementById('micIconSvg');
            micBtn.classList.remove('active');
            document.getElementById('inputBox').classList.remove('recording');
            document.getElementById('waveBox').classList.remove('active');
            document.getElementById('chatInput').placeholder = "Ask Pyrox anything...";
            micSvg.innerHTML = `<path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line>`;
        }

        async function triggerSend(e) {
            if(e) e.preventDefault();
            if (isListening && recognition) { recognition.stop(); stopVoiceUI(); }
            
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
