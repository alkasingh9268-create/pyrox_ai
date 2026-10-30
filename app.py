import os
import asyncio
import edge_tts
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
    <div style='text-align: center; margin-top: 10px; margin-bottom: 20px;'>
        <h1 style='font-size: 2.3rem; font-weight: 800; color: #ffffff; margin-bottom: 2px;'>Pyrox</h1>
        <p style='color: #9ca3af; font-size: 1.05rem;'>How can I help you today? ✨</p>
    </div>
""", unsafe_allow_html=True)

# Function to generate real Edge-TTS (Madhur Neural) Audio File
def generate_edge_audio(text, filename="response.mp3"):
    try:
        # Clean text from heavy emojis/symbols for clean audio generation
        clean_t = text.replace("*", "").replace("#", "").replace("`", "").replace("✨", "").replace("👋", "").replace("🚀", "").replace("💻", "").replace("😎", "").replace("💡", "").replace("🎯", "")
        
        async def _main():
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

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "👤"):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "audio_file" in message:
            if message["audio_file"] and os.path.exists(message["audio_file"]):
                st.audio(message["audio_file"], format="audio/mp3")

# User Chat Input
if prompt := st.chat_input("Ask Pyrox anything..."):
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Generate AI Response from Groq + Edge-TTS Audio
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("✨ Thinking & Generating Voice..."):
            if not client:
                reply = "⚠️ Groq API Key missing in Streamlit Secrets!"
                audio_path = None
            else:
                try:
                    # Using the universally available model name
                    completion = client.chat.completions.create(
                        model="llama-3.1-70b-versatile",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are Pyrox, an advanced, friendly, and Gen-Z AI assistant. Talk in a mix of natural Hindi and English (Hinglish) with cool emojis. Be sharp, direct, and helpful without sounding robotic."
                            },
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=400,
                    )
                    reply = completion.choices[0].message.content
                    
                    # Generate Server MP3 Audio via Edge-TTS
                    audio_filename = f"audio_{len(st.session_state.messages)}.mp3"
                    success = generate_edge_audio(reply, audio_filename)
                    audio_path = audio_filename if success else None
                    
                except Exception as e:
                    reply = f"⚠️ Error: {str(e)}"
                    audio_path = None
            
            st.markdown(reply)
            if audio_path and os.path.exists(audio_path):
                st.audio(audio_path, format="audio/mp3")
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": reply, 
                "audio_file": audio_path
            })
