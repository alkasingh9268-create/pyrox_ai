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

# Hide Default Streamlit Elements & Force Zero Padding
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    #MainMenu, header, footer { visibility: hidden; }
    .block-container { padding: 0rem !important; margin: 0rem !important; }
    </style>
""", unsafe_allow_html=True)

api_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")
client = Groq(api_key=api_key) if api_key else None

# Function to get Groq AI response with Full Chat History Context & Sense of Humor
def get_groq_response(messages_history):
    if not client:
        return "⚠️ Groq API Key missing in Streamlit Secrets!"
    try:
        formatted_messages = [
            {
                "role": "system",
                "content": (
                    "You are Pyrox, an exceptionally intelligent, adaptive, and emotionally aware AI collaborator with a great sense of humor. "
                    "Remember the full conversation history with the user. Never forget past context. "
                    "Talk in a smooth, natural blend of Hinglish (Hindi + English) with subtle, cool emojis ✨. "
                    "Be witty, smart, and precise."
                )
            }
        ]
        for msg in messages_history:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=formatted_messages,
            temperature=0.75,
            max_tokens=600,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error connecting to Groq: {str(e)}"

# 2. Complete HTML + CSS + JS Studio UI with Collapsible Sidebar & Fixed Viewport (No MS-TTS Bloat)
app_code = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pyrox</title>
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

        /* COLLAPSIBLE SIDEBAR WITH TWO PARALLEL LINES TOGGLE */
        .sidebar {
            width: 0px;
            background-color: #050505;
            border-right: 0px solid #141414;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 0px;
            z-index: 20;
            transition: width 0.3s ease, padding 0.3s ease, border-right 0.3s ease;
            overflow: hidden;
        }
        .sidebar.open {
            width: 220px;
            padding: 12px 10px;
            border-right: 1px solid #141414;
        }
        .sidebar-logo-header {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 4px 6px;
            margin-bottom: 10px;
        }
        .sidebar-brand-name {
            font-size: 1.1rem;
            font-weight: 700;
            color: #ffffff;
            white-space: nowrap;
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
            padding: 8px 10px;
            color: #aaaaaa;
            font-size: 13px;
            border-radius: 8px;
            cursor: pointer;
            white-space: nowrap;
            transition: background 0.2s, color 0.2s;
        }
        .menu-btn:hover {
            background-color: #141414;
            color: #ffffff;
        }

        /* MAIN CONTAINER - COMPACT HEIGHT TO AVOID SCROLLING */
        .main-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            align-items: center;
            height: 100vh;
            padding-top: 2px;
            padding-bottom: 6px;
        }

        /* TOP NAVBAR WITH TWO PARALLEL LINES */
        .top-navbar {
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 4px 15px;
        }
        .toggle-menu-btn {
            background: transparent;
            border: none;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            gap: 4px;
            padding: 6px;
        }
        .toggle-line {
            width: 20px;
            height: 2px;
            background-color: #aaaaaa;
            border-radius: 2px;
            transition: background 0.2s;
        }
        .toggle-menu-btn:hover .toggle-line {
            background-color: #ffffff;
        }

        /* CENTER LANDING HEADER */
        .center-landing-header {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            gap: 2px;
            margin-top: 5px;
        }
        .brand-title-box {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .brand-logo-large {
            width: 32px;
            height: 32px;
        }
        .brand-name-large {
            font-size: 1.6rem;
            font-weight: 800;
            color: #ffffff;
        }
        .greeting-subtext {
            font-size: 1.05rem;
            color: #9ca3af;
        }

        /* CHAT MESSAGES AREA */
        .chat-container {
            width: 100%;
            max-width: 700px;
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 10px;
            padding: 5px 12px;
        }
        .message {
            display: flex;
            flex-direction: column;
            max-width: 82%;
            line-height: 1.45;
            font-size: 0.93rem;
        }
        .user-message {
            align-self: flex-end;
            background-color: #1c1c1e;
            color: #ffffff;
            padding: 8px 14px;
            border-radius: 14px 14px 2px 14px;
            border: 1px solid #2d2d2d;
        }
        .ai-message {
            align-self: flex-start;
            background-color: #080808;
            color: #f0f0f0;
            padding: 10px 14px;
            border-radius: 14px 14px 14px 2px;
            border: 1px solid #1a1a1a;
        }

        /* INPUT BAR AREA */
        .input-wrapper {
            width: 100%;
            max-width: 700px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 3px;
            padding: 0 12px;
            margin-bottom: 2px;
        }
        .input-box {
            width: 100%;
            background-color: #080808;
            border: 1px solid #222222;
            border-radius: 26px;
            padding: 6px 12px;
            display: flex;
            align-items: center;
            gap: 10px;
            position: relative;
        }
        .input-box.recording {
            border-color: #ef4444;
            box-shadow: 0 0 12px rgba(239, 68, 68, 0.25);
        }

        /* TOOLTIP FOR STAR BUTTON */
        [data-tooltip] {
            position: relative;
        }
        [data-tooltip]:hover::after {
            content: attr(data-tooltip);
            position: absolute;
            bottom: 125%;
            left: 0;
            background-color: #1f1f1f;
            color: #ffffff;
            font-size: 11px;
            padding: 4px 8px;
            border-radius: 6px;
            white-space: nowrap;
            border: 1px solid #333;
            z-index: 1000;
        }

        .star-btn {
            cursor: pointer;
            width: 20px;
            height: 20px;
            flex-shrink: 0;
        }

        /* ULTRA THIN & WIDE GEMINI WAVE BARS */
        .gemini-wave-container {
            display: flex;
            align-items: center;
            gap: 2.5px;
            height: 20px;
            flex: 1;
            padding: 0 8px;
            display: none;
        }
        .gemini-wave-container.active {
            display: flex;
        }
        .wave-bar {
            flex: 1;
            background: linear-gradient(180deg, #ef4444, #3b82f6);
            border-radius: 2px;
            height: 20%;
            animation: waveMotion 0.45s infinite ease-in-out alternate;
        }
        @keyframes waveMotion {
            0% { height: 10%; }
            100% { height: 100%; }
        }

        .chat-input-field {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: #ffffff;
            font-size: 0.93rem;
            padding: 4px 0;
        }
        .chat-input-field::placeholder { color: #555555; }

        .mic-btn {
            background: transparent;
            border: none;
            color: #aaaaaa;
            cursor: pointer;
            display: flex;
            align-items: center;
        }
        .mic-btn.active { color: #ef4444; }

        .arrow-submit-btn {
            width: 28px;
            height: 28px;
            background-color: #ffffff;
            color: #000000;
            border: none;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            flex-shrink: 0;
        }

        .footer-disclaimer {
            font-size: 10px;
            color: #444444;
            text-align: center;
        }
    </style>
</head>
<body>

    <!-- COLLAPSIBLE SIDEBAR -->
    <div class="sidebar" id="appSidebar">
        <div>
            <div class="sidebar-logo-header">
                <svg width="22" height="22" viewBox="0 0 200 200">
                    <circle cx="100" cy="100" r="85" fill="#050505" stroke="#ffffff" stroke-width="4"/>
                    <path d="M 100 25 L 70 85 L 110 85 L 90 115 L 130 115 L 100 175" fill="none" stroke="#ffffff" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span class="sidebar-brand-name">Pyrox</span>
            </div>

            <div class="menu-list">
                <div class="menu-btn" onclick="clearChat()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 4v16m8-8H4"></path></svg>
                    <span>New Chat</span>
                </div>
                <div class="menu-btn" onclick="alert('Search Chat')">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                    <span>Search Chat</span>
                </div>
                <div class="menu-btn" onclick="alert('Library')">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                    <span>Library</span>
                </div>
                <div class="menu-btn" onclick="alert('For Students')">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 14l9-5-9-5-9 5 9 5z"></path></svg>
                    <span>For Students</span>
                </div>
            </div>
        </div>
    </div>

    <!-- MAIN WORKSPACE -->
    <div class="main-container">
        
        <!-- TOP NAVBAR WITH TWO PARALLEL LINES -->
        <div class="top-navbar">
            <button class="toggle-menu-btn" onclick="toggleSidebar()" data-tooltip="Toggle Menu">
                <div class="toggle-line"></div>
                <div class="toggle-line"></div>
            </button>
        </div>

        <!-- CENTER LANDING HEADER -->
        <div class="center-landing-header" id="landingHeader">
            <div class="brand-title-box">
                <svg class="brand-logo-large" viewBox="0 0 200 200">
                    <circle cx="100" cy="100" r="85" fill="#000000" stroke="#ffffff" stroke-width="5"/>
                    <path d="M 100 25 L 70 85 L 110 85 L 90 115 L 130 115 L 100 175" fill="none" stroke="#ffffff" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span class="brand-name-large">Pyrox</span>
            </div>
            <div class="greeting-subtext">Hi, how can I help you today? ✨</div>
        </div>

        <!-- CHAT MESSAGES CONTAINER -->
        <div class="chat-container" id="chatContainer"></div>

        <!-- INPUT BAR AREA -->
        <div class="input-wrapper">
            <div class="input-box" id="inputBox">
                <!-- STAR BUTTON WITH EXACT TOOLTIP -->
                <svg class="star-btn" viewBox="0 0 24 24" data-tooltip="Find and Photo Images Uploaded" onclick="alert('Select File / Photo to attach')">
                    <defs>
                        <linearGradient id="starGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#9C27B0"/>
                            <stop offset="100%" stop-color="#03A9F4"/>
                        </linearGradient>
                    </defs>
                    <path d="M12 0C12 6.627 6.627 12 0 12C6.627 12 12 17.373 12 24C12 17.373 17.373 12 24 12C17.373 12 12 6.627 12 0Z" fill="url(#starGrad)"/>
                </svg>

                <button id="micBtn" class="mic-btn" onclick="toggleVoice()">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                        <line x1="12" y1="19" x2="12" y2="23"></line>
                    </svg>
                </button>

                <div class="gemini-wave-container" id="waveBox">
                    <div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div>
                    <div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div>
                </div>

                <input type="text" id="chatInput" class="chat-input-field" placeholder="Ask Pyrox anything..." onkeypress="if(event.key==='Enter') sendMessage();" />

                <button class="arrow-submit-btn" onclick="sendMessage()">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
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

        function toggleSidebar() {
            document.getElementById('appSidebar').classList.toggle('open');
        }

        function toggleVoice() {
            const micBtn = document.getElementById('micBtn');
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

            recognition.onstart = function() {
                isListening = true;
                micBtn.classList.add('active');
                inputBox.classList.add('recording');
                waveBox.classList.add('active');
                inputField.style.display = 'none';
            };

            recognition.onresult = function(event) {
                let text = event.results[event.results.length - 1][0].transcript;
                inputField.value = text;
            };

            try { recognition.start(); } catch(e) {}
        }

        function stopVoiceUI() {
            isListening = false;
            document.getElementById('micBtn').classList.remove('active');
            document.getElementById('inputBox').classList.remove('recording');
            document.getElementById('waveBox').classList.remove('active');
            document.getElementById('chatInput').style.display = 'block';
        }

        function sendMessage() {
            if (isListening && recognition) { recognition.stop(); stopVoiceUI(); }
            const inputField = document.getElementById('chatInput');
            const text = inputField.value.trim();
            if(!text) return;

            const landingHeader = document.getElementById('landingHeader');
            if (landingHeader) landingHeader.style.display = 'none';

            const url = new URL(window.location.href);
            url.searchParams.set('q', encodeURIComponent(text));
            window.location.href = url.toString();
        }

        function clearChat() {
            const url = new URL(window.location.href);
            url.searchParams.delete('q');
            window.location.href = url.toString();
        }
    </script>
</body>
</html>
"""

