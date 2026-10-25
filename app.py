import streamlit as st
from groq import Groq

# Page Configuration
st.set_page_config(
    page_title="Pyrox AI",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 Pyrox AI")
st.caption("Powered by Groq API & Streamlit")

# Initialize Groq Client securely from Streamlit Secrets
try:
    groq_api_key = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=groq_api_key)
except Exception as e:
    st.error(f"Secret Configuration Error: {e}. Please ensure GROQ_API_KEY is correctly set in Streamlit Secrets.")
    st.stop()

# Sidebar Controls & Settings
with st.sidebar:
    st.header("⚙️ Controls & Settings")
    
    # Model selection
    model_name = st.selectbox(
        "Select Groq Model",
        ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
        index=0
    )
    
    # AI Persona / Tone selection
    tone = st.selectbox(
        "AI Tone / Persona",
        ["Friendly & Helpful", "Professional Expert", "Technical Developer", "Witty & Creative"]
    )
    
    system_prompts = {
        "Friendly & Helpful": "You are Pyrox AI, a warm, engaging, and helpful AI assistant.",
        "Professional Expert": "You are Pyrox AI, a professional, concise, and structured expert assistant.",
        "Technical Developer": "You are Pyrox AI, a direct, highly technical coding and development assistant.",
        "Witty & Creative": "You are Pyrox AI, a creative, witty, and engaging conversational partner."
    }
    
    system_prompt = system_prompts[tone]
    temperature = st.slider("Temperature (Creativity)", 0.0, 1.0, 0.7, 0.1)
    
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Initialize Chat History in Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Prior Chat Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle User Input & Chat Stream
if prompt := st.chat_input("Pyrox AI से कुछ भी पूछें..."):
    # Add user message to session
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Assistant Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # Construct messages payload including system prompt
            messages_payload = [{"role": "system", "content": system_prompt}] + [
                {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
            ]
            
            # Call Groq API with streaming enabled
            stream = client.chat.completions.create(
                model=model_name,
                messages=messages_payload,
                temperature=temperature,
                stream=True
            )
            
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    full_response += content
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            full_response = f"⚠️ API Connection Error: {e}"
            message_placeholder.error(full_response)
            
        # Save assistant response to session state
        st.session_state.messages.append({"role": "assistant", "content": full_response})
