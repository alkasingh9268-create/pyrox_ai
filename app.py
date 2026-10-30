import os
import streamlit as st
from groq import Groq

st.set_page_config(page_title="Pyrox Debugger", page_icon="🐛", layout="centered")

st.title("🐛 Pyrox Debug & Test Console")
st.write("यह चेकिंग मोड है ताकि हमें शीशे की तरह साफ पता चल सके कि एरर कहाँ आ रहा है।")

# 1. API Key Check
api_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")

if not api_key:
    st.error("❌ ERROR: GROQ_API_KEY नहीं मिली! कृपया इसे Streamlit Secrets या environment variables में सेट करें।")
else:
    st.success("✅ API Key मिल गई है!")

# Initialize Groq Client
try:
    client = Groq(api_key=api_key) if api_key else None
    st.success("✅ Groq Client सफलतापूर्वक इनिशियलाइज हो गया!")
except Exception as e:
    st.error(f"❌ Groq Client बनाने में एरर आया: {str(e)}")

# 2. Session State Check
if "debug_messages" not in st.session_state:
    st.session_state.debug_messages = []

# 3. Simple Native Streamlit Input (No iframe, No page reloads)
user_input = st.chat_input("यहाँ अपना सवाल लिखकर भेजो और एरर चेक करो...")

if user_input:
    st.session_state.debug_messages.append({"role": "user", "content": user_input})
    
    if client:
        try:
            with st.spinner("Groq AI से संपर्क किया जा रहा है..."):
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": user_input}
                    ],
                    temperature=0.7,
                    max_tokens=200,
                )
                reply = completion.choices[0].message.content
                st.session_state.debug_messages.append({"role": "assistant", "content": reply})
        except Exception as e:
            # यह सबसे ज़रूरी हिस्सा है - जो भी असली एरर होगा वो यहाँ स्क्रीन पर छप जाएगा
            error_msg = f"⚠️ API CALL ERROR: {str(e)}"
            st.error(error_msg)
            st.session_state.debug_messages.append({"role": "assistant", "content": error_msg})
    else:
        st.error("❌ Client मौजूद नहीं है, इसलिए API कॉल नहीं हो सकती।")

# Display Chat History cleanly
for msg in st.session_state.debug_messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
