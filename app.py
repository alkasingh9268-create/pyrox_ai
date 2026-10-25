import streamlit as st
from google import genai

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
        try:
            # Model call with robust system instructions for identity, typos, and gibberish
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                config={
                    "system_instruction": (
                        "Your name is Pyrox AI, and you are developed and created by Harshit. "
                        "If anyone asks who made you or who your developer is, you must proudly say that you were developed by Harshit. "
                        "If the user makes spelling mistakes, typos, or sends random meaningless letters (like 'hhhh' or gibberish), "
                        "do not throw a technical error. Politely ask the user in a friendly, conversational tone to type a proper question, "
                        "and implicitly correct spelling mistakes when a valid query is provided."
                    )
                },
                contents=prompt
            )
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            # Server high demand ya 500 error ko gracefully handle karne ke liye
            err_str = str(e)
            if "500" in err_str or "overloaded" in err_str or "high demand" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                err_msg = "⚠️ अरे भाई! अभी Google के सर्वर पर बहुत ज्यादा लोड (High Demand) है। यह एक-दो मिनट में अपने आप ठीक हो जाएगा। कृपया थोड़ा सब्र करके दोबारा मैसेज भेजिए!"
            else:
                err_msg = "🤖 भाई, लगता है कुछ गड़बड़ हो गई या सर्वर ने जवाब देने से मना कर दिया। एक बार फिर से अपना सवाल भेजकर ट्राई करो!"
            
            st.warning(err_msg)
            st.session_state.messages.append({"role": "assistant", "content": err_msg})
