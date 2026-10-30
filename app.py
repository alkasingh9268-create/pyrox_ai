import os
import streamlit as st
from groq import Groq

# 1. Page Configuration
st.set_page_config(
    page_title="Pyrox Studio",
    page_icon="🤖",
    layout="centered"
)

# Custom Ultra-Dark Gemini/ChatGPT CSS Theme
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    #MainMenu, header, footer { visibility: hidden; }
    
    /* Custom Chat Input Bar Styling */
    .stChatInputContainer {
        border-color: #222226 !important;
        background-color: #08080a !important;
        border-radius: 28px !important;
    }
    .stChatInputContainer textarea {
        color: #ffffff !important;
    }
    
    /* Chat Message Bubbles */
    div[data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
    }
    div[data-testid="stChatMessage"] p {
        color: #f3f4f6 !important;
        font-size: 1rem;
        line-height: 1.6;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize Groq Client
groq_api_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")
client = Groq(api_key=groq_api_key) if groq_api_key else None

# Session State for Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# App Header
st.markdown("""
    <div style='text-align: center; margin-top: 20px; margin-bottom: 30px;'>
        <h1 style='font-size: 2.5rem; font-weight: 800; color: #ffffff; margin-bottom: 5px;'>Pyrox</h1>
        <p style='color: #9ca3af; font-size: 1.1rem;'>How can I help you today? ✨</p>
    </div>
""", unsafe_allow_html=True)

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "👤"):
        st.markdown(message["content"])

# User Chat Input
if prompt := st.chat_input("Ask Pyrox anything..."):
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Generate AI Response from Groq instantly
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("✨ Thinking..."):
            if not client:
                reply = "⚠️ Groq API Key missing in Streamlit Secrets!"
            else:
                try:
                    completion = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are Pyrox, an advanced, friendly, and Gen-Z AI assistant. Talk in a mix of natural Hindi and English (Hinglish) with cool emojis. Be sharp, direct, and helpful without sounding robotic."
                            },
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=512,
                    )
                    reply = completion.choices[0].message.content
                except Exception as e:
                    reply = f"⚠️ Error: {str(e)}"
            
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
