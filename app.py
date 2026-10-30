import streamlit as st
import requests
import json

st.title("Pyrox AI - Model Test")

api_key = "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"
url = "https://api.groq.com/openai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "llama-3.3-70b-versatile",
    "messages": [
        {"role": "user", "content": "Hello! Pyrox ready hai kya?"}
    ]
}

try:
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        res_json = response.json()
        reply = res_json['choices'][0]['message']['content']
        st.success("🎉 ARRE MAZA AA GAYA! Model aur API dono pass ho gaye:")
        st.write(reply)
    else:
        st.error(f"❌ Error ({response.status_code}): {response.text}")
        
except Exception as e:
    st.error(f"Exception aagayi: {str(e)}")


