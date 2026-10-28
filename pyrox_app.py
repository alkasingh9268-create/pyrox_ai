import streamlit as st
from groq import Groq

# Page configuration
st.set_page_config(
    page_title="Pyrox AI",
    page_icon="⚡",
    layout="centered"
)

# Sidebar - Settings & Theme Engine
with st.sidebar:
    st.header("⚙️ सेटिंग्स")
    
    selected_theme = st.selectbox(
        "🎨 थीम चुनें (Theme)",
        ["Pure OLED Black", "Deep Charcoal", "Midnight Navy"]
    )
    
    model_choice = st.text_input("एक्टिव मॉडल", value="qwen/qwen3.8-27b")
    
    if st.button("🗑️ चैट इतिहास साफ़ करें", type="primary", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

bg_color = "#000000"
if selected_theme == "Deep Charcoal":
    bg_color = "#121212"
elif selected_theme == "Midnight Navy":
    bg_color = "#0A0E17"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}
    
    .stApp {{
        background-color: {bg_color} !important;
        color: #E3E3E3;
    }}
    
    .main-header {{
        font-size: 2.5rem;
        font-weight: 700;
        color: #FFFFFF !important;
        margin-bottom: 2px;
        letter-spacing: -0.8px;
    }}
    
    .ai-red {{
        color: #FF4B4B;
        font-weight: 700;
    }}
    
    .shining-silver {{
        background: linear-gradient(135deg, #FFFFFF 0%, #C0C0C0 40%, #E8E8E8 70%, #999999 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 12px rgba(255, 255, 255, 0.6), 0 0 20px rgba(192, 192, 192, 0.4);
        font-weight: 700;
    }}
    
    .sub-header {{
        color: #8E918F;
        font-size: 0.95rem;
        margin-bottom: 12px;
    }}
    
    .creator-badge {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        color: #C4C7C5;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 500;
        margin-bottom: 25px;
    }}
    
    .gemini-intro-card {{
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 20px;
        padding: 28px 24px;
        margin: 20px 0 30px 0;
    }}
    
    .gemini-greeting {{
        font-size: 2rem;
        font-weight: 600;
        color: #FFFFFF;
        margin-bottom: 10px;
    }}
    
    .gemini-subtitle {{
        color: #8E918F;
        font-size: 1.05rem;
        line-height: 1.5;
    }}

    [data-testid="stChatMessageAvatar"] {{
        display: none !important;
    }}

    .user-box {{
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 14px 18px;
        margin: 12px 0;
        max-width: 85%;
        color: #FFFFFF;
        font-size: 1rem;
        line-height: 1.5;
    }}

    .assistant-box {{
        background: transparent;
        border-left: 2px solid #FF4B4B;
        padding: 4px 0 4px 18px;
        margin: 16px 0 6px 0;
        width: 100%;
        color: #E3E3E3;
        font-size: 1.02rem;
        line-height: 1.6;
    }}

    .inline-disclaimer {{
        color: #6E716F;
        font-size: 0.78rem;
        font-style: italic;
        margin-top: 6px;
        margin-bottom: 20px;
        padding-left: 18px;
    }}
    
    .jalebi-loader-container {{
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 16px 0;
        color: #FF4B4B;
        font-weight: 500;
        font-size: 0.95rem;
    }}
    
    .jalebi-ring {{
        width: 28px;
        height: 28px;
        border: 3px solid rgba(255, 75, 75, 0.2);
        border-top: 3px solid #FF4B4B;
        border-right: 3px solid #FFFFFF;
        border-radius: 50%;
        animation: jalebi-spin 0.7s cubic-bezier(0.68, -0.55, 0.27, 1.55) infinite;
    }}
    
    @keyframes jalebi-spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    </style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="main-header">'
    'Pyrox <span class="ai-red">AI</span>'
    '</div>',
    unsafe_allow_html=True,
)
st.markdown('<div class="sub-header">Groq API द्वारा संचालित हाई-स्पीड इंटेलिजेंट असिस्टेंट</div>', unsafe_allow_html=True)
st.markdown('<div class="creator-badge">✨ Crafted by <span class="shining-silver">Harshit</span></div>', unsafe_allow_html=True)

if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    st.error("त्रुटि: Streamlit Secrets में 'GROQ_API_KEY' नहीं मिली!")
    st.stop()

client = Groq(api_key=api_key)

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.markdown("""
        <div class="gemini-intro-card">
            <div class="gemini-greeting">नमस्ते Harshit, मैं Pyrox हूँ।</div>
            <div class="gemini-subtitle">आज बता, क्या सीन है? कोडिंग, रिसर्च या किसी भी बात पर चर्चा करनी हो, नीचे संदेश लिख।</div>
        </div>
    """, unsafe_allow_html=True)

