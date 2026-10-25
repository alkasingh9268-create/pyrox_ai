import streamlit as st
from groq import Groq
import time

# Page configuration
st.set_page_config(
    page_title="Pyrox AI Studio",
    page_icon="⚡",
    layout="centered"
)

# Custom CSS for massive styling, glassmorphism, soothing dark theme, and animations
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Soothing deep dark slate theme */
    .stApp {
        background-color: #13171F;
        color: #E6EDF3;
    }
    
    .main-header {
        font-size: 2.3rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0px;
        letter-spacing: -0.5px;
    }
    
    /* Calm blue accent */
    .ai-highlight {
        color: #58A6FF;
    }
    
    .sub-header {
        color: #8B949E;
        font-size: 0.95rem;
        margin-bottom: 12px;
    }
    
    /* Professional Creator Badge */
    .creator-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(88, 166, 255, 0.1);
        border: 1px solid rgba(88, 166, 255, 0.3);
        color: #58A6FF;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-bottom: 25px;
        letter-spacing: 0.5px;
    }
    
    /* Welcome Card */
    .welcome-card {
        background: rgba(22, 27, 34, 0.7);
        border: 1px solid #30363D;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        text-align: center;
    }
    
    .welcome-card h3 {
        color: #58A6FF;
        margin-bottom: 8px;
        font-size: 1.2rem;
    }
    
    .welcome-card p {
        color: #8B949E;
        font-size: 0.9rem;
        margin: 0;
    }
    
    .footer-disclaimer {
        text-align: center;
        color: #6E7681;
        font-size: 0.8rem;
        margin-top: 20px;
        font-style: italic;
    }
    
    /* 3D Atom Spinner Animation */
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

# Header Section
st.markdown('<div class="main-header">Pyrox <span class="ai-highlight">AI</span> Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Groq API द्वारा संचालित हाई-स्पीड इंटेलिजेंट असिस्टेंट</div>', unsafe_allow_html=True)
st.markdown('<div class="creator-badge">✨ Crafted by Harshit</div>', unsafe_allow_html=True)

# Check API key from secrets
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    st.error("त्रुटि: Streamlit Secrets में 'GROQ_API_KEY' नहीं मिली! कृपया इसे सेट करें।")
    st.stop()

# Initialize Groq client
client = Groq(api_key=api_key)

# Sidebar Controls & Heavy Customization Panel
with st.sidebar:
    st.header("⚙️ Pyrox कंट्रोल पैनल")
    
    # Model Selection with robust verified fallbacks
    model_options = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-70b-8192",
        "gemma2-9b-it",
        "mixtral-8x7b-32768"
    ]
    model_choice = st.selectbox("प्राइमरी मॉडल चुनें", model_options)
    
    st.divider()
    
    # System Status Section
    st.markdown("### 📊 सिस्टम स्टेटस")
    st.success("🟢 Groq API Connected")
    
    if "messages" in st.session_state and st.session_state.messages:
        msg_count = len(st.session_state.messages)
        st.info(f"💬 कुल संदेश: {msg_count}")
    else:
        st.info("💬 चैट खाली है")
        
    st.divider()
    
    # Action Buttons
    if st.button("🗑️ चैट इतिहास साफ़ करें", type="primary", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
        
    # Export Chat Option
    if "messages" in st.session_state and st.session_state.messages:
        chat_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
        st.download_button(
            label="📥 चैट डाउनलोड करें",
            data=chat_text,
            file_name="pyrox_chat_history.txt",
            mime="text/plain",
            use_container_width=True
        )

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show Welcome Card if no messages yet
if not st.session_state.messages:
    st.markdown("""
        <div class="welcome-card">
            <h3>नमस्ते, मैं Pyrox हूँ! ⚡</h3>
            <p>यहाँ आप कोडिंग, पढ़ाई, या किसी भी विषय पर खुलकर बात कर सकते हैं। नीचे बॉक्स में अपना सवाल टाइप करें।</p>
        </div>
    """, unsafe_allow_html=True)

# Display prior chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input from chat box
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
        
        # Robust Auto-Fallback Chain (If a model gives 404/400, it automatically tries the next one!)
        models_to_try = [model_choice] + [m for m in model_options if m != model_choice]
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
                
                # Remove loader once streaming starts successfully
                loader_placeholder.empty()
                
                for chunk in completion:
                    if chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
                        message_placeholder.markdown(full_response + "▌")
                        
                message_placeholder.markdown(full_response)
                success = True
                break # Exit loop on success
                
            except Exception as e:
                last_error = str(e)
                continue # Try next fallback model silently
        
        if not success:
            loader_placeholder.empty()
            full_response = f"कनेक्शन एरर: सभी फॉલबैक मॉडल फेल हो गए। विवरण: {last_error}"
            message_placeholder.error(full_response)
            
        # Add assistant response to session state
        st.session_state.messages.append({"role": "assistant", "content": full_response})

# Footer Disclaimer
st.markdown('<div class="footer-disclaimer">Pyrox is AI and can make mistakes.</div>', unsafe_allow_html=True)
      
