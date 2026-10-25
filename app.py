import streamlit as st
from groq import Groq
from gtts import gTTS
import os

# Page configuration
st.set_page_config(
    page_title="Pyrox AI Studio",
    page_icon="⚡",
    layout="centered"
)

# Sidebar - Settings, Theme Engine & Voice Toggle
with st.sidebar:
    st.header("⚙️ सेटिंग्स")
    
    # Custom Theme Engine
    selected_theme = st.selectbox(
        "🎨 थीम चुनें (Theme)",
        ["Pure OLED Black", "Deep Charcoal", "Midnight Navy"]
    )
    
    model_choice = st.text_input("एक्टिव मॉडल", value="qwen/qwen3.8-27b")
    
    # Voice Toggle inside Sidebar
    enable_voice = st.checkbox("🔊 AI वॉयस आउटपुट चालू करें", value=False)
    
    if st.button("🗑️ चैट इतिहास साफ़ करें", type="primary", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Determine background color based on selected theme
bg_color = "#000000"
if selected_theme == "Deep Charcoal":
    bg_color = "#121212"
elif selected_theme == "Midnight Navy":
    bg_color = "#0A0E17"

# Custom CSS for Professional Layout & Metallic Silver Harshit Glow
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}
    
    /* Dynamic Pure Black / Selected Theme Background */
    .stApp {{
        background-color: {bg_color} !important;
        color: #E3E3E3;
    }}
    
    /* Header Aesthetics - Pure White Pyrox */
    .main-header {{
        font-size: 2.5rem;
        font-weight: 700;
        color: #FFFFFF !important;
        margin-bottom: 2px;
        letter-spacing: -0.8px;
    }}
    
    /* Pure Red for AI */
    .ai-red {{
        color: #FF4B4B;
        font-weight: 700;
    }}
    
    /* Ultra Shining Metallic Liquid Silver Glow for Harshit */
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
    
    /* Creator Badge */
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
        letter-spacing: 0.3px;
    }}
    
    /* Gemini Inspired Hero Intro Card */
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

    /* Remove standard Streamlit Chat Avatars completely */
    [data-testid="stChatMessageAvatar"] {{
        display: none !important;
    }}

    /* Custom Chat Container Layouts */
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
    
    /* Stunning Multi-Ring 3D Atom Spinner */
    .loader-container {{
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 14px 0;
        color: #FF4B4B;
        font-weight: 500;
        font-size: 0.95rem;
    }}
    
    .multi-atom {{
        position: relative;
        width: 26px;
        height: 26px;
    }}
    
    .orbit {{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border: 2px solid rgba(255, 75, 75, 0.25);
        border-top: 2px solid #FF4B4B;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }}
    
    .orbit:nth-child(2) {{
        animation: spin-reverse 0.6s linear infinite;
        transform: rotate(60deg);
        border-color: rgba(255, 75, 75, 0.15);
        border-bottom: 2px solid #FF4B4B;
    }}
    
    .orbit:nth-child(3) {{
        animation: spin 1s linear infinite;
        transform: rotate(120deg);
        border-color: rgba(255, 75, 75, 0.1);
        border-left: 2px solid #FF4B4B;
    }}
    
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    
    @keyframes spin-reverse {{
        0% {{ transform: rotate(360deg); }}
        100% {{ transform: rotate(0deg); }}
    }}
    </style>
""", unsafe_allow_html=True)

# Header Section
st.markdown(
    '<div class="main-header">'
    'Pyrox <span class="ai-red">AI</span> Studio'
    '</div>',
    unsafe_allow_html=True,
)
st.markdown('<div class="sub-header">Groq API द्वारा संचालित हाई-स्पीड इंटेलिजेंट असिस्टेंट</div>', unsafe_allow_html=True)
st.markdown('<div class="creator-badge">✨ Crafted by <span class="shining-silver">Harshit</span></div>', unsafe_allow_html=True)

# Check API key from secrets
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    st.error("त्रुटि: Streamlit Secrets में 'GROQ_API_KEY' नहीं मिली!")
    st.stop()

# Initialize Groq client
client = Groq(api_key=api_key)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Gemini-Style Welcome Intro if Chat History is Empty
if not st.session_state.messages:
    st.markdown("""
        <div class="gemini-intro-card">
            <div class="gemini-greeting">नमस्ते Harshit, मैं Pyrox हूँ।</div>
            <div class="gemini-subtitle">आज मैं आपकी किस प्रकार सहायता कर सकता हूँ? कोडिंग, रिसर्च या रचनात्मक कार्यों के लिए नीचे संदेश लिखें।</div>
        </div>
    """, unsafe_allow_html=True)

# Display prior chat messages cleanly without avatars
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f'<div class="user-box">{message["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="assistant-box">{message["content"]}</div>', unsafe_allow_html=True)
        st.markdown('<div class="inline-disclaimer">Pyrox is AI and can make mistakes.</div>', unsafe_allow_html=True)

# User Input Box
if prompt := st.chat_input("यहाँ अपना संदेश टाइप करें..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Render User Question on Left Box
    st.markdown(f'<div class="user-box">{prompt}</div>', unsafe_allow_html=True)

    # Loader Placeholder
    loader_placeholder = st.empty()
    loader_placeholder.markdown("""
        <div class="loader-container">
            <div class="multi-atom">
                <div class="orbit"></div>
                <div class="orbit"></div>
                <div class="orbit"></div>
            </div>
            <span>Pyrox आपका जवाब तैयार कर रहा है...</span>
        </div>
    """, unsafe_allow_html=True)
    
    message_placeholder = st.empty()
    full_response = ""
    
    try:
        recent_messages = st.session_state.messages[-4:]
        
        # Super-Strict Anti-Hallucination & Human-Like Conversational Persona System Prompt
        system_prompt = {
            "role": "system",
            "content": (
                "You are Pyrox AI Studio, a super-fast, ultra-intelligent, and warm AI assistant crafted and created by Harshit. "
                "CRITICAL INSTRUCTIONS:\n"
                "1. NEVER hallucinate or mix up random unrelated topics (e.g., never claim Python has any connection to health, fitness, or physical body terms).\n"
                "2. Talk like a sharp, friendly, and engaging human tech mentor. Use natural Hinglish or English matching the user's vibe.\n"
                "3. Keep answers direct, accurate, and structured. When asked about learning a language like Python, give a clear, simple definition first, and then practical guidance without sounding like a rigid robot.\n"
                "4. If anyone asks who created you, proudly state that you were created by Harshit."
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
            max_tokens=600
        )
        
        loader_placeholder.empty()
        
        for chunk in completion:
            if chunk.choices[0].delta.content is not None:
                full_response += chunk.choices[0].delta.content
                message_placeholder.markdown(f'<div class="assistant-box">{full_response}▌</div>', unsafe_allow_html=True)
                
        message_placeholder.markdown(f'<div class="assistant-box">{full_response}</div>', unsafe_allow_html=True)
        
        # Immediate Inline Disclaimer under the answer
        st.markdown('<div class="inline-disclaimer">Pyrox is AI and can make mistakes.</div>', unsafe_allow_html=True)
        
        # Voice Generation if enabled in sidebar
        if enable_voice and full_response:
            try:
                clean_text = full_response.replace("*", "").replace("#", "").replace("`", "")
                tts = gTTS(text=clean_text, lang='hi', slow=False)
                audio_file = "temp_response.mp3"
                tts.save(audio_file)
                st.audio(audio_file, format="audio/mp3", autoplay=True)
            except Exception:
                pass
        
    except Exception as e:
        loader_placeholder.empty()
        full_response = f"कनेक्शन एरर: {e}"
        message_placeholder.error(full_response)
        
    st.session_state.messages.append({"role": "assistant", "content": full_response})
