import streamlit as st
from groq import Groq

client = Groq(api_key="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")

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Hello! How are you?",
        }
    ],
    model="llama-3.1-8b-instant",
)

st.success("API Key aur Model ekdum sahi kaam kar rahe hain!")
st.write("🤖 AI ka reply:")
st.info(chat_completion.choices[0].message.content)
