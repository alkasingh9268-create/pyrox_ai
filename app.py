import streamlit as st
from groq import Groq

# Page configuration with custom title and icon (No "chatbot" word)
st.set_page_config(
    page_title="Pyrox AI Studio",
    page_icon="⚡",
    layout="centered"
)

# Custom CSS for colors, fonts, and styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Background and text colors */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    /* Custom Header Styling */
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #FF4B4B, #FF914D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    
    .sub-header {
        color: #a0a0a0;
        font-size: 0.95rem;
        margin-bottom: 25px;
    }
    </style>
""", unsafe_allow_html=True)

# App Logo and Header (Without the word chatbot)
st.markdown('<div class="main-header">⚡ Pyrox AI Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Groq API और Llama मॉडल्स द्वारा संचालित हाई-स्पीड असिस्टेंट</div>', unsafe_allow_html=True)

# Check API key from secrets
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    st.error("त्रुटि: Streamlit Secrets में 'GROQ_API_KEY' नहीं मिली!")
    st.stop()

# Initialize Groq client
client = Groq(api_key=api_key)

# Sidebar for controls
with st.sidebar:
    st.header("⚙️ सेटिंग्स")
    # Safe verified chat models dropdown (No classification/audio models)
    model_choice = st.selectbox(
        "मॉडल चुनें",
        ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"],
        index=0
    )
    
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
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # Keep only the last 10 messages to avoid token limit errors
            recent_messages = st.session_state.messages[-10:]
            
            completion = client.chat.completions.create(
                model=model_choice,
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in recent_messages
                ],
                stream=True,
            )
            
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
                    
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            full_response = f"कनेक्शन एरर: {e}"
            message_placeholder.error(full_response)
            
        st.session_state.messages.append({"role": "assistant", "content": full_response})
