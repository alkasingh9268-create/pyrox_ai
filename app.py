import os
import streamlit as st
from groq import Groq

# Streamlit Page Config
st.set_page_config(
    page_title="Pyrox",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Streamlit Hide Default UI Elements
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    #MainMenu, header, footer { visibility: hidden; }
    .block-container { padding: 0rem; margin: 0rem; }
    </style>
""", unsafe_allow_html=True)

# Fetch API Key
api_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")

# HTML + CSS + JS Complete Studio UI
full_app_html = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
        /* Sidebar */
        .sidebar {
            width: 75px;
            background-color: #050505;
            border-right: 1px solid #1a1a1a;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px 0;
            justify-content: space-between;
        }
        .menu-top, .menu-bottom {
            display: flex;
            flex-direction: column;
            gap: 24px;
            align-items: center;
        }
        .menu-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 5px;
            color: #888888;
            font-size: 10px;
            cursor: pointer;
            transition: color 0.2s;
        }
        .menu-item:hover { color: #ffffff; }
        .menu-icon { width: 22px; height: 22px; stroke: currentColor; fill: none; stroke-width: 2; }

        /* Main Workspace */
        .main-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: space-between;
            padding: 20px;
            height: 100vh;
            position: relative;
        }

        /* Header with Dual Color Logo (Black & Red) */
        .top-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-top: 5px;
        }
        .pyrox-logo {
            width: 42px;
            height: 42px;
        }
        .app-title {
            font-size: 1.6rem;
            font-weight: 800;
            letter-spacing: 0.5px;
            color: #ffffff;
        }

        /* Chat Workspace */
        .chat-container {
            width: 100%;
            max-width: 800px;
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 18px;
            padding: 20px 10px;
        }
        .message {
            display: flex;
            flex-direction: column;
            max-width: 80%;
            line-height: 1.6;
            font-size: 1rem;
        }
        .user-message {
            align-self: flex-end;
            background-color: #1c1c1e;
            color: #ffffff;
            padding: 14px 20px;
            border-radius: 20px 20px 4px 20px;
            border: 1px solid #333;
        }
        .ai-message {
            align-self: flex-start;
            background-color: #0d0d0d;
            color: #f1f1f1;
            padding: 16px 22px;
            border-radius: 20px 20px 20px 4px;
            border: 1px solid #222;
        }
        .ai-message .sender-name {
            font-size: 0.75rem;
            color: #ff3333;
            margin-bottom: 6px;
            font-weight: 700;
        }

        /* Bottom Input Bar Wrapper */
        .input-wrapper {
            width: 100%;
            max-width: 800px;
            position: relative;
            margin-bottom: 15px;
        }
        .input-container {
            width: 100%;
            background-color: #0a0a0a;
            border: 1px solid #262626;
            border-radius: 32px;
            padding: 10px 18px;
            display: flex;
            align-items: center;
            gap: 12px;
            position: relative;
            transition: border-color 0.3s, box-shadow 0.3s;
        }
        .input-container.active-listening {
            border-color: #ff3333;
            box-shadow: 0 0 15px rgba(255, 51, 51, 0.25);
        }

        .star-icon {
            width: 24px;
            height: 24px;
            flex-shrink: 0;
            cursor: pointer;
        }

        /* Long Audio Wave Visualizer Line next to Mic */
        .long-wave-line {
            display: flex;
            align-items: center;
            gap: 3px;
            height: 20px;
            width: 100px;
            opacity: 0.2;
            transition: opacity 0.3s;
        }
        .long-wave-line.active {
            opacity: 1;
        }
        .wave-bar {
            flex: 1;
            background-color: #ff3333;
            border-radius: 2px;
            height: 20%;
            transition: height 0.1s ease;
        }
        .long-wave-line.active .wave-bar {
            animation: wavePulse 0.8s infinite ease-in-out alternate;
        }
        .long-wave-line.active .wave-bar:nth-child(1) { animation-delay: 0.0s; }
        .long-wave-line.active .wave-bar:nth-child(2) { animation-delay: 0.1s; }
        .long-wave-line.active .wave-bar:nth-child(3) { animation-delay: 0.2s; }
        .long-wave-line.active .wave-bar:nth-child(4) { animation-delay: 0.3s; }
        .long-wave-line.active .wave-bar:nth-child(5) { animation-delay: 0.1s; }
        .long-wave-line.active .wave-bar:nth-child(6) { animation-delay: 0.2s; }
        .long-wave-line.active .wave-bar:nth-child(7) { animation-delay: 0.4s; }
        .long-wave-line.active .wave-bar:nth-child(8) { animation-delay: 0.1s; }

        @keyframes wavePulse {
            0% { height: 15%; }
            100% { height: 100%; }
        }

        .chat-input {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: #ffffff;
            font-size: 1.05rem;
            padding: 6px 0;
        }
        .chat-input::placeholder { color: #555555; }

        .input-actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .action-btn {
            background: transparent;
            border: none;
            color: #aaaaaa;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: color 0.2s;
        }
        .action-btn:hover { color: #ffffff; }
        .action-btn.listening { color: #ff3333; }

        /* Submit Button with Text & Arrow */
        .submit-btn {
            background-color: #ffffff;
            color: #000000;
            border: none;
            border-radius: 20px;
            padding: 8px 16px;
            font-size: 0.9rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 6px;
            cursor: pointer;
            transition: transform 0.2s, opacity 0.2s;
        }
        .submit-btn:hover {
            transform: scale(1.03);
            opacity: 0.9;
        }
    </style>
</head>
<body>

    <!-- Sidebar -->
    <div class="sidebar">
        <div class="menu-top">
            <div class="menu-item" onclick="clearChat()">
                <svg class="menu-icon" viewBox="0 0 24 24"><path d="M12 4v16m8-8H4"></path></svg>
                <span>New Chat</span>
            </div>
        </div>
        <div class="menu-bottom">
            <div class="menu-item">
                <svg class="menu-icon" viewBox="0 0 24 24"><path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
                <span>Profile</span>
            </div>
        </div>
    </div>

    <!-- Main Workspace -->
    <div class="main-container">
        
        <!-- Header with Dual Color Logo (Black & Red) -->
        <div class="top-header">
            <svg class="pyrox-logo" viewBox="0 0 200 200">
                <defs>
                    <linearGradient id="dualLogoGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="50%" stop-color="#000000" />
                        <stop offset="50%" stop-color="#ff3333" />
                    </linearGradient>
                </defs>
                <circle cx="100" cy="100" r="85" fill="#111111" stroke="#ff3333" stroke-width="4"/>
                <path d="M 100 25 L 70 85 L 110 85 L 90 115 L 130 115 L 100 175" fill="none" stroke="url(#dualLogoGrad)" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <h1 class="app-title">Pyrox</h1>
        </div>

        <!-- Chat History -->
        <div class="chat-container" id="chatContainer">
            <div class="message ai-message">
                <span class="sender-name">Pyrox</span>
                How can I help you today?
            </div>
        </div>

        <!-- Input Bar Area -->
        <div class="input-wrapper">
            <div class="input-container" id="inputContainerBox">
                
                <!-- Star / File Icon -->
                <svg class="star-icon" viewBox="0 0 24 24" title="Attach / Star">
                    <defs>
                        <linearGradient id="starGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#9C27B0"/>
                            <stop offset="100%" stop-color="#03A9F4"/>
                        </linearGradient>
                    </defs>
                    <path d="M12 0C12 6.627 6.627 12 0 12C6.627 12 12 17.373 12 24C12 17.373 17.373 12 24 12C17.373 12 12 6.627 12 0Z" fill="url(#starGrad)"/>
                </svg>

                <!-- Microphone Button -->
                <button id="micBtn" class="action-btn" title="Voice Input" onclick="toggleVoiceInput()">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                        <line x1="12" y1="19" x2="12" y2="23"></line>
                    </svg>
                </button>

                <!-- Long Frequency Wave Bar next to Mic -->
                <div class="long-wave-line" id="longWaveLine">
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                </div>

                <!-- Text Input Field -->
                <input type="text" id="chatInput" class="chat-input" placeholder="How can I help you today?" onkeypress="if(event.key==='Enter') sendMessage()" />

                <!-- Submit Button with Icon + "Submit" Text -->
                <div class="input-actions">
                    <button class="submit-btn" title="Submit" onclick="sendMessage()">
                        <span>Submit</span>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                            <line x1="5" y1="12" x2="19" y2="12"></line>
                            <polyline points="12 5 19 12 12 19"></polyline>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let recognition = null;
        let isRecording = false;

        function toggleVoiceInput() {
            const micBtn = document.getElementById('micBtn');
            const containerBox = document.getElementById('inputContainerBox');
            const waveLine = document.getElementById('longWaveLine');
            const inputField = document.getElementById('chatInput');

            if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
                alert("Speech recognition is not supported in this browser.");
                return;
            }

            if (isRecording) {
                recognition.stop();
                return;
            }

            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.lang = 'hi-IN';
            recognition.continuous = false;
            recognition.interimResults = false;

            recognition.onstart = function() {
                isRecording = true;
                micBtn.classList.add('listening');
                containerBox.classList.add('active-listening');
                waveLine.classList.add('active');
                inputField.placeholder = "Listening... बोलिए...";
            };

            recognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript;
                inputField.value = transcript;
                stopVoiceUI();
            };

            recognition.onerror = function() { stopVoiceUI(); };
            recognition.onend = function() { stopVoiceUI(); };

            recognition.start();
        }

        function stopVoiceUI() {
            isRecording = false;
            document.getElementById('micBtn').classList.remove('listening');
            document.getElementById('inputContainerBox').classList.remove('active-listening');
            document.getElementById('longWaveLine').classList.remove('active');
            document.getElementById('chatInput').placeholder = "How can I help you today?";
        }

        function speakResponse(text) {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                let clean = text.replace(/[`*_#\\[\\]()]/g, '');
                let utterance = new SpeechSynthesisUtterance(clean);
                utterance.rate = 0.95;  // Slightly optimized for natural flow
                utterance.pitch = 1.0;
                let voices = window.speechSynthesis.getVoices();
                let v = voices.find(val => val.lang.includes('hi-IN') || val.lang.includes('en-IN') || val.lang.includes('en-US')) || voices[0];
                if (v) utterance.voice = v;
                window.speechSynthesis.speak(utterance);
            }
        }

        function sendMessage() {
            const inputField = document.getElementById('chatInput');
            const text = inputField.value.trim();
            if (text === '') return;

            const chatContainer = document.getElementById('chatContainer');

            // Add User Message
            const userDiv = document.createElement('div');
            userDiv.className = 'message user-message';
            userDiv.innerText = text;
            chatContainer.appendChild(userDiv);

            inputField.value = '';
            chatContainer.scrollTop = chatContainer.scrollHeight;

            // Generate Response
            setTimeout(() => {
                const aiDiv = document.createElement('div');
                aiDiv.className = 'message ai-message';
                const replyText = "नमस्ते! आपका सवाल '" + text + "' प्राप्त हुआ। मैं Pyrox आपकी सेवा में हाज़िर हूँ।";
                aiDiv.innerHTML = `<span class="sender-name">Pyrox</span>${replyText}`;
                chatContainer.appendChild(aiDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
                speakResponse(replyText);
            }, 500);
        }

        function clearChat() {
            document.getElementById('chatContainer').innerHTML = `
                <div class="message ai-message">
                    <span class="sender-name">Pyrox</span>
                    How can I help you today?
                </div>
            `;
            if ('speechSynthesis' in window) window.speechSynthesis.cancel();
        }
    </script>
</body>
</html>
"""

# Render full screen app
st.components.v1.html(full_app_html, height=750, scrolling=False)