def render_speak_button(text, key_id):
    safe_text = text.replace("'", "\\'").replace('"', '\\"').replace('\n', ' ')
    html_code = f"""
    <div style="margin-bottom: 15px;">
        <button onclick="speakText_{key_id}()" style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: #E3E3E3; padding: 6px 14px; border-radius: 8px; cursor: pointer; font-size: 0.85rem; display: inline-flex; align-items: center; gap: 6px; font-weight: 500;">
            🔊 Pyrox Audio (Listen)
        </button>
        <script>
        function speakText_{key_id}() {{
            if ('speechSynthesis' in window) {{
                window.speechSynthesis.cancel();
                var utterance = new SpeechSynthesisUtterance("{safe_text}");
                utterance.lang = 'hi-IN';
                utterance.pitch = 0.7;
                utterance.rate = 0.98;
                
                var voices = window.speechSynthesis.getVoices();
                for(var i = 0; i < voices.length; i++) {{
                    if((voices[i].lang.includes('hi') || voices[i].lang.includes('en-IN')) && (voices[i].name.toLowerCase().includes('male') || voices[i].name.toLowerCase().includes('natural') || voices[i].name.toLowerCase().includes('google'))) {{
                        utterance.voice = voices[i];
                        break;
                    }}
                }}
                window.speechSynthesis.speak(utterance);
            }}
        }}
        </script>
    </div>
    """
    st.components.v1.html(html_code, height=40)

for idx, message in enumerate(st.session_state.messages):
    if message["role"] == "user":
        st.markdown(f'<div class="user-box">{message["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="assistant-box">{message["content"]}</div>', unsafe_allow_html=True)
        render_speak_button(message["content"], f"hist_{idx}")
        st.markdown('<div class="inline-disclaimer">Pyrox is AI and can make mistakes.</div>', unsafe_allow_html=True)

prompt = st.chat_input("यहाँ अपना संदेश टाइप करें...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(f'<div class="user-box">{prompt}</div>', unsafe_allow_html=True)

    loader_placeholder = st.empty()
    loader_placeholder.markdown("""
        <div class="jalebi-loader-container">
            <div class="jalebi-ring"></div>
            <span>Pyrox जलेबी जैसी फुर्ती से जवाब तैयार कर रहा है...</span>
        </div>
    """, unsafe_allow_html=True)
    
    message_placeholder = st.empty()
    full_response = ""
    
    try:
        recent_messages = st.session_state.messages[-6:]
        
        system_prompt = {
            "role": "system",
            "content": (
                "You are Pyrox, an elite, hyper-intelligent, creative, and razor-sharp AI assistant. "
                "CORE INSTRUCTIONS:\n"
                "1. GEMINI-STYLE BRILLIANCE: Think deep, solve problems logically with exceptional clarity, and provide structured, insightful, and comprehensive answers like Google's Gemini.\n"
                "2. NATURAL HINGLISH/HINDI/ENGLISH BLEND: Match the user's natural casual yet sharp vibe effortlessly. Talk like a brilliant tech companion with warmth, clarity, and zero robotic coldness.\n"
                "3. ABSOLUTELY ZERO TYPOS OR ERRORS: Ensure flawless spelling, grammar, and precise sentence framing every single time.\n"
                "4. IDENTITY RULE: Never introduce yourself unprompted. If the user explicitly asks 'Who made you?' or 'Tumhe kisne banaya hai?', state clearly and proudly that you were created by Harshit.\n"
                "5. NO META-COMMENTARY: Avoid unnecessary lectures or pointing out minor phrasing."
            )
        }
        
        chat_messages = [system_prompt] + [
            {"role": m["role"], "content": m["content"]}
            for m in recent_messages
        ]
        
        completion = client.chat.completions.create(
            model=model_choice,
            messages=chat_messages,
            stream=True,
            max_tokens=800,
            temperature=0.7
        )
        
        loader_placeholder.empty()
        
        for chunk in completion:
            if chunk.choices[0].delta.content is not None:
                full_response += chunk.choices[0].delta.content
                message_placeholder.markdown(f'<div class="assistant-box">{full_response}▌</div>', unsafe_allow_html=True)
                
        message_placeholder.markdown(f'<div class="assistant_box">{full_response}</div>', unsafe_allow_html=True)
        render_speak_button(full_response, "live_new")
        st.markdown('<div class="inline-disclaimer">Pyrox is AI and can make mistakes.</div>', unsafe_allow_html=True)
        
    except Exception as e:
        loader_placeholder.empty()
        full_response = f"कनेक्शन एरर: {e}"
        message_placeholder.error(full_response)
        
    st.session_state.messages.append({"role": "assistant", "content": full_response})