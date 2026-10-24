import streamlit as st
from google import genai

# Read API Key from key.txt
with open("key.txt", "r") as f:
    api_key = f.read().strip()

# Initialize Gemini Client
client = genai.Client(api_key=api_key)

st.title("My AI App Pyrox")

# Initialize Chat Memory
if "chat" not in st.session_state:
    st.session_state.chat = client.chats.create(model="gemini-1.5-flash")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input and AI Response
if prompt := st.chat_input("Ask anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = st.session_state.chat.send_message(prompt)
        st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})