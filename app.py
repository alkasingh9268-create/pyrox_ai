import streamlit as st
from groq import Groq

# Page configuration
st.set_page_config(
    page_title="Pyrox AI Studio",
    page_icon="⚡",
    layout="centered"
)

# Custom CSS for styling, font, colors, and animations
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0px;
    }
    
    .ai-highlight {
        color: #FF4B4B;
    }
    
    .sub-header {
        color: #a0a0a0;
        font-size: 0.95rem;
        margin-bottom: 2px;
    }
    
    .disclaimer {
        color: #6c757d;
        font-size: 0.8rem;
        margin-bottom: 25px;
        font-style: italic;
    }
    
    /* 3D Orbit / Atom Spinner Animation */
    .loader-container {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 0;
        color: #FF4B4B;
        font-weight: 600;
        font-size: 0.95rem;
    }
    
    .atom-spinner {
        width: 26px;
        height: 26px;
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
st.markdown('<div class="main-header">Pyrox <span class="ai-highlight">AI</span> Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Groq API द्वारा संचालित हाई-स्पीड असिस्टेंट</div>', unsafe_allow_html=True)
st.markdown('<div class="disclaimer">Pyrox is AI and can make mistakes.</div>', unsafe_allow_html=True)

# Check API key from secrets
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    st.error("त्रुटि: Streamlit Secrets में 'GROQ_API_KEY' नहीं मिली!")
    st.stop()

# Initialize Groq client
client = Groq(api_key=api_key)

# Dynamically fetch available models from user's account
available_models = []
try:
    models_response = client.models.list()
    available_models = [
        m.id for m in models_response.data 
        if "embed" not in m.id and "whisper" not in m.id and "audio" not in m.id
    ]
except Exception:
    pass

# Sidebar for model controls
with st.sidebar:
    st.header("⚙️ सेटिंग्स")
    
    if available_models:
        model_choice = st.selectbox("मॉडल चुनें", available_models)
    else:
        # Fallback manual input if API listing fails
        model_choice = st.text_input("मॉडल का नाम मैनुअली दर्ज करें (कंसोल से)", value="llama3-70b-8192")
    
    if st.button("चैट इतिहास साफ़ करें", type="primary"):
        st.session_state.messages = []
        st.rerun()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("यहाँ अपना संदेश टाइप करें..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Cool 3D animated loader while processing
        loader_placeholder = st.empty()
        loader_placeholder.markdown("""
            <div class="loader-container">
                <div class="atom-spinner"></div>
                <span>Pyrox आपका जवाब ढूंढ रहा है और तैयार कर रहा है...</span>
            </div>
        """, unsafe_allow_html=True)
        
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            recent_messages = st.session_state.messages[-10:]
            
            completion = client.chat.completions.create(
                model=model_choice,
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in recent_messages
                ],
                stream=True,
            )
            
            # Remove loader once streaming starts
            loader_placeholder.empty()
            
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
                    
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            loader_placeholder.empty()
            full_response = f"कनेक्शन एरर: {e}"
            message_placeholder.error(full_response)
            
        st.session_state.messages.append({"role": "assistant", "content": full_response})