# Session State Management for Chat History & Memory
if "messages" not in st.session_state:
    st.session_state.messages = []

# Handle Backend Interaction with Groq (Full History Context)
query_params = st.query_params
if "q" in query_params:
    user_prompt = query_params["q"]
    st.query_params.clear()
    
    if user_prompt:
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        reply = get_groq_response(st.session_state.messages)
        st.session_state.messages.append({
            "role": "assistant",
            "content": reply
        })

# Render Studio App Interface (Fixed Compact Height to Prevent Scrolling)
st.components.v1.html(app_code, height=620, scrolling=False)

# Render Chat history dynamically with full context
if st.session_state.messages:
    chat_history_html = "<div style='max-width:700px; margin:auto; padding: 10px; color:#fff;'>"
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            chat_history_html += f"<div style='background:#1c1c1e; padding:10px 16px; border-radius:14px; margin:6px 0; max-width:700px; text-align:right;'>👤 {msg['content']}</div>"
        else:
            chat_history_html += f"<div style='background:#080808; border:1px solid #1a1a1a; padding:12px 18px; border-radius:14px; margin:6px 0; max-width:700px;'>🤖 {msg['content']}</div>"
    chat_history_html += "</div>"
    st.markdown(chat_history_html, unsafe_allow_html=True)
