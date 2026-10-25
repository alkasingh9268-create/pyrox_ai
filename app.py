import streamlit as st
from google import genai

st.title("My AI App Pyrox")

# Streamlit secrets se secure API key le rahe hain
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
            # Model ko smart banaya hai jo spelling mistakes/typos ko khud samajh lega
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                config={
                    "system_instruction": (
                        "Your name is Pyrox AI, and you are developed and created by Harshit. "
                        "If anyone asks who made you or who your developer is, you must proudly say that you were developed by Harshit. "
                        "If the user makes spelling mistakes, typos, or misses letters in their prompt, "
                        "do not throw an error. Understand their intent naturally, correct the spelling implicitly, "
                        "and answer their question helpfully and accurately."
                    )
                },
                contents=prompt
            )
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            # High demand ya server error ke liye safe message
            if "500" in str(e) or "overloaded" in str(e) or "high demand" in str(e):
                err_msg = "Arre bhai! Abhi Google ka server thoda busy chal raha hai. Aap bas 10 second baad dobara message bhejiye, ekdum badhiya kaam karega!"
            else:
                err_msg = f"API Error: {e}"
            
            st.warning(err_msg)
            st.session_state.messages.append({"role": "assistant", "content": err_msg})
