import os
import streamlit as st
from groq import Groq

st.set_page_config(page_title="Pyrox", page_icon="⚡", layout="centered")

st.title("⚡ Pyrox - मॉडल शीशा चेकर")
st.write("यह टूल चेक कर रहा है कि आपकी API Key पर Groq का कौन सा मॉडल चल रहा है।")

api_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")

if not api_key:
    st.error("❌ API Key नहीं मिली!")
else:
    st.success("✅ API Key मौजूद है।")
    try:
        client = Groq(api_key=api_key)
        
        # Groq से पूछ रहे हैं कि इस की पर कौन से मॉडल उपलब्ध हैं
        st.write("🔍 **उपलब्ध मॉडल्स की सूची की जांच की जा रही है...**")
        
        # एक टेस्ट कॉल भेजकर देखते हैं कि कौन सा मॉडल रिस्पॉन्स देता है
        test_models = ["llama-3.3-70b-versatile", "llama3-8b-8192", "mixtral-8x7b-32768", "gemma2-9b-it"]
        working_model = None
        
        for m in test_models:
            try:
                res = client.chat.completions.create(
                    model=m,
                    messages=[{"role": "user", "content": "hi"}],
                    max_tokens=5
                )
                working_model = m
                st.success(f"🎉 **मिल गया! यह मॉडल 100% काम कर रहा है:** `{m}`")
                break
            except Exception as ex:
                st.write(f"❌ मॉडल `{m}` काम नहीं कर रहा: `{str(ex)}`")
                
        if working_model:
            st.info(f"👉 अब आप अपने मुख्य ऐप में मॉडल का नाम **`{working_model}`** रख सकते हैं!")
        else:
            st.error("⚠️ आपकी इस API Key पर कोई भी मॉडल काम नहीं कर रहा। कृपया नई API Key बनाएं।")
            
    except Exception as e:
        st.error(f"❌ कनेक्शन एरर: {str(e)}")
