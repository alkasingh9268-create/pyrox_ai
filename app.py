import streamlit as st
from google import genai
import time

# Page Configuration
st.set_page_config(page_title="Pyrox AI", page_icon="🧮", layout="centered")

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
        error_occurred = False
        
        # Automatic Retry Logic: Server busy hone par 3 baar koshish karega
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
                break  # Response mil gaya toh loop se bahar
            except Exception as e:
                err_str = str(e)
                if attempt == 2:
                    error_occurred = True
                    if "500" in err_str or "overloaded" in err_str or "high demand" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        err_msg = "⚠️ Arre bhai! Abhi Google ke server par thoda load chal raha hai. Ek second ruk kar dobara bhej, ekdam fatfat chalega!"
                    else:
                        err_msg = "🤖 Bhai, server se connect hone mein thoda lafda ho gaya. Ek baar apna sawal fir se bhej ke dekh!"
                else:
                    # Thoda sa ruk kar agli koshish karega
                    time.sleep(1.5)

        if response_text:
            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
        elif error_occurred:
            st.warning(err_msg)
            st.session_state.messages.append({"role": "assistant", "content": err_msg})
