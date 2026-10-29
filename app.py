import streamlit as st
import edge_tts
import asyncio
import os

# पेज की सेटिंग
st.set_page_config(page_title="Pyrox AI Voice", page_icon="🎙️", layout="centered")

st.title("🎙️ Pyrox - Text to Speech")
st.write("यहाँ हिंदी में टेक्स्ट लिखें और बिना किसी क्रेडिट कार्ड के नेचुरल आवाज़ सुनें।")

# यूजर से टेक्स्ट इनपुट लेने के लिए बॉक्स
text_input = st.text_area(
    "जो कहलवाना है वो यहाँ लिखें:", 
    "नमस्ते! पाइरोक्स प्रोजेक्ट में आपका स्वागत है। बताइए, मैं आपकी क्या सहायता कर सकता हूँ?"
)

if st.button("आवाज़ जनरेट करें"):
    if not text_input.strip():
        st.warning("कृपया पहले कुछ टेक्स्ट टाइप करें!")
    else:
        output_file = "output.mp3"
        voice = "hi-IN-MadhurNeural"
        
        async def generate_audio():
            communicate = edge_tts.Communicate(text_input, voice)
            await communicate.save(output_file)

        with st.spinner("आवाज़ बनाई जा रही है, कृपया प्रतीक्षा करें..."):
            try:
                # Python के नए वर्जन्स में लूप एरर से बचने का सेफ तरीका
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                loop.run_until_complete(generate_audio())
                
                st.success("ऑडियो सफलतापूर्वक तैयार हो गई है!")
                st.audio(output_file, format="audio/mp3")
                
            except Exception as e:
                st.error(f"ऑडियो जनरेट करने में दिक्कत आई: {e}")
