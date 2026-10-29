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

# 2. Complete HTML + CSS + JS Studio UI
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

        /* SIDEBAR */
        .sidebar {
            width: 230px;
            background-color: #050505;
            border-right: 1px solid #1a1a1a;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 12px 10px;
            z-index: 20;
        }
        .sidebar-logo-header {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 4px 6px;
            margin-bottom: 10px;
        }
        .sidebar-logo-header svg {
            width: 24px;
            height: 24px;
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
            gap: 3px;
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
            transition: background 0.2s, color 0.2s;
            position: relative;
        }
        .menu-btn:hover {
            background-color: #141414;
            color: #ffffff;
        }
        .menu-btn svg {
            width: 17px;
            height: 17px;
            stroke: currentColor;
            fill: none;
            stroke-width: 2;
        }
        .sidebar-bottom {
            border-top: 1px solid #1a1a1a;
            padding-top: 8px;
        }

        /* TOOLTIP HOVER HELPER */
        [data-tooltip] {
            position: relative;
        }
        [data-tooltip]:hover::after {
            content: attr(data-tooltip);
            position: absolute;
            bottom: 115%;
            left: 50%;
            transform: translateX(-50%);
            background-color: #1f1f1f;
            color: #ffffff;
            font-size: 11px;
            font-weight: 500;
            padding: 4px 8px;
            border-radius: 6px;
            white-space: nowrap;
            border: 1px solid #333;
            pointer-events: none;
            z-index: 1000;
            box-shadow: 0 4px 10px rgba(0,0,0,0.5);
        }

        /* MAIN CONTAINER (ZERO SCROLL) */
        .main-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            align-items: center;
            height: 100vh;
            padding-top: 4px;
            padding-bottom: 8px;
        }

        /* TOP NAVBAR */
        .top-navbar {
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding: 4px 20px;
            position: relative;
        }
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
            top: 36px;
            right: 0;
            width: 210px;
            background-color: #0d0d0d;
            border: 1px solid #222222;
            border-radius: 12px;
            padding: 6px 0;
            display: none;
            flex-direction: column;
            box-shadow: 0 10px 25px rgba(0,0,0,0.6);
            z-index: 100;
        }
        .dropdown-menu.show {
            display: flex;
        }
        .dropdown-item {
            padding: 9px 16px;
            font-size: 13px;
            color: #cccccc;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: background 0.2s;
        }
        .dropdown-item:hover {
            background-color: #1a1a1a;
            color: #ffffff;
        }
        .dropdown-item.login-item {
            border-bottom: 1px solid #222;
            color: #3b82f6;
            font-weight: 600;
        }

        /* CENTER LANDING HEADER */
        .center-landing-header {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            gap: 4px;
            margin-top: 2px;
        }
        .brand-title-box {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .brand-logo-large {
            width: 38px;
            height: 38px;
        }
        .brand-name-large {
            font-size: 1.9rem;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: -0.5px;
        }
        .greeting-subtext {
            font-size: 1.2rem;
            font-weight: 500;
            color: #d1d5db;
        }

        /* CHAT MESSAGES AREA */
        .chat-container {
            width: 100%;
            max-width: 800px;
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
            padding: 5px 15px;
            margin-top: 5px;
        }
        .message {
            display: flex;
            flex-direction: column;
            max-width: 82%;
            line-height: 1.5;
            font-size: 0.95rem;
        }
        .user-message {
            align-self: flex-end;
            background-color: #1c1c1e;
            color: #ffffff;
            padding: 10px 16px;
            border-radius: 16px 16px 4px 16px;
            border: 1px solid #2d2d2d;
        }
        .ai-message {
            align-self: flex-start;
            background-color: #080808;
            color: #f0f0f0;
            padding: 12px 18px;
            border-radius: 16px 16px 16px 4px;
            border: 1px solid #1a1a1a;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        /* AUDIO PLAY BUTTON */
        .audio-play-btn {
            background-color: #161618;
            color: #3b82f6;
            border: 1px solid #2a2a2e;
            border-radius: 8px;
            padding: 6px 12px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            align-self: flex-start;
            transition: background 0.2s, border-color 0.2s;
        }
        .audio-play-btn:hover {
            background-color: #1f1f23;
            border-color: #3b82f6;
            color: #60a5fa;
        }
        .audio-play-btn svg {
            width: 14px;
            height: 14px;
            fill: currentColor;
        }

        /* INPUT BAR AREA */
        .input-wrapper {
            width: 100%;
            max-width: 800px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            padding: 0 15px;
        }
        .input-box {
            width: 100%;
            background-color: #080808;
            border: 1px solid #222222;
            border-radius: 26px;
            padding: 8px 14px;
            display: flex;
            align-items: center;
            gap: 10px;
            position: relative;
            transition: border-color 0.3s;
        }
        .input-box.recording {
            border-color: #3b82f6;
            box-shadow: 0 0 12px rgba(59, 130, 246, 0.25);
        }
        .star-btn {
            cursor: pointer;
            width: 20px;
            height: 20px;
            flex-shrink: 0;
        }

        /* GEMINI WAVE BARS */
        .gemini-wave-container {
            display: flex;
            align-items: center;
            gap: 3px;
            height: 18px;
            width: 120px;
            display: none;
        }
        .gemini-wave-container.active {
            display: flex;
        }
        .wave-bar {
            flex: 1;
            background: linear-gradient(180deg, #3b82f6, #ec4899);
            border-radius: 3px;
            height: 20%;
            animation: waveMotion 0.7s infinite ease-in-out alternate;
        }
        .wave-bar:nth-child(1) { animation-delay: 0.1s; }
        .wave-bar:nth-child(2) { animation-delay: 0.3s; }
        .wave-bar:nth-child(3) { animation-delay: 0.2s; }
        .wave-bar:nth-child(4) { animation-delay: 0.5s; }
        .wave-bar:nth-child(5) { animation-delay: 0.15s; }

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
            font-size: 0.95rem;
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
            justify-content: center;
            transition: color 0.2s;
        }
        .mic-btn:hover { color: #ffffff; }
        .mic-btn.active { color: #3b82f6; }

        .arrow-submit-btn {
            width: 30px;
            height: 30px;
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

        .footer-disclaimer {
            font-size: 10.5px;
            color: #555555;
            text-align: center;
        }
    </style>
</head>
<body>

    <!-- LEFT SIDEBAR -->
    <div class="sidebar">
        <div>
            <div class="sidebar-logo-header">
                <svg viewBox="0 0 200 200">
                    <circle cx="100" cy="100" r="85" fill="#050505" stroke="#ffffff" stroke-width="4"/>
                    <path d="M 100 25 L 70 85 L 110 85 L 90 115 L 130 115 L 100 175" fill="none" stroke="#ffffff" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span class="sidebar-brand-name">Pyrox</span>
            </div>

            <div class="menu-list">
                <div class="menu-btn" onclick="clearChat()" data-tooltip="New Chat">
                    <svg viewBox="0 0 24 24"><path d="M12 4v16m8-8H4"></path></svg>
                    <span>New Chat</span>
                </div>
                <div class="menu-btn" onclick="alert('Search chat history')" data-tooltip="Search Chat">
                    <svg viewBox="0 0 24 24"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                    <span>Search Chat</span>
                </div>
                <div class="menu-btn" onclick="alert('Library: Your past discussions & study notes')" data-tooltip="Library">
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
            <div class="menu-btn" onclick="alert('Settings Panel')" data-tooltip="Settings">
                <svg viewBox="0 0 24 24"><path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                <span>Settings</span>
            </div>
        </div>
    </div>

    <!-- MAIN WORKSPACE -->
    <div class="main-container">
        
        <!-- TOP NAVBAR WITH RIGHT TRIPLE DOTS -->
        <div class="top-navbar">
            <div class="three-dots-wrapper">
                <button class="dots-btn" onclick="toggleDropdown()" data-tooltip="More Options">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="5" r="1.5"></circle>
                        <circle cx="12" cy="12" r="1.5"></circle>
                        <circle cx="12" cy="19" r="1.5"></circle>
                    </svg>
                </button>
                <div class="dropdown-menu" id="dropdownMenu">
                    <div class="dropdown-item login-item" onclick="alert('Redirecting to Gmail Login...')">
                        📧 Login with Gmail
                    </div>
                    <div class="dropdown-item" onclick="alert('Conversation link copied!')">🔗 Share Conversation</div>
                    <div class="dropdown-item" onclick="alert('Find in chat')">🔍 Find in Chat</div>
                    <div class="dropdown-item" onclick="alert('Chat pinned')">📌 Pin Chat</div>
                    <div class="dropdown-item" onclick="alert('Exporting PDF...')">📄 Download PDF / Export</div>
                    <div class="dropdown-item" style="color:#ef4444;" onclick="clearChat()">🗑️ Delete Chat</div>
                </div>
            </div>
        </div>

        <!-- CENTER LANDING HEADER -->
        <div class="center-landing-header">
            <div class="brand-title-box">
                <svg class="brand-logo-large" viewBox="0 0 200 200">
                    <circle cx="100" cy="100" r="85" fill="#000000" stroke="#ffffff" stroke-width="5"/>
                    <path d="M 100 25 L 70 85 L 110 85 L 90 115 L 130 115 L 100 175" fill="none" stroke="#ffffff" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span class="brand-name-large">Pyrox</span>
            </div>
            <div class="greeting-subtext">Hi, how can I help you today?</div>
        </div>

        <!-- CHAT MESSAGES CONTAINER -->
        <div class="chat-container" id="chatContainer"></div>

        <!-- INPUT BAR AREA -->
        <div class="input-wrapper">
            <div class="input-box" id="inputBox">
                
                <!-- STAR ICON WITH HOVER TOOLTIP -->
                <svg class="star-btn" viewBox="0 0 24 24" data-tooltip="Attach File & Photo" onclick="alert('Select File / Photo to attach')">
                    <defs>
                        <linearGradient id="starGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#9C27B0"/>
                            <stop offset="100%" stop-color="#03A9F4"/>
                        </linearGradient>
                    </defs>
                    <path d="M12 0C12 6.627 6.627 12 0 12C6.627 12 12 17.373 12 24C12 17.373 17.373 12 24 12C17.373 12 12 6.627 12 0Z" fill="url(#starGrad)"/>
                </svg>

                <!-- MIC BUTTON WITH HOVER TOOLTIP -->
                <button id="micBtn" class="mic-btn" data-tooltip="Voice Input" onclick="toggleVoice()">
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
                </div>

                <!-- CHAT INPUT FIELD -->
                <input type="text" id="chatInput" class="chat-input-field" placeholder="Ask Pyrox anything..." onkeypress="if(event.key==='Enter') sendMessage();" />

                <!-- ARROW SUBMIT BUTTON WITH HOVER TOOLTIP -->
                <button class="arrow-submit-btn" data-tooltip="Submit" onclick="sendMessage()">
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

        function toggleDropdown() {
            document.getElementById('dropdownMenu').classList.toggle('show');
        }

        window.onclick = function(event) {
            if (!event.target.closest('.three-dots-wrapper')) {
                const m = document.getElementById('dropdownMenu');
                if(m) m.classList.remove('show');
            }
        }

        function openStudentSetup() {
            let goal = prompt("आप किस परीक्षा या कक्षा की तैयारी कर रहे हैं? (जैसे: NEET, JEE, School, College)");
            if(!goal) return;
            let standard = prompt("आपकी कक्षा या वर्ष कौन सा है? (जैसे: Class 9, Class 11, B.Tech 1st Year)");
            if(!standard) return;
            
            alert("बहुत बढ़िया! " + standard + " (" + goal + ") के लिए आपका स्टडी रूटीन सेट कर दिया गया है। अब आप मुझसे कोई भी चैप्टर या टॉपिक पूछ सकते हैं!");
        }

        function toggleVoice() {
            if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
                alert("Speech recognition not supported.");
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
                micBtn.setAttribute('data-tooltip', 'Stop Microphone');
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
            const micBtn = document.getElementById('micBtn');
            micBtn.classList.remove('active');
            micBtn.setAttribute('data-tooltip', 'Voice Input');
            document.getElementById('inputBox').classList.remove('recording');
            document.getElementById('waveBox').classList.remove('active');
            document.getElementById('chatInput').placeholder = "Ask Pyrox anything...";
        }

        // FIXED AND ROBUST MALE SPEECH SYNTHESIS ENGINE
        function speakText(text) {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel(); // Stop any ongoing speech
                
                let cleanText = text.replace(/[`*_#\\[\\]()]/g, '');
                let utterance = new SpeechSynthesisUtterance(cleanText);
                utterance.rate = 1.0;
                utterance.pitch = 0.95; // Masculine tone

                // Try to pick a proper voice immediately or wait for voices
                let voices = window.speechSynthesis.getVoices();
                if (voices.length === 0) {
                    window.speechSynthesis.onvoiceschanged = () => {
                        voices = window.speechSynthesis.getVoices();
                        assignVoiceAndSpeak(utterance, voices);
                    };
                } else {
                    assignVoiceAndSpeak(utterance, voices);
                }
            } else {
                alert("Speech synthesis not supported in this browser.");
            }
        }

        function assignVoiceAndSpeak(utterance, voices) {
            let targetVoice = voices.find(v => 
                (v.name.includes("Madhur") || v.name.includes("Prabhat") || v.name.includes("Male") || v.name.includes("David") || v.name.includes("George") || v.name.includes("Hemant")) &&
                (v.lang.includes("hi") || v.lang.includes("en"))
            ) || voices.find(v => v.lang.includes("hi-IN") || v.lang.includes("en-IN")) || voices[0];
            
            if (targetVoice) {
                utterance.voice = targetVoice;
            }
            window.speechSynthesis.speak(utterance);
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

            // AI Response with Working Audio Button
            setTimeout(() => {
                const aiDiv = document.createElement('div');
                aiDiv.className = 'message ai-message';
                
                let reply = "";
                const lower = text.toLowerCase();

                if (/^[a-z]{5,}$/i.test(text) && !["hello","hi","hey"].includes(lower)) {
                    reply = "माफ़ कीजिए, मैं आपका प्रश्न समझ नहीं पाया। कृपया स्पष्ट रूप से बताएं कि मैं आपकी क्या सहायता कर सकता हूँ?";
                } 
                else if (lower.includes("stupid") || lower.includes("pagal") || lower.includes("bakwas") || lower.includes("ghatiya")) {
                    reply = "माफ़ कीजिए, मुझसे कोई गलती हुई होगी। कृपया बताएं कि मैं इसे कैसे सुधार सकता हूँ और आपकी क्या मदद कर सकता हूँ?";
                } 
                else {
                    reply = "जी, आपकी बात समझ आ गई है। बताइए, इसमें आपकी किस प्रकार सहायता की जाए?";
                }

                // Clean string escaping for HTML inline function call
                const safeReply = reply.replace(/'/g, "\\'").replace(/"/g, '&quot;');

                aiDiv.innerHTML = `
                    <div>${reply}</div>
                    <button class="audio-play-btn" onclick="speakText('${safeReply}')">
                        <svg viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/></svg>
                        Listen to audio
                    </button>
                `;
                chatContainer.appendChild(aiDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;

                speakText(reply);
            }, 400);
        }

        function clearChat() {
            document.getElementById('chatContainer').innerHTML = '';
            if ('speechSynthesis' in window) window.speechSynthesis.cancel();
        }
    </script>
</body>
</html>
"""

# Render in Streamlit with precise height constraint (620px to prevent any scroll on load)
st.components.v1.html(app_code, height=620, scrolling=False)
