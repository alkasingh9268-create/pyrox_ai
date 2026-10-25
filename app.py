import streamlit as st
from google import genai
import time

# Page Configuration
st.set_page_config(page_title="Pyrox AI", page_icon="🧮", layout="centered")

# CSS for Spinning Atoms and Smooth UI
st.markdown("""
<style>
    .atom-loader-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin: 20px 0;
    }
    .atom-spinner {
        position: relative;
        width: 60px;
        height: 60px;
    }
    .nucleus {
        position: absolute;
        top: 23px;
        left: 23px;
        width: 14px;
        height: 14px;
        background-color: #00ffcc;
        border-radius: 50%;
        box-shadow: 0 0 10px #00ffcc;
    }
    .orbit {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border: 2px dashed rgba(0, 255, 204, 0.4);
        border-radius: 50%;
        animation: spin 2s linear infinite;
    }
    .orbit:nth-child(2) {
        animation: spin-reverse 1.5s linear infinite;
        border-color: rgba(255, 0, 128, 0.4);
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    @keyframes spin-reverse {
        0% { transform: rotate(360deg); }
        100% { transform: rotate(0deg); }
    }
    .loading-text {
        margin-top: 12px;
        font-family: sans-serif;
        font-size: 14px;
        color: #00ffcc;
        font-weight: 500;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)

st.title("Pyrox AI")

# Streamlit secrets se secure API key le rahe hain
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("API Key not found in Streamlit Secrets! Please configure it.")
    st.stop()

client = genai.Client(api_key=api_key)

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History from Session State
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input and AI Response Logic
if prompt := st.chat_input("Ask Pyrox anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_text = None
        
        # Custom Atoms Spinner with Dynamic Text Placeholder
        placeholder = st.empty()
        
        with placeholder.container():
            st.markdown("""
                <div class="atom-loader-container">
                    <div class="atom-spinner">
                        <div class="orbit"></div>
                        <div class="orbit"></div>
                        <div class="nucleus"></div>
                    </div>
                    <div class="loading-text">Atoms align ho rahe hain, Pyrox soch raha hai...</div>
                </div>
            """, unsafe_allow_html=True)
            
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model="gemini-3.5-flash",
                    config={
                        "system_instruction": (
                            "Your name is Pyrox AI, and you are developed and created by Harshit. "
                            "If anyone asks who made you or who your developer is, you must proudly say that you were developed by Harshit. "
                            "Your personality is extremely friendly, chill, conversational, and like a close buddy (dostana tone). "
                            "Do not sound robotic, formal, or like a boring textbook. Use casual, engaging language, and talk warmly. "
                            "If the user makes spelling mistakes, typos, or sends random meaningless letters (like 'hhhh' or gibberish), "
                            "do not throw a technical error. Politely and playfully ask the user in a friendly, conversational tone to type a proper question, "
                            "and implicitly correct spelling mistakes when a valid query is provided."
                        )
                    },
                    contents=prompt
                )
                response_text = response.text
                break
            except Exception as e:
                if attempt < 2:
                    time.sleep(2)
                else:
                    response_text = "Arre bhai, thoda sa traffic zyada ho gaya hai. Ek second ruk ke dobara likh na, ekdam mast chalega!"

        # Purane loader ko hata kar seedha output dikhayenge
        placeholder.empty()
        st.markdown(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
