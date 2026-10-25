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

# Directly fetch available models for YOUR API key
available_models = []
fetch_error = ""
try:
    models_response = client.models.list()
    # Filter out audio/embedding models, keep text chat models
    available_models = [
        m.id for m in models_response.data 
        if "embed" not in m.id and "whisper" not in m.id and "audio" not in m.id and "orpheus" not in m.id
    ]
except Exception as e:
    fetch_error = str(e)

# Sidebar for controls
with st.sidebar:
    st.header("⚙️ Settings")
    
    if available_models:
        # Show dropdown of models actually available on your key
        model_choice = st.selectbox("Select Your Active Model", available_models)
    else:
        st.warning("ऑटो-लिस्ट नहीं आई। अपने Groq डैशबोर्ड से सही मॉडल नाम यहाँ टाइप करें:")
        model_choice = st.text_input("Enter Model Name Manually", value="llama-3.1-8b-instant")
        if fetch_error:
            st.caption(f"Debug: {fetch_error}")
    
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
            # Keep only the last 10 messages to prevent size errors
            recent_messages = st.session_state.messages[-10:]
            
            completion = client.chat.completions.create(
                model=model_choice,
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in recent_messages
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
