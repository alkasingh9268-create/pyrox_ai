import streamlit as st
from groq import Groq

st.set_page_config(page_title="Model Checker", layout="centered")

st.title("🔍 Groq Model Inspector")

# Check API key from secrets
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    st.error("Streamlit Secrets में 'GROQ_API_KEY' नहीं मिली!")
    st.stop()

# Initialize Groq client
client = Groq(api_key=api_key)

st.subheader("📋 आपकी API Key पर उपलब्ध सभी मॉडल्स की सूची:")

try:
    # Fetching exact models allowed for this specific key
    response = client.models.list()
    
    if response and response.data:
        model_names = [m.id for m in response.data]
        
        # Display each model cleanly on the screen
        for idx, m_name in enumerate(model_names, 1):
            st.markdown(f"**{idx}.** `{m_name}`")
            
        st.success(f"कुल {len(model_names)} मॉडल मिले हैं जो आपकी चाबी पर काम कर सकते हैं!")
    else:
        st.warning("कोई मॉडल नहीं मिला।")

except Exception as e:
    st.error(f"कनेक्शन या ऑथेंटिकेशन में दिक्कत है: {e}")
