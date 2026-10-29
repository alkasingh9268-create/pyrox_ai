import asyncio
import edge_tts
import os

# हिंदी में जो भी कहलवाना है वो यहाँ लिख दे
TEXT = "नमस्ते! पाइरोक्स प्रोजेक्ट में आपका स्वागत है। बताइए, मैं आपकी क्या सहायता कर सकता हूँ?"

# Microsoft की सबसे बेहतरीन और नेचुरल हिंदी आवाज़ (Madhur ya Swara)
VOICE = "hi-IN-MadhurNeural" 
OUTPUT_FILE = "output.mp3"

async def generate_audio():
    communicate = edge_tts.Communicate(TEXT, VOICE)
    await communicate.save(OUTPUT_FILE)
    print(f"आवाज़ सफलतापूपर्वक सेव हो गई है: {OUTPUT_FILE}")

if __name__ == "__main__":
    # कोड को चलाने के लिए
    asyncio.run(generate_audio())
