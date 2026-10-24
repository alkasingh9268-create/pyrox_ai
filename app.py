import streamlit as st
from google import genai

st.title("My AI App Pyrox")

# API Key check
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["AQ.Ab8RN6IceYTKZkdsGC8NwJmNjffg6H4AhtnviDZgCMbnrKssqA"]
else:
    api_key = "YOUR_API_KEY_HERE" # अगर secrets में नहीं है तो यहाँ सीधे अपनी असली की डालकर चेक कर सकते हैं

try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"Client Init Error: {e}")

# Initialize Chat History
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
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"API Connection Error: {e}")
