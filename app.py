import streamlit as st
from groq import Groq

# Page configuration
st.set_page_config(
    page_title="Pyrox AI Chatbot",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 Pyrox AI Chatbot")

# Check API key from secrets
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    st.error("त्रुटि: Streamlit Secrets में 'GROQ_API_KEY' नहीं मिली!")
    st.stop()

# Initialize Groq client
client = Groq(api_key=api_key)

# Fetch available models directly from your API key
available_models = []
try:
    models_response = client.models.list()
    available_models = [m.id for m in models_response.data if "embed" not in m.id and "whisper" not in m.id]
except Exception as e:
    pass

# Sidebar for controls
with st.sidebar:
    st.header("⚙️ Settings")
    
    if available_models:
        model_choice = st.selectbox("Select Your Key's Active Model", available_models)
    else:
        # Fallback text input if auto-fetch fails, so you have full control
        model_choice = st.text_input("Enter Model Name Manually", value="llama-3.1-70b-versatile")
    
    if st.button("Clear Chat History", type="primary"):
        st.session_state.messages = []
        st.rerun()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("यहाँ अपना संदेश टाइप करें..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            completion = client.chat.completions.create(
                model=model_choice,
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            )
            
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
                    
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            full_response = f"कनेक्शन एरर: {e}"
            message_placeholder.error(full_response)
            
        st.session_state.messages.append({"role": "assistant", "content": full_response})
