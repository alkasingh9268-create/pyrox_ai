import os
import asyncio
import json
import edge_tts
import requests
import streamlit as st

# ==============================================================================
# PYROX STUDIO - MASTER APPLICATION CONFIGURATION (Lines 1 - 50)
# ==============================================================================

st.set_page_config(
    page_title="Pyrox",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Default Streamlit Elements & Force Zero Padding for Full Custom UI
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    #MainMenu, header, footer { visibility: hidden; }
    .block-container { padding: 0rem !important; margin: 0rem !important; }
    </style>
""", unsafe_allow_html=True)

# API Key Setup
api_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")

# Session State Management for Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# ==============================================================================
# MICROSOFT EDGE NEURAL TEXT-TO-SPEECH (Madhur Neural - Male Voice) (Lines 51 - 120)
# ==============================================================================

def generate_edge_audio(text, filename="response.mp3"):
    """
    Generates premium natural Indian Male Neural Voice using Edge-TTS.
    """
    try:
        # Clean text from special markdown symbols for crisp audio reading
        clean_t = text.replace("*", "").replace("#", "").replace("`", "").replace("✨", "").replace("👋", "").replace("🚀", "").replace("💻", "").replace("😎", "").replace("💡", "").replace("🎯", "")
        
        async def _main():
            # hi-IN-MadhurNeural is a premium, natural-sounding Indian Male Neural Voice
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

# ==============================================================================
# GROQ API DIRECT HTTP HANDLER (Bypasses SDK ModuleNotFoundError) (Lines 121 - 200)
# ==============================================================================

def get_groq_response(user_prompt):
    """
    Direct HTTP request implementation to Groq API endpoint for Llama 3.3 70B model.
    100% reliable, zero dependency errors.
    """
    if not api_key:
        return "⚠️ Groq API Key missing in Streamlit Secrets!"
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": "You are Pyrox, an advanced, highly intelligent, and Gen-Z friendly AI assistant. Talk in a smooth mix of natural Hindi and English (Hinglish) with cool emojis ✨. Give crisp, highly accurate, and engaging answers."
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 512
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        if response.status_code == 200:
            res_json = response.json()
            return res_json['choices'][0]['message']['content']
        else:
            return f"⚠️ API Error ({response.status_code}): {response.text}"
    except Exception as e:
        return f"⚠️ Network Exception: {str(e)}"

# ==============================================================================
# BACKEND QUERY PARAMETER PROCESSOR (Lines 201 - 250)
# ==============================================================================

query_params = st.query_params
if "q" in query_params:
    user_prompt = query_params["q"]
    st.query_params.clear()
    
    if user_prompt:
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        reply = get_groq_response(user_prompt)
        
        # Generate Server-side Microsoft Edge-TTS Audio File with Male Voice
        audio_filename = f"audio_{len(st.session_state.messages)}.mp3"
        success = generate_edge_audio(reply, audio_filename)
        audio_path = audio_filename if success else None
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": reply,
            "audio_file": audio_path
        })

# Convert Python chat history into JSON string for frontend injection
chat_history_json = json.dumps(st.session_state.messages)

# ==============================================================================
# FULL STUDIO UI & FRONTEND ENGINE (HTML/CSS/JS) (Lines 251 - 769+)
# ==============================================================================

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

        /* COLLAPSIBLE / EXPANDABLE SIDEBAR */
        .sidebar {{
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
        }}
        .sidebar.expanded {{
            width: 230px;
            padding: 12px 10px;
            border-right: 1px solid #141414;
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
            white-space: nowrap;
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
            flex-shrink: 0;
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

        /* MAIN CONTAINER (600px height compact frame layout) */
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
            justify-content: space-between;
            padding: 4px 20px;
            position: relative;
        }}
        .hamburger-btn {{
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
        .hamburger-btn:hover {{
            color: #ffffff;
            background-color: #1a1a1a;
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
        .dropdown-item.login-item {{
            border-bottom: 1px solid #222;
            color: #3b82f6;
            font-weight: 600;
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
            transition: border-color 0.3s, box-shadow 0.3s;
        }}
        .input-box.recording {{
            border-color: #ef4444;
            box-shadow: 0 0 15px rgba(239, 68, 68, 0.25);
        }}
        .star-btn {{
            cursor: pointer;
            width: 20px;
            height: 20px;
            flex-shrink: 0;
        }}

        /* GEMINI WAVE BARS */
        .gemini-wave-container {{
            display: flex;
            align-items: center;
            gap: 3.5px;
            height: 20px;
            width: 120px;
            display: none;
        }}
        .gemini-wave-container.active {{
            display: flex;
        }}
        .wave-bar {{
            flex: 1;
            background: linear-gradient(180deg, #ef4444, #3b82f6);
            border-radius: 3px;
            height: 20%;
            animation: waveMotion 0.6s infinite ease-in-out alternate;
        }}
        .wave-bar:nth-child(1) {{ animation-delay: 0.1s; }}
        .wave-bar:nth-child(2) {{ animation-delay: 0.3s; }}
        .wave-bar:nth-child(3) {{ animation-delay: 0.2s; }}
        .wave-bar:nth-child(4) {{ animation-delay: 0.5s; }}
        .wave-bar:nth-child(5) {{ animation-delay: 0.15s; }}

        @keyframes waveMotion {{
            0% {{ height: 15%; }}
            100% {{ height: 100%; }}
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

        .mic-btn {{
            background: transparent;
            border: none;
            color: #aaaaaa;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: color 0.2s, transform 0.2s;
        }}
        .mic-btn:hover {{ color: #ffffff; transform: scale(1.1); }}
        .mic-btn.active {{ color: #ef4444; }}

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
            transition: transform 0.2s, opacity 0.2s;
        }}
        .arrow-submit-btn:hover {{
            transform: scale(1.05);
            opacity: 0.9;
        }}

        .footer-disclaimer {{
            font-size: 10.5px;
            color: #555555;
            text-align: center;
        }}
    </style>
</head>
<body>

    <!-- COLLAPSIBLE SIDEBAR -->
    <div class="sidebar" id="sidebar">
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
                <div class="menu-btn" onclick="alert('Library: Past notes & discussions')" data-tooltip="Library">
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
        
        <!-- TOP NAVBAR -->
        <div class="top-navbar">
            <button class="hamburger-btn" onclick="toggleSidebar()" data-tooltip="Toggle Menu">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="3" y1="12" x2="21" y2="12"></line>
                    <line x1="3" y1="6" x2="21" y2="6"></line>
                    <line x1="3" y1="18" x2="21" y2="18"></line>
                </svg>
            </button>

            <div class="three-dots-wrapper">
                <button class="dots-btn" onclick="toggleDropdown()" data-tooltip="More Options">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="5" r="1.5"></circle>
                        <circle cx="12" cy="12" r="1.5"></circle>
                        <circle cx="12" cy="19" r="1.5"></circle>
                    </svg>
                </button>
                <div class="dropdown-menu" id="dropdownMenu">
                    <div class="dropdown-item login-item" onclick="alert('Redirecting to Gmail Login...')">📧 Login with Gmail</div>
                    <div class="dropdown-item" onclick="alert('Conversation link copied!')">🔗 Share Conversation</div>
                    <div class="dropdown-item" onclick="alert('Find in chat')">🔍 Find in Chat</div>
                    <div class="dropdown-item" onclick="alert('Chat pinned')">📌 Pin Chat</div>
                    <div class="dropdown-item" onclick="alert('Exporting PDF...')">📄 Download PDF / Export</div>
                    <div class="dropdown-item" style="color:#ef4444;" onclick="clearChat()">🗑️ Delete Chat</div>
                </div>
            </div>
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
            <div class="greeting-subtext">Hi, how can I help you today?</div>
        </div>

        <!-- CHAT MESSAGES CONTAINER -->
        <div class="chat-container" id="chatContainer"></div>

        <!-- INPUT BAR AREA -->
        <div class="input-wrapper">
            <div class="input-box" id="inputBox">
                <svg class="star-btn" viewBox="0 0 24 24" data-tooltip="Attach File & Photo" onclick="alert('Select File / Photo to attach')">
                    <defs>
                        <linearGradient id="starGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#9C27B0"/>
                            <stop offset="100%" stop-color="#03A9F4"/>
                        </linearGradient>
                    </defs>
                    <path d="M12 0C12 6.627 6.627 12 0 12C6.627 12 12 17.373 12 24C12 17.373 17.373 12 24 12C17.373 12 12 6.627 12 0Z" fill="url(#starGrad)"/>
                </svg>

                <button id="micBtn" class="mic-btn" data-tooltip="Voice Input" onclick="toggleVoice()">
                    <svg id="micIconSvg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                        <line x1="12" y1="19" x2="12" y2="23"></line>
                    </svg>
                </button>

                <div class="gemini-wave-container" id="waveBox">
                    <div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div>
                </div>

                <input type="text" id="chatInput" class="chat-input-field" placeholder="Ask Pyrox anything..." onkeypress="if(event.key==='Enter') triggerSend();" />

                <button class="arrow-submit-btn" data-tooltip="Submit" onclick="triggerSend()">
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
        let accumulatedSpeech = "";
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

        function toggleSidebar() {{
            document.getElementById('sidebar').classList.toggle('expanded');
        }}

        function toggleDropdown() {{
            document.getElementById('dropdownMenu').classList.toggle('show');
        }}

        window.onclick = function(event) {{
            if (!event.target.closest('.three-dots-wrapper')) {{
                const m = document.getElementById('dropdownMenu');
                if(m) m.classList.remove('show');
            }}
        }}

        function openStudentSetup() {{
            let goal = prompt("आप किस परीक्षा या कक्षा की तैयारी कर रहे हैं? (जैसे: NEET, JEE, School, College)");
            if(!goal) return;
            let standard = prompt("आपकी कक्षा या वर्ष कौन सा है? (जैसे: Class 9, Class 11, B.Tech 1st Year)");
            if(!standard) return;
            alert("बहुत बढ़िया! " + standard + " (" + goal + ") के लिए आपका स्टडी रूटीन सेट कर दिया गया है।");
        }}

        function toggleVoice() {{
            const micBtn = document.getElementById('micBtn');
            const micSvg = document.getElementById('micIconSvg');
            const inputBox = document.getElementById('inputBox');
            const waveBox = document.getElementById('waveBox');
            const inputField = document.getElementById('chatInput');

            if (isListening) {{
                if (recognition) recognition.stop();
                stopVoiceUI();
                return;
            }}

            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {{
                alert("Speech recognition not supported in your browser.");
                return;
            }}

            recognition = new SpeechRecognition();
            recognition.lang = 'hi-IN';
            recognition.continuous = true;
            recognition.interimResults = true;

            accumulatedSpeech = inputField.value ? inputField.value + " " : "";

            recognition.onstart = function() {{
                isListening = true;
                micBtn.classList.add('active');
                inputBox.classList.add('recording');
                waveBox.classList.add('active');
                inputField.placeholder = "Listening continuously...";
                micSvg.innerHTML = `<rect x="6" y="4" width="4" height="16" fill="currentColor"/><rect x="14" y="4" width="4" height="16" fill="currentColor"/>`;
            }};

            recognition.onresult = function(event) {{
                let interim = '';
                for (let i = event.resultIndex; i < event.results.length; ++i) {{
                    if (event.results[i].isFinal) {{
                        accumulatedSpeech += event.results[i][0].transcript + " ";
                    }} else {{
                        interim += event.results[i][0].transcript;
                    }}
                }}
                inputField.value = accumulatedSpeech + interim;
            }};

            recognition.onend = function() {{
                if (isListening) {{ try {{ recognition.start(); }} catch(e) {{}} }}
            }};

            try {{ recognition.start(); }} catch(e) {{}}
        }}

        function stopVoiceUI() {{
            isListening = false;
            const micBtn = document.getElementById('micBtn');
            const micSvg = document.getElementById('micIconSvg');
            micBtn.classList.remove('active');
            document.getElementById('inputBox').classList.remove('recording');
            document.getElementById('waveBox').classList.remove('active');
            document.getElementById('chatInput').placeholder = "Ask Pyrox anything...";
            micSvg.innerHTML = `<path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line>`;
        }}

        function triggerSend() {{
            if (isListening && recognition) {{ recognition.stop(); stopVoiceUI(); }}
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

# Render Studio App Interface with 600px Compact Height
st.components.v1.html(app_code, height=600, scrolling=False)
