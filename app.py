import streamlit as st
from groq import Groq

client = Groq(api_key="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")

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Hello!",
        }
    ],
    model="llama3-8b-8192",
)

st.success("API Key aur Model dono ekdam fit kaam kar rahe hain!")
st.write("🤖 AI Reply:")
st.info(chat_completion.choices[0].message.content)
