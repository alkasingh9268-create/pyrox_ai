import streamlit as st
import requests

st.title("Pyrox AI - Whisper Voice Test")

api_key = "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"
url = "https://api.groq.com/openai/v1/audio/transcriptions"

# Ek choti si audio file upload karne ka option
uploaded_file = st.file_uploader("Apne phone ya laptop se koi choti audio file (mp3/wav) daal:", type=["mp3", "wav", "m4a", "ogg"])

if uploaded_file is not None:
    # Audio play karke sunne ke liye
    st.audio(uploaded_file)
    
    if st.button("🚀 Whisper se Text mein Badlo"):
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        files = {
            "file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
        }
        
        data = {
            "model": "whisper-large-v3-turbo"
        }
        
        with st.spinner("Whisper sun raha hai... thoda sabr kar bhai!"):
            try:
                response = requests.post(url, headers=headers, files=files, data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    st.success("🎉 Maza aa gaya! Audio se text ban gaya:")
                    st.write(result.get("text"))
                else:
                    st.error(f"❌ Error ({response.status_code}): {response.text}")
                    
            except Exception as e:
                st.error(f"Exception aagayi: {str(e)}")
