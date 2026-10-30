import os
import streamlit as st
from groq import Groq

# Page Configuration
st.set_page_config(
    page_title="Pyrox",
    page_icon="⚡",
    layout="centered"
)

# Custom Styling for Dark Theme
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    #MainMenu, header, footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Pyrox")
st.write("✨ नेटिव चैट कंसोल — बिना रीलोड, बिना रुकावट।")

# API Key Initialization
api_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")
client = Groq(api_key=api_key) if api_key else None

if not api_key:
    st.error("⚠️ कृपया Streamlit Secrets में अपनी GROQ_API_KEY सेट करें।")

# Initialize Session State for Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Prior Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Native Streamlit Chat Input
if prompt := st.chat_input("Pyrox से कुछ भी पूछें..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Assistant Response via Groq API (Updated Active Model)
    if client:
        with st.chat_message("assistant"):
            with st.spinner("Pyrox सोच रहा है... ✨"):
                try:
                    formatted_messages = [
                        {
                            "role": "system",
                            "content": (
                                "You are Pyrox, an exceptionally intelligent, adaptive, and emotionally aware AI collaborator with a great sense of humor. "
                                "Remember the full conversation history. Talk in a smooth, natural blend of Hinglish (Hindi + English) with cool emojis ✨."
                            )
                        }
                    ]
                    for msg in st.session_state.messages:
                        formatted_messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })

                    completion = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",  # Updated active model
                        messages=formatted_messages,
                        temperature=0.75,
                        max_tokens=600,
                    )
                    reply = completion.choices[0].message.content
                    st.markdown(reply)
                    
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                
                except Exception as e:
                    error_msg = f"⚠️ API Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    else:
        st.error("❌ Groq Client उपलब्ध नहीं है।")
