import streamlit as st
import urllib.request
import json

# Page Config
st.set_page_config(page_title="Pyrox AI", page_icon="⚡", layout="centered")

# Custom Dark Theme CSS & 3D Atom Animation
st.markdown("""
<style>
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    .chat-header {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 700;
        color: #58a6ff;
        margin-bottom: 20px;
    }
    /* 3D Atom Animation Loader */
    .atom-loader {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100px;
    }
    .atom {
        position: relative;
        width: 60px;
        height: 60px;
        border-radius: 50%;
    }
    .nucleus {
        position: absolute;
        top: 50%;
        left: 50%;
        width: 12px;
        height: 12px;
        background: #58a6ff;
        border-radius: 50%;
        transform: translate(-50%, -50%);
        box-shadow: 0 0 10px #58a6ff;
    }
    .ring {
        position: absolute;
        width: 100%;
        height: 100%;
        border: 2px solid rgba(88, 166, 255, 0.5);
        border-radius: 50%;
        animation: spin 1.5s linear infinite;
    }
    .ring:nth-child(2) {
        transform: rotateX(60deg) rotateY(0deg);
    }
    .ring:nth-child(3) {
        transform: rotateX(60deg) rotateY(60deg);
    }
    .ring:nth-child(4) {
        transform: rotateX(60deg) rotateY(120deg);
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>
""", unsafe_allow_html=True)

# App Title
st.markdown("<h1 class='chat-header'>Pyrox AI</h1>", unsafe_allow_html=True)

# Fetch API Key from Streamlit Secrets
api_key = None
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]

# Handle Missing API Key Gracefully
if not api_key:
    st.error("API Key not found in Streamlit Secrets! Please configure GROQ_API_KEY in Secrets.")
    st.stop()

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input Box
if prompt := st.chat_input("Ask Pyrox AI..."):
    # Display User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response from Groq API via urllib REST API
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        
        # Show 3D Atom Animation while loading
        response_placeholder.markdown("""
        <div class="atom-loader">
            <div class="atom">
                <div class="nucleus"></div>
                <div class="ring"></div>
                <div class="ring"></div>
                <div class="ring"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        try:
            # Prepare API Payload
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key.strip()}",
                "Content-Type": "application/json"
            }
            
            # Formatting System & Message Context
            formatted_messages = [{"role": "system", "content": "You are Pyrox AI, a highly performant and helpful AI assistant."}]
            for msg in st.session_state.messages:
                formatted_messages.append({"role": msg["role"], "content": msg["content"]})

            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": formatted_messages,
                "temperature": 0.7
            }

            # Send HTTP Request with strict 10s Timeout
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
                reply = result["choices"][0]["message"]["content"]

            # Display Final AI Response
            response_placeholder.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

        except Exception as e:
            response_placeholder.error(f"Error connecting to Groq API: {str(e)}")
            
