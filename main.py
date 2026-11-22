import asyncio
import base64
import datetime
import io
import os
import re
from typing import Optional
import urllib.parse
import zipfile
import xml.etree.ElementTree as ET

import edge_tts
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests

app = FastAPI(title="Pyrox AI Studio")

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
SERP_API_KEY = os.environ.get("SERPAPI_API_KEY", "").strip()

MAX_CHAT_CHARS = 8000
CACHED_TEXT_MODEL: Optional[str] = None
VISION_MODEL_ID = "qwen/qwen3.8-27b"


class ChatRequest(BaseModel):
    message: str
    voice: str = "hi-IN-MadhurNeural"
    user_name: Optional[str] = None
    theme_label: str = "Pyrox"
    model_mode: str = "Pyrox Only"
    enable_tts: bool = False
    image_data_url: Optional[str] = None
    file_name: Optional[str] = None
    file_data_url: Optional[str] = None
    regenerate: bool = False


class FeedbackRequest(BaseModel):
    reason: str
    details: Optional[str] = ""
    response_snippet: Optional[str] = ""


class ListenRequest(BaseModel):
    text: str
    voice: str = "hi-IN-MadhurNeural"


def resolve_groq_text_model() -> str:
    global CACHED_TEXT_MODEL
    if CACHED_TEXT_MODEL:
        return CACHED_TEXT_MODEL

    preferred_models = [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
    ]
    if not GROQ_API_KEY:
        return preferred_models[0]

    try:
        res = requests.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            timeout=5,
        )
        if res.status_code == 200:
            available = {
                m.get("id", "")
                for m in res.json().get("data", [])
                if m.get("id")
            }
            for pref in preferred_models:
                if pref in available:
                    CACHED_TEXT_MODEL = pref
                    return pref
            filtered = [
                m_id
                for m_id in available
                if "guard" not in m_id.lower() and "whisper" not in m_id.lower()
            ]
            if filtered:
                CACHED_TEXT_MODEL = filtered[0]
                return filtered[0]
    except Exception:
        pass

    CACHED_TEXT_MODEL = preferred_models[0]
    return preferred_models[0]


def get_special_day_note(dt: datetime.datetime) -> str:
    md = (dt.month, dt.day)
    fixed_days = {
        (1, 1): "New Year's Day",
        (1, 14): "Makar Sankranti / Pongal period",
        (1, 26): "Republic Day (India)",
        (8, 15): "Independence Day (India)",
        (10, 2): "Gandhi Jayanti",
        (12, 25): "Christmas",
    }
    if md in fixed_days:
        return f"Special Day Note: Today is {fixed_days[md]}."
    return "Special Day Note: Check live search if asking about a lunar/movable festival or today's exact special observance."


def should_search_web(message: str) -> bool:
    q = message.lower().strip()
    if len(q) <= 3:
        return False
    triggers = [
        "aaj",
        "kal",
        "today",
        "tomorrow",
        "news",
        "latest",
        "festival",
        "tyohar",
        "holiday",
        "weather",
        "price",
        "rate",
        "score",
        "2025",
        "2026",
        "2027",
        "current",
        "kab hai",
        "kya chal raha",
        "trend",
        "update",
    ]
    return any(t in q for t in triggers)


def search_live_context(query: str) -> str:
    now = datetime.datetime.now()
    today_str = now.strftime("%A, %d %B %Y")
    special_note = get_special_day_note(now)
    base_info = f"Current Date & Time: {today_str} (India). {special_note}"

    if SERP_API_KEY:
        try:
            encoded = requests.utils.quote(query)
            url = (
                f"https://serpapi.com/search.json?q={encoded}"
                f"&api_key={SERP_API_KEY}&hl=en&gl=in"
            )
            res = requests.get(url, timeout=7)
            if res.status_code == 200:
                data = res.json()
                snippets = [
                    item.get("snippet", "")
                    for item in data.get("organic_results", [])[:4]
                    if item.get("snippet")
                ]
                if snippets:
                    return f"{base_info}\nLive Web Search Results: {' | '.join(snippets)}"
        except Exception:
            pass

    try:
        ddg_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        res = requests.get(
            ddg_url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=6,
        )
        if res.status_code == 200:
            raw_snippets = re.findall(
                r'class="result__snippet"[^>]*>(.*?)</a>', res.text, flags=re.S
            )
            cleaned_snips = []
            for s in raw_snippets[:3]:
                txt = re.sub(r"<[^>]+>", " ", s)
                txt = re.sub(r"\s+", " ", txt).strip()
                if txt:
                    cleaned_snips.append(txt)
            if cleaned_snips:
                return f"{base_info}\nLive Web Search Results: {' | '.join(cleaned_snips)}"
    except Exception:
        pass

    return base_info


def extract_text_from_data_url(
    file_name: Optional[str], data_url: Optional[str]
) -> tuple[str, Optional[str]]:
    """
    Returns (extracted_text, image_data_url_if_image).
    If the attached file is an image, returns ("", data_url) so vision model reads it directly.
    """
    if not data_url or "," not in data_url:
        return "", None

    header, b64_part = data_url.split(",", 1)
    header_lower = header.lower()
    lower_name = (file_name or "").lower()

    if "image/" in header_lower or lower_name.endswith(
        (".png", ".jpg", ".jpeg", ".webp", ".gif")
    ):
        normalized_url = (
            data_url
            if data_url.startswith("data:image/")
            else f"data:image/jpeg;base64,{b64_part}"
        )
        return "", normalized_url

    try:
        raw_bytes = base64.b64decode(b64_part)

        if lower_name.endswith(".docx"):
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
                xml_bytes = zf.read("word/document.xml")
                root = ET.fromstring(xml_bytes)
                texts = [elem.text for elem in root.iter() if elem.text]
                return " ".join(texts)[:4500].strip(), None

        if lower_name.endswith(".pdf"):
            try:
                import pypdf

                reader = pypdf.PdfReader(io.BytesIO(raw_bytes))
                pages_txt = []
                for page in reader.pages[:15]:
                    t = page.extract_text() or ""
                    if t.strip():
                        pages_txt.append(t.strip())
                joined = "\n".join(pages_txt)[:4500].strip()
                if joined:
                    return joined, None
            except Exception:
                pass
            return (
                "[PDF file attached, but PDF text parser library is not installed on server. Ask user to paste text or share a clear photo/screenshot of the page.]",
                None,
            )

        decoded = raw_bytes.decode("utf-8", errors="ignore")
        cleaned = re.sub(r"\s+", " ", decoded).strip()
        if cleaned:
            return cleaned[:4500], None
        return (
            f"[Attached file '{file_name or 'document'}' had no readable plain text.]",
            None,
        )
    except Exception:
        return f"[Could not read attached file '{file_name or 'document'}'.]", None


def looks_hindi_or_hinglish(text: str) -> bool:
    if re.search(r"[\u0900-\u097F]", text):
        return True
    hinglish_markers = {
        "kya",
        "hai",
        "hain",
        "kaise",
        "kaisa",
        "batao",
        "bata",
        "karo",
        "karna",
        "mera",
        "meri",
        "aaj",
        "kal",
        "nahi",
        "haan",
        "bhai",
        "yaar",
        "kuch",
        "kyun",
        "kab",
        "kahan",
        "bharna",
        "likha",
        "photo",
        "samjhao",
    }
    words = set(re.findall(r"[a-zA-Z']+", text.lower()))
    return len(words.intersection(hinglish_markers)) >= 1


async def generate_edge_audio(
    text: str, voice_name: str, filename: str = "static/response.mp3"
) -> bool:
    try:
        cleaned = re.sub(r"[*_`#~]+", "", text)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if not cleaned:
            return False
        communicate = edge_tts.Communicate(cleaned[:700], voice_name, rate="+10%")
        await communicate.save(filename)
        return True
    except Exception:
        return False


def is_short_greeting(message: str) -> bool:
    normalized = re.sub(r"[^a-zA-Z\s]", "", message).strip().lower()
    return normalized in {
        "hi",
        "hii",
        "hiii",
        "hey",
        "hello",
        "namaste",
        "yo",
        "sup",
    }


def detect_language_style(message: str) -> str:
    if re.search(r"[\u0900-\u097F]", message):
        return "Natural Hindi / Hinglish (easy, clear, friendly)"
    if looks_hindi_or_hinglish(message):
        return "Natural Hinglish (Roman Hindi + English words naturally, like a smart Indian study/tech helper)"
    return "Clear, practical English (or Hinglish if user mixes Hindi words)"


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    if not GROQ_API_KEY:
        return JSONResponse(
            status_code=400,
            content={"detail": "GROQ_API_KEY environment variable missing."},
        )

    user_msg = req.message.strip()
    if len(user_msg) > MAX_CHAT_CHARS:
        return JSONResponse(
            status_code=400,
            content={
                "detail": f"Message too large ({len(user_msg)} chars). Keep input under {MAX_CHAT_CHARS} characters."
            },
        )

    doc_text, file_image_url = extract_text_from_data_url(
        req.file_name, req.file_data_url
    )
    final_image_url = req.image_data_url or file_image_url

    if not user_msg and not final_image_url and not doc_text:
        return JSONResponse(
            status_code=400, content={"detail": "Message cannot be empty."}
        )

    has_vision_input = bool(final_image_url)
    model_id = VISION_MODEL_ID if has_vision_input else resolve_groq_text_model()

    try:
        used_search = should_search_web(user_msg)
        now = datetime.datetime.now()
        context_block = (
            search_live_context(user_msg)
            if used_search
            else f"Current Date: {now.strftime('%A, %d %B %Y')} (India). {get_special_day_note(now)}"
        )

        short_mode = (
            is_short_greeting(user_msg) and not has_vision_input and not doc_text
        )
        user_label = (
            req.user_name.strip()
            if req.user_name and req.user_name.strip()
            else ""
        )
        identity_line = f"User name: {user_label}." if user_label else ""
        lang_mode = detect_language_style(user_msg or "kya likha hai")
        regen_rule = (
            " Provide a fresh, clearer explanation without repeating identical wording."
            if req.regenerate
            else ""
        )

        creator_rule = (
            "IDENTITY & CREATOR RULE: You are Pyrox, created by Harshit. "
            "Whenever anyone asks who made you, who created you, or who your creator/developer is, "
            "clearly say you were created by Harshit. Never say Alibaba or any other company made you."
        )

        vision_rule = (
            "VISION & WORKSHEET RULE: When an image/photo is provided, carefully read all visible text, questions, "
            "blanks, numbers, and instructions. Tell the user clearly what is written and give accurate, step-by-step "
            "answers or what to fill in each blank. If part of the image is blurry or cut off, say exactly what is unclear."
            if has_vision_input
            else ""
        )

        core_persona = (
            "You are Pyrox, a helpful, sharp, and practical AI assistant for students and everyday users. "
            f"{creator_rule} {vision_rule} "
            "Keep explanations clear, structured, and easy to follow. Never guess or invent facts when uncertain."
        )

        if short_mode:
            system_prompt = (
                f"{core_persona} Mode: {req.model_mode}. {context_block} {identity_line} "
                f"Style: {lang_mode}. Reply in 1 crisp, natural sentence.{regen_rule}"
            )
        else:
            system_prompt = (
                f"{core_persona} Mode: {req.model_mode}. {context_block} {identity_line} "
                f"Style: {lang_mode}. Give a direct, clear answer first, then helpful breakdown.{regen_rule}"
            )

        text_parts = []
        if user_msg:
            text_parts.append(user_msg)
        elif has_vision_input:
            text_parts.append(
                "Is photo/page mein kya likha hai? Agar koi questions ya fill in the blanks hain to clearly batao ki kya bharna hai aur kyun."
            )
        elif doc_text:
            text_parts.append(
                "Is attached file ko padhkar summary aur main points/answers clearly batao."
            )

        if doc_text:
            text_parts.append(
                f"[Attached Document: {req.file_name or 'file'}]\n{doc_text}"
            )

        combined_text = "\n\n".join(text_parts)

        if has_vision_input:
            user_content = [
                {"type": "text", "text": combined_text},
                {"type": "image_url", "image_url": {"url": final_image_url}},
            ]
        else:
            user_content = combined_text

        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.65 if req.regenerate else 0.45,
            "max_tokens": 220 if short_mode else 1100,
        }

        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=35,
        )

        if res.status_code != 200 and has_vision_input:
            # Fallback to text model with clear note if vision model id is unavailable on account
            fallback_model = resolve_groq_text_model()
            fallback_payload = {
                "model": fallback_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"{combined_text}\n[Note: Image was attached by user ({req.file_name or 'photo'}), but vision model returned: {res.text[:180]}]",
                    },
                ],
                "temperature": 0.45,
                "max_tokens": 900,
            }
            res2 = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=fallback_payload,
                timeout=30,
            )
            if res2.status_code == 200:
                reply_text = res2.json()["choices"][0]["message"]["content"].strip()
                model_id = fallback_model
            else:
                return JSONResponse(
                    status_code=res.status_code,
                    content={"detail": f"Groq API error: {res.text[:250]}"},
                )
        elif res.status_code != 200:
            return JSONResponse(
                status_code=res.status_code,
                content={"detail": f"Groq API error: {res.text[:250]}"},
            )
        else:
            reply_text = res.json()["choices"][0]["message"]["content"].strip()

        audio_url = None
        if req.enable_tts:
            voice_to_use = (
                "hi-IN-MadhurNeural"
                if looks_hindi_or_hinglish(reply_text)
                else req.voice
            )
            ok = await generate_edge_audio(
                reply_text, voice_to_use, "static/response.mp3"
            )
            if ok:
                audio_url = f"/static/response.mp3?v={int(asyncio.get_event_loop().time() * 1000)}"

        return {
            "reply": reply_text,
            "audio_url": audio_url,
            "model": model_id,
            "searched_web": used_search,
        }

    except Exception as exc:
        return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.post("/api/listen")
