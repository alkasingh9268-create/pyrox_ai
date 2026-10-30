import streamlit as st
import requests

st.title("🪞 Pyrox - The Mirror (Model Checker)")

api_key = "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"
url = "https://api.groq.com/openai/v1/models"

headers = {
    "Authorization": f"Bearer {api_key}"
}

try:
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        models = data.get("data", [])
        
        st.success(f"🎉 शीशा साफ़ है! तेरी API Key बिल्कुल सही है और इसपर कुल {len(models)} models available हैं:")
        
        for model in models:
            st.code(model.get("id"))
    else:
        st.error(f"❌ Error ({response.status_code}): {response.text}")
        
except Exception as e:
    st.error(f"Exception aagayi: {str(e)}")
