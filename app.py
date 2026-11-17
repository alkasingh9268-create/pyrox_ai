import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from groq import Groq

app = FastAPI()

# अपनी Groq API की यहाँ कुंजी (Key) डालें या एनवायरनमेंट वेरिएबल सेट करें
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "YOUR_GROQ_API_KEY_HERE")
client = Groq(api_key=GROQ_API_KEY)

class ChatRequest(BaseModel):
    message: str

@app.get("/", response_class=HTMLResponse)
async def serve_home():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>index.html not found</h1>"

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        # सिस्टम प्रॉम्प्ट ताकि एआई अजीब पैटर्न में जवाब न दे और एकदम प्राकृतिक रूप से बात करे
        system_prompt = (
            "You are Pyrox, an intelligent, helpful, and friendly AI assistant. "
            "Always reply directly, naturally, and clearly in conversational language (Hindi or English matching the user). "
            "Never use robotic formatting, strange markdown artifacts, or repetitive patterns. "
            "Keep explanations concise, accurate, and structured well."
        )

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # या आपका पसंदीदा Groq मॉडल
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.message}
            ],
            temperature=0.7,
            max_tokens=1024,
        )

        reply_text = completion.choices[0].message.content.strip()
        
        return {"reply": reply_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str.error(e) if hasattr(e, 'error') else str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
  
