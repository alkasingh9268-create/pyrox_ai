import os
import asyncio
import re
import requests
import edge_tts
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
SERP_API_KEY = os.environ.get("SERPAPI_API_KEY", "").strip()

class ChatRequest(BaseModel):
    message: str
    voice: str = "hi-IN-MadhurNeural"
    user_name: str = "Master Creator"
    student_mode: str = "General"

def get_live_groq_model():
    if not API_KEY:
        return None, "GROQ_API_KEY Missing in Render Environment!"
    
    url = "https://api.groq.com/openai/v1/models"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            models_data = res.json().get("data", [])
            valid_ids = [m.get("id") for m in models_data if m.get("id")]
            
            chat_models = [
                m_id for m_id in valid_ids 
                if "guard" not in m_id.lower() and "whisper" not in m_id.lower()
            ]
            
            if chat_models:
                for priority in ["llama", "gpt-oss", "qwen"]:
                    for m_id in chat_models:
                        if priority in m_id.lower():
                            return m_id, f"Success (Picked {m_id})"
                return chat_models[0], f"Success (Picked {chat_models[0]})"
            
            return "llama-3.3-70b-versatile", "Fallback Model"
        else:
            return "llama-3.3-70b-versatile", "Fallback Model due to API status"
    except Exception as e:
        return "llama-3.3-70b-versatile", f"Fallback due to error: {str(e)}"

def search_live_web(query: str) -> str:
    if not SERP_API_KEY:
        return ""
    try:
        url = f"https://serpapi.com/search.json?q={requests.utils.quote(query)}&api_key={SERP_API_KEY}&hl=hi&gl=in"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            organic = data.get("organic_results", [])
            snippets = [item.get("snippet", "") for item in organic[:3] if item.get("snippet")]
            return " ".join(snippets)
    except Exception as e:
        print("SerpApi Error:", e)
    return ""

@app.get("/api/debug")
async def debug_key():
    model, status = get_live_groq_model()
    return JSONResponse({
        "status": status,
        "active_working_model": model,
        "groq_key_present": bool(API_KEY),
        "serp_key_present": bool(SERP_API_KEY)
    })

