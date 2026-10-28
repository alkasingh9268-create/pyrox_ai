import os
import streamlit as st
from groq import Groq

# ==========================================
# 1. PAGE CONFIGURATION & METADATA
# ==========================================
st.set_page_config(
    page_title="Pyrox AI - Ultimate Professional Studio",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. ADVANCED CUSTOM STYLING & ULTRA UI (CSS)
# ==========================================
st.markdown("""
    <style>
    .main {
        background-color: #0b0f19;
        color: #f3f4f6;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    .stSidebar {
        background-color: #111827;
        border-right: 1px solid #1f2937;
    }
    .stTextInput input, .stTextArea textarea {
        background-color: #1f2937;
        color: #ffffff;
        border-radius: 14px;
        border: 1px solid #374151;
        padding: 14px;
        font-size: 15px;
    }
    .stChatMessage {
        border-radius: 18px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2), 0 4px 6px -4px rgba(0, 0, 0, 0.2);
    }
    .stChatMessage[data-testid="stChatMessage-user"] {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
        border: 1px solid #4338ca;
    }
    .stChatMessage[data-testid="stChatMessage-assistant"] {
        background-color: #111827;
        border: 1px solid #1f2937;
    }
    .custom-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 0px 25px 0px;
        border-bottom: 2px solid #1f2937;
        margin-bottom: 30px;
    }
    .title-text {
        font-size: 36px;
        font-weight: 900;
        background: linear-gradient(90deg, #6366f1, #a855f7, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
    }
    .badge-online {
        background-color: rgba(16, 185, 129, 0.1);
        color: #10b981;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        border: 1px solid rgba(16, 185, 129, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. SIDEBAR CONTROL PANEL & CONFIGURATIONS
# ==========================================
with st.sidebar:
    st.markdown("### 🎛️ Pyrox AI Master Engine")
    st.markdown("---")
    
    # Model Selection Hub
    selected_model = st.selectbox(
        "🧠 Select Intelligence Core",
        [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768"
        ],
        index=0
    )
    
    # Advanced Parameters
    temperature = st.slider(
        "✨ Creativity / Temperature", 
        min_value=0.0, 
        max_value=1.0, 
        value=0.7, 
        step=0.1,
        help="Higher values make output more creative, lower values make it more deterministic."
    )
    
    max_tokens_limit = st.slider(
        "📏 Max Response Length (Tokens)",
        min_value=512,
        max_value=8192,
        value=4096,
        step=512
    )
    
    st.markdown("---")
    st.markdown("### 🔊 Voice & Speech Studio")
    voice_enabled = st.toggle("Enable Ultra-Realistic Audio Output", value=True)
    voice_pitch = st.slider("Voice Pitch Adjustment", 0.5, 1.5, 1.0, 0.1)
    voice_rate = st.slider("Speech Rate / Speed", 0.5, 2.0, 1.0, 0.1)
    
    st.markdown("---")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with col_s2:
        if st.button("🔄 Hard Reset", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
            
    st.markdown("""
        <div style='text-align: center; color: #6b7280; font-size: 11px; margin-top: 40px;'>
            Pyrox AI Enterprise Edition v4.5<br>Powered by Groq Cloud & Streamlit
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# 4. MAIN INTERFACE HEADER DESIGN
# ==========================================
st.markdown("""
    <div class="custom-header">
        <div class="title-text">🤖 Pyrox AI Studio Pro</div>
        <div><span class="badge-online">● System Online & Ready</span></div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 5. API KEY & CLIENT VALIDATION
# ==========================================
api_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")

if not api_key:
    st.error("🚨 **CRITICAL CONFIGURATION ERROR:** Groq API Key गायब है! कृपया Streamlit Cloud के Secrets में `GROQ_API_KEY` सेट करें।")
else:
    client = Groq(api_key=api_key)

    # Initialize Session History with Elite System Persona
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "system", 
                "content": "You are Pyrox AI, an elite, highly professional, sharp, and multi-disciplinary AI assistant designed for elite developers and creators. Provide comprehensive, precise, professional, and well-formatted technical and general responses."
            }
        ]

    # Render Chat History (Excluding System Prompt)
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # ==========================================
    # 6. JAVASCRIPT / HTML AUDIO SYNTHESIS INJECTION
    # ==========================================
    if voice_enabled:
        tts_engine_script = f"""
        <script>
        function playPyroxVoice(textToSpeak) {{
            if ('speechSynthesis' in window) {{
                window.speechSynthesis.cancel();
                let cleanText = textToSpeak.replace(/[`*_#\\[\\]()]/g, '');
                let utterance = new SpeechSynthesisUtterance(cleanText);
                utterance.rate = {voice_rate};
                utterance.pitch = {voice_pitch};
                
                let voices = window.speechSynthesis.getVoices();
                let targetVoice = voices.find(v => v.lang.includes('en-IN') || v.lang.includes('hi-IN') || v.lang.includes('en-US')) || voices[0];
                if (targetVoice) {{
                    utterance.voice = targetVoice;
                }}
                window.speechSynthesis.speak(utterance);
            }}
        }}
        </script>
        """
        st.markdown(tts_engine_script, unsafe_allow_html=True)

    # ==========================================
    # 7. CHAT INPUT & CORE GENERATION PIPELINE
    # ==========================================
    if prompt := st.chat_input("Pyrox से कुछ भी पूछें... (यहाँ अपना प्रॉम्ट दर्ज करें)"):
        # Append User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate Assistant Streaming Response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                chat_completion = client.chat.completions.create(
                    model=selected_model,
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                    stream=True,
                    temperature=temperature,
                    max_tokens=max_tokens_limit
                )
                
                for chunk in chat_completion:
                    if chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
                        message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
                
                # Trigger Browser Voice Synthesis Post-Generation
                if voice_enabled:
                    safe_string = full_response.replace('"', '\\"').replace('\n', ' ').replace("'", "\\'")
                    st.markdown(f"""
                        <script>
                            playPyroxVoice("{safe_string[:400]}");
                        </script>
                    """, unsafe_allow_html=True)
                    
            except Exception as e:
                full_response = f"⚠️ **Groq API Processing Exception:** `{str(e)}`"
                message_placeholder.error(full_response)

        # Append Assistant Response to Memory State
        st.session_state.messages.append({"role": "assistant", "content": full_response})
