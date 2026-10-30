import streamlit as st
import requests
import json
import asyncio
import edge_tts
import tempfile
import os

st.markdown("<h1 style='text-align: center; color: #ff4b4b;'>🔥 Pyrox AI Assistant</h1>", unsafe_allow_html=True)
st.write("---")

# API Setup
api_key = "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"
url = "https://api.groq.com/openai/v1/chat/completions"

# Input field
user_input = st.text_input("✍️ Apna sawal yahan likh:", "Pyrox ke baare mein kuch achhi baatein batao.")

# Async function to generate Microsoft Neural Voice (MP3)
async def generate_speech(text):
    # 'hi-IN-SwaraNeural' ekdum natural Hindi/Indian English female neural voice hai
    # Tu chahe toh English ke liye 'en-US-AriaNeural' bhi use kar sakta hai
    voice = "hi-IN-SwaraNeural" 
    
    communicate = edge_tts.Communicate(text, voice)
    
    # Temporary file banakar usme audio save karenge
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        tmp_path = tmp_file.name
        
    await communicate.save(tmp_path)
    return tmp_path

if st.button("🚀 Qwen se Pucho aur Microsoft Voice mein Suno"):
    if user_input.strip() == "":
        st.warning("Pehle kuch likh toh bhai!")
    else:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "qwen/qwen3.8-27b",
            "messages": [
                {"role": "user", "content": user_input}
            ]
        }
        
        with st.spinner("🤖 Qwen soch raha hai aur Microsoft Neural Voice taiyar ho rahi hai..."):
            try:
                # 1. Qwen se text jawab mangwana
                response = requests.post(url, headers=headers, data=json.dumps(payload))
                
                if response.status_code == 200:
                    res_json = response.json()
                    reply = res_json['choices'][0]['message']['content']
                    
                    st.success("✨ Qwen ka Jawab:")
                    st.write(reply)
                    
                    # 2. Microsoft ki high-quality Neural Voice generate karna
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    audio_path = loop.run_until_complete(generate_speech(reply))
                    
                    # 3. Streamlit par audio player dikhana taaki saaf-suthri awaz sunai de
                    st.markdown("### 🎧 Microsoft Natural Audio Output:")
                    st.audio(audio_path, format="audio/mp3")
                    
                else:
                    st.error(f"❌ Error ({response.status_code}): {response.text}")
                    
            except Exception as e:
                st.error(f"Exception aagayi: {str(e)}")
