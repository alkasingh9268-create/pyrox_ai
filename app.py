import os
import asyncio
import json
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

# Hide Default Streamlit Elements & Force Zero Padding for Full Studio Look
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    #MainMenu, header, footer { visibility: hidden; }
    .block-container { padding: 0rem !important; margin: 0rem !important; }
    </style>
""", unsafe_allow_html=True)

# Initialize Groq Client Safely
api_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")
client = Groq(api_key=api_key) if api_key else None

# Session State Management for Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Function to generate real Microsoft Edge-TTS (Madhur Neural - Male Voice) Audio File
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

# Function to get intelligent Gen-Z AI response from Groq
def get_groq_response(user_prompt):
    if not client:
        return "⚠️ Groq API Key missing in Streamlit Secrets or Environment Variables!"
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are Pyrox, an advanced, highly intelligent, and Gen-Z friendly AI assistant. Talk in a smooth mix of natural Hindi and English (Hinglish) with cool emojis ✨. Give crisp, highly accurate, and engaging answers."
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            temperature=0.7,
            max_tokens=512,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error connecting to Groq: {str(e)}"

# Handle Backend Interaction via Query Params
query_params = st.query_params
if "q" in query_params:
    user_prompt = query_params["q"]
    st.query_params.clear()
    
    if user_prompt:
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        reply = get_groq_response(user_prompt)
        
        audio_filename = f"audio_{len(st.session_state.messages)}.mp3"
        success = generate_edge_audio(reply, audio_filename)
        audio_path = audio_filename if success else None
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": reply,
            "audio_file": audio_path
        })

# Convert Python chat history into JSON string
chat_history_json = json.dumps(st.session_state.messages)

# 2. Complete HTML + CSS + JS Studio UI
app_code = f"""
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pyrox Studio</title>
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
            height: 100vh;
            overflow: hidden;
        }}

        /* SIDEBAR ULTRA MAX DARK */
        .sidebar {{
            width: 230px;
            background-color: #050505;
            border-right: 1px solid #141414;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 12px 10px;
            z-index: 20;
        }}
        .sidebar-logo-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 4px 6px;
            margin-bottom: 10px;
        }}
        .sidebar-logo-header svg {{
            width: 24px;
            height: 24px;
        }}
        .sidebar-brand-name {{
            font-size: 1.1rem;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: 0.5px;
        }}
        .menu-list {{
            display: flex;
            flex-direction: column;
            gap: 3px;
        }}
        .menu-btn {{
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
        }}
        .menu-btn:hover {{
            background-color: #141414;
            color: #ffffff;
        }}
        .menu-btn svg {{
            width: 17px;
            height: 17px;
            stroke: currentColor;
            fill: none;
            stroke-width: 2;
        }}
        .sidebar-bottom {{
            border-top: 1px solid #141414;
            padding-top: 8px;
        }}

        /* TOOLTIP HOVER HELPER */
        [data-tooltip] {{
            position: relative;
        }}
        [data-tooltip]:hover::after {{
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
        }}

        /* MAIN CONTAINER */
        .main-container {{
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            align-items: center;
            height: 100vh;
            padding-top: 4px;
            padding-bottom: 8px;
        }}

        /* TOP NAVBAR */
        .top-navbar {{
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding: 4px 20px;
            position: relative;
        }}
        .three-dots-wrapper {{
            position: relative;
        }}
        .dots-btn {{
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
        }}
        .dots-btn:hover {{
            color: #ffffff;
            background-color: #1a1a1a;
        }}
        .dropdown-menu {{
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
        }}
        .dropdown-menu.show {{
            display: flex;
        }}
        .dropdown-item {{
            padding: 9px 16px;
            font-size: 13px;
            color: #cccccc;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: background 0.2s;
        }}
        .dropdown-item:hover {{
            background-color: #1a1a1a;
            color: #ffffff;
        }}

        /* CENTER LANDING HEADER */
        .center-landing-header {{
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            gap: 4px;
            margin-top: 2px;
        }}
        .brand-title-box {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .brand-logo-large {{
            width: 38px;
            height: 38px;
        }}
        .brand-name-large {{
            font-size: 1.9rem;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: -0.5px;
        }}
        .greeting-subtext {{
            font-size: 1.2rem;
            font-weight: 500;
            color: #d1d5db;
        }}

        /* CHAT MESSAGES AREA */
        .chat-container {{
            width: 100%;
            max-width: 800px;
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
            padding: 5px 15px;
            margin-top: 5px;
        }}
        .message {{
            display: flex;
            flex-direction: column;
            max-width: 82%;
            line-height: 1.5;
            font-size: 0.95rem;
            gap: 8px;
        }}
        .user-message {{
            align-self: flex-end;
            background-color: #1c1c1e;
            color: #ffffff;
            padding: 10px 16px;
            border-radius: 16px 16px 4px 16px;
            border: 1px solid #2d2d2d;
        }}
        .ai-message {{
            align-self: flex-start;
            background-color: #080808;
            color: #f0f0f0;
            padding: 12px 18px;
            border-radius: 16px 16px 16px 4px;
            border: 1px solid #1a1a1a;
            display: flex;
            flex-direction: column;
            gap: 8px;
            width: 100%;
            max-width: 100%;
        }}
        audio {{
            width: 100%;
            height: 32px;
            margin-top: 6px;
            filter: invert(100%) hue-rotate(180deg);
        }}

        /* INPUT BAR AREA */
        .input-wrapper {{
            width: 100%;
            max-width: 800px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            padding: 0 15px;
        }}
        .input-box {{
            width: 100%;
            background-color: #080808;
            border: 1px solid #222222;
            border-radius: 26px;
            padding: 8px 14px;
            display: flex;
            align-items: center;
            gap: 10px;
            position: relative;
        }}
        .chat-input-field {{
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: #ffffff;
            font-size: 0.95rem;
            padding: 4px 0;
        }}
        .chat-input-field::placeholder {{ color: #555555; }}

        .arrow-submit-btn {{
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
        }}
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
                <div class="menu-btn" onclick="clearChat()">
                    <svg viewBox="0 0 24 24"><path d="M12 4v16m8-8H4"></path></svg>
                    <span>New Chat</span>
                </div>
            </div>
        </div>
    </div>

    <!-- MAIN WORKSPACE -->
    <div class="main-container">
        <div class="top-navbar">
            <div class="three-dots-wrapper">
                <button class="dots-btn" onclick="toggleDropdown()">⚙️</button>
            </div>
        </div>

        <div class="center-landing-header" id="landingHeader">
            <div class="brand-title-box">
                <span class="brand-name-large">Pyrox</span>
            </div>
            <div class="greeting-subtext">Hi, how can I help you today?</div>
        </div>

        <div class="chat-container" id="chatContainer"></div>

        <div class="input-wrapper">
            <div class="input-box" id="inputBox">
                <input type="text" id="chatInput" class="chat-input-field" placeholder="Ask Pyrox anything..." onkeypress="if(event.key==='Enter') triggerSend();" />
                <button class="arrow-submit-btn" onclick="triggerSend()">➔</button>
            </div>
        </div>
    </div>

    <script>
        const chatMessages = {chat_history_json};

        window.onload = function() {{
            const container = document.getElementById('chatContainer');
            const landing = document.getElementById('landingHeader');

            if (chatMessages.length > 0) {{
                landing.style.display = 'none';
                chatMessages.forEach(msg => {{
                    const div = document.createElement('div');
                    div.className = 'message ' + (msg.role === 'user' ? 'user-message' : 'ai-message');
                    
                    if (msg.role === 'user') {{
                        div.innerText = msg.content;
                    }} else {{
                        let htmlContent = `<div>${{msg.content}}</div>`;
                        if (msg.audio_file) {{
                            htmlContent += `<audio controls autoplay><source src="${{msg.audio_file}}" type="audio/mp3"></audio>`;
                        }}
                        div.innerHTML = htmlContent;
                    }}
                    container.appendChild(div);
                }});
                container.scrollTop = container.scrollHeight;
            }} else {{
                landing.style.display = 'flex';
            }}
        }};

        function triggerSend() {{
            const inputField = document.getElementById('chatInput');
            const text = inputField.value.trim();
            if(!text) return;

            const url = new URL(window.location.href);
            url.searchParams.set('q', encodeURIComponent(text));
            window.location.href = url.toString();
        }}

        function clearChat() {{
            const url = new URL(window.location.href);
            url.searchParams.delete('q');
            window.location.href = url.toString();
        }}
    </script>
</body>
</html>
"""

st.components.v1.html(app_code, height=600, scrolling=False)
        
       
