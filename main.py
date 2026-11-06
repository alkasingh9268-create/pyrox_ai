import os
import asyncio
import requests
import edge_tts
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

# Static folder taaki audio files securely save aur serve ho sakein
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

API_KEY = os.environ.get("GROQ_API_KEY", "").strip()

class ChatRequest(BaseModel):
    message: str

def get_live_groq_model():
    """Groq server se live check karega ki is waqt teri key par kaun sa model active hai"""
    if not API_KEY:
        return None, "GROQ_API_KEY Missing in Render Environment!"
    try:
        res = requests.get("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {API_KEY}"}, timeout=10)
        if res.status_code == 200:
            models = res.json().get("data", [])
            chat_models = [m.get("id") for m in models if m.get("id") and "guard" not in m.get("id").lower() and "whisper" not in m.get("id").lower()]
            if chat_models:
                for p in ["llama", "gpt-oss", "qwen"]:
                    for m in chat_models:
                        if p in m.lower():
                            return m, f"Success ({m})"
                return chat_models[0], f"Success ({chat_models[0]})"
        return None, "No active models found"
    except Exception as e:
        return None, str(e)

@app.get("/api/debug")
async def debug_key():
    model, status = get_live_groq_model()
    return JSONResponse({"status": status, "active_model": model})

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
    
    active_model, status_msg = get_live_groq_model()
    if not active_model:
        raise HTTPException(status_code=400, detail=f"Groq API Error: {status_msg}")

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
                "content": "You are Pyrox, an advanced Gen-Z AI assistant created for users in India (specifically Delhi context). Talk in a smooth mix of natural Hindi and English (Hinglish) with cool emojis ✨. Keep explanations conversational, natural, and friendly—never robotic or textbook-like."
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
            raise HTTPException(status_code=response.status_code, detail=f"Groq API ({active_model}): {response.text}")
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
            transition: background 0.2s, color 0.2s; position: relative; white-space: nowrap;
        }
        .menu-btn:hover { background-color: #141414; color: #ffffff; }
        .menu-btn svg { width: 18px; height: 18px; stroke: currentColor; fill: none; stroke-width: 2; flex-shrink: 0; }
        .sidebar-bottom { border-top: 1px solid #141414; padding-top: 8px; }

        /* TOOLTIP HOVER HELPER */
        [data-tooltip] { position: relative; }
        [data-tooltip]:hover::after {
            content: attr(data-tooltip); position: absolute; bottom: 115%; left: 50%;
            transform: translateX(-50%); background-color: #1f1f1f; color: #ffffff;
            font-size: 11px; font-weight: 500; padding: 4px 8px; border-radius: 6px;
            white-space: nowrap; border: 1px solid #333; pointer-events: none; z-index: 1000;
            box-shadow: 0 4px 10px rgba(0,0,0,0.5);
        }

        /* MAIN WORKSPACE */
        .main-container { flex: 1; display: flex; flex-direction: column; justify-content: space-between; align-items: center; height: 100vh; padding-top: 4px; padding-bottom: 8px; position: relative; }

        /* TOP NAVBAR */
        .top-navbar { width: 100%; display: flex; align-items: center; justify-content: space-between; padding: 6px 20px; position: relative; z-index: 10; }
        .hamburger-btn, .dots-btn {
            background: transparent; border: none; color: #aaaaaa; cursor: pointer;
            padding: 6px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
            transition: color 0.2s, background 0.2s;
        }
        .hamburger-btn:hover, .dots-btn:hover { color: #ffffff; background-color: #1a1a1a; }
        .three-dots-wrapper { position: relative; }
        .dropdown-menu {
            position: absolute; top: 38px; right: 0; width: 220px;
            background-color: #0d0d0d; border: 1px solid #222222; border-radius: 12px;
            padding: 6px 0; display: none; flex-direction: column; box-shadow: 0 10px 25px rgba(0,0,0,0.7); z-index: 100;
        }
        .dropdown-menu.show { display: flex; }
        .dropdown-item {
            padding: 10px 16px; font-size: 13px; color: #cccccc; cursor: pointer;
            display: flex; align-items: center; gap: 10px; transition: background 0.2s;
        }
        .dropdown-item:hover { background-color: #1a1a1a; color: #ffffff; }
        .dropdown-item.login-item { border-bottom: 1px solid #222; color: #3b82f6; font-weight: 600; }

        /* SEARCH OVERLAY BAR IN CHAT */
        .search-bar-overlay {
            position: absolute; top: 50px; width: 90%; max-width: 500px;
            background-color: #111; border: 1px solid #333; border-radius: 20px;
            padding: 6px 14px; display: none; align-items: center; gap: 10px; z-index: 50;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }
        .search-bar-overlay input { flex: 1; background: transparent; border: none; outline: none; color: #fff; font-size: 13px; }

        /* CENTER LANDING HEADER */
        .center-landing-header { display: flex; flex-direction: column; align-items: center; text-align: center; gap: 6px; margin-top: 15px; }
        .brand-title-box { display: flex; align-items: center; gap: 12px; }
        .brand-name-large { font-size: 2.2rem; font-weight: 800; color: #ffffff; letter-spacing: -0.5px; }
        .greeting-subtext { font-size: 1.15rem; font-weight: 500; color: #888888; }

        /* CHAT MESSAGES CONTAINER */
        .chat-container { width: 100%; max-width: 800px; flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; padding: 10px 15px; margin-top: 5px; }
        .message { display: flex; flex-direction: column; max-width: 82%; line-height: 1.5; font-size: 0.95rem; gap: 8px; }
        .user-message { align-self: flex-end; background-color: #1c1c1e; color: #ffffff; padding: 10px 16px; border-radius: 16px 16px 4px 16px; border: 1px solid #2d2d2d; }
        .ai-message {
            align-self: flex-start; background-color: #080808; color: #f0f0f0;
            padding: 14px 18px; border-radius: 16px 16px 16px 4px; border: 1px solid #1a1a1a;
            display: flex; flex-direction: column; gap: 8px; width: 100%; max-width: 100%;
        }
        audio { width: 100%; height: 32px; margin-top: 6px; filter: invert(100%) hue-rotate(180deg); }

        /* INPUT BAR AREA */
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
                <div class="menu-btn" onclick="clearChat()" data-tooltip="New Chat">
                    <svg viewBox="0 0 24 24"><path d="M12 4v16m8-8H4"></path></svg>
                    <span>New Chat</span>
                </div>
                <div class="menu-btn" onclick="toggleSearchOverlay()" data-tooltip="Search Chat">
                    <svg viewBox="0 0 24 24"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                    <span>Search Chat</span>
                </div>
                <div class="menu-btn" onclick="openLibrary()" data-tooltip="Library">
                    <svg viewBox="0 0 24 24"><path d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                    <span>Library</span>
                </div>
                <div class="menu-btn" onclick="openStudentSetup()" data-tooltip="For Students">
                    <svg viewBox="0 0 24 24"><path d="M12 14l9-5-9-5-9 5 9 5z"></path><path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0112 20.055a11.952 11.952 0 01-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z"></path></svg>
                    <span>For Students</span>
                </div>
            </div>
        </div>
        <div class="sidebar-bottom">
            <div class="menu-btn" onclick="openSettings()" data-tooltip="Settings">
                <svg viewBox="0 0 24 24"><path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                <span>Settings</span>
            </div>
        </div>
    </div>

    <!-- MAIN CONTAINER -->
    <div class="main-container">
        
        <!-- SEARCH OVERLAY BAR -->
        <div class="search-bar-overlay" id="searchOverlay">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="2"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
            <input type="text" id="searchInput" placeholder="Search in conversation..." onkeyup="filterChatMessages(this.value)">
            <span style="color:#666; font-size:12px; cursor:pointer;" onclick="toggleSearchOverlay()">✕</span>
        </div>

        <!-- TOP NAVBAR -->
        <div class="top-navbar">
            <button type="button" class="hamburger-btn" onclick="toggleSidebar()" data-tooltip="Toggle Menu">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="3" y1="12" x2="21" y2="12"></line>
                    <line x1="3" y1="6" x2="21" y2="6"></line>
                    <line x1="3" y1="18" x2="21" y2="18"></line>
                </svg>
            </button>

            <div class="three-dots-wrapper">
                <button type="button" class="dots-btn" onclick="toggleDropdown()" data-tooltip="More Options">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="5" r="1.5"></circle>
                        <circle cx="12" cy="12" r="1.5"></circle>
                        <circle cx="12" cy="19" r="1.5"></circle>
                    </svg>
                </button>
                <div class="dropdown-menu" id="dropdownMenu">
                    <div class="dropdown-item login-item" onclick="loginWithGmail()">📧 Login with Gmail</div>
                    <div class="dropdown-item" onclick="shareConversation()">🔗 Share Conversation</div>
                    <div class="dropdown-item" onclick="toggleSearchOverlay()">🔍 Find in Chat</div>
                    <div class="dropdown-item" onclick="pinChatToggle()">📌 <span id="pinText">Pin Chat</span></div>
                    <div class="dropdown-item" onclick="exportChatPDF()">📄 Export Chat Text</div>
                    <div class="dropdown-item" style="color:#ef4444;" onclick="clearChat()">🗑️ Delete Chat</div>
                </div>
            </div>
        </div>

        <!-- CENTER LANDING HEADER -->
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

        <!-- CHAT MESSAGES AREA -->
        <div class="chat-container" id="chatContainer"></div>

        <!-- INPUT BAR AREA -->
        <div class="input-wrapper">
            <div class="input-box" id="inputBox">
                <svg style="cursor:pointer; width:20px; height:20px; flex-shrink:0;" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="2" data-tooltip="Attach File & Photo" onclick="triggerFileAttach()">
                    <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"></path>
                </svg>
                <input type="file" id="hiddenFileInput" style="display:none;" onchange="handleFileSelect(event)">

                <button type="button" id="micBtn" class="mic-btn" data-tooltip="Voice Input" onclick="toggleVoice(event)">
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

                <button type="button" class="arrow-submit-btn" data-tooltip="Submit" onclick="triggerSend(event)">
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
        window.isListening = false;
        window.recognition = null;
        window.accumulatedSpeech = "";
        window.isPinned = false;

        window.toggleSidebar = function() { 
            const sb = document.getElementById('sidebar');
            if(sb) sb.classList.toggle('expanded'); 
        };

        window.toggleDropdown = function() { 
            const menu = document.getElementById('dropdownMenu');
            if(menu) menu.classList.toggle('show'); 
        };

        window.onclick = function(event) {
            if (!event.target.closest('.three-dots-wrapper')) {
                const m = document.getElementById('dropdownMenu');
                if(m) m.classList.remove('show');
            }
        };

        window.loginWithGmail = function() {
            window.toggleDropdown();
            let email = prompt("Enter your Gmail address to log in:");
            if(email && email.includes("@")) { 
                alert("✅ Welcome " + email + "! Logged in successfully to Pyrox."); 
            } else if(email) {
                alert("⚠️ Please enter a valid Gmail address!");
            }
        };

        window.shareConversation = function() {
            window.toggleDropdown();
            navigator.clipboard.writeText(window.location.href);
            alert("🔗 Conversation link copied to clipboard successfully!");
        };

        window.toggleSearchOverlay = function() {
            window.toggleDropdown();
            const overlay = document.getElementById('searchOverlay');
            if (overlay) {
                overlay.style.display = (overlay.style.display === 'flex') ? 'none' : 'flex';
                if(overlay.style.display === 'flex') {
                    const input = document.getElementById('searchInput');
                    if(input) input.focus();
                }
            }
        };

        window.filterChatMessages = function(query) {
            const msgs = document.querySelectorAll('.message');
            const lowerQuery = query.toLowerCase();
            msgs.forEach(m => {
                if(m.innerText.toLowerCase().includes(lowerQuery)) {
                    m.style.display = 'flex';
                } else {
                    m.style.display = 'none';
                }
            });
        };

        window.pinChatToggle = function() {
            window.toggleDropdown();
            window.isPinned = !window.isPinned;
            const pt = document.getElementById('pinText');
            if(pt) pt.innerText = window.isPinned ? "Unpin Chat" : "Pin Chat";
            alert(window.isPinned ? "📌 Chat pinned to the top!" : "📌 Chat unpinned!");
        };

        window.exportChatPDF = function() {
            window.toggleDropdown();
            const msgs = document.querySelectorAll('.message');
            if(msgs.length === 0) { 
                alert("Nothing to export yet!"); 
                return; 
            }
            let textContent = "--- Pyrox Studio Conversation Export ---\n\n";
            msgs.forEach(m => { textContent += m.innerText + "\n\n"; });
            const blob = new Blob([textContent], { type: 'text/plain' });
            const anchor = document.createElement('a');
            anchor.href = URL.createObjectURL(blob);
            anchor.download = 'Pyrox_Chat_Export.txt';
            anchor.click();
            alert("📄 Chat text exported successfully!");
        };

        window.clearChat = function() {
            window.toggleDropdown();
            if(confirm("Are you sure you want to clear this chat?")) {
                const container = document.getElementById('chatContainer');
                if(container) container.innerHTML = '';
                const landing = document.getElementById('landingHeader');
                if(landing) landing.style.display = 'flex';
            }
        };

        window.openLibrary = function() {
            alert("📚 Library: Your saved discussions, notes, and history will appear here!");
        };

        window.openSettings = function() {
            alert("⚙️ Settings: Theme, Audio preferences, and account configurations.");
        };

        window.triggerFileAttach = function() { 
            const fileInput = document.getElementById('hiddenFileInput');
            if(fileInput) fileInput.click(); 
        };

        window.handleFileSelect = function(event) {
            const file = event.target.files[0];
            if(file) {
                alert("📎 Attached file successfully: " + file.name);
                const inputField = document.getElementById('chatInput');
                if(inputField) inputField.value = "[Attached: " + file.name + "] " + inputField.value;
            }
        };

        window.openStudentSetup = function() {
            let goal = prompt("आप किस परीक्षा या कक्षा की तैयारी कर रहे हैं? (जैसे: NEET, JEE, School, College)");
            if(!goal) return;
            let standard = prompt("आपकी कक्षा या वर्ष कौन सा है? (जैसे: Class 9, Class 11,
