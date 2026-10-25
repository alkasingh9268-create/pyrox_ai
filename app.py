import streamlit as st
from groq import Groq

# Page Config
st.set_page_config(page_title="Pyrox AI", page_icon="⚡", layout="centered")

# Custom Dark Theme CSS & 3D Atom Animation
st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .chat-header { text-align: center; font-size: 2.5rem; font-weight: 700; color: #58a6ff; margin-bottom: 20px; }
    .atom-loader { display: flex; justify-content: center; align-items: center; height: 100px; }
    .atom { position: relative; width: 60px; height: 60px; border-radius: 50%; }
    .nucleus { position: absolute; top: 50%; left: 50%; width: 12px; height: 12px; background: #58a6ff; border-radius: 50%; transform: translate(-50%, -50%); box-shadow: 0 0 10px #58a6ff; }
    .ring { position: absolute; width: 100%; height: 100%; border: 2px solid rgba(88, 166, 255, 0.5); border-radius: 50%; animation: spin 1.5s linear infinite; }
    .ring:nth-child(2) { transform: rotateX(60deg) rotateY(0deg); }
    .ring:nth-child(3) { transform: rotateX(60deg) rotateY(60deg); }
    .ring:nth-child(4) { transform: rotateX(60deg) rotateY(120deg); }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='chat-header'>Pyrox AI</h1>", unsafe_allow_html=True)

# सीधा कोड के अंदर की हार्डकोड कर दी है ताकि सीक्रेट्स का चक्कर ही खत्म हो जाए
api_key = "gsk_U1okzlm0236ZS8fUk6nItWGdyb3FY02iQBWJ9ohR2jEEQiERjGcem"

try:
    client = Groq(api_key=api_key)
except Exception as e:
    st.error(f"Error initializing Groq client: {e}")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask Pyrox AI..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        response_placeholder.markdown("""
        <div class="atom-loader">
            <div class="atom">
                <div class="nucleus"></div>
                <div class="ring"></div>
                <div class="ring"></div>
                <div class="ring"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        try:
            formatted_messages = [{"role": "system", "content": "You are Pyrox AI, a highly performant and helpful AI assistant."}]
            for msg in st.session_state.messages:
                formatted_messages.append({"role": msg["role"], "content": msg["content"]})

            chat_completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=formatted_messages,
                temperature=0.7
            )
            
            reply = chat_completion.choices[0].message.content
            response_placeholder.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

        except Exception as e:
            response_placeholder.error(f"Error connecting to Groq API: {str(e)}")
