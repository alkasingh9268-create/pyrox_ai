import streamlit as st
import requests
import json

st.title("Pyrox AI - Qwen Master Test")

# Groq ki asli API key aur official Groq endpoint
api_key = "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"
url = "https://api.groq.com/openai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "qwen/qwen3.8-27b",
    "messages": [
        {"role": "user", "content": "Hello! Pyrox ke liye Qwen model test kar rahe hain."}
    ]
}

try:
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        res_json = response.json()
        reply = res_json['choices'][0]['message']['content']
        st.success("🎉 Maza aa gaya! Qwen model ne ekdum mast reply diya:")
        st.write(reply)
    else:
        st.error(f"❌ Error ({response.status_code}): {response.text}")
        
except Exception as e:
    st.error(f"Exception aagayi: {str(e)}")
