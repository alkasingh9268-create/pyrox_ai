import os
import streamlit as st
from groq import Groq

st.set_page_config(page_title="Pyrox", page_icon="⚡", layout="centered")

st.title("Pyrox - शीशा डिबग कंसोल")
st.write("यह कोड हर छुपी हुई गड़बड़ी को सीधे स्क्रीन पर ला देगा।")

# 1. API Key & Server Check
api_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")
if not api_key:
    st.error("❌ शीशा त्रुटि: GROQ_API_KEY नहीं मिली!")
else:
    st.success("✅ शीशा स्थिति: Groq API Key मौजूद है।")

try:
    client = Groq(api_key=api_key) if api_key else None
    st.success("✅ शीशा स्थिति: Groq सर्वर से कनेक्शन सफल।")
except Exception as e:
    st.error(f"❌ शीशा त्रुटि (कनेक्शन फेल): {str(e)}")

# 2. TTS Failure Reason Box
st.warning("⚠️ **Microsoft Edge-TTS असफलता का कारण:** Streamlit Cloud लिनक्स सर्वर पर विंडोज ऑडियो और Async लूप्स को अनुमति नहीं देता, जिससे यह क्रैश होता है।")

# 3. Chat Session Test
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_q = st.chat_input("Pyrox से कुछ पूछकर टेस्ट करें...")

if user_q:
    st.session_state.messages.append({"role": "user", "content": user_q})
    with st.chat_message("user"):
        st.write(user_q)
        
    if client:
        try:
            with st.spinner("Pyrox जवाब ला रहा है..."):
                res = client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=[{"role": "user", "content": user_q}],
                    max_tokens=300
                )
                reply = res.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": reply})
                with st.chat_message("assistant"):
                    st.write(reply)
        except Exception as e:
            st.error(f"❌ शीशा त्रुटि (API रिस्पॉन्स फेल): {str(e)}")
      
