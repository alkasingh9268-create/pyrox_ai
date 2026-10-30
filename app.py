import os
import asyncio
import edge_tts
import streamlit as st
from groq import Groq

# 1. Page Configuration
st.set_page_config(
    page_title="Pyrox Studio",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Default Streamlit Elements & Force Zero Padding for Custom Studio Look
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    #MainMenu, header, footer { visibility: hidden; }
    .block-container { padding: 0rem !important; margin: 0rem !important; }
    iframe { width: 100% !important; height: 100vh !important; border: none; }
    </style>
""", unsafe_allow_html=True)

# Initialize Groq Client
groq_api_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")
client = Groq(api_key=groq_api_key) if groq_api_key else None

# Function to generate real Edge-TTS (Madhur Neural) Audio File on server
def generate_edge_audio(text, filename="response.mp3"):
    try:
        clean_t = text.replace("*", "").replace("#", "").replace("`", "").replace("✨", "").replace("👋", "").replace("🚀", "").replace("💻", "").replace("😎", "").replace("💡", "").replace("🎯", "")
        
        async def _main():
            communicate = edge_tts.Communicate(clean_t, "hi-IN-MadhurNeural")
            await communicate.save(filename)
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(_main())
        return True
    except Exception as e:
        print("TTS Error:", e)
        return False

# 2. Full-Fledged HTML + CSS + JS Studio Frontend UI
app_code = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pyrox Studio</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        body {
            background-color: #000000;
            color: #ffffff;
            display: flex;
            height: 100vh;
            overflow: hidden;
            position: relative;
        }

        /* BACKGROUND SUBTLE ELECTRIC GLOW */
        body::before {
            content: '';
            position: absolute;
            top: -50px;
            left: 50%;
            transform: translateX(-50%);
            width: 600px;
            height: 200px;
            background: radial-gradient(circle, rgba(239, 68, 68, 0.08) 0%, rgba(59, 130, 246, 0.04) 50%, transparent 80%);
            z-index: 0;
            pointer-events: none;
        }

        /* SIDEBAR (GEMINI STYLE COLLAPSIBLE) */
        .sidebar {
            width: 0px;
            background-color: #050505;
            border-right: none;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 0px;
            z-index: 20;
            overflow: hidden;
            transition: width 0.3s ease, padding 0.3s ease, border-right 0.3s ease;
        }
        .sidebar.expanded {
            width: 250px;
            padding: 14px 12px;
            border-right: 1px solid #161618;
        }
        .sidebar-logo-header {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 4px 6px;
            margin-bottom: 12px;
            white-space: nowrap;
        }
        .sidebar-brand-name {
            font-size: 1.15rem;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: 0.5px;
        }
        .menu-list {
            display: flex;
            flex-direction: column;
            gap: 4px;
            white-space: nowrap;
        }
        .menu-btn {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 9px 10px;
            color: #aaaaaa;
            font-size: 13.5px;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.2s, color 0.2s;
        }
        .menu-btn:hover {
            background-color: #161618;
            color: #ffffff;
        }
        .menu-btn svg {
            width: 18px; height: 18px; stroke: currentColor; fill: none; stroke-width: 2; flex-shrink: 0;
        }

        /* CHAT HISTORY SECTION */
        .history-section {
            margin-top: 15px;
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 4px;
            white-space: nowrap;
        }
        .history-title {
            font-size: 11px; color: #555; text-transform: uppercase; letter-spacing: 1px; padding-left: 6px; margin-bottom: 4px;
        }
        .history-item {
            font-size: 13px; color: #b0b0b0; padding: 7px 10px; border-radius: 6px; cursor: pointer; overflow: hidden; text-overflow: ellipsis; transition: background 0.2s, color 0.2s;
        }
        .history-item:hover { background-color: #161618; color: #fff; }

        .sidebar-bottom { border-top: 1px solid #161618; padding-top: 10px; white-space: nowrap; }

        /* MAIN CONTAINER */
        .main-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            align-items: center;
            height: 100vh;
            padding-top: 4px;
            padding-bottom: 10px;
            z-index: 10;
        }

        /* TOP NAVBAR */
        .top-navbar {
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 20px;
        }
        .nav-left { display: flex; align-items: center; gap: 12px; }
        .expand-sidebar-btn {
            background: transparent; border: none; color: #aaaaaa; cursor: pointer; padding: 6px; border-radius: 50%; display: flex; align-items: center; justify-content: center; transition: color 0.2s, background 0.2s;
        }
        .expand-sidebar-btn:hover { color: #fff; background: #161618; }
        
        .top-brand { font-size: 1.2rem; font-weight: 700; letter-spacing: 0.5px; color: #fff; }

        .three-dots-wrapper { position: relative; }
        .dots-btn {
            background: transparent; border: none; color: #aaaaaa; cursor: pointer; padding: 6px; border-radius: 50%; display: flex; align-items: center; justify-content: center; transition: color 0.2s, background 0.2s;
        }
        .dots-btn:hover { color: #ffffff; background-color: #161618; }
        
        .dropdown-menu {
            position: absolute; top: 38px; right: 0; width: 210px; background-color: #0d0d0f; border: 1px solid #222226; border-radius: 12px; padding: 6px 0; display: none; flex-direction: column; box-shadow: 0 10px 25px rgba(0,0,0,0.7); z-index: 100;
        }
        .dropdown-menu.show { display: flex; }
        .dropdown-item {
            padding: 9px 16px; font-size: 13px; color: #cccccc; cursor: pointer; display: flex; align-items: center; gap: 10px; transition: background 0.2s;
        }
        .dropdown-item:hover { background-color: #161618; color: #ffffff; }

        /* CENTER LANDING HEADER */
        .center-landing-header {
            display: flex; flex-direction: column; align-items: center; text-align: center; gap: 8px; margin-top: 12vh;
        }
        .brand-logo-large { width: 50px; height: 50px; }
        .brand-name-large { font-size: 2.4rem; font-weight: 800; color: #ffffff; letter-spacing: -0.5px; }
        .greeting-subtext { font-size: 1.25rem; font-weight: 500; color: #9ca3af; }

        /* CHAT CONTAINER */
        .chat-container {
            width: 100%; max-width: 820px; flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 16px; padding: 10px 15px; scroll-behavior: smooth;
        }
        .message { display: flex; flex-direction: column; max-width: 85%; line-height: 1.6; font-size: 1rem; }
        .user-message {
            align-self: flex-end; background-color: #1c1c1e; color: #ffffff; padding: 12px 18px; border-radius: 18px 18px 4px 18px; border: 1px solid #2d2d30;
        }
        .ai-message {
            align-self: flex-start; background-color: #0a0a0c; color: #f3f4f6; padding: 14px 20px; border-radius: 18px 18px 18px 4px; border: 1px solid #1f1f23; display: flex; flex-direction: column; gap: 12px;
        }

        /* INPUT BAR */
        .input-wrapper {
            width: 100%; max-width: 820px; display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 0 15px;
        }
        .input-box {
            width: 100%; background-color: #08080a; border: 1px solid #222226; border-radius: 28px; padding: 10px 16px; display: flex; align-items: center; gap: 12px; position: relative; transition: border-color 0.3s, box-shadow 0.3s;
        }
        .input-box.recording { border-color: #ef4444; box-shadow: 0 0 20px rgba(239, 68, 68, 0.3); }
        .star-btn { cursor: pointer; width: 22px; height: 22px; flex-shrink: 0; }

        /* WAVE BARS */
        .gemini-wave-container {
            display: flex; align-items: center; gap: 4px; height: 22px; width: 130px; display: none;
        }
        .gemini-wave-container.active { display: flex; }
        .wave-bar {
            flex: 1; background: linear-gradient(180deg, #ef4444, #3b82f6); border-radius: 4px; height: 20%; animation: waveMotion 0.6s infinite ease-in-out alternate;
        }
        .wave-bar:nth-child(1) { animation-delay: 0.1s; }
        .wave-bar:nth-child(2) { animation-delay: 0.3s; }
        .wave-bar:nth-child(3) { animation-delay: 0.2s; }
        .wave-bar:nth-child(4) { animation-delay: 0.5s; }
        .wave-bar:nth-child(5) { animation-delay: 0.15s; }
        @keyframes waveMotion { 0% { height: 15%; } 100% { height: 100%; } }

        .chat-input-field {
            flex: 1; background: transparent; border: none; outline: none; color: #ffffff; font-size: 1rem; padding: 4px 0;
        }
        .chat-input-field::placeholder { color: #666666; }

        .mic-btn { background: transparent; border: none; color: #aaaaaa; cursor: pointer; display: flex; align-items: center; transition: color 0.2s; }
        .mic-btn:hover { color: #ffffff; }
        .mic-btn.active { color: #ef4444; }

        .arrow-submit-btn {
            width: 34px; height: 34px; background-color: #ffffff; color: #000000; border: none; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: transform 0.2s;
        }
        .arrow-submit-btn:hover { transform: scale(1.06); }

        .footer-disclaimer { font-size: 11px; color: #555; text-align: center; }
    </style>
</head>
<body>

    <!-- SIDEBAR -->
    <div class="sidebar" id="sidebar">
        <div>
            <div class="sidebar-logo-header">
                <svg width="24" height="24" viewBox="0 0 200 200">
                    <circle cx="100" cy="100" r="85" fill="#050505" stroke="#ffffff" stroke-width="6"/>
                    <path d="M 100 25 L 70 85 L 110 85 L 90 115 L 130 115 L 100 175" fill="none" stroke="#ffffff" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span class="sidebar-brand-name">Pyrox</span>
            </div>

            <div class="menu-list">
                <div class="menu-btn" onclick="alert('Starting New Chat...')">
                    <svg viewBox="0 0 24 24"><path d="M12 4v16m8-8H4"></path></svg>
                    <span>New Chat</span>
                </div>
                <div class="menu-btn" onclick="alert('Search feature')">
                    <svg viewBox="0 0 24 24"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                    <span>Search Chat</span>
                </div>
                <div class="menu-btn" onclick="alert('Library: Saved notes')">
                    <svg viewBox="0 0 24 24"><path d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                    <span>Library</span>
                </div>
            </div>

            <div class="history-section" id="historySection">
                <div class="history-title">Recent Chats</div>
            </div>
        </div>

        <div class="sidebar-bottom">
            <div class="menu-btn" onclick="alert('Settings')">
                <svg viewBox="0 0 24 24"><path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                <span>Settings</span>
            </div>
        </div>
    </div>

    <!-- MAIN WORKSPACE -->
    <div class="main-container">
        
        <!-- TOP NAVBAR -->
        <div class="top-navbar">
            <div class="nav-left">
                <button class="expand-sidebar-btn" onclick="toggleSidebar()">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="3" y1="12" x2="21" y2="12"></line>
                        <line x1="3" y1="6" x2="21" y2="6"></line>
                        <line x1="3" y1="18" x2="21" y2="18"></line>
                    </svg>
                </button>
                <div class="top-brand">Pyrox</div>
            </div>

            <div class="three-dots-wrapper">
                <button class="dots-btn" onclick="toggleDropdown()">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="5" r="1.5"></circle>
                        <circle cx="12" cy="12" r="1.5"></circle>
                        <circle cx="12" cy="19" r="1.5"></circle>
                    </svg>
                </button>
                <div class="dropdown-menu" id="dropdownMenu">
                    <div class="dropdown-item" onclick="alert('Google Gmail Login')">📧 Login with Gmail</div>
                    <div class="dropdown-item" onclick="alert('Link Copied!')">🔗 Share Conversation</div>
                    <div class="dropdown-item" onclick="alert('Exporting PDF...')">📄 Download PDF / Export</div>
                    <div class="dropdown-item" style="color:#ef4444;" onclick="alert('Chat cleared')">🗑️ Delete Chat</div>
                </div>
            </div>
        </div>

        <!-- CENTER LANDING HEADER -->
        <div class="center-landing-header" id="landingHeader">
            <svg class="brand-logo-large" viewBox="0 0 200 200">
                <circle cx="100" cy="100" r="85" fill="#000000" stroke="#ffffff" stroke-width="6"/>
                <path d="M 100 25 L 70 85 L 110 85 L 90 115 L 130 115 L 100 175" fill="none" stroke="#ffffff" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <div class="brand-name-large">Pyrox</div>
            <div class="greeting-subtext">How can I help you today? ✨</div>
        </div>

        <!-- CHAT CONTAINER -->
        <div class="chat-container" id="chatContainer"></div>

        <!-- INPUT BAR -->
        <div class="input-wrapper">
            <div class="input-box" id="inputBox">
                <svg class="star-btn" viewBox="0 0 24 24" onclick="alert('Attach file or photo')">
                    <defs>
                        <linearGradient id="starGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#9C27B0"/>
                            <stop offset="100%" stop-color="#03A9F4"/>
                        </linearGradient>
                    </defs>
                    <path d="M12 0C12 6.627 6.627 12 0 12C6.627 12 12 17.373 12 24C12 17.373 17.373 12 24 12C17.373 12 12 6.627 12 0Z" fill="url(#starGrad)"/>
                </svg>

                <button id="micBtn" class="mic-btn" onclick="toggleVoice()">
                    <svg id="micIconSvg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                        <line x1="12" y1="19" x2="12" y2="23"></line>
                    </svg>
                </button>

                <div class="gemini-wave-container" id="waveBox">
                    <div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div>
                </div>

                <input type="text" id="chatInput" class="chat-input-field" placeholder="Ask Pyrox anything..." onkeypress="if(event.key==='Enter') sendMessage();" />

                <button class="arrow-submit-btn" onclick="sendMessage()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                        <line x1="5" y1="12" x2="19" y2="12"></line>
                        <polyline points="12 5 19 12 12 19"></polyline>
                    </svg>
                </button>
            </div>
            <div class="footer-disclaimer">Pyrox AI • Global Launch Nov 2026</div>
        </div>
    </div>

    <script>
        let isListening = false;
        let recognition = null;
        let accumulatedSpeech = "";

        function toggleSidebar() {
            document.getElementById('sidebar').classList.toggle('expanded');
        }

        function toggleDropdown() {
            document.getElementById('dropdownMenu').classList.toggle('show');
        }

        window.onclick = function(event) {
            if (!event.target.closest('.three-dots-wrapper') && !event.target.closest('.expand-sidebar-btn')) {
                const m = document.getElementById('dropdownMenu');
                if(m) m.classList.remove('show');
            }
        }

        function toggleVoice() {
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
                alert("Speech recognition not supported.");
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
                inputField.placeholder = "Listening...";
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

        function sendMessage() {
            if (isListening && recognition) { recognition.stop(); stopVoiceUI(); }
            let inputField = document.getElementById('chatInput');
            let text = inputField.value.trim();
            if(!text) return;

            let landingHeader = document.getElementById('landingHeader');
            if(landingHeader) landingHeader.style.display = 'none';

            let chatContainer = document.getElementById('chatContainer');
            
            // Add user message
            let userDiv = document.createElement('div');
            userDiv.className = 'message user-message';
            userDiv.innerText = text;
            chatContainer.appendChild(userDiv);

            // Add history
            let historySection = document.getElementById('historySection');
            let hItem = document.createElement('div');
            hItem.className = 'history-item';
            hItem.innerText = text.length > 22 ? text.substring(0, 22) + '...' : text;
            historySection.appendChild(hItem);

            inputField.value = '';
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    </script>
</body>
</html>
"""

# Handle Python Side Groq LLM & Edge-TTS Generation
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render Studio App Interface
st.components.v1.html(app_code, height=780, scrolling=False)