async def generate_edge_audio(text, voice_name="hi-IN-MadhurNeural", filename="static/response.mp3"):
    try:
        clean_t = re.sub(r'[^\w\s.,!?-]', '', text)
        clean_t = clean_t.replace("*", "").replace("#", "").replace("`", "").replace("~", "")
        # Ensure full words are spoken cleanly without clipping
        communicate = edge_tts.Communicate(clean_t, voice_name, rate="+15%")
        await communicate.save(filename)
        return True
    except Exception as e:
        print("TTS Error:", e)
        return False

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    if not API_KEY:
        return JSONResponse(status_code=400, content={"detail": "Groq API Key missing in environment variables!"})
    
    try:
        web_context = search_live_web(req.message)
        active_model, _ = get_live_groq_model()
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        system_content = (
            f"You are Pyrox, a brilliant, chill, direct, and professional AI buddy created by your master developer. "
            f"The user mode is set to: {req.student_mode}. "
            "CRITICAL FORMATTING RULE: NEVER write long, boring paragraphs. You MUST ALWAYS structure your answers using "
            "bold section headings, clear bullet points, and numbered steps so it is extremely easy to read instantly. "
            "CRITICAL LANGUAGE RULE: Talk in smooth, natural Hinglish. Keep sentences crisp, direct, and perfectly clear. "
            "CRITICAL IDENTITY RULE: If anyone asks who created you, proudly state you were built by your master developer. Never mention OpenAI."
        )
        
        if web_context:
            system_content += f"\n\nLive Web Search Context: {web_context}"

        payload = {
            "model": active_model if active_model else "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": req.message}
            ],
            "temperature": 0.7,
            "max_tokens": 512
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            res_json = response.json()
            reply = res_json['choices'][0]['message']['content']
            
            audio_path = "static/response.mp3"
            success = await generate_edge_audio(reply, req.voice, audio_path)
            
            return {
                "reply": reply,
                "audio_url": f"/{audio_path}?t={asyncio.get_event_loop().time()}" if success else None
            }
        else:
            return JSONResponse(status_code=response.status_code, content={"detail": f"Groq API Error: {response.text}"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Server Exception: {str(e)}"})

@app.get("/", response_class=HTMLResponse)
async def read_index():
    html_content = """<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pyrox Studio - AI Assistant</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background-color: #000000; color: #ffffff; display: flex; height: 100vh; overflow: hidden; position: relative; }

        /* Background strictly restricted to bottom 75% */
        .cyber-wave-bg {
            position: absolute; top: 25%; left: 0; width: 100%; height: 75%;
            pointer-events: none; z-index: 1; overflow: hidden;
            transition: opacity 1.5s ease-in-out; opacity: 1;
        }
        .cyber-wave-bg.fade-out { opacity: 0; }
        
        .wave-line {
            position: absolute; width: 200%; height: 90px; opacity: 0.15;
            background: linear-gradient(90deg, transparent, #3b82f6, #8b5cf6, #3b82f6, transparent);
            animation: waveMove 6s infinite linear;
        }
        .wave-line:nth-child(1) { top: 20%; animation-duration: 5s; filter: drop-shadow(0 0 10px #3b82f6); }
        .wave-line:nth-child(2) { top: 55%; animation-duration: 8s; opacity: 0.1; filter: drop-shadow(0 0 12px #8b5cf6); }
        .wave-line:nth-child(3) { top: 80%; animation-duration: 6s; opacity: 0.08; }

        @keyframes waveMove {
            0% { transform: translateX(-50%) translateY(0) rotate(0deg); }
            50% { transform: translateX(0%) translateY(20px) rotate(2deg); }
            100% { transform: translateX(-50%) translateY(0) rotate(0deg); }
        }

        /* Sidebar & Expand Menu */
        .sidebar {
            width: 0px; background-color: #060608; border-right: none;
            display: flex; flex-direction: column; justify-content: space-between;
            padding: 0px; z-index: 20; overflow: hidden;
            transition: width 0.3s ease, padding 0.3s ease, border-right 0.3s ease;
        }
        .sidebar.expanded { width: 260px; padding: 14px 12px; border-right: 1px solid #1a1a1e; }
        .sidebar-logo-header { display: flex; align-items: center; gap: 12px; padding: 6px; margin-bottom: 14px; }
        .sidebar-brand-name { font-size: 1.15rem; font-weight: 700; color: #ffffff; letter-spacing: 0.5px; }
        
        .menu-section-title { font-size: 0.75rem; text-transform: uppercase; color: #6b7280; padding: 8px 10px 4px 10px; font-weight: 600; letter-spacing: 0.5px; }
        .menu-list { display: flex; flex-direction: column; gap: 4px; }
        .menu-btn {
            display: flex; align-items: center; gap: 12px; padding: 10px 12px;
            color: #d1d5db; font-size: 13.5px; border-radius: 8px; cursor: pointer;
            transition: background 0.2s, color 0.2s; white-space: nowrap;
        }
        .menu-btn:hover { background-color: #18181b; color: #ffffff; }
        .menu-btn svg { width: 18px; height: 18px; stroke: currentColor; fill: none; stroke-width: 2; flex-shrink: 0; }
        .sidebar-bottom { border-top: 1px solid #18181b; padding-top: 10px; }

        .main-container { flex: 1; display: flex; flex-direction: column; justify-content: space-between; align-items: center; height: 100vh; padding-top: 4px; padding-bottom: 8px; position: relative; z-index: 5; }
        
        .top-navbar { width: 100%; display: flex; align-items: center; justify-content: space-between; padding: 10px 20px; position: relative; z-index: 10; }
        .hamburger-btn, .dots-btn { background: transparent; border: none; color: #aaaaaa; cursor: pointer; padding: 6px; border-radius: 50%; display: flex; align-items: center; justify-content: center; transition: color 0.2s, background 0.2s; }
        .hamburger-btn:hover, .dots-btn:hover { color: #ffffff; background-color: #1a1a1a; }
        
        .three-dots-wrapper { position: relative; }
        .dropdown-menu {
            position: absolute; top: 40px; right: 0; width: 210px;
            background-color: #111115; border: 1px solid #222228; border-radius: 12px;
            padding: 6px 0; display: none; flex-direction: column; box-shadow: 0 10px 25px rgba(0,0,0,0.8); z-index: 100;
        }
        .dropdown-menu.show { display: flex; }
        .dropdown-item {
            padding: 10px 16px; font-size: 13px; color: #cccccc; cursor: pointer;
            display: flex; align-items: center; gap: 10px; transition: background 0.2s;
        }
        .dropdown-item:hover { background-color: #1f1f23; color: #ffffff; }

        /* Modals */
        .modal-overlay {
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background: rgba(0,0,0,0.75); display: none; align-items: center; justify-content: center; z-index: 1000;
        }
        .modal-card {
            background: #121216; border: 1px solid #2a2a32; border-radius: 16px;
            width: 90%; max-width: 420px; padding: 24px; display: flex; flex-direction: column; gap: 16px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.9);
        }
        .modal-title { font-size: 1.1rem; font-weight: 700; color: #fff; display: flex; align-items: center; justify-content: space-between; }
        .modal-body { font-size: 0.9rem; color: #aaa; display: flex; flex-direction: column; gap: 10px; }
        .modal-btn {
            background: #1c1c24; border: 1px solid #333340; color: #fff; padding: 10px 14px;
            border-radius: 10px; cursor: pointer; text-align: left; font-size: 0.9rem; transition: 0.2s;
        }
        .modal-btn:hover { background: #2c2c38; border-color: #555566; }
        .modal-close-btn {
            background: #fff; color: #000; border: none; padding: 8px 16px;
            border-radius: 8px; font-weight: 600; cursor: pointer; align-self: flex-end; margin-top: 5px;
        }

        /* Clean Header & Rotational Dynamic Greetings */
        .center-landing-header { display: flex; flex-direction: column; align-items: center; text-align: center; gap: 10px; margin-top: 15px; padding: 0 15px; }
        .brand-title-box { display: flex; align-items: center; gap: 12px; }
        .brand-name-large { font-size: 2.3rem; font-weight: 800; color: #ffffff; letter-spacing: -0.5px; }
        
        .greeting-box { display: flex; flex-direction: column; gap: 4px; margin-top: 4px; }
        .greeting-title { font-size: 1.2rem; font-weight: 700; color: #3b82f6; }
        .greeting-subtext { font-size: 0.95rem; font-weight: 400; color: #9ca3af; }

        /* Working Suggestions Grid */
        .suggestions-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; width: 100%; max-width: 720px; margin-top: 16px; padding: 0 10px; }
        .suggestion-card {
            background: #09090d; border: 1px solid #1a1a22; border-radius: 14px; padding: 12px 14px;
            cursor: pointer; text-align: left; transition: all 0.2s; display: flex; flex-direction: column; gap: 4px;
        }
        .suggestion-card:hover { background: #14141c; border-color: #3b82f6; transform: translateY(-2px); }
        .card-title { font-size: 0.88rem; font-weight: 600; color: #ffffff; }
        .card-desc { font-size: 0.78rem; color: #6b7280; }

        /* Chat Container & Structured Formatting */
        .chat-container { width: 100%; max-width: 800px; flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; padding: 10px 15px; margin-top: 5px; }
        .message { display: flex; flex-direction: column; max-width: 85%; line-height: 1.6; font-size: 0.95rem; gap: 8px; }
        .user-message { align-self: flex-end; background-color: #1c1c24; color: #ffffff; padding: 10px 16px; border-radius: 16px 16px 4px 16px; border: 1px solid #2d2d3a; }
        .ai-message { align-self: flex-start; background-color: #08080c; color: #f3f4f6; padding: 14px 18px; border-radius: 16px 16px 16px 4px; border: 1px solid #16161f; width: 100%; max-width: 100%; }
        
        .ai-message ul, .ai-message ol { padding-left: 20px; margin: 6px 0; }
        .ai-message li { margin-bottom: 4px; }
        .ai-message p { margin-bottom: 6px; }
        .ai-message strong { color: #60a5fa; }

        .audio-player-box { display: flex; align-items: center; gap: 10px; margin-top: 8px; }
        .play-audio-btn {
            background: #1c1c24; border: 1px solid #333340; color: #fff; padding: 6px 14px;
            border-radius: 20px; font-size: 0.85rem; cursor: pointer; display: flex; align-items: center; gap: 6px;
            transition: 0.2s;
        }
        .play-audio-btn:hover { background: #2c2c38; border-color: #3b82f6; }

        .input-wrapper { width: 100%; max-width: 800px; display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 0 15px; }
        .input-box {
            width: 100%; background-color: #08080c; border: 1px solid #1f1f28;
            border-radius: 26px; padding: 8px 16px; display: flex; align-items: center; gap: 10px; position: relative;
            transition: border-color 0.3s, box-shadow 0.3s;
        }
        .input-box.recording { border-color: #3b82f6; box-shadow: 0 0 20px rgba(59, 130, 246, 0.3); }

        /* High-Frequency Sharp Equalizer Spikes */
        .equalizer-wave-container { display: flex; align-items: center; gap: 3px; height: 26px; width: 140px; display: none; }
        .equalizer-wave-container.active { display: flex; }
        .freq-bar { flex: 1; background: linear-gradient(180deg, #3b82f6, #8b5cf6, #ffffff); border-radius: 1px; height: 15%; animation: spikeMotion 0.4s infinite ease-in-out alternate; }
        .freq-bar:nth-child(odd) { animation-delay: 0.1s; }
        .freq-bar:nth-child(even) { animation-delay: 0.25s; }

        @keyframes spikeMotion { 0% { height: 10%; } 100% { height: 100%; } }

        .chat-input-field { flex: 1; background: transparent; border: none; outline: none; color: #ffffff; font-size: 0.95rem; padding: 4px 0; }
        .chat-input-field::placeholder { color: #555560; }

        .mic-btn, .file-btn { background: transparent; border: none; color: #9ca3af; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: color 0.2s, transform 0.2s; }
        .mic-btn:hover, .file-btn:hover { color: #ffffff; transform: scale(1.1); }
        .mic-btn.active { color: #3b82f6; }

        .arrow-submit-btn {
            width: 32px; height: 32px; background-color: #ffffff; color: #000000;
            border: none; border-radius: 50%; display: flex; align-items: center; justify-content: center;
            cursor: pointer; transition: transform 0.2s, opacity 0.2s;
        }
        .arrow-submit-btn:hover { transform: scale(1.05); opacity: 0.9; }
        .footer-disclaimer { font-size: 10.5px; color: #4b5563; text-align: center; }
    </style>
</head>
<body>

    <div class="cyber-wave-bg" id="cyberWaveBg">
        <div class="wave-line"></div>
        <div class="wave-line"></div>
        <div class="wave-line"></div>
    </div>

    <!-- Settings Modal -->
    <div class="modal-overlay" id="settingsModal">
        <div class="modal-card">
            <div class="modal-title">Pyrox Studio Settings <span style="cursor:pointer;" onclick="closeModal('settingsModal')">✕</span></div>
            <div class="modal-body">
                <p style="font-size: 0.85rem; color:#888;">Select AI Voice Assistant:</p>
                <button class="modal-btn" onclick="setVoice('hi-IN-MadhurNeural', 'Madhur (Female)')">👩 Madhur (Female - Smooth Expressive)</button>
                <button class="modal-btn" onclick="setVoice('hi-IN-PrabhatNeural', 'Prabhat (Male)')">👨 Prabhat (Male - Deep Professional)</button>
                
                <p style="font-size: 0.85rem; color:#888; margin-top:10px;">Student Academic Mode:</p>
                <button class="modal-btn" onclick="setStudentMode('School (Class 9-12)')">🏫 School Student Mode</button>
                <button class="modal-btn" onclick="setStudentMode('College / University')">🎓 College / University Mode</button>
            </div>
            <button class="modal-close-btn" onclick="closeModal('settingsModal')">Done</button>
        </div>
    </div>

    <!-- Library Modal -->
    <div class="modal-overlay" id="libraryModal">
        <div class="modal-card">
            <div class="modal-title">Pyrox Library & History <span style="cursor:pointer;" onclick="closeModal('libraryModal')">✕</span></div>
            <div class="modal-body" id="libraryContent">
                <p style="color: #666; font-size: 0.85rem; text-align: center; padding: 15px 0;">No saved items in library yet. Export or bookmark your answers!</p>
            </div>
            <button class="modal-close-btn" onclick="closeModal('libraryModal')">Close</button>
        </div>
    </div>

    <!-- Schedule & Routine Modal -->
    <div class="modal-overlay" id="scheduleModal">
        <div class="modal-card">
            <div class="modal-title">Productivity & Schedule <span style="cursor:pointer;" onclick="closeModal('scheduleModal')">✕</span></div>
            <div class="modal-body">
                <button class="modal-btn" onclick="selectSuggestion('Create a structured 7-day study and coding time-table for me.')">📅 Generate Weekly Study Plan</button>
                <button class="modal-btn" onclick="selectSuggestion('Make a healthy daily meal & hydration schedule.')">🥗 Daily Diet & Health Schedule</button>
                <button class="modal-btn" onclick="selectSuggestion('Set up a YouTube video content creation schedule.')">🎬 Content Creation Routine</button>
            </div>
            <button class="modal-close-btn" onclick="closeModal('scheduleModal')">Close</button>
        </div>
    </div>

    <!-- Pro Upgrade Modal -->
    <div class="modal-overlay" id="upgradeModal">
        <div class="modal-card">
            <div class="modal-title">✨ Pyrox Pro Membership <span style="cursor:pointer;" onclick="closeModal('upgradeModal')">✕</span></div>
            <div class="modal-body">
                <p style="font-size:0.9rem; color:#ccc;">Unlock unlimited high-speed inference, advanced voice synthesis, and dedicated coding assistants.</p>
                <button class="modal-btn" style="background:linear-gradient(135deg, #3b82f6, #8b5cf6); font-weight:600; text-align:center;" onclick="alert('⚡ Pro Plan Activated successfully!')">Activate Pro Access</button>
            </div>
            <button class="modal-close-btn" onclick="closeModal('upgradeModal')">Close</button>
        </div>
    </div>

    <!-- Sidebar / Expand Menu -->
    <div class="sidebar" id="sidebar">
        <div>
            <div class="sidebar-logo-header">
                <svg width="28" height="28" viewBox="0 0 100 100" fill="none" stroke="#ffffff" stroke-width="4" stroke-linejoin="round">
                    <polygon points="50,5 63,35 95,38 71,60 78,92 50,75 22,92 29,60 5,38 37,35" stroke-width="5" opacity="1.0" />
                    <polygon points="50,22 59,42 80,44 64,59 69,80 50,68 31,80 36,59 20,44 41,42" stroke-width="3" opacity="0.65" />
                    <polygon points="50,34 55,47 68,48 58,58 61,71 50,63 39,71 42,58 32,48 45,47" stroke-width="2" opacity="0.35" fill="#ffffff" />
                </svg>
                <span class="sidebar-brand-name">Pyrox Studio</span>
            </div>
            <div class="menu-section-title">Workspace</div>
            <div class="menu-list">
                <div class="menu-btn" onclick="clearChat()">
                    <svg viewBox="0 0 24 24"><path d="M12 4v16m8-8H4"></path></svg>
                    <span>New Chat</span>
                </div>
                <div class="menu-btn" onclick="openModal('libraryModal')">
                    <svg viewBox="0 0 24 24"><path d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                    <span>Library & History</span>
                </div>
                <div class="menu-btn" onclick="openModal('scheduleModal')">
                    <svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                    <span>Schedule & Routine</span>
                </div>
            </div>
            <div class="menu-section-title" style="margin-top: 10px;">Account</div>
            <div class="menu-list">
                <div class="menu-btn" onclick="openModal('upgradeModal')">
                    <svg viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
                    <span>Upgrade to Pro</span>
                </div>
            </div>
        </div>
        <div class="sidebar-bottom">
            <div class="menu-btn" onclick="openModal('settingsModal')">
                <svg viewBox="0 0 24 24"><path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                <span>Settings</span>
            </div>
        </div>
    </div>

    <!-- Main Container -->
    <div class="main-container" id="mainContainer">
        <div class="top-navbar">
            <button type="button" class="hamburger-btn" onclick="toggleSidebar(event)">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="3" y1="12" x2="21" y2="12"></line>
                    <line x1="3" y1="6" x2="21" y2="6"></line>
                    <line x1="3" y1="18" x2="21" y2="18"></line>
                </svg>
            </button>

            <div class="three-dots-wrapper" id="dotsWrapper">
                <button type="button" class="dots-btn" onclick="toggleDropdown(event)">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="5" r="1.5"></circle>
                        <circle cx="12" cy="12" r="1.5"></circle>
                        <circle cx="12" cy="19" r="1.5"></circle>
                    </svg>
                </button>
                <div class="dropdown-menu" id="dropdownMenu">
                    <div class="dropdown-item" onclick="openModal('settingsModal')">⚙️ Settings</div>
                    <div class="dropdown-item" onclick="openModal('libraryModal')">📚 Library</div>
                    <div class="dropdown-item" onclick="openModal('scheduleModal')">📅 Schedule</div>
                    <div class="dropdown-item" onclick="exportChat()">📄 Export Chat</div>
                    <div class="dropdown-item" style="color:#ef4444;" onclick="clearChat()">🗑️ Clear Chat</div>
                </div>
            </div>
        </div>

        <div class="center-landing-header" id="landingHeader">
            <div class="brand-title-box">
                <svg width="44" height="44" viewBox="0 0 100 100" fill="none" stroke="#ffffff" stroke-linejoin="round">
                    <polygon points="50,5 63,35 95,38 71,60 78,92 50,75 22,92 29,60 5,38 37,35" stroke-width="4.5" opacity="1.0" />
                    <polygon points="50,22 59,42 80,44 64,59 69,80 50,68 31,80 36,59 20,44 41,42" stroke-width="3" opacity="0.6" />
                    <polygon points="50,34 55,47 68,48 58,58 61,71 50,63 39,71 42,58 32,48 45,47" stroke-width="2" opacity="0.3" fill="#ffffff" />
                </svg>
                <span class="brand-name-large">Pyrox</span>
            </div>
            
            <!-- Rotational Dynamic Greetings -->
            <div class="greeting-box" id="dynamicGreetingBox">
                <div class="greeting-title" id="greetingTitle">Namaste, Master Creator!</div>
                <div class="greeting-subtext" id="greetingSubtitle">Aaj padhai, coding ya content creation me kahan help chahiye?</div>
            </div>

            <!-- Assistant Suggestions Grid -->
            <div class="suggestions-grid">
                <div class="suggestion-card" onclick="selectSuggestion('Schedule and weekly routine banana hai mujhe, meri help karo.')">
                    <span class="card-title">📅 Schedule & Routine</span>
                    <span class="card-desc">Weekly time-table & productivity planner</span>
                </div>
                <div class="suggestion-card" onclick="selectSuggestion('Ek healthy aur tasty daily meal plan ready karke do.')">
                    <span class="card-title">🥗 Meal & Health Planner</span>
                    <span class="card-desc">Personalized daily food & diet strategy</span>
                </div>
                <div class="suggestion-card" onclick="selectSuggestion('Mujhe coding aur studies ke liye fast revision plan chahiye.')">
                    <span class="card-title">📝 Student Study Hub</span>
                    <span class="card-desc">Smart exam & project preparation guide</span>
                </div>
                <div class="suggestion-card" onclick="selectSuggestion('Viral YouTube & Social Media Content Ideas batao.')">
                    <span class="card-title">💡 Creative Content Ideas</span>
                    <span class="card-desc">Trending script & video concepts</span>
                </div>
            </div>
        </div>

        <div class="chat-container" id="chatContainer"></div>

        <div class="input-wrapper">
            <div class="input-box" id="inputBox">
                <button type="button" class="file-btn" onclick="triggerFileSelect()" title="Attach Photo or File">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"></path>
                    </svg>
                </button>
                <input type="file" id="hiddenFileInput" style="display:none;" onchange="handleFileAttach(event)">

                <button type="button" id="micBtn" class="mic-btn" onclick="toggleVoice(event)">
                    <svg id="micIconSvg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                        <line x1="12" y1="19" x2="12" y2="23"></line>
                    </svg>
                </button>

                <!-- Sharp Equalizer Spikes -->
                <div class="equalizer-wave-container" id="waveBox">
                    <div class="freq-bar"></div><div class="freq-bar"></div><div class="freq-bar"></div><div class="freq-bar"></div>
                    <div class="freq-bar"></div><div class="freq-bar"></div><div class="freq-bar"></div><div class="freq-bar"></div>
                    <div class="freq-bar"></div><div class="freq-bar"></div><div class="freq-bar"></div><div class="freq-bar"></div>
                    <div class="freq-bar"></div><div class="freq-bar"></div><div class="freq-bar"></div><div class="freq-bar"></div>
                </div>

                <input type="text" id="chatInput" class="chat-input-field" placeholder="Ask Pyrox anything..." onkeypress="if(event.key==='Enter'){ event.preventDefault(); triggerSend(); }" />

                <button type="button" class="arrow-submit-btn" onclick="triggerSend(event)">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                        <line x1="5" y1="12" x2="19" y2="12"></line>
                        <polyline points="12 5 19 12 12 19"></polyline>
                    </svg>
                </button>
            </div>
            <div class="footer-disclaimer">Pyrox AI • Built for Master Creator</div>
        </div>
    </div>

    <script>
        let isListening = false;
        let recognition = null;
        let accumulatedSpeech = "";
        let currentVoice = localStorage.getItem('pyrox_voice') || 'hi-IN-MadhurNeural';
        let currentUserName = localStorage.getItem('pyrox_user') || 'Master Creator';
        let currentStudentMode = localStorage.getItem('pyrox_mode') || 'General Student';
        let isFirstMessage = true;

        // Rotational Dynamic Greetings on Load
        const greetingsList = [
            { title: "Namaste, Master Creator!", sub: "Aaj padhai, coding ya content creation me kahan help chahiye?" },
            { title: "Hello Bhai! Pyrox is ready.", sub: "Batao aaj konsa project ya goal tackle karna hai?" },
            { title: "Welcome back, Creator!", sub: "Apna sawal pucho ya niche diye gaye options me se select karo." },
            { title: "Ready for high productivity?", sub: "Pyrox yahan hai, seedha point par baat karte hain." }
        ];

        window.onload = function() {
            const rand = greetingsList[Math.floor(Math.random() * greetingsList.length)];
            document.getElementById('greetingTitle').innerText = rand.title;
            document.getElementById('greetingSubtitle').innerText = rand.sub;
        };

        function toggleSidebar(e) {
            if(e) e.stopPropagation();
            const sb = document.getElementById('sidebar');
            sb.classList.toggle('expanded');
        }

        function toggleDropdown(e) {
            if(e) e.stopPropagation();
            const menu = document.getElementById('dropdownMenu');
            menu.classList.toggle('show');
        }

        function openModal(modalId) {
            const dropdown = document.getElementById('dropdownMenu');
            if(dropdown) dropdown.classList.remove('show');
            document.getElementById(modalId).style.display = 'flex';
        }

        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
        }

        function setVoice(voiceCode, voiceName) {
            currentVoice = voiceCode;
            localStorage.setItem('pyrox_voice', currentVoice);
            alert("✅ Voice set to: " + voiceName);
            closeModal('settingsModal');
        }

        function setStudentMode(modeName) {
            currentStudentMode = modeName;
            localStorage.setItem('pyrox_mode', currentStudentMode);
            alert("🎓 Student Mode updated to: " + modeName);
            closeModal('settingsModal');
        }

        function triggerFileSelect() {
            document.getElementById('hiddenFileInput').click();
        }

        function handleFileAttach(event) {
            const file = event.target.files[0];
            if(file) {
                const inputField = document.getElementById('chatInput');
                inputField.value = `[Attached File: ${file.name}] ` + inputField.value;
            }
        }

        function selectSuggestion(promptText) {
            const inputField = document.getElementById('chatInput');
            inputField.value = promptText;
            triggerSend();
        }

        window.onclick = function(event) {
            const sb = document.getElementById('sidebar');
            const menu = document.getElementById('dropdownMenu');
            
            if (!event.target.closest('#sidebar') && !event.target.closest('.hamburger-btn')) {
                if(sb) sb.classList.remove('expanded');
            }
            if (!event.target.closest('.three-dots-wrapper')) {
                if(menu) menu.classList.remove('show');
            }
        };

        function exportChat() {
            const msgs = document.querySelectorAll('.message');
            if(msgs.length === 0) { alert("No chat to export!"); return; }
            let text = "--- Pyrox Chat Export ---\\n\\n";
            msgs.forEach(m => text += m.innerText + "\\n\\n");
            const blob = new Blob([text], {type: 'text/plain'});
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'Pyrox_Chat.txt';
            a.click();
        }

        function clearChat() {
            document.getElementById('chatContainer').innerHTML = '';
            document.getElementById('landingHeader').style.display = 'flex';
            isFirstMessage = true;
            const bgWave = document.getElementById('cyberWaveBg');
            if(bgWave) {
                bgWave.style.display = 'block';
                bgWave.classList.remove('fade-out');
            }
        }

        function appendMsg(sender, text) {
            const container = document.getElementById('chatContainer');
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${sender === 'user' ? 'user-message' : 'ai-message'}`;
            msgDiv.innerHTML = text;
            container.appendChild(msgDiv);
            container.scrollTop = container.scrollHeight;
            return msgDiv;
        }

        function playAudio(audioId) {
            const audioEle = document.getElementById(audioId);
            if(audioEle) audioEle.play();
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
                inputField.placeholder = "Listening live audio frequency...";
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

            if (isFirstMessage) {
                const bgWave = document.getElementById('cyberWaveBg');
                if(bgWave) {
                    bgWave.classList.add('fade-out');
                    setTimeout(() => { bgWave.style.display = 'none'; }, 1500);
                }
                isFirstMessage = false;
            }

            appendMsg('user', text);
            const aiDiv = appendMsg('ai', '⚡ Pyrox soch raha hai...');

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text, voice: currentVoice, user_name: currentUserName, student_mode: currentStudentMode })
                });

                if(!response.ok) {
                    const errData = await response.json();
                    aiDiv.innerText = "⚠️ Error: " + (errData.detail || "Something went wrong");
                    return;
                }

                const data = await response.json();
                let htmlContent = `<div>${data.reply}</div>`;
                if(data.audio_url) {
                    const uniqueAudioId = 'audio_' + Date.now();
                    htmlContent += `
                        <div class="audio-player-box">
                            <button class="play-audio-btn" onclick="playAudio('${uniqueAudioId}')">
                                🔊 Play Audio
                            </button>
                            <audio id="${uniqueAudioId}" src="${data.audio_url}"></audio>
                        </div>
                    `;
                }
                aiDiv.innerHTML = htmlContent;
            } catch (err) {
                aiDiv.innerText = "⚠️ Server Connection Failed!";
            }
        }
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
