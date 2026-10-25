import streamlit as st
from groq import Groq

# Page configuration
st.set_page_config(
    page_title="Pyrox AI Chatbot",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 Pyrox AI Chatbot")
st.markdown("Groq API द्वारा संचालित।")

# Check and initialize Groq client using Streamlit secrets
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    st.error("त्रुटि: Streamlit Secrets में 'GROQ_API_KEY' नहीं मिली!")
    st.stop()

# Initialize the Groq client
client = Groq(api_key=api_key)

# Dynamically fetch available models so it never gives model_not_found/decommissioned error
try:
    models_response = client.models.list()
    available_models = [m.id for m in models_response.data if "embedding" not in m.id]
except Exception as e:
    available_models = []

# Sidebar for controls
with st.sidebar:
    st.header("⚙️ Settings")
    if available_models:
        model_choice = st.selectbox("Choose Model", available_models, index=0)
    else:
        model_choice = "llama-3.3-70b-versatile"
        st.warning("मॉडल लिस्ट लोड नहीं हो पाई, डिफ़ॉल्ट उपयोग हो रहा है।")
    
    if st.button("Clear Chat History", type="primary"):
        st.session_state.messages = []
        st.rerun()

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display prior chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input from chat box
if prompt := st.chat_input("यहाँ अपना संदेश टाइप करें..."):
    # Add user message to session state
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message in chat container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # Request completion from Groq API with streaming enabled
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
            
        # Add assistant response to session state
        st.session_state.messages.append({"role": "assistant", "content": full_response})
