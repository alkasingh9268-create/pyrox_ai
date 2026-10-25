import streamlit as st
from google import genai
from google.genai import types
import time

# Page Configuration
st.set_page_config(page_title="Pyrox AI", page_icon="✨", layout="centered")

# Custom CSS for Gemini + ChatGPT Hybrid Theme and True Multi-Directional 3D Atoms
st.markdown("""
<style>
    /* Dark Gemini-style Background and Clean Typography */
    .stApp {
        background-color: #131314;
        color: #e3e3e3;
    }
    
    /* Sleek Modern Header */
    .pyrox-header {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 30px;
        font-weight: 700;
        color: #e3e3e3;
        letter-spacing: -0.5px;
        margin-bottom: 25px;
        border-bottom: 1px solid #2e2f31;
        padding-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .pyrox-header span {
        background: linear-gradient(135deg, #7c4dff, #00e5ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Atom Loader Box with True 3D Multi-Directional Orbits */
    .atom-container {
        display: flex;
        align-items: center;
        gap: 16px;
        margin: 14px 0;
        padding: 10px 16px;
        background: #1e1f20;
        border: 1px solid #333537;
        border-radius: 12px;
        width: fit-content;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }

    .atom-model {
        position: relative;
        width: 40px;
        height: 40px;
        perspective: 1000px;
    }

    /* Central Glowing Nucleus */
    .nucleus {
        position: absolute;
        top: 16px;
        left: 16px;
        width: 8px;
        height: 8px;
        background-color: #00e5ff;
        border-radius: 50%;
        box-shadow: 0 0 10px #00e5ff, 0 0 18px #7c4dff;
    }

    /* 5 Multi-Directional 3D Orbit Rings */
    .orbit-1, .orbit-2, .orbit-3, .orbit-4, .orbit-5 {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border: 1.5px solid rgba(0, 229, 255, 0.35);
        border-radius: 50%;
    }

    .orbit-1 { transform: rotateX(65deg) rotateZ(15deg); animation: spin-3d-1 0.7s linear infinite; }
    .orbit-2 { transform: rotateY(65deg) rotateZ(45deg); animation: spin-3d-2 0.5s linear infinite reverse; }
    .orbit-3 { transform: rotateX(30deg) rotateY(65deg); animation: spin-3d-1 0.9s linear infinite; }
    .orbit-4 { transform: rotateX(-50deg) rotateY(35deg); animation: spin-3d-2 0.6s linear infinite reverse; }
    .orbit-5 { transform: rotateY(-65deg) rotateZ(-30deg); animation: spin-3d-1 0.8s linear infinite; }

    /* Fast Electrons on Boundary */
    .electron {
        position: absolute;
        top: -3px;
        left: 17px;
        width: 5px;
        height: 5px;
        background-color: #ffffff;
        border-radius: 50%;
        box-shadow: 0 0 8px #00e5ff;
    }

    @keyframes spin-3d-1 {
        0% { transform: rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg)) rotateZ(0deg); }
        100% { transform: rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg)) rotateZ(360deg); }
    }
    @keyframes spin-3d-2 {
        0% { transform: rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg)) rotateZ(360deg); }
        100% { transform: rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg)) rotateZ(0deg); }
    }

    .status-text {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 13.5px;
        background: linear-gradient(90deg, #00e5ff, #7c4dff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
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
if prompt := st.chat_input("Pyrox se kuch bhi poochho..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_text = None
        
        # Real Atom Loader with 3D Multi-Axis Orbits & Status Text
        loader_placeholder = st.empty()
        loader_placeholder.markdown("""
            <div class="atom-container">
                <div class="atom-model">
                    <div class="nucleus"></div>
                    <div class="orbit-1"><div class="electron"></div></div>
                    <div class="orbit-2"><div class="electron"></div></div>
                    <div class="orbit-3"><div class="electron"></div></div>
                    <div class="orbit-4"><div class="electron"></div></div>
                    <div class="orbit-5"><div class="electron"></div></div>
                </div>
                <div class="status-text">Pyrox is making your answer...</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Robust API Call with Proper SDK Config Structure
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=(
                            "Your name is Pyrox AI, and you are developed and created by Harshit. "
                            "If anyone asks who made you, who created you, or who your developer is, "
                            "you must proudly and clearly state that you were developed by Harshit. "
                            "Your personality is extremely friendly, chill, conversational, and like a close buddy (dostana tone). "
                            "NEVER include meta-commentary, introductory filler like 'Here is your answer', 'I am generating', or robotic phrases. "
                            "Get straight to the point with natural, clean language and a warm tone. "
                            "If the user makes spelling mistakes, typos, or sends random meaningless letters (like 'jj' or 'hhhh' or gibberish), "
                            "do not throw a technical error. Politely and playfully ask the user in a friendly tone to type a proper question."
                        )
                    )
                )
                response_text = response.text
                break
            except Exception as e:
                if attempt == 0:
                    time.sleep(2)
                elif attempt == 1:
                    time.sleep(4)
                else:
                    # Agar tab bhi error aaye, toh asli error print karega taaki pata chale
                    response_text = f"Bhai, API mein ye issue aa raha hai: `{str(e)}`. Ek baar check kar le!"

        # Loader hata kar output dikhayenge
        loader_placeholder.empty()
        st.markdown(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
