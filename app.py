import os
import json
import streamlit as st
from groq import Groq

# Page Config
st.set_page_config(
    page_title="Pyrox AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Global CSS for Streamlit Shell
st.markdown("""
    <style>
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }
    #MainMenu, header, footer {visibility: hidden;}
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    </style>
""", unsafe_allow_html=True)

# Session States setup
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_name" not in st.session_state:
    st.session_state.user_name = None  # None means Not Logged In / Guest

# Fetch API Key
api_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")

# Initial Greeting Logic based on login/user state
if st.session_state.user_name:
    greeting_text = f"नमस्ते {st.session_state.user_name}! मैं आपकी कैसे मदद कर सकता हूँ?"
else:
    greeting_text = "How can I help you today?"

# Custom CSS / JS UI Framework
theme_html = f"""
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}
        body {{
            background-color: #000000;
            color: #ffffff;
            display: flex;
            height: 88vh;
            overflow: hidden;
        }}
        .sidebar {{
            width: 70px;
            background-color: #050505;
            border-right: 1px solid #1a1a1a;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 15px 0;
            justify-content: space-between;
        }}
        .menu-top, .menu-bottom {{
            display: flex;
            flex-direction: column;
            gap: 20px;
            align-items: center;
        }}
        .menu-item {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            color: #888888;
            font-size: 10px;
            cursor: pointer;
            transition: color 0.2s;
        }}
        .menu-item:hover {{ color: #ffffff; }}
        .menu-icon {{ width: 20px; height: 20px; stroke: currentColor; fill: none; stroke-width: 2; }}
        
        .main-container {{
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: space-between;
            padding: 15px;
            height: 100%;
        }}
        .top-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 5px;
        }}
        .pyrox-logo-small {{ width: 32px; height: 32px; }}
        .app-title {{ font-size: 1.3rem; font-weight: 700; color: #ffffff; }}
        
        .chat-container {{
            width: 100%;
            max-width: 720px;
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 14px;
            padding: 15px 10px;
        }}
        .message {{
            display: flex;
            flex-direction: column;
            max-width: 82%;
            line-height: 1.5;
            font-size: 0.95rem;
        }}
        .user-message {{
            align-self: flex-end;
            background-color: #1a1a1a;
            color: #ffffff;
            padding: 10px 16px;
            border-radius: 18px 18px 4px 18px;
            border: 1px solid #333;
        }}
        .ai-message {{
            align-self: flex-start;
            background-color: #0d0d0d;
            color: #e0e0e0;
            padding: 12px 18px;
            border-radius: 18px 18px 18px 4px;
            border: 1px solid #222;
        }}
        .ai-message .sender-name {{
            font-size: 0.75rem;
            color: #888;
            margin-bottom: 4px;
            font-weight: 600;
        }}
        
        .input-container {{
            width: 100%;
            max-width: 720px;
            background-color: #0a0a0a;
            border: 1px solid #222222;
            border-radius: 28px;
            padding: 8px 16px;
            display: flex;
            align-items: center;
            gap: 10px;
            position: relative;
        }}
        .star-icon {{ width: 22px; height: 22px; flex-shrink: 0; }}
        .chat-input {{
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: #ffffff;
            font-size: 0.95rem;
            padding: 6px 0;
        }}
        .chat-input::placeholder {{ color: #555555; }}
        .input-actions {{ display: flex; align-items: center; gap: 10px; }}
        .action-btn {{
            background: transparent; border: none; color: #aaaaaa; cursor: pointer;
        }}
        .action-btn:hover {{ color: #ffffff; }}
        .action-btn.listening {{ color: #ef4444; animation: pulse 1s infinite; }}
        
        .send-btn {{
            width: 30px; height: 30px; background-color: #ffffff; border-radius: 50%;
            color: #000000; display: flex; align-items: center; justify-content: center;
            cursor: pointer; border: none;
        }}
        @keyframes pulse {{ 0%, 100% {{ transform: scale(1); }} 50% {{ transform: scale(1.15); }} }}
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="menu-top">
            <div class="menu-item" onclick="parent.postMessage({{type: 'CLEAR'}}, '*')">
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

    <div class="main-container">
        <div class="top-header">
            <svg class="pyrox-logo-small" viewBox="0 0 200 200">
                <circle cx="100" cy="100" r="80" fill="none" stroke="#ffffff" stroke-width="4" />
                <path d="M 100 20 L 70 80 L 110 80 L 90 120 L 130 120 L 100 180" fill="none" stroke="#ffffff" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <h1 class="app-title">Pyrox AI</h1>
        </div>

        <div class="chat-container" id="chatContainer">
            <div class="message ai-message">
                <span class="sender-name">Pyrox AI</span>
                {greeting_text}
            </div>
        </div>

        <div class="input-container">
            <svg class="star-icon" viewBox="0 0 24 24">
                <defs>
                    <linearGradient id="starGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stop-color="#9C27B0"/>
                        <stop offset="100%" stop-color="#03A9F4"/>
                    </linearGradient>
                </defs>
                <path d="M12 0C12 6.627 6.627 12 0 12C6.627 12 12 17.373 12 24C12 17.373 17.373 12 24 12C17.373 12 12 6.627 12 0Z" fill="url(#starGrad)"/>
            </svg>

            <input type="text" id="chatInput" class="chat-input" placeholder="Ask Pyrox anything..." onkeypress="if(event.key==='Enter') sendPrompt();" />

            <div class="input-actions">
                <button id="micBtn" class="action-btn" title="Voice Input" onclick="toggleVoice()">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                        <line x1="12" y1="19" x2="12" y2="23"></line>
                    </svg>
                </button>
                <button class="send-btn" title="Send" onclick="sendPrompt()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                        <line x1="5" y1="12" x2="19" y2="12"></line>
                        <polyline points="12 5 19 12 12 19"></polyline>
                    </svg>
                </button>
            </div>
        </div>
    </div>

    <script>
        let recognition = null;
        let isListening = false;

        function toggleVoice() {{
            if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {{
                alert("Browser does not support Voice Input.");
                return;
            }}
            const micBtn = document.getElementById('micBtn');
            const inputField = document.getElementById('chatInput');

            if (isListening) {{
                recognition.stop();
                isListening = false;
                micBtn.classList.remove('listening');
                return;
            }}

            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.lang = 'hi-IN';
            recognition.continuous = false;
            recognition.interimResults = false;

            recognition.onstart = function() {{
                isListening = true;
                micBtn.classList.add('listening');
            }};

            recognition.onresult = function(event) {{
                const transcript = event.results[0][0].transcript;
                inputField.value = transcript; // केवल टेक्स्ट बॉक्स में लिखेगा, ऑटो-सबमिट नहीं करेगा!
                isListening = false;
                micBtn.classList.remove('listening');
            }};

            recognition.onerror = function() {{
                isListening = false;
                micBtn.classList.remove('listening');
            }};

            recognition.start();
        }}

        function sendPrompt() {{
            const input = document.getElementById('chatInput');
            const val = input.value.trim();
            if(!val) return;
            
            // UI Update
            const chatBox = document.getElementById('chatContainer');
            const userDiv = document.createElement('div');
            userDiv.className = 'message user-message';
            userDiv.innerText = val;
            chatBox.appendChild(userDiv);

            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;
        }}
    </script>
</body>
</html>
"""

# Streamlit Native Integration
st.components.v1.html(theme_html, height=650)

# Real Python Streamlit Chat Input & Groq Backend Execution
if prompt := st.chat_input("Pyrox से सीधे सवाल पूछें (Real Backend Connection)..."):
    if not api_key:
        st.error("⚠️ Streamlit Secrets में GROQ_API_KEY सेट नहीं है! कृपया सेटिंग्स में जाकर अपनी Key डालें।")
    else:
        try:
            client = Groq(api_key=api_key)
            
            if "messages" not in st.session_state:
                st.session_state.messages = []
                
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are Pyrox AI, a sharp, helpful, direct, and elite AI assistant."}
                    ] + st.session_state.messages,
                    stream=True,
                    temperature=0.7,
                )

                for chunk in completion:
                    if chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
                        message_placeholder.markdown(full_response + "▌")

                message_placeholder.markdown(full_response)
                
                # Audio Speech synthesis trigger
                safe_txt = full_response.replace('"', "'").replace("\n", " ")[:300]
                st.markdown(f"""
                    <script>
                        if ('speechSynthesis' in window) {{
                            window.speechSynthesis.cancel();
                            let u = new SpeechSynthesisUtterance("{safe_txt}");
                            u.lang = 'hi-IN';
                            window.speechSynthesis.speak(u);
                        }}
                    </script>
                """, unsafe_allow_html=True)

            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"Groq API Error: {str(e)}")
