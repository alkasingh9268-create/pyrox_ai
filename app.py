import streamlit as st
from google import genai

st.title("My AI App Pyrox")

# Streamlit secrets से सुरक्षित तरीके से API key ले रहे हैं
api_key = st.secrets["GEMINI_API_KEY"]

client = genai.Client(api_key=api_key)

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
                model="gemini-2.5-flash",
                contents=prompt
            )


            
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"API Error: {e}")
