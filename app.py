import os
import streamlit as st
from groq import Groq

# 1. Page Configuration
st.set_page_config(
    page_title="Pyrox Studio",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Global Streamlit Styling Clean-up
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    #MainMenu, header, footer { visibility: hidden; }
    .block-container { padding: 0rem; margin: 0rem; }
    </style>
""", unsafe_allow_html=True)

api_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")

# 3. Complete Unified HTML + CSS + JS App
app_code = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pyrox AI</title>
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
        }

        /* SIDEBAR (Visible only when Logged In) */
        .sidebar {
            width: 240px;
            background-color: #050505;
            border-right: 1px solid #1a1a1a;
            display: none;
            flex-direction: column;
            justify-content: space-between;
            padding: 16px 12px;
            z-index: 20;
        }
        .sidebar.active {
            display: flex;
        }
        .sidebar-top {
            display: flex;
            flex-direction: column;
            gap: 18px;
        }
        .sidebar-logo-header {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 4px 8px;
        }
        .sidebar-logo-header svg {
            width: 28px;
            height: 28px;
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
        }
        .menu-btn {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 12px;
            color: #aaaaaa;
            font-size: 13.5px;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.2s, color 0.2s;
        }
        .menu-btn:hover {
            background-color: #141414;
            color: #ffffff;
        }
        .menu-btn svg {
            width: 18px;
            height: 18px;
            stroke: currentColor;
            fill: none;
            stroke-width: 2;
        }
        .sidebar-bottom {
            border-top: 1px solid #1a1a1a;
            padding-top: 12px;
        }

        /* MAIN APP WORKSPACE */
        .main-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            align-items: center;
            position: relative;
            height: 100vh;
        }

        /* TOP NAVBAR */
        .top-navbar {
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 24px;
            border-bottom: 1px solid #121212;
        }
        .header-left {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .top-logo {
            width: 32px;
            height: 32px;
        }
        .top-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: #ffffff;
        }

        /* LOGIN LANDING VIEW (When not logged in) */
        .landing-view {
            position: absolute;
            top: 45%;
            left: 50%;
            transform: translate(-50%, -50%);
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            gap: 20px;
            width: 100%;
            max-width: 600px;
            padding: 0 20px;
        }
        .landing-logo {
            width: 70px;
            height: 70px;
        }
        .landing-title {
            font-size: 2.5rem;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: -0.5px;
        }
        .landing-greeting {
            font-size: 2rem;
            font-weight: 600;
            color: #e5e7eb;
            margin-top: 5px;
        }
        .google-login-btn {
            background-color: #ffffff;
            color: #000000;
            font-weight: 600;
            font-size: 0.95rem;
            padding: 12px 24px;
            border-radius: 24px;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: transform 0.2s, opacity 0.2s;
            margin-top: 10px;
        }
        .google-login-btn:hover {
            transform: scale(1.03);
            opacity: 0.9;
        }

        /* CHAT INTERFACE VIEW (Hidden initially until logged in) */
        .chat-app-view {
            width: 100%;
            flex: 1;
            display: none;
            flex-direction: column;
            align-items: center;
            justify-content: space-between;
            overflow: hidden;
        }
        .chat-app-view.active {
            display: flex;
        }

        .chat-container {
            width: 100%;
            max-width: 820px;
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 20px;
            padding: 20px 15px;
        }
        .message {
            display: flex;
            flex-direction: column;
            max-width: 82%;
            line-height: 1.6;
            font-size: 0.98rem;
        }
        .user-message {
            align-self: flex-end;
            background-color: #1a1a1a;
            color: #ffffff;
            padding: 12px 18px;
            border-radius: 18px 18px 4px 18px;
            border: 1px solid #2a2a2a;
        }
        .ai-message {
            align-self: flex-start;
            background-color: #080808;
            color: #f0f0f0;
            padding: 14px 20px;
            border-radius: 18px 18px 18px 4px;
            border: 1px solid #1a1a1a;
            position: relative;
        }
        .speak-btn {
            background: transparent;
            border: none;
            color: #888888;
            cursor: pointer;
            margin-top: 8px;
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            transition: color 0.2s;
        }
        .speak-btn:hover { color: #ffffff; }

        /* INPUT BAR WITH GEMINI WAVE */
        .input-wrapper {
            width: 100%;
            max-width: 820px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
            margin-bottom: 10px;
            padding: 0 15px;
        }
        .input-box {
            width: 100%;
            background-color: #080808;
            border: 1px solid #222222;
            border-radius: 28px;
            padding: 10px 16px;
            display: flex;
            align-items: center;
            gap: 12px;
            position: relative;
            transition: border-color 0.3s;
        }
        .input-box.recording {
            border-color: #3b82f6;
            box-shadow: 0 0 15px rgba(59, 130, 246, 0.25);
        }
        .star-btn {
            cursor: pointer;
            width: 22px;
            height: 22px;
            flex-shrink: 0;
        }

        /* PROFESSIONAL GEMINI WAVE VISUALIZER */
        .gemini-wave-container {
            display: flex;
            align-items: center;
            gap: 4px;
            height: 22px;
            width: 140px;
            display: none;
        }
        .gemini-wave-container.active {
            display: flex;
        }
        .wave-bar {
            flex: 1;
            background: linear-gradient(180deg, #3b82f6, #ec4899);
            border-radius: 4px;
            height: 20%;
            animation: waveMotion 0.7s infinite ease-in-out alternate;
        }
        .wave-bar:nth-child(1) { animation-delay: 0.1s; }
        .wave-bar:nth-child(2) { animation-delay: 0.3s; }
        .wave-bar:nth-child(3) { animation-delay: 0.2s; }
        .wave-bar:nth-child(4) { animation-delay: 0.5s; }
        .wave-bar:nth-child(5) { animation-delay: 0.15s; }
        .wave-bar:nth-child(6) { animation-delay: 0.35s; }
        .wave-bar:nth-child(7) { animation-delay: 0.25s; }

        @keyframes waveMotion {
            0% { height: 15%; }
            100% { height: 100%; }
        }

        .chat-input-field {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: #ffffff;
            font-size: 1rem;
            padding: 6px 0;
        }
        .chat-input-field::placeholder { color: #555555; }

        .mic-btn {
            background: transparent;
            border: none;
            color: #aaaaaa;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: color 0.2s;
        }
        .mic-btn:hover { color: #ffffff; }
        .mic-btn.active { color: #3b82f6; }

        .arrow-submit-btn {
            width: 34px;
            height: 34px;
            background-color: #ffffff;
            color: #000000;
            border: none;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: transform 0.2s, opacity 0.2s;
        }
        .arrow-submit-btn:hover {
            transform: scale(1.05);
            opacity: 0.9;
        }

        /* DISCLAIMER FOOTER */
        .footer-disclaimer {
            font-size: 11px;
            color: #666666;
            text-align: center;
            padding-bottom: 4px;
        }

        /* THREE DOTS DROPDOWN */
        .three-dots-wrapper { position: relative; }
        .dots-btn {
            background: transparent; border: none; color: #aaaaaa; cursor: pointer; padding: 6px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
        }
        .dots-btn:hover { color: #ffffff; background-color: #1a1a1a; }
        .dropdown-menu {
            position: absolute; top: 40px; right: 0; width: 210px; background-color: #0d0d0d; border: 1px solid #222222; border-radius: 12px; padding: 6px 0; display: none; flex-direction: column; z-index: 100; box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        }
        .dropdown-menu.show { display: flex; }
        .dropdown-item {
            padding: 10px 16px; font-size: 13px; color: #cccccc; cursor: pointer; display: flex; align-items: center; gap: 10px; transition: background 0.2s;
        }
        .dropdown-item:hover { background-color: #1a1a1a; color: #ffffff; }
        .dropdown-item.danger { color: #ef4444; }
    </style>
</head>
<body>

    <!-- LEFT SIDEBAR -->
    <div class="sidebar" id="appSidebar">
        <div class="sidebar-top">
            <div class="sidebar-logo-header">
                <svg viewBox="0 0 200 200">
                    <circle cx="100" cy="100" r="85" fill="#050505" stroke="#ffffff" stroke-width="4"/>
                    <path d="M 100 25 L 70 85 L 110 85 L 90 115 L 130 115 L 100 175" fill="none" stroke="#ffffff" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span class="sidebar-brand-name">Pyrox</span>
            </div>

            <div class="menu-list">
                <div class="menu-btn" onclick="clearChat()">
                    <svg viewBox="0 0 24 24"><path d="M12 4v16m8-8H4"></path></svg>
                    <span>New Chat</span>
                </div>
                <div class="menu-btn" onclick="alert('Search chat opened')">
                    <svg viewBox="0 0 24 24"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                    <span>Search Chat</span>
                </div>
                <div class="menu-btn" onclick="alert('Library: NCERT Class 9, Python Modules & Content Planner loaded.')">
                    <svg viewBox="0 0 24 24"><path d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                    <span>Library</span>
                </div>
                <div class="menu-btn" onclick="alert('Images generator ready.')">
                    <svg viewBox="0 0 24 24"><path d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                    <span>Images</span>
                </div>
                <div class="menu-btn" onclick="alert('Schedule & Daily routine loaded.')">
                    <svg viewBox="0 0 24 24"><path d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                    <span>Schedule</span>
                </div>
                <div class="menu-btn" onclick="alert('For Students: NCERT Class 9 & Python modules active.')">
                    <svg viewBox="0 0 24 24"><path d="M12 14l9-5-9-5-9 5 9 5z"></path><path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0112 20.055a11.952 11.952 0 01-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z"></path></svg>
                    <span>For Students</span>
                </div>
            </div>
        </div>

        <div class="sidebar-bottom">
            <div class="menu-btn" onclick="alert('Settings panel')">
                <svg viewBox="0 0 24 24"><path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                <span>Settings</span>
            </div>
        </div>
    </div>

    <!-- MAIN WORKSPACE -->
    <div class="main-container">
        
        <!-- TOP NAVBAR (Visible after login) -->
        <div class="top-navbar" id="topNavbar" style="display: none;">
            <div class="header-left">
                <svg class="top-logo" viewBox="0 0 200 200">
                    <circle cx="100" cy="100" r="85" fill="#000000" stroke="#ffffff" stroke-width="4"/>
                    <path d="M 100 25 L 70 85 L 110 85 L 90 115 L 130 115 L 100 175" fill="none" stroke="#ffffff" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span class="top-title">Pyrox</span>
            </div>

            <div class="three-dots-wrapper">
                <button class="dots-btn" onclick="toggleDropdown()">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="5" r="1.5"></circle>
                        <circle cx="12" cy="12" r="1.5"></circle>
                        <circle cx="12" cy="19" r="1.5"></circle>
                    </svg>
                </button>
                <div class="dropdown-menu" id="dropdownMenu">
                    <div class="dropdown-item" onclick="alert('Conversation link copied!')">🔗 Share Conversation</div>
                    <div class="dropdown-item" onclick="alert('Find in chat')">🔍 Find in Chat</div>
                    <div class="dropdown-item" onclick="alert('Chat pinned')">📌 Pin Chat</div>
                    <div class="dropdown-item" onclick="alert('Rename chat')">✏️ Rename</div>
                    <div class="dropdown-item" onclick="alert('Exporting PDF...')">📄 Download PDF / Export</div>
                    <div class="dropdown-item danger" onclick="clearChat()">🗑️ Delete Chat</div>
                </div>
            </div>
        </div>

        <!-- LANDING VIEW (NOT LOGGED IN) -->
        <div class="landing-view" id="landingView">
            <svg class="landing-logo" viewBox="0 0 200 200">
                <circle cx="100" cy="100" r="85" fill="#000000" stroke="#ffffff" stroke-width="5"/>
                <path d="M 100 25 L 70 85 L 110 85 L 90 115 L 130 115 L 100 175" fill="none" stroke="#ffffff" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <div>
                <h1 class="landing-title">Pyrox</h1>
                <h2 class="landing-greeting">How can I help you today?</h2>
            </div>
            <button class="google-login-btn" onclick="loginWithGmail()">
                <svg width="18" height="18" viewBox="0 0 24 24"><path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.66-5.17 3.66-9.17z"/><path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.19v3.15C3.17 21.3 7.24 24 12 24z"/><path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.19C.43 8.12 0 9.87 0 11.7s.43 3.58 1.19 5.12l4.09-3.15z"/><path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.24 0 3.17 2.7 1.19 6.58l4.09 3.15c.95-2.83 3.6-4.98 6.72-4.98z"/></svg>
                Login with Gmail
            </button>
        </div>

        <!-- CHAT APPLICATION VIEW (LOGGED IN) -->
        <div class="chat-app-view" id="chatAppView">
            <div class="chat-container" id="chatContainer">
                <div class="message ai-message">
                    Namaste! Main Pyrox hoon. Batayein, aaj main aapki kya madad kar sakta hoon?
                    <button class="speak-btn" onclick="speakText(this.previousSibling.textContent)">🔊 Suno</button>
                </div>
            </div>

            <!-- INPUT BAR WITH GEMINI WAVE -->
            <div class="input-wrapper">
                <div class="input-box" id="inputBox">
                    <svg class="star-btn" viewBox="0 0 24 24">
                        <defs>
                            <linearGradient id="starGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" stop-color="#9C27B0"/>
                                <stop offset="100%" stop-color="#03A9F4"/>
                            </linearGradient>
                        </defs>
                        <path d="M12 0C12 6.627 6.627 12 0 12C6.627 12 12 17.373 12 24C12 17.373 17.373 12 24 12C17.373 12 12 6.627 12 0Z" fill="url(#starGrad)"/>
                    </svg>

                    <button id="micBtn" class="mic-btn" title="Voice Input" onclick="toggleVoice()">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                            <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                            <line x1="12" y1="19" x2="12" y2="23"></line>
                        </svg>
                    </button>

                    <!-- GEMINI VOICE WAVE BARS -->
                    <div class="gemini-wave-container" id="waveBox">
                        <div class="wave-bar"></div>
                        <div class="wave-bar"></div>
                        <div class="wave-bar"></div>
                        <div class="wave-bar"></div>
                        <div class="wave-bar"></div>
                        <div class="wave-bar"></div>
                        <div class="wave-bar"></div>
                    </div>

                    <input type="text" id="chatInput" class="chat-input-field" placeholder="Ask Pyrox anything..." onkeypress="if(event.key==='Enter') sendMessage();" />

                    <button class="arrow-submit-btn" title="Send" onclick="sendMessage()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                            <line x1="5" y1="12" x2="19" y2="12"></line>
                            <polyline points="12 5 19 12 12 19"></polyline>
                        </svg>
                    </button>
                </div>
                <div class="footer-disclaimer">Pyrox is AI and can make mistakes</div>
            </div>
        </div>
    </div>

    <script>
        let isListening = false;
        let recognition = null;

        function loginWithGmail() {
            document.getElementById('landingView').style.display = 'none';
            document.getElementById('appSidebar').classList.add('active');
            document.getElementById('topNavbar').style.display = 'flex';
            document.getElementById('chatAppView').classList.add('active');
        }

        function toggleDropdown() {
            document.getElementById('dropdownMenu').classList.toggle('show');
        }

        window.onclick = function(event) {
            if (!event.target.closest('.three-dots-wrapper')) {
                const m = document.getElementById('dropdownMenu');
                if(m) m.classList.remove('show');
            }
        }

        function toggleVoice() {
            if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
                alert("Speech Recognition not supported.");
                return;
            }

            const micBtn = document.getElementById('micBtn');
            const inputBox = document.getElementById('inputBox');
            const waveBox = document.getElementById('waveBox');
            const inputField = document.getElementById('chatInput');

            if (isListening) {
                recognition.stop();
                return;
            }

            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.lang = 'hi-IN';

            recognition.onstart = function() {
                isListening = true;
                micBtn.classList.add('active');
                inputBox.classList.add('recording');
                waveBox.classList.add('active');
                inputField.placeholder = "Listening...";
            };

            recognition.onresult = function(event) {
                inputField.value = event.results[0][0].transcript;
                stopVoiceUI();
            };

            recognition.onerror = function() { stopVoiceUI(); };
            recognition.onend = function() { stopVoiceUI(); };

            recognition.start();
        }

        function stopVoiceUI() {
            isListening = false;
            document.getElementById('micBtn').classList.remove('active');
            document.getElementById('inputBox').classList.remove('recording');
            document.getElementById('waveBox').classList.remove('active');
            document.getElementById('chatInput').placeholder = "Ask Pyrox anything...";
        }

        function speakText(text) {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                let clean = text.replace(/[`*_#\\[\\]()]/g, '');
                let utterance = new SpeechSynthesisUtterance(clean);
                utterance.rate = 1.0;
                utterance.pitch = 1.0;
                let voices = window.speechSynthesis.getVoices();
                let v = voices.find(val => val.lang.includes('hi-IN') || val.lang.includes('en-IN')) || voices[0];
                if (v) utterance.voice = v;
                window.speechSynthesis.speak(utterance);
            }
        }

        function sendMessage() {
            const inputField = document.getElementById('chatInput');
            const text = inputField.value.trim();
            if(!text) return;

            const chatContainer = document.getElementById('chatContainer');

            // User bubble
            const userDiv = document.createElement('div');
            userDiv.className = 'message user-message';
            userDiv.innerText = text;
            chatContainer.appendChild(userDiv);

            inputField.value = '';
            chatContainer.scrollTop = chatContainer.scrollHeight;

            // AI response logic with safety & humility guardrails
            setTimeout(() => {
                const aiDiv = document.createElement('div');
                aiDiv.className = 'message ai-message';
                
                let reply = "";
                const lower = text.toLowerCase();

                if (/^[a-z]{5,}$/i.test(text) && !["hello","hi","hey"].includes(lower)) {
                    reply = "Maaf kijiye, main aapka prashna samajh nahi paya. Kripya spasht roop se batayein ki main aapki kya sahayata kar sakta hoon?";
                } 
                else if (lower.includes("stupid") || lower.includes("pagal") || lower.includes("bakwas") || lower.includes("ghatiya")) {
                    reply = "Maaf kijiye, mujhse koi galti hui hogi. Kripya batayein ki main ise kaise sudhaar sakta hoon aur aapki kya madad kar sakta hoon?";
                } 
                else {
                    reply = "Ji, aapki baat samajh aa gayi hai. Bataiye, isme aapki kis prakaar sahayata ki jaye?";
                }

                aiDiv.innerHTML = `${reply} <button class="speak-btn" onclick="speakText(this.previousSibling.textContent)">🔊 Suno</button>`;
                chatContainer.appendChild(aiDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;

                speakText(reply);
            }, 400);
        }

        function clearChat() {
            document.getElementById('chatContainer').innerHTML = `
                <div class="message ai-message">
                    Nayi chat shuru ho chuki hai. Batayein kya karna hai?
                    <button class="speak-btn" onclick="speakText(this.previousSibling.textContent)">🔊 Suno</button>
                </div>
            `;
            if ('speechSynthesis' in window) window.speechSynthesis.cancel();
        }
    </script>
</body>
</html>
"""

# Render in Streamlit
st.components.v1.html(app_code, height=765, scrolling=False)