async def listen_endpoint(req: ListenRequest):
    if not req.text.strip():
        return JSONResponse(
            status_code=400, content={"detail": "Nothing to read aloud."}
        )
    voice_to_use = (
        "hi-IN-MadhurNeural"
        if looks_hindi_or_hinglish(req.text)
        else req.voice
    )
    stamp = int(asyncio.get_event_loop().time() * 1000)
    filename = "static/listen_out.mp3"
    ok = await generate_edge_audio(req.text, voice_to_use, filename)
    if not ok:
        return JSONResponse(
            status_code=500, content={"detail": "Unable to generate voice audio."}
        )
    return {"audio_url": f"/static/listen_out.mp3?v={stamp}"}


@app.post("/api/feedback")
async def feedback_endpoint(req: FeedbackRequest):
    return {"status": "recorded", "reason": req.reason}


@app.get("/", response_class=HTMLResponse)
async def index():
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, interactive-widget=resizes-content" />
    <title>Pyrox AI</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        :root {
            --bg-main: #070709;
            --bg-surface: #111116;
            --bg-elevated: #1b1b22;
            --border-subtle: #2e2e38;
            --border-user: #6366f1;
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --text-muted: #94a3b8;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            -webkit-tap-highlight-color: transparent;
        }

        html, body {
            height: 100dvh;
            width: 100%;
            background-color: var(--bg-main);
            color: var(--text-primary);
            overflow: hidden;
            font-weight: 500;
            font-size: 16px;
            transition: background-color 0.85s cubic-bezier(0.22, 1, 0.36, 1), color 0.85s ease;
        }

        body.pre-login-white {
            background-color: #ffffff;
            color: #09090b;
        }

        .pyrox-fog-layer {
            position: fixed;
            inset: -12%;
            pointer-events: none;
            z-index: 1;
            opacity: 0.46;
            background:
                radial-gradient(circle at 22% 24%, rgba(56, 189, 248, 0.24), transparent 44%),
                radial-gradient(circle at 78% 28%, rgba(168, 85, 247, 0.22), transparent 46%),
                radial-gradient(circle at 52% 76%, rgba(236, 72, 153, 0.18), transparent 48%);
            filter: blur(28px);
            animation: pyroxFogDrift 14s ease-in-out infinite alternate;
        }

        @keyframes pyroxFogDrift {
            0% { transform: translate3d(-2%, -2%, 0) scale(1); }
            50% { transform: translate3d(2.5%, 1.5%, 0) scale(1.04); }
            100% { transform: translate3d(-1.5%, 2.5%, 0) scale(1.02); }
        }

        .splash-overlay {
            position: fixed;
            inset: 0;
            background-color: #ffffff;
            color: #09090b;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 600;
            overflow: hidden;
            transition: opacity 0.35s ease, transform 0.35s ease;
        }

        .splash-overlay.done {
            opacity: 0;
            transform: scale(1.04);
            pointer-events: none;
        }

        .splash-stage {
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 14px;
        }

        .splash-star-wrap {
            z-index: 3;
            animation: pogoStarPop 0.75s cubic-bezier(0.22, 1.45, 0.36, 1) forwards;
        }

        .splash-word-flash {
            font-size: 2.6rem;
            font-weight: 800;
            letter-spacing: 0.6px;
            color: #09090b;
            opacity: 0;
            transform: translateX(-30px) skewX(-12deg);
            animation: flashRevealPyrox 0.75s cubic-bezier(0.16, 1, 0.3, 1) 0.14s forwards;
        }

        @keyframes pogoStarPop {
            0% { transform: scale(0.15) rotate(-140deg); opacity: 0; }
            55% { transform: scale(1.25) rotate(12deg); opacity: 1; }
            80% { transform: scale(0.94) rotate(-6deg); }
            100% { transform: scale(1) rotate(0deg); opacity: 1; }
        }

        @keyframes flashRevealPyrox {
            0% { opacity: 0; transform: translateX(-32px) skewX(-16deg); }
            45% { opacity: 1; transform: translateX(4px) skewX(-6deg); }
            100% { opacity: 1; transform: translateX(0) skewX(0deg); }
        }

        .pyrox-welcome-screen,
        .onboarding-signup-screen {
            position: fixed;
            inset: 0;
            background-color: #ffffff;
            color: #09090b;
            z-index: 530;
            display: none;
            flex-direction: column;
            justify-content: space-between;
            padding: 20px 22px 26px 22px;
            overflow-y: auto;
        }

        .pyrox-welcome-screen.show,
        .onboarding-signup-screen.show {
            display: flex;
        }

        .onboarding-top-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .onboarding-cross-btn {
            width: 40px;
            height: 40px;
            border-radius: 999px;
            border: 1px solid #cbd5e1;
            background-color: #f8fafc;
            color: #09090b;
            font-size: 1.1rem;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .onboarding-body {
            max-width: 440px;
            width: 100%;
            margin: auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .onboarding-title {
            font-size: 1.72rem;
            font-weight: 800;
            color: #09090b;
            margin-bottom: 2px;
        }

        .white-label {
            font-size: 0.92rem;
            font-weight: 700;
            color: #1e293b;
        }

        .white-input {
            width: 100%;
            background-color: #f8fafc;
            border: 1px solid #94a3b8;
            color: #09090b;
            border-radius: 11px;
            padding: 12px 14px;
            font-size: 1.02rem;
            font-weight: 600;
            outline: none;
        }

        .white-primary-btn {
            width: 100%;
            padding: 13px 15px;
            border-radius: 11px;
            border: none;
            background-color: #09090b;
            color: #ffffff;
            font-size: 1.04rem;
            font-weight: 700;
            cursor: pointer;
            margin-top: 4px;
        }

        .white-google-btn {
            width: 100%;
            padding: 14px 16px;
            border-radius: 12px;
            border: 1px solid #64748b;
            background-color: #ffffff;
            color: #09090b;
            font-size: 1.06rem;
            font-weight: 800;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }

        .white-or {
            text-align: center;
            font-size: 0.88rem;
            color: #475569;
            font-weight: 700;
        }

        .app-shell {
            display: flex;
            height: 100dvh;
            width: 100%;
            position: relative;
            overflow: hidden;
            z-index: 2;
        }

        .sidebar {
            position: fixed;
            top: 0;
            left: 0;
            height: 100dvh;
            width: 0;
            background-color: var(--bg-surface);
            border-right: 1px solid transparent;
            overflow-y: auto;
            overflow-x: hidden;
            transition: width 0.24s ease, border-color 0.24s ease, padding 0.24s ease;
            z-index: 60;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .sidebar.open {
            width: 76vw;
            min-width: 248px;
            max-width: 330px;
            border-right-color: var(--border-subtle);
            padding: 16px 12px;
        }

        .sidebar-top {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .sidebar-title {
            font-size: 1.16rem;
            font-weight: 800;
            color: var(--text-primary);
            padding: 4px 8px 12px 8px;
            border-bottom: 1px solid var(--border-subtle);
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
        }

        .sidebar-brand-group {
            display: flex;
            align-items: center;
            gap: 8px;
            min-width: 0;
        }

        .nav-item {
            padding: 11px 12px;
            border-radius: 10px;
            font-size: 1.02rem;
            font-weight: 650;
            color: var(--text-primary);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .nav-item:hover {
            background-color: var(--bg-elevated);
        }

        .quota-pill {
            font-size: 0.78rem;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 999px;
            background-color: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            color: var(--text-secondary);
        }

        .model-sublist {
            display: none;
            flex-direction: column;
            gap: 4px;
            margin-left: 8px;
            padding-left: 8px;
            border-left: 1px solid var(--border-subtle);
        }

        .model-sublist.show {
            display: flex;
        }

        .model-option {
            padding: 9px 10px;
            border-radius: 8px;
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--text-secondary);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .model-option.active {
            background-color: var(--bg-elevated);
            color: var(--text-primary);
        }

        .all-history-block {
            display: flex;
            flex-direction: column;
            gap: 4px;
            margin-top: 2px;
            padding: 4px 10px 10px 10px;
        }

        .plain-history-line {
            padding: 8px 6px;
            border-radius: 8px;
            font-size: 0.94rem;
            font-weight: 550;
            color: var(--text-secondary);
            cursor: pointer;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .plain-history-line:hover {
            background-color: var(--bg-elevated);
            color: var(--text-primary);
        }

        .sidebar-footer {
            border-top: 1px solid var(--border-subtle);
            padding-top: 10px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .google-pill {
            padding: 11px 10px;
            border-radius: 10px;
            border: 1px solid var(--border-subtle);
            background-color: var(--bg-elevated);
            font-size: 0.96rem;
            font-weight: 700;
            color: var(--text-primary);
            cursor: pointer;
            text-align: center;
        }

        .main-area {
            flex: 1;
            min-width: 0;
            min-height: 0;
            height: 100dvh;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            position: relative;
        }

        .top-bar {
            height: 60px;
            padding: 0 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background-color: var(--bg-surface);
            border-bottom: 1px solid var(--border-subtle);
            flex-shrink: 0;
            z-index: 20;
        }

        .top-left {
            display: flex;
            align-items: center;
            gap: 10px;
            min-height: 36px;
            min-width: 0;
        }

        .menu-toggle-btn {
            background-color: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            color: var(--text-primary);
            width: 40px;
            height: 40px;
            border-radius: 11px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            flex-shrink: 0;
        }

        .menu-toggle-btn.hidden-burger {
            display: none;
        }

        .brand-heading {
            font-size: 1.22rem;
            font-weight: 800;
            letter-spacing: 0.2px;
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .top-right {
            display: flex;
            align-items: center;
            gap: 7px;
            position: relative;
            flex-shrink: 0;
        }

        .header-gmail-btn {
            background-color: var(--bg-elevated);
            color: var(--text-primary);
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            padding: 7px 11px;
            font-size: 0.84rem;
            font-weight: 700;
            cursor: pointer;
            max-width: 120px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .dots-btn {
            background-color: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            color: var(--text-primary);
            width: 38px;
            height: 38px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
        }

        .dots-menu {
            position: absolute;
            top: 46px;
            right: 0;
            width: 200px;
            background-color: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 6px;
            display: none;
            flex-direction: column;
            gap: 2px;
            z-index: 80;
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.55);
        }

        .dots-menu.show {
            display: flex;
        }

        .dots-item {
            padding: 11px 12px;
            border-radius: 8px;
            font-size: 0.98rem;
            font-weight: 600;
            color: var(--text-primary);
            cursor: pointer;
        }

        .dots-item:hover {
            background-color: var(--bg-elevated);
        }

        .status-strip {
            display: none;
            padding: 8px 14px;
            font-size: 0.92rem;
            font-weight: 650;
            background-color: var(--bg-surface);
            border-bottom: 1px solid var(--border-subtle);
            color: var(--text-secondary);
        }

        .status-strip.show {
            display: block;
        }

        .scroll-stage {
            flex: 1;
            min-height: 0;
            overflow-y: auto;
            padding: 18px 15px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .greeting-center {
            margin: auto;
            text-align: center;
            max-width: 560px;
            padding: 20px 10px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 14px;
        }

        .greeting-logo-row {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
        }

        .greeting-logo-title {
            font-size: 2.1rem;
            font-weight: 800;
            letter-spacing: 0.3px;
            color: var(--text-primary);
        }

        .greeting-center h1 {
            font-size: 1.56rem;
            font-weight: 750;
            color: var(--text-primary);
            line-height: 1.44;
        }

        .starter-chips-row {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 8px;
            margin-top: 4px;
        }

        .starter-chip {
            padding: 9px 13px;
            border-radius: 999px;
            border: 1px solid var(--border-subtle);
            background-color: var(--bg-surface);
            color: var(--text-primary);
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
        }

        .msg-row {
            display: flex;
            flex-direction: column;
            max-width: 92%;
            gap: 8px;
        }

        .msg-user {
            align-self: flex-end;
            background-color: var(--bg-elevated);
            color: var(--text-primary);
            border: 1px solid var(--border-user);
            border-radius: 16px 16px 4px 16px;
            padding: 12px 16px;
            font-size: 1.12rem;
            font-weight: 550;
            line-height: 1.62;
            word-break: break-word;
        }

        .msg-ai {
            align-self: flex-start;
            width: 100%;
            max-width: 100%;
            color: var(--text-primary);
            font-size: 1.14rem;
            font-weight: 500;
            line-height: 1.75;
            padding: 4px 2px;
        }

        .msg-ai p {
            margin-bottom: 10px;
        }

        .code-block-wrap {
            position: relative;
            margin: 8px 0 12px 0;
        }

        .code-copy-btn {
            position: absolute;
            top: 8px;
            right: 8px;
            padding: 5px 10px;
            border-radius: 6px;
            border: 1px solid var(--border-subtle);
            background-color: var(--bg-surface);
            color: var(--text-primary);
            font-size: 0.78rem;
            font-weight: 700;
            cursor: pointer;
        }

        .msg-ai pre {
            background-color: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            padding: 12px;
            overflow-x: auto;
            font-size: 0.96rem;
        }

        .msg-actions {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 4px;
        }

        .icon-symbol-btn {
            width: 36px;
            height: 36px;
            border-radius: 9px;
            background: transparent;
            border: none;
            color: var(--text-secondary);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
        }

        .icon-symbol-btn.liquid-filled {
            color: #ffffff;
        }

        .icon-symbol-btn.liquid-filled svg path {
            fill: rgba(255, 255, 255, 0.92);
        }

        .thinking-dots {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 2px;
        }

        .thinking-dots span {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: var(--text-secondary);
            animation: twoDotPulse 1s infinite ease-in-out;
        }

        .thinking-dots span:nth-child(2) {
            animation-delay: 0.22s;
        }

        @keyframes twoDotPulse {
            0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
            40% { transform: translateY(-6px); opacity: 1; }
        }

        .bottom-dock {
            flex-shrink: 0;
            width: 100%;
            padding: 8px 10px 8px 10px;
            background-color: var(--bg-surface);
            border-top: 1px solid var(--border-subtle);
            position: relative;
            z-index: 30;
            transform: translateY(24px);
            opacity: 0;
            transition: transform 0.55s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.45s ease;
        }

        .bottom-dock.dock-slid-up {
            transform: translateY(0);
            opacity: 1;
        }

        .attachment-chip-bar {
            display: none;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            margin-bottom: 6px;
            padding: 7px 12px;
            border-radius: 11px;
            background-color: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            font-size: 0.88rem;
            font-weight: 650;
            color: var(--text-primary);
        }

        .attachment-chip-bar.show {
            display: flex;
        }

        .plus-menu {
            position: absolute;
            bottom: 98px;
            left: 12px;
            width: 276px;
            background-color: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: 14px;
            padding: 10px;
            display: none;
            flex-direction: column;
            gap: 8px;
            z-index: 70;
            box-shadow: 0 14px 32px rgba(0, 0, 0, 0.55);
        }

        .plus-menu.show {
            display: flex;
        }

        .plus-big-btn {
            padding: 12px 13px;
            border-radius: 10px;
            background-color: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            color: var(--text-primary);
            font-size: 1rem;
            font-weight: 650;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            text-align: left;
        }

        .plus-small-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 6px;
            padding-top: 6px;
            border-top: 1px solid var(--border-subtle);
        }

        .plus-small-btn {
            padding: 9px 7px;
            border-radius: 8px;
            background-color: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            color: var(--text-primary);
            font-size: 0.86rem;
            font-weight: 650;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }

        .input-shell {
            display: flex;
            align-items: center;
            gap: 8px;
            min-height: 64px;
            background-color: var(--bg-main);
            border: 1px solid var(--border-subtle);
            border-radius: 24px;
            padding: 8px 10px;
        }

        .icon-action-btn {
            width: 44px;
            height: 44px;
            border-radius: 13px;
            border: 1px solid var(--border-subtle);
            background-color: var(--bg-elevated);
            color: var(--text-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            flex-shrink: 0;
            font-size: 1.25rem;
            font-weight: 700;
        }

        .icon-action-btn.open-minus {
            transform: rotate(90deg);
        }

        .icon-action-btn.mic-recording {
            border-color: var(--border-user);
            background-color: var(--bg-surface);
        }

        .curved-stop-square {
            width: 16px;
            height: 16px;
            border-radius: 4px;
            background-color: var(--text-primary);
            display: inline-block;
        }

        .prompt-input {
            flex: 1;
            min-width: 0;
            min-height: 44px;
            max-height: 120px;
            background: transparent;
            border: none;
            outline: none;
            color: var(--text-primary);
            font-size: 1.1rem;
            font-weight: 550;
            resize: none;
            padding: 9px 4px;
            line-height: 1.42;
        }

        .send-btn, .stop-btn {
            width: 46px;
            height: 46px;
            border-radius: 15px;
            border: none;
            background-color: var(--text-primary);
            color: var(--bg-main);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            flex-shrink: 0;
            font-size: 1.35rem;
            font-weight: 800;
        }

        .stop-btn {
            display: none;
            background-color: var(--bg-elevated);
            color: var(--text-primary);
            border: 1px solid var(--border-user);
        }

        .stop-btn.visible {
            display: flex;
        }

        .send-btn.hidden-send {
            display: none;
        }

        .ai-disclaimer {
            text-align: center;
            font-size: 0.78rem;
            color: var(--text-muted);
            margin-top: 6px;
            font-weight: 550;
        }

        .overlay-modal {
            position: fixed;
            inset: 0;
            background-color: rgba(0, 0, 0, 0.72);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 120;
            padding: 14px;
        }

        .overlay-modal.show {
            display: flex;
        }

        .overlay-modal.camera-sheet {
            align-items: flex-end;
            background-color: rgba(0, 0, 0, 0.45);
            padding: 0;
        }

        .modal-box {
            width: 100%;
            max-width: 460px;
            max-height: 90dvh;
            overflow-y: auto;
            background-color: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: 18px;
            padding: 18px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            color: var(--text-primary);
        }

        .feedback-box {
            width: 100%;
            max-width: 480px;
            min-height: 70dvh;
            max-height: 85dvh;
            overflow-y: auto;
            background-color: #18181b;
            color: #f8fafc;
            border: 1px solid #3f3f46;
            border-radius: 18px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            gap: 14px;
        }

        .feedback-reasons-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .reason-chip {
            padding: 9px 12px;
            border-radius: 10px;
            border: 1px solid #52525b;
            background-color: #27272a;
            color: #f8fafc;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
        }

        .reason-chip.active {
            background-color: #f8fafc;
            color: #09090b;
            border-color: #f8fafc;
        }

        .camera-sheet .modal-box {
            max-width: 640px;
            height: 75dvh;
            border-radius: 22px 22px 0 0;
        }

        .modal-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-weight: 750;
            font-size: 1.12rem;
        }

        .close-x {
            background: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            color: var(--text-primary);
            border-radius: 8px;
            padding: 6px 11px;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 700;
        }

        .field-label {
            font-size: 0.92rem;
            font-weight: 650;
            color: var(--text-secondary);
        }

        .field-input {
            width: 100%;
            background-color: var(--bg-main);
            border: 1px solid var(--border-subtle);
            color: var(--text-primary);
            border-radius: 10px;
            padding: 11px 12px;
            font-size: 1rem;
            font-weight: 550;
            outline: none;
        }

        .action-btn {
            background-color: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            color: var(--text-primary);
            border-radius: 10px;
            padding: 11px 13px;
            font-size: 0.98rem;
            font-weight: 650;
            cursor: pointer;
        }

        .video-frame {
            flex: 1;
            min-height: 0;
            background-color: #000000;
            border-radius: 14px;
            overflow: hidden;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        video {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .cam-status-msg {
            color: #e2e8f0;
            font-size: 0.94rem;
            padding: 14px;
            text-align: center;
        }

        .cam-bar {
            display: flex;
            align-items: center;
            justify-content: space-around;
            gap: 10px;
            padding-top: 4px;
        }

        .shutter-circle {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            border: 4px solid var(--text-primary);
            background-color: transparent;
            position: relative;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .shutter-circle::after {
            content: "";
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background-color: var(--text-primary);
        }

        .robot-check-box {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px;
            border-radius: 10px;
            background: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            font-size: 0.95rem;
            font-weight: 650;
            cursor: pointer;
        }
    </style>
</head>
<body class="pre-login-white">
<div class="pyrox-fog-layer" aria-hidden="true"></div>

<svg width="0" height="0" style="position:absolute;visibility:hidden;">
    <defs>
        <linearGradient id="pyroxOuterGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#38bdf8" />
            <stop offset="50%" stop-color="#6366f1" />
            <stop offset="100%" stop-color="#a855f7" />
        </linearGradient>
        <linearGradient id="pyroxMidGrad" x1="100%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#60a5fa" />
            <stop offset="55%" stop-color="#818cf8" />
            <stop offset="100%" stop-color="#ec4899" />
        </linearGradient>
        <linearGradient id="pyroxCoreGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#ffffff" />
            <stop offset="100%" stop-color="#bae6fd" />
        </linearGradient>
    </defs>
</svg>

<div class="splash-overlay" id="splashOverlay">
    <div class="splash-stage">
        <div class="splash-star-wrap">
            <svg width="52" height="52" viewBox="0 0 100 100" fill="none">
                <path d="M50 4 C55 34, 66 45, 96 50 C66 55, 55 66, 50 96 C45 66, 34 55, 4 50 C34 45, 45 34, 50 4 Z" fill="url(#pyroxOuterGrad)" />
                <path d="M50 20 C53 40, 60 47, 80 50 C60 53, 53 60, 50 80 C47 60, 40 53, 20 50 C40 47, 47 40, 50 20 Z" fill="url(#pyroxMidGrad)" />
                <path d="M50 34 C51.5 44, 56 48.5, 66 50 C56 51.5, 51.5 56, 50 66 C48.5 56, 44 51.5, 34 50 C44 48.5, 48.5 44, 50 34 Z" fill="url(#pyroxCoreGrad)" />
            </svg>
        </div>
        <div class="splash-word-flash" id="splashWord">Pyrox</div>
    </div>
</div>

<div class="pyrox-welcome-screen" id="pyroxWelcomeScreen">
    <div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:14px;padding:16px;">
        <svg width="56" height="56" viewBox="0 0 100 100" fill="none">
            <path d="M50 4 C55 34, 66 45, 96 50 C66 55, 55 66, 50 96 C45 66, 34 55, 4 50 C34 45, 45 34, 50 4 Z" fill="url(#pyroxOuterGrad)" />
            <path d="M50 20 C53 40, 60 47, 80 50 C60 53, 53 60, 50 80 C47 60, 40 53, 20 50 C40 47, 47 40, 50 20 Z" fill="url(#pyroxMidGrad)" />
            <path d="M50 34 C51.5 44, 56 48.5, 66 50 C56 51.5, 51.5 56, 50 66 C48.5 56, 44 51.5, 34 50 C44 48.5, 48.5 44, 50 34 Z" fill="url(#pyroxCoreGrad)" />
        </svg>
        <div style="font-size:1.85rem;font-weight:800;letter-spacing:0.2px;color:#09090b;">Welcome to Pyrox</div>
        <p style="max-width:340px;font-size:0.98rem;color:#475569;line-height:1.5;">
            Photo khinch kar padho, fill-in-the-blanks samjho, ya file aur chat se turant madad lo.
        </p>
    </div>

    <div style="width:100%;max-width:420px;margin:0 auto;display:flex;flex-direction:column;gap:10px;padding:12px 12px 20px 12px;">
        <div style="font-size:0.74rem;text-align:center;color:#64748b;line-height:1.45;margin-bottom:4px;">
            Pyrox can make mistakes, so check anything important. By continuing, you agree to Pyrox terms and privacy policy.
        </div>
        <button type="button" class="action-btn" style="background-color:#09090b;color:#ffffff;font-weight:800;padding:13px 16px;border-radius:999px;" onclick="openGoogleAccountChooser()">
            G &nbsp; Continue with Google
        </button>
        <button type="button" class="action-btn" style="background-color:#f8fafc;color:#09090b;font-weight:700;padding:13px 16px;border-radius:999px;" onclick="openSignUpFormScreen()">
            Log in or sign up
        </button>
        <button type="button" style="background:none;border:none;color:#09090b;font-size:0.96rem;font-weight:700;padding:8px;cursor:pointer;" onclick="skipWelcomeToDarkApp()">
            Skip
        </button>
    </div>
</div>

<div class="onboarding-signup-screen" id="onboardingSignupScreen">
    <div class="onboarding-top-row">
        <div style="display:flex;align-items:center;gap:8px;">
            <svg width="28" height="28" viewBox="0 0 100 100" fill="none">
                <path d="M50 4 C55 34, 66 45, 96 50 C66 55, 55 66, 50 96 C45 66, 34 55, 4 50 C34 45, 45 34, 50 4 Z" fill="url(#pyroxOuterGrad)" />
                <path d="M50 20 C53 40, 60 47, 80 50 C60 53, 53 60, 50 80 C47 60, 40 53, 20 50 C40 47, 47 40, 50 20 Z" fill="url(#pyroxMidGrad)" />
                <path d="M50 34 C51.5 44, 56 48.5, 66 50 C56 51.5, 51.5 56, 50 66 C48.5 56, 44 51.5, 34 50 C44 48.5, 48.5 44, 50 34 Z" fill="url(#pyroxCoreGrad)" />
            </svg>
            <span style="font-weight:800;font-size:1.12rem;color:#09090b;">Pyrox</span>
        </div>
        <button type="button" class="onboarding-cross-btn" onclick="skipWelcomeToDarkApp()" aria-label="Skip sign up">✕</button>
    </div>

    <div class="onboarding-body">
        <div class="onboarding-title">Sign up to Pyrox</div>

        <label class="white-label" for="obEmail">Email</label>
        <input type="email" class="white-input" id="obEmail" placeholder="name@gmail.com" />

        <label class="white-label" for="obName">Name</label>
        <input type="text" class="white-input" id="obName" placeholder="Your name" />

        <label style="display:flex;align-items:center;gap:8px;font-size:0.9rem;font-weight:650;color:#1e293b;margin-top:2px;">
            <input type="checkbox" id="obRobotCheck" />
            <span>I am not a robot (Human verification)</span>
        </label>

        <button type="button" class="white-primary-btn" onclick="completeOnboardingForm()">Continue</button>

        <div class="white-or">or</div>

        <button type="button" class="white-google-btn" onclick="openGoogleAccountChooser()">
            <span>G</span>
            <span>Continue with Google</span>
        </button>
    </div>

    <div style="text-align:center;font-size:0.82rem;color:#475569;">
        Tap ✕ to enter Pyrox studio
    </div>
</div>

<div class="overlay-modal" id="googleChooserModal" onclick="closeModal('googleChooserModal')">
    <div class="modal-box" style="background-color:#ffffff;color:#09090b;border-radius:20px;padding:22px 18px;max-width:390px;" onclick="event.stopPropagation()">
        <div style="display:flex;flex-direction:column;align-items:center;text-align:center;gap:6px;">
            <svg width="34" height="34" viewBox="0 0 100 100" fill="none">
                <path d="M50 4 C55 34, 66 45, 96 50 C66 55, 55 66, 50 96 C45 66, 34 55, 4 50 C34 45, 45 34, 50 4 Z" fill="url(#pyroxOuterGrad)" />
                <path d="M50 20 C53 40, 60 47, 80 50 C60 53, 53 60, 50 80 C47 60, 40 53, 20 50 C40 47, 47 40, 50 20 Z" fill="url(#pyroxMidGrad)" />
                <path d="M50 34 C51.5 44, 56 48.5, 66 50 C56 51.5, 51.5 56, 50 66 C48.5 56, 44 51.5, 34 50 C44 48.5, 48.5 44, 50 34 Z" fill="url(#pyroxCoreGrad)" />
            </svg>
            <div style="font-size:1.35rem;font-weight:700;color:#0f172a;">Choose an account</div>
            <div style="font-size:0.9rem;color:#475569;">to continue to Pyrox</div>
        </div>

        <label style="display:flex;align-items:center;gap:8px;font-size:0.88rem;font-weight:700;color:#0f172a;padding:8px 6px;background:#f1f5f9;border-radius:10px;margin-top:6px;">
            <input type="checkbox" id="chooserRobotCheck" checked />
            <span>I am not a robot</span>
        </label>

        <div style="display:flex;flex-direction:column;margin-top:6px;">
            <button type="button" onclick="selectChooserAccount('Harshit', 'harshit@pyrox.app')" style="display:flex;align-items:center;gap:12px;padding:12px 8px;background:none;border:none;border-bottom:1px solid #e2e8f0;text-align:left;cursor:pointer;color:#0f172a;">
                <span style="width:36px;height:36px;border-radius:999px;background:#2563eb;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;">H</span>
                <span style="display:flex;flex-direction:column;">
                    <strong style="font-size:0.95rem;">Harshit</strong>
                    <span style="font-size:0.82rem;color:#475569;">harshit@pyrox.app</span>
                </span>
            </button>

            <button type="button" onclick="closeModal('googleChooserModal'); openModal('googleModal');" style="display:flex;align-items:center;gap:12px;padding:13px 8px;background:none;border:none;text-align:left;cursor:pointer;color:#0f172a;font-weight:650;font-size:0.92rem;">
                <span>+ Add another account</span>
            </button>
        </div>
    </div>
</div>

<div class="app-shell" id="appShell">
    <aside class="sidebar" id="sidebar" onclick="event.stopPropagation()">
        <div class="sidebar-top">
            <div class="sidebar-title">
                <div class="sidebar-brand-group">
                    <svg width="24" height="24" viewBox="0 0 100 100" fill="none">
                        <path d="M50 4 C55 34, 66 45, 96 50 C66 55, 55 66, 50 96 C45 66, 34 55, 4 50 C34 45, 45 34, 50 4 Z" fill="url(#pyroxOuterGrad)" />
                        <path d="M50 20 C53 40, 60 47, 80 50 C60 53, 53 60, 50 80 C47 60, 40 53, 20 50 C40 47, 47 40, 50 20 Z" fill="url(#pyroxMidGrad)" />
                        <path d="M50 34 C51.5 44, 56 48.5, 66 50 C56 51.5, 51.5 56, 50 66 C48.5 56, 44 51.5, 34 50 C44 48.5, 48.5 44, 50 34 Z" fill="url(#pyroxCoreGrad)" />
                    </svg>
                    <span id="sidebarThemeTitle">Pyrox</span>
                </div>
                <span style="font-size:0.92rem;color:var(--text-secondary);cursor:pointer;" onclick="closeSidebar()">✕</span>
            </div>

            <div class="nav-item" onclick="newChat(); closeSidebar();">+ New Chat</div>

            <div class="nav-item" onclick="openCamera(); closeSidebar();">
                <span>Camera Vision</span>
                <span class="quota-pill">Read</span>
            </div>

            <div class="nav-item" onclick="triggerFilePicker(); closeSidebar();">
                <span>File Vision</span>
                <span class="quota-pill">Docs</span>
            </div>

            <div class="nav-item" onclick="toggleModelSublist()">Pyrox Only ▾</div>
            <div class="model-sublist" id="modelSublist">
                <div class="model-option active" id="optPyroxOnly" onclick="selectModelMode('Pyrox Only')">
                    <span>Pyrox Only</span>
                    <span>Active</span>
                </div>
            </div>

            <div class="nav-item" onclick="toggleAllHistorySection()">All ▾</div>
            <div class="all-history-block" id="libraryFolders"></div>
        </div>

        <div class="sidebar-footer">
            <div class="google-pill" id="googleAccountBtn" onclick="openModal('googleModal')">
                Gmail with Pyrox
            </div>
            <div class="nav-item" onclick="openModal('settingsModal')">Settings</div>
        </div>
    </aside>

    <main class="main-area" id="mainArea">
        <header class="top-bar">
            <div class="top-left">
                <button type="button" class="menu-toggle-btn" id="burgerBtn" onclick="openSidebar(event)" aria-label="Open menu">
                    <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
                        <line x1="3" y1="6" x2="21" y2="6"></line>
                        <line x1="3" y1="12" x2="21" y2="12"></line>
                        <line x1="3" y1="18" x2="21" y2="18"></line>
                    </svg>
                </button>
                <span class="brand-heading" id="headerBrandTitle">Pyrox</span>
            </div>

            <div class="top-right" onclick="event.stopPropagation()">
                <button type="button" class="header-gmail-btn" id="headerGmailBtn" onclick="openModal('googleModal')">
                    Gmail
                </button>
                <button type="button" class="dots-btn" id="dotsBtn" onclick="toggleDotsMenu(event)" aria-label="More options">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                        <circle cx="12" cy="5" r="2"></circle>
                        <circle cx="12" cy="12" r="2"></circle>
                        <circle cx="12" cy="19" r="2"></circle>
                    </svg>
                </button>

                <div class="dots-menu" id="dotsMenu">
                    <div class="dots-item" onclick="newChat(); closeDotsMenu();">Clear Chat</div>
                    <div class="dots-item" onclick="exportChat(); closeDotsMenu();">Export Chat</div>
                    <div class="dots-item" onclick="openModal('libraryModal'); closeDotsMenu();">All Chats</div>
                    <div class="dots-item" onclick="openModal('settingsModal'); closeDotsMenu();">Settings</div>
                </div>
            </div>
        </header>

        <div class="status-strip" id="statusStrip"></div>

        <section class="scroll-stage" id="scrollStage">
            <div class="greeting-center" id="greetingBox">
                <div class="greeting-logo-row">
                    <svg width="46" height="46" viewBox="0 0 100 100" fill="none">
                        <path d="M50 4 C55 34, 66 45, 96 50 C66 55, 55 66, 50 96 C45 66, 34 55, 4 50 C34 45, 45 34, 50 4 Z" fill="url(#pyroxOuterGrad)" />
                        <path d="M50 20 C53 40, 60 47, 80 50 C60 53, 53 60, 50 80 C47 60, 40 53, 20 50 C40 47, 47 40, 50 20 Z" fill="url(#pyroxMidGrad)" />
                        <path d="M50 34 C51.5 44, 56 48.5, 66 50 C56 51.5, 51.5 56, 50 66 C48.5 56, 44 51.5, 34 50 C44 48.5, 48.5 44, 50 34 Z" fill="url(#pyroxCoreGrad)" />
                    </svg>
                    <span class="greeting-logo-title" id="greetingBrandName">Pyrox</span>
                </div>
                <h1 id="greetingText">Swagatam! Kya padhna ya samajhna hai aaj?</h1>
                <div class="starter-chips-row">
                    <button type="button" class="starter-chip" onclick="useStarterPrompt('Photo ya page mein kya likha hai aur fill in the blanks mein kya bharna hai?')">Read photo / blanks</button>
                    <button type="button" class="starter-chip" onclick="useStarterPrompt('Kisi topic ko Hinglish mein aasan tarike se samjhao')">Explain simply</button>
                    <button type="button" class="starter-chip" onclick="useStarterPrompt('Help me write and debug Python code')">Coding help</button>
                </div>
            </div>
        </section>

        <footer class="bottom-dock dock-slid-up" id="bottomDock" onclick="event.stopPropagation()">
            <div class="attachment-chip-bar" id="attachmentChipBar">
                <span id="attachmentChipLabel">Attached file</span>
                <button type="button" class="close-x" onclick="clearPendingAttachment()">✕</button>
            </div>

            <div class="plus-menu" id="plusMenu">
                <button type="button" class="plus-big-btn" onclick="triggerFilePicker()">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                    </svg>
                    <span>File Vision</span>
                </button>
                <button type="button" class="plus-big-btn" onclick="openCamera()">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                        <circle cx="12" cy="13" r="4"></circle>
                    </svg>
                    <span>Camera Vision</span>
                </button>
                <div class="plus-small-grid">
                    <button type="button" class="plus-small-btn" onclick="promptCanvasMode()">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 20h9"></path>
                            <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
                        </svg>
                        <span>Notes / Canvas</span>
                    </button>
                </div>
            </div>

            <input type="file" id="filePicker" accept="image/*,.pdf,.txt,.doc,.docx,.py,.js,.html,.css,.json,.md" style="display:none;" onchange="handleFileSelected(event)" />

            <div class="input-shell">
                <button type="button" class="icon-action-btn" id="plusBtn" onclick="togglePlusMenu(event)" title="More actions">+</button>

                <button type="button" class="icon-action-btn" id="micBtn" onclick="toggleDictation(event)" title="Voice input">
                    <svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                        <line x1="12" y1="19" x2="12" y2="23"></line>
                    </svg>
                </button>

                <textarea
                    id="promptInput"
                    class="prompt-input"
                    rows="1"
                    placeholder="Ask Pyrox..."
                    autocomplete="off"
                    autocorrect="off"
                    autocapitalize="sentences"
                    spellcheck="false"
                    onfocus="handleInputFocus()"
                    onkeydown="handleInputKeydown(event)"
                ></textarea>

                <button type="button" class="stop-btn" id="stopGenBtn" onclick="stopGeneration()">■</button>
                <button type="button" class="send-btn" id="sendBtn" onclick="sendMessage()">↑</button>
            </div>
            <div class="ai-disclaimer">Pyrox is AI and can make mistakes.</div>
        </footer>
    </main>
</div>

<div class="overlay-modal" id="googleModal" onclick="closeModal('googleModal')">
    <div class="modal-box" onclick="event.stopPropagation()">
        <div class="modal-head">
            <span>Gmail with Pyrox</span>
            <button type="button" class="close-x" onclick="closeModal('googleModal')">✕</button>
        </div>

        <div id="connectedAccountCard" style="padding:10px 12px;border-radius:10px;background:var(--bg-elevated);border:1px solid var(--border-subtle);font-size:0.9rem;color:var(--text-secondary);">
            Not connected yet
        </div>

        <button type="button" class="white-google-btn" style="background-color:var(--bg-elevated);color:var(--text-primary);border-color:var(--border-user);" onclick="openGoogleAccountChooser()">
            <span style="font-weight:900;">G</span>
            <span>Choose Google Account</span>
        </button>

        <div class="white-or">or</div>

        <label class="field-label" for="googleEmailInput">Email</label>
        <input type="email" class="field-input" id="googleEmailInput" placeholder="you@gmail.com" />

        <label class="field-label" for="googleNameInput">Name</label>
        <input type="text" class="field-input" id="googleNameInput" placeholder="Your name" />

        <label class="robot-check-box">
            <input type="checkbox" id="gmailRobotCheck" />
            <span>I am not a robot (Verify human access)</span>
        </label>

        <button type="button" class="action-btn" onclick="saveAccountForm()">Save & Connect</button>

        <button type="button" class="action-btn" style="border-color:#ef4444;color:#fca5a5;" onclick="openLogoutConfirmModal()">
            Log Out / Switch Account
        </button>
        <div id="accountStatusMsg" style="font-size:0.86rem;color:var(--text-secondary);"></div>
    </div>
</div>

<div class="overlay-modal" id="logoutConfirmModal" onclick="closeModal('logoutConfirmModal')">
    <div class="modal-box" style="max-width:390px;" onclick="event.stopPropagation()">
        <div class="modal-head">
            <span>Confirm Log Out</span>
            <button type="button" class="close-x" onclick="closeModal('logoutConfirmModal')">✕</button>
        </div>
        <p style="font-size:0.95rem;color:var(--text-secondary);line-height:1.5;">
            Kya aap sach mein apne connected Gmail account se log out karna chahte hain?
        </p>
        <label class="robot-check-box">
            <input type="checkbox" id="logoutRobotCheck" />
            <span>I am not a robot</span>
        </label>
        <div id="logoutErrorMsg" style="font-size:0.85rem;color:#fca5a5;"></div>
        <div style="display:flex;gap:10px;justify-content:flex-end;">
            <button type="button" class="action-btn" onclick="closeModal('logoutConfirmModal')">Cancel</button>
            <button type="button" class="action-btn" style="background:#dc2626;border-color:#f87171;color:#fff;" onclick="confirmLogoutAccount()">Yes, Log Out</button>
        </div>
    </div>
</div>

<div class="overlay-modal" id="settingsModal" onclick="closeModal('settingsModal')">
    <div class="modal-box" onclick="event.stopPropagation()">
        <div class="modal-head">
            <span>Settings</span>
            <button type="button" class="close-x" onclick="closeModal('settingsModal')">Close</button>
        </div>
        <label class="field-label" for="customThemeInput">Custom Theme Name</label>
        <input type="text" class="field-input" id="customThemeInput" placeholder="e.g. Pyrox, Studio Dark" />
        <button type="button" class="action-btn" onclick="saveThemeName()">Save Theme Name</button>
        <button type="button" class="action-btn" id="ttsToggleBtn" onclick="toggleTtsPreference()">Auto Voice Reply: Off</button>
        <button type="button" class="action-btn" onclick="clearSavedFolders()">Clear Chat History</button>
    </div>
</div>

<div class="overlay-modal" id="libraryModal" onclick="closeModal('libraryModal')">
    <div class="modal-box" onclick="event.stopPropagation()">
        <div class="modal-head">
            <span>All Chats</span>
            <button type="button" class="close-x" onclick="closeModal('libraryModal')">Close</button>
        </div>
        <div id="libraryModalBody" style="display:flex;flex-direction:column;gap:8px;font-size:0.98rem;color:var(--text-secondary);">
            No chats yet.
        </div>
    </div>
</div>

<div class="overlay-modal" id="feedbackModal" onclick="closeModal('feedbackModal')">
    <div class="feedback-box" onclick="event.stopPropagation()">
        <div style="display:flex;flex-direction:column;gap:14px;">
            <div class="modal-head">
                <span>Feedback</span>
                <button type="button" class="close-x" onclick="closeModal('feedbackModal')">✕</button>
            </div>
            <p style="font-size:0.96rem;color:#e2e8f0;">
                Select what went wrong with this response:
            </p>
            <div class="feedback-reasons-grid" id="feedbackReasonsGrid">
                <button type="button" class="reason-chip" onclick="toggleFeedbackReason(this)">Unsafe</button>
                <button type="button" class="reason-chip" onclick="toggleFeedbackReason(this)">Not factually correct</button>
                <button type="button" class="reason-chip" onclick="toggleFeedbackReason(this)">Don't follow instruction</button>
                <button type="button" class="reason-chip" onclick="toggleFeedbackReason(this)">Personalization issue</button>
                <button type="button" class="reason-chip" onclick="toggleFeedbackReason(this)">Wrong language</button>
                <button type="button" class="reason-chip" onclick="toggleFeedbackReason(this)">Poorly formatted</button>
                <button type="button" class="reason-chip" onclick="toggleFeedbackReason(this)">Generally bland</button>
                <button type="button" class="reason-chip" onclick="toggleFeedbackReason(this)">Too harmful action</button>
            </div>
            <textarea id="feedbackCustomNote" class="field-input" rows="3" placeholder="Additional note (optional)..." style="background-color:#27272a;color:#f8fafc;border-color:#52525b;"></textarea>
        </div>

        <button type="button" class="action-btn" style="background-color:#f8fafc;color:#09090b;font-weight:800;font-size:1rem;" onclick="submitBadFeedback()">
            Submit
        </button>
    </div>
</div>

<div class="overlay-modal camera-sheet" id="cameraModal" onclick="closeCamera()">
    <div class="modal-box" onclick="event.stopPropagation()">
        <div class="modal-head">
            <span>Camera Vision</span>
            <button type="button" class="close-x" onclick="closeCamera()">Close</button>
        </div>
        <div class="video-frame" id="cameraFrame">
            <video id="cameraVideo" autoplay playsinline muted></video>
            <div class="cam-status-msg" id="camStatusMsg"></div>
            <canvas id="cameraCanvas" style="display:none;"></canvas>
        </div>
        <div class="cam-bar">
            <button type="button" class="action-btn" onclick="flipCamera()">Flip</button>
            <button type="button" class="shutter-circle" onclick="captureCameraPhoto()" aria-label="Take photo"></button>
            <button type="button" class="action-btn" id="flashToggleBtn" onclick="toggleFlash()">Flash: Off</button>
        </div>
    </div>
</div>

<script>
    const NORMAL_DAILY_LIMIT = 40;
    const CODING_DAILY_LIMIT = 30;
    const WARNING_REMAINING_THRESHOLD = 5;
    const MAX_INPUT_CHARS = 6000;

    let chatStarted = false;
    let activeAbortController = null;
    let isRequestInFlight = false;
    let selectedModelMode = "Pyrox Only";
    let currentFacingMode = "environment";
    let cameraStream = null;
    let flashEnabled = false;
    let ttsEnabled = false;
    let pendingAttachmentDataUrl = null;
    let pendingFileDataUrl = null;
    let pendingAttachmentName = "";
    let activeFolderId = null;
    let latestAudioPlayer = null;
    let feedbackTargetSnippet = "";
    let activeDislikeBtn = null;

    let recognition = null;
    let isDictating = false;

    const MIC_SVG = `
        <svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
            <line x1="12" y1="19" x2="12" y2="23"></line>
        </svg>
    `;

    function isUserSignedUp() {
        return Boolean(localStorage.getItem("pyrox_signed_up"));
    }

    function syncHeaderAccountUI() {
        const gBtn = document.getElementById("headerGmailBtn");
        const sideBtn = document.getElementById("googleAccountBtn");
        const card = document.getElementById("connectedAccountCard");
        const name = (localStorage.getItem("pyrox_user_name") || "").trim();
        const email = (localStorage.getItem("pyrox_user_email") || "").trim();

        if (gBtn) {
            gBtn.textContent = name ? `Gmail: ${name.split(" ")[0]}` : "Gmail";
        }
        if (sideBtn) {
            sideBtn.textContent = name ? `Gmail: ${name}` : "Gmail with Pyrox";
        }
        if (card) {
            card.textContent = (name || email)
                ? `Connected (Verified): ${name || "User"} (${email || "No email"})`
                : "Not connected yet";
        }
    }

    function triggerInputSlideUp() {
        const dock = document.getElementById("bottomDock");
        if (!dock) return;
        dock.classList.remove("dock-slid-up");
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                dock.classList.add("dock-slid-up");
            });
        });
    }

    function transitionToDarkStudio() {
        document.getElementById("pyroxWelcomeScreen")?.classList.remove("show");
        document.getElementById("onboardingSignupScreen")?.classList.remove("show");
        closeModal("googleChooserModal");
        setTimeout(() => {
            document.body.classList.remove("pre-login-white");
            syncHeaderAccountUI();
            refreshGreeting();
            triggerInputSlideUp();
        }, 60);
    }

    function runSplashAndWelcomeFlow() {
        const splash = document.getElementById("splashOverlay");
        const welcome = document.getElementById("pyroxWelcomeScreen");

        setTimeout(() => {
            splash.classList.add("done");
            setTimeout(() => {
                splash.style.display = "none";
                if (!isUserSignedUp() && !sessionStorage.getItem("pyrox_skipped_signup")) {
                    welcome.classList.add("show");
                } else {
                    transitionToDarkStudio();
                }
            }, 350);
        }, 920);
    }

    function openGoogleAccountChooser() {
        openModal("googleChooserModal");
    }

    function openSignUpFormScreen() {
        document.getElementById("pyroxWelcomeScreen")?.classList.remove("show");
        document.getElementById("onboardingSignupScreen")?.classList.add("show");
    }

    function skipWelcomeToDarkApp() {
        sessionStorage.setItem("pyrox_skipped_signup", "1");
        transitionToDarkStudio();
    }

    function selectChooserAccount(name, email) {
        const chk = document.getElementById("chooserRobotCheck");
        if (chk && !chk.checked) {
            alert("Please tick 'I am not a robot' first.");
            return;
        }
        localStorage.setItem("pyrox_user_name", name);
        localStorage.setItem("pyrox_user_email", email);
        localStorage.setItem("pyrox_signed_up", "1");
        transitionToDarkStudio();
    }

    function completeOnboardingForm() {
        const chk = document.getElementById("obRobotCheck");
        if (chk && !chk.checked) {
            alert("Please tick 'I am not a robot' before continuing.");
            return;
        }
        const nameVal = document.getElementById("obName").value.trim();
        const emailVal = document.getElementById("obEmail").value.trim();
        if (nameVal) localStorage.setItem("pyrox_user_name", nameVal);
        if (emailVal) localStorage.setItem("pyrox_user_email", emailVal);
        localStorage.setItem("pyrox_signed_up", "1");
        transitionToDarkStudio();
    }

    function openLogoutConfirmModal() {
        document.getElementById("logoutErrorMsg").textContent = "";
        const chk = document.getElementById("logoutRobotCheck");
        if (chk) chk.checked = false;
        openModal("logoutConfirmModal");
    }

    function confirmLogoutAccount() {
        const chk = document.getElementById("logoutRobotCheck");
        if (!chk || !chk.checked) {
            document.getElementById("logoutErrorMsg").textContent = "Pehle 'I am not a robot' tick karein.";
            return;
        }
        localStorage.removeItem("pyrox_user_name");
        localStorage.removeItem("pyrox_user_email");
        localStorage.removeItem("pyrox_signed_up");
        syncHeaderAccountUI();
        refreshGreeting();
        document.getElementById("accountStatusMsg").textContent = "Logged out safely.";
        closeModal("logoutConfirmModal");
        closeModal("googleModal");
    }

    function showPendingAttachmentChip(label) {
        const bar = document.getElementById("attachmentChipBar");
        const txt = document.getElementById("attachmentChipLabel");
        if (bar && txt) {
            txt.textContent = `Attached: ${label}`;
            bar.classList.add("show");
        }
    }

    function clearPendingAttachment() {
        pendingAttachmentDataUrl = null;
        pendingFileDataUrl = null;
        pendingAttachmentName = "";
        const bar = document.getElementById("attachmentChipBar");
        if (bar) bar.classList.remove("show");
    }

    function getTodayKey() {
        const now = new Date();
        return `${now.getFullYear()}-${now.getMonth() + 1}-${now.getDate()}`;
    }

    function getUsageToday() {
        const saved = JSON.parse(localStorage.getItem("pyrox_daily_usage") || "{}");
        if (saved.date !== getTodayKey()) return { total: 0, heavy: 0 };
        return {
            total: Number(saved.total || 0),
            heavy: Number(saved.heavy || 0),
        };
    }

    function recordQuestionUsage(isHeavy) {
        const curr = getUsageToday();
        const next = {
            total: curr.total + 1,
            heavy: curr.heavy + (isHeavy ? 1 : 0),
        };
        localStorage.setItem(
            "pyrox_daily_usage",
            JSON.stringify({ date: getTodayKey(), ...next })
        );
        updateLimitWarningBanner(isHeavy);
        return next;
    }

    function isDailyLimitReached(isHeavy) {
        const curr = getUsageToday();
        if (curr.total >= NORMAL_DAILY_LIMIT) return true;
        if (isHeavy && curr.heavy >= CODING_DAILY_LIMIT) return true;
        return false;
    }

    function updateLimitWarningBanner(isHeavyContext = false) {
        const curr = getUsageToday();
        const remNormal = Math.max(0, NORMAL_DAILY_LIMIT - curr.total);
        const remHeavy = Math.max(0, CODING_DAILY_LIMIT - curr.heavy);
        const banner = document.getElementById("statusStrip");

        if (curr.total >= NORMAL_DAILY_LIMIT) {
            banner.textContent = "Daily 40-question limit reached. Resets tomorrow.";
            banner.classList.add("show");
        } else if (isHeavyContext && curr.heavy >= CODING_DAILY_LIMIT) {
            banner.textContent = "Daily 30-question coding/heavy limit reached. Resets tomorrow.";
            banner.classList.add("show");
        } else if (remNormal <= WARNING_REMAINING_THRESHOLD || (isHeavyContext && remHeavy <= WARNING_REMAINING_THRESHOLD)) {
            const rem = isHeavyContext ? Math.min(remNormal, remHeavy) : remNormal;
            banner.textContent = `${rem} questions remaining today before daily reset.`;
            banner.classList.add("show");
        } else if (!banner.dataset.searching && !banner.dataset.limitAlert) {
            banner.textContent = "";
            banner.classList.remove("show");
        }
    }

    function setSearchingBanner(active) {
        const banner = document.getElementById("statusStrip");
        delete banner.dataset.limitAlert;
        if (active) {
            banner.dataset.searching = "1";
            banner.textContent = "Searching live web...";
            banner.classList.add("show");
        } else {
            delete banner.dataset.searching;
            updateLimitWarningBanner();
        }
    }

    function checkInputCharLimit(text) {
        const banner = document.getElementById("statusStrip");
        if ((text || "").length > MAX_INPUT_CHARS) {
            banner.dataset.limitAlert = "1";
            banner.textContent = `Input limit is ${MAX_INPUT_CHARS} characters (${text.length} entered). Send in smaller parts.`;
            banner.classList.add("show");
            return false;
        }
        if (banner.dataset.limitAlert) {
            delete banner.dataset.limitAlert;
            updateLimitWarningBanner();
        }
        return true;
    }

    function getUserName() {
        return localStorage.getItem("pyrox_user_name") || "";
    }

    function getThemeLabel() {
        return localStorage.getItem("pyrox_theme_label") || "Pyrox";
    }

    function refreshGreeting() {
        const name = getUserName().trim();
        const el = document.getElementById("greetingText");
        if (el) {
            el.textContent = name
                ? `Swagatam ${name}! Kya padhna ya samajhna hai aaj?`
                : "Swagatam! Kya padhna ya samajhna hai aaj?";
        }
    }

    function refreshThemeLabel() {
        const label = getThemeLabel().trim() || "Pyrox";
        document.getElementById("headerBrandTitle").textContent = label;
        document.getElementById("sidebarThemeTitle").textContent = label;
        document.getElementById("splashWord").textContent = label;
        const greetBrand = document.getElementById("greetingBrandName");
        if (greetBrand) greetBrand.textContent = label;
        document.getElementById("customThemeInput").value = label;
    }

    function useStarterPrompt(text) {
        if (isRequestInFlight) return;
        const input = document.getElementById("promptInput");
        input.value = text;
        sendMessage();
    }

    function openSidebar(e) {
        if (e) e.stopPropagation();
        document.getElementById("sidebar").classList.add("open");
        document.getElementById("burgerBtn").classList.add("hidden-burger");
    }

    function closeSidebar() {
        document.getElementById("sidebar").classList.remove("open");
        document.getElementById("burgerBtn").classList.remove("hidden-burger");
    }

    function toggleDotsMenu(e) {
        if (e) e.stopPropagation();
        document.getElementById("dotsMenu").classList.toggle("show");
    }

    function closeDotsMenu() {
        document.getElementById("dotsMenu").classList.remove("show");
    }

    function togglePlusMenu(e) {
        if (e) e.stopPropagation();
        const menu = document.getElementById("plusMenu");
        const btn = document.getElementById("plusBtn");
        const open = menu.classList.toggle("show");
        btn.classList.toggle("open-minus", open);
        btn.textContent = open ? "−" : "+";
    }

    function closePlusMenu() {
        document.getElementById("plusMenu").classList.remove("show");
        const btn = document.getElementById("plusBtn");
        btn.classList.remove("open-minus");
        btn.textContent = "+";
    }

    document.addEventListener("click", () => {
        closeSidebar();
        closeDotsMenu();
        closePlusMenu();
    });

    function toggleModelSublist() {
        document.getElementById("modelSublist").classList.toggle("show");
    }

    function toggleAllHistorySection() {
        const block = document.getElementById("libraryFolders");
        block.style.display = block.style.display === "none" ? "flex" : "none";
    }

    function selectModelMode(mode) {
        selectedModelMode = mode;
        document.getElementById("optPyroxOnly").classList.toggle("active", mode === "Pyrox Only");
    }

    function openModal(id) {
        if (id === "libraryModal") renderLibraryModal();
        if (id === "googleModal") syncHeaderAccountUI();
        document.getElementById(id).classList.add("show");
    }

    function closeModal(id) {
        document.getElementById(id).classList.remove("show");
    }

    function saveAccountForm() {
        const chk = document.getElementById("gmailRobotCheck");
        if (chk && !chk.checked) {
            document.getElementById("accountStatusMsg").textContent = "Please tick 'I am not a robot' before saving.";
            return;
        }
        const name = document.getElementById("googleNameInput").value.trim();
        const email = document.getElementById("googleEmailInput").value.trim();
        if (name) localStorage.setItem("pyrox_user_name", name);
        if (email) localStorage.setItem("pyrox_user_email", email);
        localStorage.setItem("pyrox_signed_up", "1");
        syncHeaderAccountUI();
        refreshGreeting();
        closeModal("googleModal");
    }

    function saveThemeName() {
        const val = document.getElementById("customThemeInput").value.trim();
        if (val) {
            localStorage.setItem("pyrox_theme_label", val);
            refreshThemeLabel();
        }
        closeModal("settingsModal");
    }

    function toggleTtsPreference() {
        ttsEnabled = !ttsEnabled;
        document.getElementById("ttsToggleBtn").textContent = `Auto Voice Reply: ${ttsEnabled ? "On" : "Off"}`;
    }

    function loadFolders() {
        return JSON.parse(localStorage.getItem("pyrox_folders") || "[]");
    }

    function saveFolders(folders) {
        localStorage.setItem("pyrox_folders", JSON.stringify(folders.slice(0, 30)));
    }

    function ensureFolderForPrompt(promptText) {
        const folders = loadFolders();
        if (!activeFolderId) {
            const cleanTitle = (promptText || "New Chat").replace(/\s+/g, " ").trim().slice(0, 34);
            const newFolder = {
                id: "fld_" + Date.now(),
                title: cleanTitle || "New Chat",
                items: [],
            };
            folders.unshift(newFolder);
            activeFolderId = newFolder.id;
            saveFolders(folders);
            renderLibraryFolders();
        }
        return activeFolderId;
    }

    function appendItemToActiveFolder(role, content) {
        if (!activeFolderId) return;
        const folders = loadFolders();
        const target = folders.find((f) => f.id === activeFolderId);
        if (target) {
            target.items.push({ role, content: content.slice(0, 600) });
            saveFolders(folders);
        }
    }

    function renderLibraryFolders() {
        const box = document.getElementById("libraryFolders");
        const folders = loadFolders();
        box.innerHTML = "";
        if (!folders.length) {
            const empty = document.createElement("div");
            empty.className = "plain-history-line";
            empty.textContent = "No recent chats";
            box.appendChild(empty);
            return;
        }
        folders.slice(0, 14).forEach((f) => {
            const line = document.createElement("div");
            line.className = "plain-history-line";
            line.textContent = f.title;
            line.onclick = () => {
                openFolderInStage(f.id);
                closeSidebar();
            };
            box.appendChild(line);
        });
    }

    function openFolderInStage(folderId) {
        const folders = loadFolders();
        const target = folders.find((f) => f.id === folderId);
        if (!target) return;
        activeFolderId = target.id;
        const stage = document.getElementById("scrollStage");
        stage.innerHTML = "";
        chatStarted = true;
        target.items.forEach((m) => {
            if (m.role === "user") {
                const row = document.createElement("div");
                row.className = "msg-row msg-user";
                row.textContent = m.content;
                stage.appendChild(row);
            } else {
                appendAIMessage(renderRichMarkdown(m.content), m.content, "");
            }
        });
        stage.scrollTop = stage.scrollHeight;
    }

    function renderLibraryModal() {
        const body = document.getElementById("libraryModalBody");
        const folders = loadFolders();
        if (!folders.length) {
            body.textContent = "No chats yet.";
            return;
        }
        body.innerHTML = "";
        folders.forEach((f) => {
            const line = document.createElement("div");
            line.className = "plain-history-line";
            line.textContent = `${f.title} (${f.items.length})`;
            line.onclick = () => {
                closeModal("libraryModal");
                openFolderInStage(f.id);
            };
            body.appendChild(line);
        });
    }

    function clearSavedFolders() {
        localStorage.removeItem("pyrox_folders");
        activeFolderId = null;
        renderLibraryFolders();
        renderLibraryModal();
    }

    function newChat() {
        stopGeneration();
        clearPendingAttachment();
        activeFolderId = null;
        const stage = document.getElementById("scrollStage");
        stage.innerHTML = `
            <div class="greeting-center" id="greetingBox">
                <div class="greeting-logo-row">
                    <svg width="46" height="46" viewBox="0 0 100 100" fill="none">
                        <path d="M50 4 C55 34, 66 45, 96 50 C66 55, 55 66, 50 96 C45 66, 34 55, 4 50 C34 45, 45 34, 50 4 Z" fill="url(#pyroxOuterGrad)" />
                        <path d="M50 20 C53 40, 60 47, 80 50 C60 53, 53 60, 50 80 C47 60, 40 53, 20 50 C40 47, 47 40, 50 20 Z" fill="url(#pyroxMidGrad)" />
                        <path d="M50 34 C51.5 44, 56 48.5, 66 50 C56 51.5, 51.5 56, 50 66 C48.5 56, 44 51.5, 34 50 C44 48.5, 48.5 44, 50 34 Z" fill="url(#pyroxCoreGrad)" />
                    </svg>
                    <span class="greeting-logo-title" id="greetingBrandName">${getThemeLabel()}</span>
                </div>
                <h1 id="greetingText"></h1>
                <div class="starter-chips-row">
                    <button type="button" class="starter-chip" onclick="useStarterPrompt('Photo ya page mein kya likha hai aur fill in the blanks mein kya bharna hai?')">Read photo / blanks</button>
                    <button type="button" class="starter-chip" onclick="useStarterPrompt('Kisi topic ko Hinglish mein aasan tarike se samjhao')">Explain simply</button>
                    <button type="button" class="starter-chip" onclick="useStarterPrompt('Help me write and debug Python code')">Coding help</button>
                </div>
            </div>
        `;
        refreshGreeting();
        chatStarted = false;
    }

    function exportChat() {
        const text = document.getElementById("scrollStage").innerText.trim();
        if (!text) return;
        const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "pyrox_chat.txt";
        a.click();
        URL.revokeObjectURL(url);
    }

    function handleInputFocus() {
        closePlusMenu();
        closeDotsMenu();
        setTimeout(() => {
            const stage = document.getElementById("scrollStage");
            stage.scrollTop = stage.scrollHeight;
        }, 120);
    }

    function handleInputKeydown(e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    }

    function triggerFilePicker() {
        closePlusMenu();
        document.getElementById("filePicker").click();
    }

    function handleFileSelected(e) {
        const file = e.target.files && e.target.files[0];
        if (!file) return;
        pendingAttachmentName = file.name;
        const reader = new FileReader();
        reader.onload = () => {
            if (file.type && file.type.startsWith("image/")) {
                pendingAttachmentDataUrl = reader.result;
                pendingFileDataUrl = null;
            } else {
                pendingFileDataUrl = reader.result;
                pendingAttachmentDataUrl = null;
            }
            showPendingAttachmentChip(file.name);
            document.getElementById("promptInput").focus();
        };
        reader.readAsDataURL(file);
        e.target.value = "";
    }

    function promptCanvasMode() {
        closePlusMenu();
        const input = document.getElementById("promptInput");
        input.value = "Canvas draft: ";
        input.focus();
    }

    async function openCamera() {
        closePlusMenu();
        document.getElementById("cameraModal").classList.add("show");
        await startCameraStream();
    }

    async function startCameraStream() {
        stopCameraStream();
        const video = document.getElementById("cameraVideo");
        const statusEl = document.getElementById("camStatusMsg");
        statusEl.textContent = "Starting camera...";

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            statusEl.textContent = "Camera API not supported in this browser/context (requires HTTPS or localhost).";
            return;
        }

        const attempts = [
            { video: { facingMode: { ideal: currentFacingMode } }, audio: false },
            { video: true, audio: false },
        ];

        for (const constraints of attempts) {
            try {
                cameraStream = await navigator.mediaDevices.getUserMedia(constraints);
                video.srcObject = cameraStream;
                statusEl.textContent = "";
                return;
            } catch (_) {}
        }

        statusEl.textContent = "Camera permission blocked or no camera device found.";
    }

    function stopCameraStream() {
        if (cameraStream) {
            cameraStream.getTracks().forEach((t) => t.stop());
            cameraStream = null;
        }
        const video = document.getElementById("cameraVideo");
        if (video) video.srcObject = null;
    }

    function closeCamera() {
        stopCameraStream();
        document.getElementById("cameraModal").classList.remove("show");
    }

    async function flipCamera() {
        currentFacingMode = currentFacingMode === "environment" ? "user" : "environment";
        await startCameraStream();
    }

    async function toggleFlash() {
        flashEnabled = !flashEnabled;
        document.getElementById("flashToggleBtn").textContent = `Flash: ${flashEnabled ? "On" : "Off"}`;
        if (cameraStream) {
            const track = cameraStream.getVideoTracks()[0];
            const caps = track && track.getCapabilities ? track.getCapabilities() : {};
            if (caps.torch) {
                try {
                    await track.applyConstraints({ advanced: [{ torch: flashEnabled }] });
                } catch (_) {}
            }
        }
    }

    function captureCameraPhoto() {
        const video = document.getElementById("cameraVideo");
        const canvas = document.getElementById("cameraCanvas");
        if (!video.videoWidth || !video.videoHeight) {
            document.getElementById("camStatusMsg").textContent = "Camera frame not ready yet. Wait a second or check permission.";
            return;
        }
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext("2d").drawImage(video, 0, 0);
        pendingAttachmentDataUrl = canvas.toDataURL("image/jpeg", 0.88);
        pendingFileDataUrl = null;
        pendingAttachmentName = "camera_photo.jpg";
        showPendingAttachmentChip("camera_photo.jpg");
        closeCamera();
        document.getElementById("promptInput").focus();
    }

    function setMicButtonAsStopSquare(recording) {
        const micBtn = document.getElementById("micBtn");
        micBtn.classList.toggle("mic-recording", recording);
        micBtn.innerHTML = recording ? `<span class="curved-stop-square"></span>` : MIC_SVG;
        micBtn.title = recording ? "Stop dictation" : "Voice input";
    }

    function toggleDictation(e) {
        if (e) e.stopPropagation();
        if (isDictating) {
            stopDictationManual(false);
            return;
        }

        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        const inputEl = document.getElementById("promptInput");
        if (!SR || !inputEl) return;

        const baseText = inputEl.value.trim();
        let finalCommitted = "";

        recognition = new SR();
        recognition.lang = "hi-IN";
        recognition.continuous = false;
        recognition.interimResults = true;

        recognition.onstart = () => {
            isDictating = true;
            setMicButtonAsStopSquare(true);
        };

        recognition.onresult = (event) => {
            if (!isDictating) return;
            let interim = "";
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const seg = event.results[i][0].transcript || "";
                if (event.results[i].isFinal) {
                    finalCommitted += (finalCommitted ? " " : "") + seg.trim();
                } else {
                    interim += seg;
                }
            }
            const merged = [baseText, finalCommitted, interim.trim()].filter(Boolean).join(" ").trim();
            inputEl.value = merged;
            checkInputCharLimit(merged);
        };

        recognition.onerror = () => {
            stopDictationManual(false);
        };

        recognition.onend = () => {
            isDictating = false;
            setMicButtonAsStopSquare(false);
            recognition = null;
        };

        try {
            recognition.start();
        } catch (_) {
            stopDictationManual(false);
        }
    }

    function stopDictationManual(clearInputText = false) {
        isDictating = false;
        setMicButtonAsStopSquare(false);
        if (recognition) {
            recognition.onresult = null;
            recognition.onend = null;
            recognition.onerror = null;
            try { recognition.stop(); } catch (_) {}
            try { recognition.abort(); } catch (_) {}
            recognition = null;
        }
        if (clearInputText) {
            const inp = document.getElementById("promptInput");
            if (inp) inp.value = "";
        }
    }

    function markChatStarted() {
        if (!chatStarted) {
            chatStarted = true;
            const g = document.getElementById("greetingBox");
            if (g) g.remove();
        }
    }

    function renderRichMarkdown(mdText) {
        const rawHtml = marked.parse(mdText || "");
        const container = document.createElement("div");
        container.innerHTML = rawHtml;
        container.querySelectorAll("pre").forEach((pre) => {
            const wrap = document.createElement("div");
            wrap.className = "code-block-wrap";
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "code-copy-btn";
            btn.textContent = "Copy";
            btn.onclick = () => {
                const codeText = pre.innerText || "";
                navigator.clipboard.writeText(codeText).catch(() => {});
                btn.textContent = "Copied";
                setTimeout(() => (btn.textContent = "Copy"), 1100);
            };
            pre.parentNode.insertBefore(wrap, pre);
            wrap.appendChild(pre);
            wrap.appendChild(btn);
        });
        return container.innerHTML;
    }

    function appendUserMessage(text, imgUrl, fileLabel) {
        markChatStarted();
        const stage = document.getElementById("scrollStage");
        const row = document.createElement("div");
        row.className = "msg-row msg-user";
        if (imgUrl && imgUrl.startsWith("data:image/")) {
            const img = document.createElement("img");
            img.src = imgUrl;
            img.style.maxWidth = "220px";
            img.style.borderRadius = "10px";
            img.style.marginBottom = "6px";
            row.appendChild(img);
        }
        if (fileLabel && !imgUrl) {
            const fBadge = document.createElement("div");
            fBadge.style.fontSize = "0.86rem";
            fBadge.style.color = "var(--text-secondary)";
            fBadge.style.marginBottom = "4px";
            fBadge.textContent = `File: ${fileLabel}`;
            row.appendChild(fBadge);
        }
        const span = document.createElement("div");
        span.textContent = text;
        row.appendChild(span);
        stage.appendChild(row);
        stage.scrollTop = stage.scrollHeight;
    }

    async function speakTextOnDemand(text, btnEl) {
        if (!text) return;
        btnEl.classList.add("liquid-filled");
        try {
            const res = await fetch("/api/listen", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text }),
            });
            const data = await res.json();
            if (res.ok && data.audio_url) {
                if (latestAudioPlayer) latestAudioPlayer.pause();
                latestAudioPlayer = new Audio(data.audio_url);
                latestAudioPlayer.onended = () => btnEl.classList.remove("liquid-filled");
                latestAudioPlayer.play().catch(() => btnEl.classList.remove("liquid-filled"));
            } else {
                btnEl.classList.remove("liquid-filled");
            }
        } catch (_) {
            btnEl.classList.remove("liquid-filled");
        }
    }

    function buildResponseActionsBar(plainText, originalPrompt) {
        const bar = document.createElement("div");
        bar.className = "msg-actions";

        const likeBtn = document.createElement("button");
        likeBtn.type = "button";
        likeBtn.className = "icon-symbol-btn";
        likeBtn.title = "Good";
        likeBtn.innerHTML = `
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3z"></path>
                <path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
            </svg>
        `;

        const dislikeBtn = document.createElement("button");
        dislikeBtn.type = "button";
        dislikeBtn.className = "icon-symbol-btn";
        dislikeBtn.title = "Bad";
        dislikeBtn.innerHTML = `
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3z"></path>
                <path d="M17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path>
            </svg>
        `;

        likeBtn.onclick = () => {
            likeBtn.classList.toggle("liquid-filled");
            if (likeBtn.classList.contains("liquid-filled")) {
                dislikeBtn.classList.remove("liquid-filled");
            }
        };

        dislikeBtn.onclick = () => {
            likeBtn.classList.remove("liquid-filled");
            activeDislikeBtn = dislikeBtn;
            feedbackTargetSnippet = plainText.slice(0, 200);
            openModal("feedbackModal");
        };

        const cycleBtn = document.createElement("button");
        cycleBtn.type = "button";
        cycleBtn.className = "icon-symbol-btn";
        cycleBtn.title = "Regenerate";
        cycleBtn.innerHTML = `
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="23 4 23 10 17 10"></polyline>
                <polyline points="1 20 1 14 7 14"></polyline>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
            </svg>
        `;
        cycleBtn.onclick = () => {
            if (originalPrompt && !isRequestInFlight) {
                sendMessage(originalPrompt, true);
            }
        };

        const listenBtn = document.createElement("button");
        listenBtn.type = "button";
        listenBtn.className = "icon-symbol-btn";
        listenBtn.title = "Listen";
        listenBtn.innerHTML = `
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                <path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                <path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path>
            </svg>
        `;
        listenBtn.onclick = () => speakTextOnDemand(plainText, listenBtn);

        const copyBtn = document.createElement("button");
        copyBtn.type = "button";
        copyBtn.className = "icon-symbol-btn";
        copyBtn.title = "Copy";
        copyBtn.innerHTML = `
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
        `;
        copyBtn.onclick = () => {
            navigator.clipboard.writeText(plainText).catch(() => {});
            copyBtn.classList.add("liquid-filled");
            setTimeout(() => copyBtn.classList.remove("liquid-filled"), 950);
        };

        const shareBtn = document.createElement("button");
        shareBtn.type = "button";
        shareBtn.className = "icon-symbol-btn";
        shareBtn.title = "Share / Export";
        shareBtn.innerHTML = `
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="18" cy="5" r="3"></circle>
                <circle cx="6" cy="12" r="3"></circle>
                <circle cx="18" cy="19" r="3"></circle>
                <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
                <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
            </svg>
        `;
        shareBtn.onclick = () => {
            if (navigator.share) {
                navigator.share({ title: "Pyrox AI", text: plainText }).catch(() => {});
            } else {
                exportChat();
            }
        };

        bar.appendChild(likeBtn);
        bar.appendChild(dislikeBtn);
        bar.appendChild(cycleBtn);
        bar.appendChild(listenBtn);
        bar.appendChild(copyBtn);
        bar.appendChild(shareBtn);
        return bar;
    }

    function appendAIMessage(htmlContent, plainText, originalPrompt) {
        markChatStarted();
        const stage = document.getElementById("scrollStage");
        const row = document.createElement("div");
        row.className = "msg-row msg-ai";

        const bodyDiv = document.createElement("div");
        bodyDiv.innerHTML = htmlContent;
        row.appendChild(bodyDiv);

        if (plainText) {
            row.appendChild(buildResponseActionsBar(plainText, originalPrompt));
        }

        stage.appendChild(row);
        stage.scrollTop = stage.scrollHeight;
        return { row, bodyDiv };
    }

    function toggleFeedbackReason(chip) {
        chip.classList.toggle("active");
    }

    async function submitBadFeedback() {
        const activeChips = Array.from(
            document.querySelectorAll("#feedbackReasonsGrid .reason-chip.active")
        ).map((c) => c.textContent);
        const note = document.getElementById("feedbackCustomNote").value.trim();
        const reasonStr = activeChips.join(", ") || "General feedback";

        try {
            await fetch("/api/feedback", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    reason: reasonStr,
                    details: note,
                    response_snippet: feedbackTargetSnippet,
                }),
            });
        } catch (_) {}

        if (activeDislikeBtn) {
            activeDislikeBtn.classList.add("liquid-filled");
            activeDislikeBtn = null;
        }

        document.querySelectorAll("#feedbackReasonsGrid .reason-chip").forEach((c) => c.classList.remove("active"));
        document.getElementById("feedbackCustomNote").value = "";
        closeModal("feedbackModal");
    }

    function playAudioFromUrl(url) {
        if (!ttsEnabled || !url) return;
        if (latestAudioPlayer) latestAudioPlayer.pause();
        latestAudioPlayer = new Audio(url);
        latestAudioPlayer.play().catch(() => {});
    }

    function setGeneratingState(generating) {
        isRequestInFlight = generating;
        document.getElementById("sendBtn").classList.toggle("hidden-send", generating);
        document.getElementById("stopGenBtn").classList.toggle("visible", generating);
    }

    function stopGeneration() {
        if (activeAbortController) {
            activeAbortController.abort();
            activeAbortController = null;
        }
        setSearchingBanner(false);
        setGeneratingState(false);
    }

    function detectHeavyCodingIntent(text) {
        return /\b(python|code|coding|script|function|bug|error|html|css|javascript|js|fastapi|sql|algorithm|debug)\b/i.test(
            text
        );
    }

    async function sendMessage(overrideText = null, isRegenerate = false) {
        if (isRequestInFlight) return;
        if (isDictating) stopDictationManual(false);

        const input = document.getElementById("promptInput");
        const raw = overrideText !== null ? String(overrideText).trim() : input.value.trim();

        if (!checkInputCharLimit(raw)) return;
        if (!raw && !pendingAttachmentDataUrl && !pendingFileDataUrl) return;

        const messageToSend = raw || `Please read ${pendingAttachmentName || "this attachment"} and tell me what is written and what needs to be done.`;
        const isHeavy = detectHeavyCodingIntent(messageToSend);

        if (isDailyLimitReached(isHeavy)) {
            updateLimitWarningBanner(isHeavy);
            return;
        }

        const attachmentToSend = pendingAttachmentDataUrl;
        const fileToSend = pendingFileDataUrl;
        const fileNameToSend = pendingAttachmentName;

        clearPendingAttachment();

        if (overrideText === null) {
            input.value = "";
            input.placeholder = "Ask Pyrox...";
        }

        ensureFolderForPrompt(messageToSend);
        appendUserMessage(messageToSend, attachmentToSend, fileNameToSend);
        appendItemToActiveFolder("user", messageToSend);
        recordQuestionUsage(isHeavy);

        const { row, bodyDiv } = appendAIMessage(
            `<div class="thinking-dots"><span></span><span></span></div>`,
            "",
            messageToSend
        );

        activeAbortController = new AbortController();
        setGeneratingState(true);

        const searchLikely = /\b(aaj|kal|today|tomorrow|news|latest|festival|tyohar|weather|price|rate|2025|2026|2027|kab hai|kya chal raha)\b/i.test(
            messageToSend
        );

        if (searchLikely) setSearchingBanner(true);

        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: messageToSend,
                    user_name: getUserName(),
                    theme_label: getThemeLabel(),
                    model_mode: selectedModelMode,
                    enable_tts: ttsEnabled,
                    image_data_url: attachmentToSend,
                    file_name: fileNameToSend,
                    file_data_url: fileToSend,
                    regenerate: isRegenerate,
                }),
                signal: activeAbortController.signal,
            });
            const data = await res.json();
            if (!res.ok) {
                bodyDiv.textContent = data.detail || "Request failed.";
            } else {
                const reply = data.reply || "";
                bodyDiv.innerHTML = renderRichMarkdown(reply);
                row.appendChild(buildResponseActionsBar(reply, messageToSend));
                appendItemToActiveFolder("ai", reply);
                if (data.audio_url) playAudioFromUrl(data.audio_url);
            }
        } catch (err) {
            bodyDiv.textContent = err.name === "AbortError" ? "Stopped." : "Connection error.";
        } finally {
            activeAbortController = null;
            setSearchingBanner(false);
            setGeneratingState(false);
            const stage = document.getElementById("scrollStage");
            stage.scrollTop = stage.scrollHeight;
        }
    }

    syncHeaderAccountUI();
    runSplashAndWelcomeFlow();
    refreshGreeting();
    refreshThemeLabel();
    renderLibraryFolders();
    updateLimitWarningBanner();
</script>
</body>
</html>
"""
    return html
