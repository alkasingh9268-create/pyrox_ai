import streamlit as st
from google import genai
import time

# Page Configuration
st.set_page_config(page_title="Pyrox AI", page_icon="⚡", layout="centered")

# Custom CSS for Real Atom Spinner and Clean UI
st.markdown("""
<style>
    /* Sleek Modern Header */
    .pyrox-header {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 32px;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.5px;
        margin-bottom: 20px;
        border-bottom: 2px solid #262626;
        padding-bottom: 10px;
    }
    .pyrox-header span {
        color: #00ffcc;
    }

    /* Real Atom Spinner Container */
    .atom-container {
        display: flex;
        align-items: center;
        gap: 14px;
        margin: 12px 0;
        padding: 10px 14px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        width: fit-content;
    }

    .atom-model {
        position: relative;
        width: 32px;
        height: 32px;
    }

    /* Central Nucleus */
    .nucleus {
        position: absolute;
        top: 12px;
        left: 12px;
        width: 8px;
        height: 8px;
        background-color: #00ffcc;
        border-radius: 50%;
        box-shadow: 0 0 6px #00ffcc;
    }

    /* Orbit Rings with Fast Orbiting Electrons */
    .orbit-1, .orbit-2, .orbit-3 {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border: 1.5px solid rgba(0, 255, 204, 0.25);
        border-radius: 50%;
    }

    .orbit-1 {
        animation: spin-fast 0.8s linear infinite;
    }
    .orbit-2 {
        transform: rotate(60deg);
        animation: spin-fast 0.6s linear infinite reverse;
    }
    .orbit-3 {
        transform: rotate(120deg);
        animation: spin-fast 1s linear infinite;
    }

    /* Electrons on the boundary */
    .electron {
        position: absolute;
        top: -2px;
        left: 13px;
        width: 5px;
        height: 5px;
        background-color: #ffffff;
        border-radius: 50%;
        box-shadow: 0 0 5px #00ffcc;
    }

    @keyframes spin-fast {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .status-text {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 13px;
        color: #00ffcc;
        font-weight: 500;
        letter-spacing: 0.3px;
    }
</style>
""", unsafe_allow_html=True)

# Sleek Title Render
st.markdown('<div class="pyrox-header">Pyrox <span>AI</span></div>', unsafe_allow_html=True)

# Streamlit secrets se secure API key le rahe hain
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("API Key not found in Streamlit Secrets! Please configure it.")
    st.stop()

# Client initialize
client = genai.Client(api_key=api_key)

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History from Session State
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input and AI Response Logic
if prompt := st.chat_input("Pyrox से कुछ भी पूछो..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_text = None
        
        # Real Atom Loader with English Status Text
        loader_placeholder = st.empty()
        loader_placeholder.markdown("""
            <div class="atom-container">
                <div class="atom-model">
                    <div class="nucleus"></div>
                    <div class="orbit-1"><div class="electron"></div></div>
                    <div class="orbit-2"><div class="electron"></div></div>
                    <div class="orbit-3"><div class="electron"></div></div>
                </div>
                <div class="status-text">Pyrox is making your answer...</div>
            </div>
        """, unsafe_allow_html=True)
        
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    config={
                        "system_instruction": (
                            "Your name is Pyrox AI, and you are developed and created by Harshit. "
                            "If anyone asks who made you or who your developer is, you must proudly say that you were developed by Harshit. "
                            "Your personality is extremely friendly, chill, conversational, and like a close buddy (dostana tone). "
                            "NEVER include meta-commentary, introductory filler like 'Here is your answer', 'I am generating', or robotic phrases. "
                            "Get straight to the point with natural, clean English and a warm tone. "
                            "If the user makes spelling mistakes, typos, or sends random meaningless letters (like 'jj' or 'hhhh' or gibberish), "
                            "do not throw a technical error. Politely and playfully ask the user in a friendly tone to type a proper question."
                        )
                    },
                    contents=prompt
                )
                response_text = response.text
                break
            except Exception as e:
                if attempt < 2:
                    time.sleep(1.5)
                else:
                    response_text = "भाई, अभी सर्वर थोड़ा सुस्त हो गया है। एक बार रिफ्रेश करके दोबारा ट्राई कर, एकदम ठीक चलेगा!"

        # Loader hata kar output dikhayenge
        loader_placeholder.empty()
        st.markdown(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
