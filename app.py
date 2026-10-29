import os
import streamlit as st
from groq import Groq

# 1. Streamlit Base Config
st.set_page_config(
    page_title="Pyrox Studio",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit Default Headers
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    #MainMenu, header, footer { visibility: hidden; }
    .block-container { padding: 0rem; margin: 0rem; }
    </style>
""", unsafe_allow_html=True)

api_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")

# 2. Complete HTML + CSS + JS Unified UI
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

        /* LEFT SIDEBAR */
        .sidebar {
            width: 230px;
            background-color: #050505;
            border-right: 1px solid #1a1a1a;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 16px 12px;
            z-index: 20;
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
            width: 26px;
            height: 26px;
        }
        .sidebar-brand-name {
            font-size: 1.1rem;
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

        /* MAIN WORKSPACE */
        .main-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            align-items: center;
            position: relative;
            height: 100vh;
        }

        /* TOP BAR WITH RIGHT THREE-DOTS MENU */
        .top-navbar {
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 24px;
            border-bottom: 1px solid #121212;
            position: relative;
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

        /* THREE DOTS DROPDOWN MENU */
        .three-dots-wrapper {
            position: relative;
        }
        .dots-btn {
            background: transparent;
            border: none;
            color: #aaaaaa;
            cursor: pointer;
            padding: 6px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: color 0.2s, background 0.2s;
        }
        .dots-btn:hover {
            color: #ffffff;
            background-color: #1a1a1a;
        }
        .dropdown-menu {
            position: absolute;
            top: 40px;
            right: 0;
            width: 210px;
            background-color: #0d0d0d;
            border: 1px solid #222222;
            border-radius: 12px;
            padding: 6px 0;
            display: none;
            flex-direction: column;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            z-index: 100;
        }
        .dropdown-menu.show {
            display: flex;
        }
        .dropdown-item {
            padding: 10px 16px;
            font-size: 13px;
            color: #cccccc;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: background 0.2s, color 0.2s;
        }
        .dropdown-item:hover {
            background-color: #1a1a1a;
            color: #ffffff;
        }
        .dropdown-item.danger {
            color: #ef4444;
        }
        .dropdown-item.danger:hover {
            background-color: rgba(239, 68, 68, 0.1);
        }

        /* CHAT WORKSPACE AREA */
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
        }

        /* INPUT AREA WITH GEMINI-STYLE WAVE */
        .input-wrapper {
            width: 100%;
            max-width: 820px;
            position: relative;
            margin-bottom: 20px;
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
            border-color: #ef4444;
            box-shadow: 0 0 12px rgba(239, 68, 68, 0.2);
        }
        .star-btn {
            cursor: pointer;
            width: 22px;
            height: 22px;
            flex-shrink: 0;
        }

        /* GEMINI WAVE ANIMATION */
        .gemini-wave-container {
            display: flex;
            align-items: center;
            gap: 3px;
            height: 18px;
            width: 110px;
            display: none;
        }
        .gemini-wave-container.active {
            display: flex;
        }
        .wave-bar {
            flex: 1;
            background-color: #ef4444;
            border-radius: 2px;
            height: 20%;
            animation: waveMotion 0.8s infinite ease-in-out alternate;
        }
        .wave-bar:nth-child(1) { animation-delay: 0.1s; }
        .wave-bar:nth-child(2) { animation-delay: 0.3s; }
        .wave-bar:nth-child(3) { animation-delay: 0.2s; }
        .wave-bar:nth-child(4) { animation-delay: 0.4s; }
        .wave-bar:nth-child(5) { animation-delay: 0.15s; }
        .wave-bar:nth-child(6) { animation-delay: 0.35s; }

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
        .mic-btn.active { color: #ef4444; }

        /* CLEAN ARROW SUBMIT BUTTON ONLY */
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
    </style>
</head>
<body>

    <!-- LEFT SIDEBAR WITH BRAND LOGO & OPTIONS -->
    <div class="sidebar">
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
                <div class="menu-btn">
                    <svg viewBox="0 0 24 24"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                    <span>Search Chat</span>
                </div>
                <div class="menu-btn">
                    <svg viewBox="0 0 24 24"><path d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                    <span>Library</span>
                </div>
                <div class="menu-btn">
                    <svg viewBox="0 0 24 24"><path d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                    <span>Images</span>
                </div>
                <div class="menu-btn">
                    <svg viewBox="0 0 24 24"><path d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                    <span>Schedule</span>
                </div>
                <div class="menu-btn">
                    <svg viewBox="0 0 24 24"><path d="M12 14l9-5-9-5-9 5 9 5z"></path><path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0112 20.055a11.952 11.952 0 01-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z"></path></svg>
                    <span>For Students</span>
                </div>
            </div>
        </div>

        <div class="sidebar-bottom">
            <div class="menu-btn">
                <svg viewBox="0 0 24 24"><path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                <span>Settings</span>
            </div>
        </div>
    </div>

    <!-- MAIN WORKSPACE -->
    <div class="main-container">
        
        <!-- TOP NAVBAR WITH BRAND & RIGHT TRIPLE DOT MENU -->
        <div class="top-navbar">
            <div class="header-left">
                <svg class="top-logo" viewBox="0 0 200 200">
                    <circle cx="100" cy="100" r="85" fill="#000000" stroke="#ffffff" stroke-width="4"/>
                    <path d="M 100 25 L 70 85 L 110 85 L 90 115 L 130 115 L 100 175" fill="none" stroke="#ffffff" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span class="top-title">Pyrox</span>
            </div>

            <!-- THREE DOTS CONTROL MENU -->
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
                    <div class="dropdown-item">🔍 Find in Chat</div>
                    <div class="dropdown-item">📌 Pin Chat</div>
                    <div class="dropdown-item">✏️ Rename</div>
                    <div class="dropdown-item">📄 Download PDF / Export</div>
                    <div class="dropdown-item danger" onclick="clearChat()">🗑️ Delete Chat</div>
                </div>
            </div>
        </div>

        <!-- CHAT MESSAGES -->
        <div class="chat-container" id="chatContainer">
            <div class="message ai-message">
                How can I help you today?
            </div>
        </div>

        <!-- INPUT BAR AREA -->
        <div class="input-wrapper">
            <div class="input-box" id="inputBox">
                
                <!-- STAR ICON -->
                <svg class="star-btn" viewBox="0 0 24 24">
                    <defs>
                        <linearGradient id="starGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#9C27B0"/>
                            <stop offset="100%" stop-color="#03A9F4"/>
                        </linearGradient>
                    </defs>
                    <path d="M12 0C12 6.627 6.627 12 0 12C6.627 12 12 17.373 12 24C12 17.373 17.373 12 24 12C17.373 12 12 6.627 12 0Z" fill="url(#starGrad)"/>
                </svg>

                <!-- MIC BUTTON -->
                <button id="micBtn" class="mic-btn" title="Voice Input" onclick="toggleVoice()">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                        <line x1="12" y1="19" x2="12" y2="23"></line>
                    </svg>
                </button>

                <!-- GEMINI WAVE BARS -->
                <div class="gemini-wave-container" id="waveBox">
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                </div>

                <!-- TEXT INPUT -->
                <input type="text" id="chatInput" class="chat-input-field" placeholder="How can I help you today?" onkeypress="if(event.key==='Enter') sendMessage();" />

                <!-- CLEAN ARROW BUTTON -->
                <button class="arrow-submit-btn" title="Send" onclick="sendMessage()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                        <line x1="5" y1="12" x2="19" y2="12"></line>
                        <polyline points="12 5 19 12 12 19"></polyline>
                    </svg>
                </button>
            </div>
        </div>
    </div>

    <script>
        let isListening = false;
        let recognition = null;

        function toggleDropdown() {
            const menu = document.getElementById('dropdownMenu');
            menu.classList.toggle('show');
        }

        window.onclick = function(event) {
            if (!event.target.closest('.three-dots-wrapper')) {
                document.getElementById('dropdownMenu').classList.remove('show');
            }
        }

        function toggleVoice() {
            if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
                alert("Speech Recognition not supported in browser.");
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
            document.getElementById('chatInput').placeholder = "How can I help you today?";
        }

        // HIGH QUALITY SHARP & CRISP VOICE ENGINE (Edge Neural Style)
        function speakResponse(text) {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                let cleanText = text.replace(/[`*_#\\[\\]()]/g, '');
                let utterance = new SpeechSynthesisUtterance(cleanText);
                utterance.rate = 1.0;
                utterance.pitch = 1.0;

                let voices = window.speechSynthesis.getVoices();
                // Select Best Crisp Neural Voice
                let targetVoice = voices.find(v => v.name.includes("Swara") || v.name.includes("Natural") || v.lang.includes("hi-IN") || v.lang.includes("en-IN")) || voices[0];
                if (targetVoice) utterance.voice = targetVoice;

                window.speechSynthesis.speak(utterance);
            }
        }

        function sendMessage() {
            const inputField = document.getElementById('chatInput');
            const text = inputField.value.trim();
            if(!text) return;

            const chatContainer = document.getElementById('chatContainer');

            // Append User Message
            const userDiv = document.createElement('div');
            userDiv.className = 'message user-message';
            userDiv.innerText = text;
            chatContainer.appendChild(userDiv);

            inputField.value = '';
            chatContainer.scrollTop = chatContainer.scrollHeight;

            // SMART HUMBLE RESPONSE LOGIC (No Spam / No Arrogance)
            setTimeout(() => {
                const aiDiv = document.createElement('div');
                aiDiv.className = 'message ai-message';
                
                let reply = "";
                const lower = text.toLowerCase();

                // Handling Gibberish / Random letters
                if (/^[a-z]{5,}$/i.test(text) && !["hello","hi","hey"].includes(lower)) {
                    reply = "माफ़ कीजिए, मैं आपका प्रश्न समझ नहीं पाया। कृपया स्पष्ट रूप से बताएं कि मैं आपकी क्या सहायता कर सकता हूँ?";
                } 
                // Handling Anger / Abusive / Frustration politely
                else if (lower.includes("stupid") || lower.includes("pagal") || lower.includes("bakwas") || lower.includes("ghatiya")) {
                    reply = "माफ़ कीजिए, मुझसे कोई गलती हुई होगी। कृपया बताएं कि मैं इसे कैसे सुधार सकता हूँ और आपकी क्या मदद कर सकता हूँ?";
                } 
                // General Polite Response
                else {
                    reply = "जी, आपकी बात समझ आ गई। बताइए, इसमें आपकी किस प्रकार सहायता की जाए?";
                }

                aiDiv.innerText = reply;
                chatContainer.appendChild(aiDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;

                speakResponse(reply);
            }, 400);
        }

        function clearChat() {
            document.getElementById('chatContainer').innerHTML = `
                <div class="message ai-message">
                    How can I help you today?
                </div>
            `;
            if ('speechSynthesis' in window) window.speechSynthesis.cancel();
        }
    </script>
</body>
</html>
"""

# Render Full Studio UI in Streamlit
st.components.v1.html(app_code, height=760, scrolling=False)


        
