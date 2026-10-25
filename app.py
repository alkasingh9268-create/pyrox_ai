import streamlit as st
from groq import Groq

# Page configuration
st.set_page_config(
    page_title="Pyrox AI Studio",
    page_icon="⚡",
    layout="centered"
)

# Custom CSS for soothing eye-friendly dark theme, fonts, badges, and 3D atom animation
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Soothing, eye-relaxing deep dark slate theme */
    .stApp {
        background-color: #13171F;
        color: #E6EDF3;
    }
    
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0px;
    }
    
    /* Eye-friendly calm blue accent */
    .ai-highlight {
        color: #58A6FF;
    }
    
    .sub-header {
        color: #8B949E;
        font-size: 0.95rem;
        margin-bottom: 10px;
    }
    
    /* Professional Sleek Creator Badge */
    .creator-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(88, 166, 255, 0.1);
        border: 1px solid rgba(88, 166, 255, 0.3);
        color: #58A6FF;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 25px;
        letter-spacing: 0.5px;
    }
    
    .footer-disclaimer {
        text-align: center;
        color: #8B949E;
        font-size: 0.8rem;
        margin-top: 15px;
        font-style: italic;
    }
    
    /* 3D Orbit / Atom Spinner Animation with calming colors */
    .loader-container {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 0;
        color: #58A6FF;
        font-weight: 600;
        font-size: 0.95rem;
    }
    
    .atom-spinner {
        width: 26px;
        height: 26px;
        border: 3px solid rgba(88, 166, 255, 0.2);
        border-top: 3px solid #58A6FF;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    </style>
""", unsafe_allow_html=True)

# Header Section with Professional Badge
st.markdown('<div class="main-header">Pyrox <span class="ai-highlight">AI</span> Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Groq API द्वारा संचालित हाई-स्पीड असिस्टेंट</div>', unsafe_allow_html=True)
st.markdown('<div class="creator-badge">✨ Crafted by Harshit</div>', unsafe_allow_html=True)

# Check API key from secrets
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    st.error("त्रुटि: Streamlit Secrets में 'GROQ_API_KEY' नहीं मिली!")
    st.stop()

# Initialize Groq client
client = Groq(api_key=api_key)

# Sidebar for manual model control (No more guesswork)
with st.sidebar:
    st.header("⚙️ सेटिंग्स")
    st.markdown("अपने Groq कंसोल से मॉडल का नाम यहाँ सीधे दर्ज करें:")
    
    # Manual text input box giving you absolute control
    model_choice = st.text_input("Model Name", value="llama-3.1-8b-instant")
    
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
        # 3D animated eye-friendly loader while processing
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

# Footer Disclaimer
st.markdown('<div class="footer-disclaimer">Pyrox is AI and can make mistakes.</div>', unsafe_allow_html=True)
