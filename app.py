import streamlit as st
from groq import Groq

# Page configuration
st.set_page_config(
    page_title="Pyrox AI Studio",
    page_icon="⚡",
    layout="centered"
)

# Custom CSS for Pure Pitch-Black, Red AI, and Shining Gold only on Harshit's name
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Pure Pitch Black Background */
    .stApp {
        background-color: #000000;
        color: #E3E3E3;
    }
    
    /* Header Aesthetics */
    .main-header {
        font-size: 2.4rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 2px;
        letter-spacing: -0.8px;
    }
    
    /* Pyrox P in Gold */
    .gold-letter {
        color: #FFB703;
        font-weight: 700;
    }
    
    /* Pure Red for AI */
    .ai-red {
        color: #FF4B4B;
        font-weight: 700;
    }
    
    /* Only Harshit's name shines metallic gold */
    .shining-gold {
        background: linear-gradient(135deg, #FFE55C 0%, #FFB703 50%, #F18701 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 10px rgba(255, 215, 0, 0.4);
        font-weight: 700;
    }
    
    .sub-header {
        color: #8E918F;
        font-size: 0.95rem;
        margin-bottom: 12px;
    }
    
    /* Creator Badge */
    .creator-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #C4C7C5;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 500;
        margin-bottom: 25px;
        letter-spacing: 0.3px;
    }
    
    /* Gemini Inspired Hero Intro Card */
    .gemini-intro-card {
        background: #0A0A0A;
        border: 1px solid #1A1A1A;
        border-radius: 20px;
        padding: 28px 24px;
        margin: 20px 0 30px 0;
    }
    
    .gemini-greeting {
        font-size: 2rem;
        font-weight: 600;
        color: #FFFFFF;
        margin-bottom: 10px;
    }
    
    .gemini-subtitle {
        color: #8E918F;
        font-size: 1.05rem;
        line-height: 1.5;
    }

    /* Footer Disclaimer */
    .footer-disclaimer {
        text-align: center;
        color: #8E918F;
        font-size: 0.8rem;
        margin-top: 25px;
        font-style: italic;
    }
    
    /* Red Loading Spinner */
    .loader-container {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 14px 0;
        color: #FF4B4B;
        font-weight: 500;
        font-size: 0.95rem;
    }
    
    .atom-spinner {
        width: 24px;
        height: 24px;
        border: 3px solid rgba(255, 75, 75, 0.2);
        border-top: 3px solid #FF4B4B;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    </style>
""", unsafe_allow_html=True)

# Header Section
st.markdown(
    '<div class="main-header">'
    '<span class="gold-letter">P</span>yrox '
    '<span class="ai-red">AI</span> Studio'
    '</div>',
    unsafe_allow_html=True,
)
st.markdown('<div class="sub-header">Groq API द्वारा संचालित हाई-स्पीड इंटेलिजेंट असिस्टेंट</div>', unsafe_allow_html=True)
st.markdown('<div class="creator-badge">✨ Crafted by <span class="shining-gold">Harshit</span></div>', unsafe_allow_html=True)

# Check API key from secrets
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    st.error("त्रुटि: Streamlit Secrets में 'GROQ_API_KEY' नहीं मिली!")
    st.stop()

# Initialize Groq client
client = Groq(api_key=api_key)

# Only 100% stable, active models (No decommissioned models allowed)
active_models = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant"
]

# Sidebar Controls
with st.sidebar:
    st.header("⚙️ सेटिंग्स")
    model_choice = st.selectbox("एक्टिव मॉडल चुनें", active_models, index=0)
    
    if st.button("🗑️ चैट इतिहास साफ़ करें", type="primary", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Gemini-Style Welcome Intro if Chat History is Empty
if not st.session_state.messages:
    st.markdown("""
        <div class="gemini-intro-card">
            <div class="gemini-greeting">नमस्ते, मैं Pyrox हूँ।</div>
            <div class="gemini-subtitle">आज मैं आपकी किस प्रकार सहायता कर सकता हूँ? कोडिंग, रिसर्च या रचनात्मक कार्यों के लिए नीचे संदेश लिखें।</div>
        </div>
    """, unsafe_allow_html=True)

# Display prior chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input Box
if prompt := st.chat_input("यहाँ अपना संदेश टाइप करें..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Red Animated Loader
        loader_placeholder = st.empty()
        loader_placeholder.markdown("""
            <div class="loader-container">
                <div class="atom-spinner"></div>
                <span>Pyrox आपका जवाब तैयार कर रहा है...</span>
            </div>
        """, unsafe_allow_html=True)
        
        message_placeholder = st.empty()
        full_response = ""
        
        models_to_try = [model_choice] + [m for m in active_models if m != model_choice]
        success = False
        last_error = ""
        
        for trial_model in models_to_try:
            try:
                recent_messages = st.session_state.messages[-10:]
                
                completion = client.chat.completions.create(
                    model=trial_model,
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in recent_messages
                    ],
                    stream=True,
                )
                
                loader_placeholder.empty()
                
                for chunk in completion:
                    if chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
                        message_placeholder.markdown(full_response + "▌")
                        
                message_placeholder.markdown(full_response)
                success = True
                break
                
            except Exception as e:
                last_error = str(e)
                continue
        
        if not success:
            loader_placeholder.empty()
            full_response = f"कनेक्शन एरर: {last_error}"
            message_placeholder.error(full_response)
            
        st.session_state.messages.append({"role": "assistant", "content": full_response})

# Footer Disclaimer
st.markdown('<div class="footer-disclaimer">Pyrox is AI and can make mistakes.</div>', unsafe_allow_html=True)
