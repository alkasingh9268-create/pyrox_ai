import asyncio
import base64
import datetime
import os
import re
from typing import Optional

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
HF_API_KEY = (
    os.environ.get("HF_API_KEY", "").strip()
    or os.environ.get("HUGGINGFACE_API_KEY", "").strip()
)

CACHED_GROQ_MODEL: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    voice: str = "hi-IN-MadhurNeural"
    user_name: Optional[str] = None
    theme_label: str = "Pyrox"
    model_mode: str = "Pyrox Only"
    enable_tts: bool = True
    image_data_url: Optional[str] = None


class ImageRequest(BaseModel):
    prompt: str
    model_id: str = "black-forest-labs/FLUX.1-schnell"


class FeedbackRequest(BaseModel):
    reason: str
    details: Optional[str] = ""
    response_snippet: Optional[str] = ""


class ListenRequest(BaseModel):
    text: str
    voice: str = "hi-IN-MadhurNeural"


def resolve_groq_model() -> str:
    global CACHED_GROQ_MODEL
    if CACHED_GROQ_MODEL:
        return CACHED_GROQ_MODEL

    default_model = "llama-3.3-70b-versatile"
    if not GROQ_API_KEY:
        return default_model

    try:
        res = requests.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            timeout=5,
        )
        if res.status_code == 200:
            ids = [
                m.get("id", "")
                for m in res.json().get("data", [])
                if m.get("id")
            ]
            filtered = [
                m_id
                for m_id in ids
                if "guard" not in m_id.lower() and "whisper" not in m_id.lower()
            ]
            for pref in ["llama-3.3-70b-versatile", "llama", "qwen", "gemma"]:
                for m_id in filtered:
                    if pref in m_id.lower():
                        CACHED_GROQ_MODEL = m_id
                        return m_id
            if filtered:
                CACHED_GROQ_MODEL = filtered[0]
                return filtered[0]
    except Exception:
        pass

    CACHED_GROQ_MODEL = default_model
    return default_model


def is_heavy_coding_query(message: str) -> bool:
    q = message.lower()
    coding_terms = [
        "python",
        "code",
        "coding",
        "script",
        "function",
        "bug",
        "error",
        "html",
        "css",
        "javascript",
        "js",
        "fastapi",
        "sql",
        "algorithm",
        "debug",
        "class ",
        "def ",
        "import ",
    ]
    return any(term in q for term in coding_terms)


def should_search_web(message: str) -> bool:
    q = message.lower()
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
        "score",
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
    today_str = datetime.datetime.now().strftime("%A, %d %B %Y")
    base_info = f"Current Date & Time: {today_str} (India)."
    if not SERP_API_KEY:
        return base_info

    try:
        encoded = requests.utils.quote(query)
        url = f"https://serpapi.com/search.json?q={encoded}&api_key={SERP_API_KEY}&hl=en&gl=in"
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
    return base_info


async def generate_edge_audio(
    text: str, voice_name: str, filename: str = "static/response.mp3"
) -> bool:
    try:
        cleaned = re.sub(r"[*_`#~]+", "", text)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if not cleaned:
            return False
        communicate = edge_tts.Communicate(cleaned[:650], voice_name, rate="+20%")
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


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    if not GROQ_API_KEY:
        return JSONResponse(
            status_code=400,
            content={"detail": "GROQ_API_KEY environment variable missing."},
        )

    user_msg = req.message.strip()
    if not user_msg and not req.image_data_url:
        return JSONResponse(
            status_code=400, content={"detail": "Message cannot be empty."}
        )

    try:
        model_id = resolve_groq_model()
        used_search = should_search_web(user_msg)
        context_block = (
            search_live_context(user_msg)
            if used_search
            else f"Current Date: {datetime.datetime.now().strftime('%A, %d %B %Y')} (India)."
        )

        short_mode = is_short_greeting(user_msg) and not req.image_data_url
        user_label = (
            req.user_name.strip()
            if req.user_name and req.user_name.strip()
            else ""
        )
        identity_line = (
            f"The user's name is {user_label}." if user_label else ""
        )

        if short_mode:
            system_prompt = (
                f"You are Pyrox ({req.model_mode} mode). {context_block} {identity_line} "
                "Reply in 1 short, natural, friendly sentence using Roman Hinglish. "
                "Do NOT use bullet points or numbered lists for a simple greeting."
            )
        else:
            system_prompt = (
                f"You are Pyrox ({req.model_mode} mode). {context_block} {identity_line} "
                "Reply fast, clearly, and naturally in smooth Roman Hinglish. "
                "Use bullet points or numbered steps ONLY when genuinely helpful for multi-step or structured info; "
                "for casual or direct questions, write normal clean paragraphs without forced bullets. "
                "Keep dates, festivals, and current events accurate according to the current date."
            )

        effective_prompt = user_msg or "User shared an image."
        if req.image_data_url and "vision" not in model_id.lower():
            effective_prompt = (
                f"{effective_prompt}\n[Note: User attached an image from camera/file. "
                "If image pixels cannot be inspected directly by this text model, politely mention that "
                "and ask what specific detail they want help with.]"
            )

        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": effective_prompt},
            ],
            "temperature": 0.65,
            "max_tokens": 200 if short_mode else 750,
        }

        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=25,
        )

        if res.status_code != 200:
            return JSONResponse(
                status_code=res.status_code,
                content={"detail": f"Groq API error: {res.text[:250]}"},
            )

        reply_text = res.json()["choices"][0]["message"]["content"].strip()
        audio_url = None
        if req.enable_tts:
            ok = await generate_edge_audio(reply_text, req.voice, "static/response.mp3")
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
    stamp = int(asyncio.get_event_loop().time() * 1000)
    filename = "static/listen_out.mp3"
    ok = await generate_edge_audio(req.text, req.voice, filename)
    if not ok:
        return JSONResponse(
            status_code=500, content={"detail": "Unable to generate voice audio."}
        )
    return {"audio_url": f"/static/listen_out.mp3?v={stamp}"}


@app.post("/api/generate-image")
async def generate_image_endpoint(req: ImageRequest):
    if not HF_API_KEY:
        return JSONResponse(
            status_code=400,
            content={
                "detail": "HF_API_KEY missing in environment variables. Set HF_API_KEY on Render first."
            },
        )

    prompt = req.prompt.strip()
    if not prompt:
        return JSONResponse(
            status_code=400, content={"detail": "Please enter an image prompt."}
        )

    model_id = req.model_id.strip() or "black-forest-labs/FLUX.1-schnell"
    router_url = f"https://router.huggingface.co/hf-inference/models/{model_id}"
    legacy_url = f"https://api-inference.huggingface.co/models/{model_id}"

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "image/png",
    }
    body = {"inputs": prompt}

    try:
        resp = requests.post(router_url, headers=headers, json=body, timeout=65)
        if resp.status_code == 404:
            resp = requests.post(legacy_url, headers=headers, json=body, timeout=65)

        if resp.status_code != 200:
            err_msg = resp.text[:250] if resp.text else "Image generation failed"
            return JSONResponse(
                status_code=resp.status_code,
                content={"detail": f"Hugging Face error: {err_msg}"},
            )

        content_type = resp.headers.get("content-type", "image/png")
        b64_img = base64.b64encode(resp.content).decode("utf-8")
        return {
            "image_data": f"data:{content_type};base64,{b64_img}",
            "model": model_id,
        }
    except Exception as exc:
        return JSONResponse(status_code=500, content={"detail": str(exc)})


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
            --bg-main: #09090b;
            --bg-surface: #121216;
            --bg-elevated: #1a1a20;
            --border-subtle: #2a2a32;
            --border-user: #52525b;
            --text-primary: #f4f4f5;
            --text-secondary: #c4c4cc;
            --text-muted: #8e8e98;
            --accent-upgrade: #2563eb;
            --accent-upgrade-border: #3b82f6;
        }

        body.light-mode {
            --bg-main: #ffffff;
            --bg-surface: #f8fafc;
            --bg-elevated: #f1f5f9;
            --border-subtle: #cbd5e1;
            --border-user: #64748b;
            --text-primary: #09090b;
            --text-secondary: #1e293b;
            --text-muted: #64748b;
            --accent-upgrade: #2563eb;
            --accent-upgrade-border: #1d4ed8;
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
            transition: background-color 0.2s ease, color 0.2s ease;
        }

        /* Pogo-style Flashy Star + Pyrox Splash Entry */
        .splash-overlay {
            position: fixed;
            inset: 0;
            background-color: var(--bg-main);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 600;
            overflow: hidden;
            transition: opacity 0.32s ease, transform 0.32s ease;
        }

        .splash-overlay.done {
            opacity: 0;
            transform: scale(1.05);
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
            font-size: 2.5rem;
            font-weight: 800;
            letter-spacing: 0.6px;
            color: var(--text-primary);
            opacity: 0;
            transform: translateX(-30px) skewX(-12deg);
            animation: flashRevealPyrox 0.75s cubic-bezier(0.16, 1, 0.3, 1) 0.14s forwards;
        }

        @keyframes pogoStarPop {
            0% {
                transform: scale(0.15) rotate(-140deg);
                opacity: 0;
            }
            55% {
                transform: scale(1.25) rotate(12deg);
                opacity: 1;
            }
            80% {
                transform: scale(0.94) rotate(-6deg);
            }
            100% {
                transform: scale(1) rotate(0deg);
                opacity: 1;
            }
        }

        @keyframes flashRevealPyrox {
            0% {
                opacity: 0;
                transform: translateX(-32px) skewX(-16deg);
                text-shadow: 0 0 24px rgba(255, 255, 255, 0.9);
            }
            45% {
                opacity: 1;
                transform: translateX(4px) skewX(-6deg);
                text-shadow: 0 0 18px rgba(59, 130, 246, 0.85);
            }
            100% {
                opacity: 1;
                transform: translateX(0) skewX(0deg);
                text-shadow: none;
            }
        }

        /* Full-Screen White Onboarding Sign-Up Tab after Splash (if not logged in) */
        .onboarding-signup-screen {
            position: fixed;
            inset: 0;
            background-color: #ffffff;
            color: #09090b;
            z-index: 520;
            display: none;
            flex-direction: column;
            justify-content: space-between;
            padding: 20px 22px 26px 22px;
            overflow-y: auto;
        }

        .onboarding-signup-screen.show {
            display: flex;
        }

        .onboarding-top-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .onboarding-cross-btn {
            width: 38px;
            height: 38px;
            border-radius: 999px;
            border: 1px solid #cbd5e1;
            background-color: #f8fafc;
            color: #09090b;
            font-size: 1.05rem;
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
            font-size: 1.65rem;
            font-weight: 800;
            color: #09090b;
            margin-bottom: 2px;
        }

        .white-label {
            font-size: 0.88rem;
            font-weight: 700;
            color: #1e293b;
        }

        .white-input {
            width: 100%;
            background-color: #f8fafc;
            border: 1px solid #cbd5e1;
            color: #09090b;
            border-radius: 10px;
            padding: 11px 13px;
            font-size: 0.98rem;
            font-weight: 550;
            outline: none;
        }

        .white-input:focus {
            border-color: #2563eb;
        }

        .white-primary-btn {
            width: 100%;
            padding: 12px 14px;
            border-radius: 10px;
            border: none;
            background-color: #09090b;
            color: #ffffff;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            margin-top: 4px;
        }

        .white-google-btn {
            width: 100%;
            padding: 14px 16px;
            border-radius: 12px;
            border: 1px solid #94a3b8;
            background-color: #ffffff;
            color: #09090b;
            font-size: 1.05rem;
            font-weight: 800;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }

        .white-or {
            text-align: center;
            font-size: 0.85rem;
            color: #64748b;
            font-weight: 600;
        }

        .app-shell {
            display: flex;
            height: 100dvh;
            width: 100%;
            position: relative;
            overflow: hidden;
        }

        /* Expandable Sidebar */
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
            width: 44vw;
            min-width: 185px;
            max-width: 340px;
            border-right-color: var(--border-subtle);
            padding: 16px 12px;
        }

        .sidebar-top {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .sidebar-title {
            font-size: 1.12rem;
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
            padding: 12px 12px;
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
            transition: background-color 0.15s ease, transform 0.1s ease;
        }

        .nav-item:hover {
            background-color: var(--bg-elevated);
        }

        .nav-item:active {
            transform: scale(0.97);
        }

        .quota-pill {
            font-size: 0.74rem;
            font-weight: 700;
            padding: 2px 7px;
            border-radius: 999px;
            background-color: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            color: var(--text-secondary);
        }

        .model-sublist {
            display: none;
            flex-direction: column;
            gap: 5px;
            margin-left: 8px;
            padding-left: 8px;
            border-left: 1px solid var(--border-subtle);
        }

        .model-sublist.show {
            display: flex;
        }

        .model-option {
            padding: 10px 10px;
            border-radius: 8px;
            font-size: 0.92rem;
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

        .library-folders {
            display: none;
            flex-direction: column;
            gap: 6px;
            margin-top: 2px;
            padding-left: 6px;
        }

        .library-folders.show {
            display: flex;
        }

        .folder-chip {
            padding: 9px 10px;
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-secondary);
            background-color: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            cursor: pointer;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .folder-chip:hover {
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
            font-size: 0.92rem;
            font-weight: 700;
            color: var(--text-primary);
            cursor: pointer;
            text-align: center;
        }

        /* Main column */
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
            height: 58px;
            padding: 0 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
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
            background: transparent;
            border: 1px solid var(--border-subtle);
            color: var(--text-primary);
            width: 38px;
            height: 38px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            flex-shrink: 0;
            transition: transform 0.12s ease, background-color 0.15s ease;
        }

        .menu-toggle-btn.hidden-burger {
            display: none;
        }

        .menu-toggle-btn:active,
        .icon-action-btn:active,
        .send-btn:active,
        .stop-btn:active,
        .action-btn:active {
            transform: scale(0.95);
        }

        .brand-heading {
            font-size: 1.15rem;
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
            gap: 6px;
            position: relative;
            flex-shrink: 0;
        }

        .header-signup-btn {
            background-color: var(--bg-elevated);
            color: var(--text-primary);
            border: 1px solid var(--border-user);
            border-radius: 10px;
            padding: 6px 10px;
            font-size: 0.8rem;
            font-weight: 700;
            cursor: pointer;
        }

        .header-signup-btn.logged-in-hide {
            display: none;
        }

        .upgrade-btn {
            position: relative;
            overflow: hidden;
            background-color: var(--accent-upgrade);
            color: #ffffff;
            border: 1px solid var(--accent-upgrade-border);
            border-radius: 14px 4px 14px 4px;
            padding: 7px 12px;
            font-size: 0.84rem;
            font-weight: 700;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }

        .upgrade-btn.shine-active::after {
            content: "";
            position: absolute;
            top: -130%;
            left: -40%;
            width: 65%;
            height: 340%;
            background: linear-gradient(
                115deg,
                transparent 20%,
                rgba(255, 255, 255, 0.65) 50%,
                transparent 80%
            );
            transform: rotate(22deg);
            animation: upgradeSweep 2.1s ease-in-out infinite;
        }

        @keyframes upgradeSweep {
            0% {
                top: -130%;
                opacity: 0;
            }
            25% {
                opacity: 1;
            }
            75% {
                top: 130%;
                opacity: 1;
            }
            100% {
                top: 130%;
                opacity: 0;
            }
        }

        .dots-btn {
            background: transparent;
            border: 1px solid var(--border-subtle);
            color: var(--text-primary);
            width: 36px;
            height: 36px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
        }

        .dots-menu {
            position: absolute;
            top: 44px;
            right: 0;
            width: 195px;
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
            padding: 10px 12px;
            border-radius: 8px;
            font-size: 0.94rem;
            font-weight: 600;
            color: var(--text-primary);
            cursor: pointer;
        }

        .dots-item:hover {
            background-color: var(--bg-elevated);
        }

        .status-strip {
            display: none;
            padding: 7px 14px;
            font-size: 0.88rem;
            font-weight: 650;
            background-color: var(--bg-surface);
            border-bottom: 1px solid var(--border-subtle);
            color: var(--text-secondary);
        }

        .status-strip.show {
            display: block;
        }

        /* Greeting & Chat stage */
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
            font-size: 2rem;
            font-weight: 800;
            letter-spacing: 0.3px;
            color: var(--text-primary);
        }

        .greeting-center h1 {
            font-size: 1.55rem;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1.42;
            letter-spacing: 0.1px;
        }

        .msg-row {
            display: flex;
            flex-direction: column;
            max-width: 90%;
            gap: 8px;
        }

        .msg-user {
            align-self: flex-end;
            background-color: var(--bg-elevated);
            color: var(--text-primary);
            border: 1px solid var(--border-user);
            border-radius: 16px 16px 4px 16px;
            padding: 12px 16px;
            font-size: 1.06rem;
            font-weight: 550;
            line-height: 1.6;
            letter-spacing: 0.15px;
            word-break: break-word;
        }

        .msg-ai {
            align-self: flex-start;
            width: 100%;
            max-width: 100%;
            color: var(--text-primary);
            font-size: 1.08rem;
            font-weight: 500;
            line-height: 1.72;
            letter-spacing: 0.15px;
            word-spacing: 1px;
            padding: 4px 2px;
        }

        .msg-ai p {
            margin-bottom: 10px;
        }

        .msg-ai pre {
            background-color: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            padding: 12px;
            overflow-x: auto;
            margin: 8px 0 12px 0;
            font-size: 0.9rem;
        }

        .msg-ai code {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        }

        .msg-ai ul, .msg-ai ol {
            padding-left: 22px;
            margin: 8px 0 12px 0;
        }

        .msg-ai li {
            margin-bottom: 6px;
        }

        .msg-ai img {
            max-width: 100%;
            max-height: 380px;
            border-radius: 14px;
            border: 1px solid var(--border-subtle);
            margin-top: 6px;
        }

        /* Clean icon-only response action bar */
        .msg-actions {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 4px;
        }

        .icon-symbol-btn {
            width: 34px;
            height: 34px;
            border-radius: 9px;
            background-color: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            color: var(--text-secondary);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
        }

        .icon-symbol-btn:hover,
        .icon-symbol-btn.selected-act {
            color: var(--text-primary);
            border-color: var(--border-user);
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
            0%, 80%, 100% {
                transform: translateY(0);
                opacity: 0.4;
            }
            40% {
                transform: translateY(-6px);
                opacity: 1;
            }
        }

        /* Bottom Dock */
        .bottom-dock {
            flex-shrink: 0;
            width: 100%;
            padding: 8px 10px 8px 10px;
            background-color: var(--bg-main);
            border-top: 1px solid var(--border-subtle);
            position: relative;
            z-index: 30;
        }

        .image-generating-strip {
            display: none;
            margin-bottom: 6px;
            padding: 6px 12px;
            border-radius: 10px;
            background-color: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            font-size: 0.84rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .image-generating-strip.show {
            display: block;
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
            font-size: 0.98rem;
            font-weight: 650;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            text-align: left;
        }

        .plus-big-btn:hover {
            background-color: var(--bg-main);
        }

        .plus-small-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 6px;
            padding-top: 6px;
            border-top: 1px solid var(--border-subtle);
        }

        .plus-small-btn {
            padding: 9px 7px;
            border-radius: 8px;
            background-color: var(--bg-main);
            border: 1px solid var(--border-subtle);
            color: var(--text-secondary);
            font-size: 0.8rem;
            font-weight: 650;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 5px;
        }

        .plus-small-btn:hover {
            color: var(--text-primary);
        }

        .input-shell {
            display: flex;
            align-items: center;
            gap: 8px;
            min-height: 64px;
            background-color: var(--bg-surface);
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
            font-size: 1.2rem;
            font-weight: 700;
            transition: transform 0.18s ease, border-color 0.18s ease;
        }

        .icon-action-btn.open-minus {
            transform: rotate(90deg);
        }

        .icon-action-btn.mic-recording {
            border-color: var(--border-user);
            background-color: var(--bg-main);
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
            font-size: 1.04rem;
            font-weight: 550;
            resize: none;
            padding: 9px 4px;
            line-height: 1.4;
        }

        .prompt-input::placeholder {
            color: var(--text-muted);
        }

        .prompt-input.hidden-while-speaking {
            display: none;
        }

        /* Tightly spaced frequency meter inside input shell while speaking */
        .freq-meter {
            display: none;
            flex: 1;
            align-items: center;
            justify-content: center;
            gap: 2px;
            height: 36px;
            padding: 0 6px;
        }

        .freq-meter.visible {
            display: flex;
        }

        .freq-bar {
            width: 2.5px;
            height: 3px;
            border-radius: 2px;
            background-color: var(--text-primary);
            transition: height 0.06s linear;
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
            font-size: 0.74rem;
            color: var(--text-muted);
            margin-top: 5px;
            font-weight: 500;
        }

        /* Modals */
        .overlay-modal {
            position: fixed;
            inset: 0;
            background-color: rgba(0, 0, 0, 0.65);
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
            background-color: rgba(0, 0, 0, 0.35);
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
            background-color: #27272a;
            color: #f4f4f5;
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
            background-color: #18181b;
            color: #f4f4f5;
            font-size: 0.88rem;
            font-weight: 600;
            cursor: pointer;
        }

        .reason-chip.active {
            background-color: #f4f4f5;
            color: #09090b;
            border-color: #f4f4f5;
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
            font-size: 1.08rem;
        }

        .close-x {
            background: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            color: var(--text-primary);
            border-radius: 8px;
            padding: 5px 10px;
            cursor: pointer;
            font-size: 0.88rem;
            font-weight: 700;
        }

        .field-label {
            font-size: 0.88rem;
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
            font-size: 0.96rem;
            font-weight: 550;
            outline: none;
        }

        .action-btn {
            background-color: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            color: var(--text-primary);
            border-radius: 10px;
            padding: 11px 13px;
            font-size: 0.94rem;
            font-weight: 650;
            cursor: pointer;
        }

        .compare-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.92rem;
        }

        .compare-table th,
        .compare-table td {
            padding: 10px 6px;
            border-bottom: 1px solid var(--border-subtle);
            text-align: left;
            font-weight: 600;
        }

        .compare-table th:nth-child(2),
        .compare-table td:nth-child(2),
        .compare-table th:nth-child(3),
        .compare-table td:nth-child(3) {
            text-align: center;
            width: 68px;
        }

        .single-price-banner {
            border: 1px solid var(--accent-upgrade-border);
            background-color: var(--bg-elevated);
            border-radius: 14px;
            padding: 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .old-price {
            text-decoration: line-through;
            color: var(--text-muted);
            font-size: 0.96rem;
            margin-right: 6px;
        }

        .new-price {
            font-size: 1.32rem;
            font-weight: 800;
            color: var(--text-primary);
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
    </style>
</head>
<body>
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

<!-- 1. Pogo-style Flashy Star + Pyrox Splash Entry -->
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

<!-- 2. Full White Sign-Up Tab right after Splash (Email, Name, Password + Single Google button + Cross skip) -->
<div class="onboarding-signup-screen" id="onboardingSignupScreen">
    <div class="onboarding-top-row">
        <div style="display:flex;align-items:center;gap:8px;">
            <svg width="28" height="28" viewBox="0 0 100 100" fill="none">
                <path d="M50 4 C55 34, 66 45, 96 50 C66 55, 55 66, 50 96 C45 66, 34 55, 4 50 C34 45, 45 34, 50 4 Z" fill="url(#pyroxOuterGrad)" />
                <path d="M50 20 C53 40, 60 47, 80 50 C60 53, 53 60, 50 80 C47 60, 40 53, 20 50 C40 47, 47 40, 50 20 Z" fill="url(#pyroxMidGrad)" />
                <path d="M50 34 C51.5 44, 56 48.5, 66 50 C56 51.5, 51.5 56, 50 66 C48.5 56, 44 51.5, 34 50 C44 48.5, 48.5 44, 50 34 Z" fill="url(#pyroxCoreGrad)" />
            </svg>
            <span style="font-weight:800;font-size:1.1rem;color:#09090b;">Pyrox</span>
        </div>
        <button type="button" class="onboarding-cross-btn" onclick="skipOnboardingToWelcome()" aria-label="Skip sign up">✕</button>
    </div>

    <div class="onboarding-body">
        <div class="onboarding-title">Sign up to Pyrox</div>

        <label class="white-label" for="obEmail">Email</label>
        <input type="email" class="white-input" id="obEmail" placeholder="name@gmail.com" />

        <label class="white-label" for="obName">Name</label>
        <input type="text" class="white-input" id="obName" placeholder="Your name" />

        <label class="white-label" for="obPassword">Password</label>
        <input type="password" class="white-input" id="obPassword" placeholder="Create a password" />

        <button type="button" class="white-primary-btn" onclick="completeOnboardingForm()">Create account</button>

        <div class="white-or">or</div>

        <button type="button" class="white-google-btn" onclick="completeOnboardingGoogle()">
            <span>G</span>
            <span>Sign up with Google</span>
        </button>
    </div>

    <div style="text-align:center;font-size:0.78rem;color:#64748b;">
        Tap ✕ to continue with Swagatam welcome screen
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
                <span style="font-size:0.88rem;color:var(--text-secondary);cursor:pointer;" onclick="closeSidebar()">✕</span>
            </div>

            <div class="nav-item" onclick="newChat(); closeSidebar();">+ New Chat</div>
            <div class="nav-item" onclick="toggleLibraryFolders()">Library</div>
            <div class="library-folders" id="libraryFolders"></div>

            <div class="nav-item" onclick="activateImageModeBar(); closeSidebar();">
                <span>Images</span>
                <span class="quota-pill" id="sidebarImgQuota">2/2</span>
            </div>

            <div class="nav-item" onclick="openModal('videoModal'); closeSidebar();">
                <span>Video</span>
                <span class="quota-pill">Soon</span>
            </div>

            <div class="nav-item" onclick="toggleModelSublist()">Pyrox Only ▾</div>
            <div class="model-sublist" id="modelSublist">
                <div class="model-option active" id="optPyroxOnly" onclick="selectModelMode('Pyrox Only')">
                    <span>Pyrox Only</span>
                    <span>Active</span>
                </div>
                <div class="model-option" id="optProModel" onclick="openModal('upgradeModal'); closeSidebar();">
                    <span>Pro Model</span>
                    <span>Upgrade</span>
                </div>
            </div>
        </div>

        <div class="sidebar-footer">
            <div class="google-pill" id="googleAccountBtn" onclick="openModal('googleModal')">
                Continue with Google
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
                <button type="button" class="header-signup-btn" id="headerSignUpBtn" onclick="openModal('googleModal')">
                    Sign Up
                </button>
                <button type="button" class="upgrade-btn shine-active" id="upgradeBtn" onclick="openModal('upgradeModal')">
                    Upgrade
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
                    <div class="dots-item" onclick="openModal('libraryModal'); closeDotsMenu();">Library</div>
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
                <h1 id="greetingText">Swagatam! Namaste, main aapki aaj kaise madad kar sakta hoon?</h1>
            </div>
        </section>

        <footer class="bottom-dock" id="bottomDock" onclick="event.stopPropagation()">
            <div class="image-generating-strip" id="imageModeBanner">
                Image generation mode active — enter prompt to generate image
            </div>

            <div class="plus-menu" id="plusMenu">
                <button type="button" class="plus-big-btn" onclick="triggerFilePicker()">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                    </svg>
                    <span>File</span>
                </button>
                <button type="button" class="plus-big-btn" onclick="openCamera()">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                        <circle cx="12" cy="13" r="4"></circle>
                    </svg>
                    <span>Camera</span>
                </button>
                <button type="button" class="plus-big-btn" onclick="openModal('libraryModal')">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
                        <polyline points="2 17 12 22 22 17"></polyline>
                        <polyline points="2 12 12 17 22 12"></polyline>
                    </svg>
                    <span>Drive</span>
                </button>
                <div class="plus-small-grid">
                    <button type="button" class="plus-small-btn" onclick="activateImageModeBar(); closePlusMenu();">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                            <circle cx="8.5" cy="8.5" r="1.5"></circle>
                            <polyline points="21 15 16 10 5 21"></polyline>
                        </svg>
                        <span>Image Creation</span>
                    </button>
                    <button type="button" class="plus-small-btn" onclick="promptCanvasMode()">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 20h9"></path>
                            <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
                        </svg>
                        <span>Canvas</span>
                    </button>
                </div>
            </div>

            <input type="file" id="filePicker" accept="image/*,.pdf,.txt,.doc,.docx" style="display:none;" onchange="handleFileSelected(event)" />

            <div class="input-shell">
                <button type="button" class="icon-action-btn" id="plusBtn" onclick="togglePlusMenu(event)" title="More actions">+</button>

                <button type="button" class="icon-action-btn" id="micBtn" onclick="toggleDictation(event)" title="Voice input">
                    <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1">
                        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                        <line x1="12" y1="19" x2="12" y2="23"></line>
                    </svg>
                </button>

                <div class="freq-meter" id="freqMeter">
                    <div class="freq-bar"></div>
                    <div class="freq-bar"></div>
                    <div class="freq-bar"></div>
                    <div class="freq-bar"></div>
                    <div class="freq-bar"></div>
                    <div class="freq-bar"></div>
                    <div class="freq-bar"></div>
                    <div class="freq-bar"></div>
                    <div class="freq-bar"></div>
                    <div class="freq-bar"></div>
                    <div class="freq-bar"></div>
                    <div class="freq-bar"></div>
                    <div class="freq-bar"></div>
                    <div class="freq-bar"></div>
                    <div class="freq-bar"></div>
                    <div class="freq-bar"></div>
                    <div class="freq-bar"></div>
                    <div class="freq-bar"></div>
                </div>

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

<!-- Account / Sign-In Modal -->
<div class="overlay-modal" id="googleModal" onclick="closeModal('googleModal')">
    <div class="modal-box" onclick="event.stopPropagation()">
        <div class="modal-head">
            <span>Sign up for Pyrox</span>
            <button type="button" class="close-x" onclick="closeModal('googleModal')">✕</button>
        </div>

        <button type="button" class="google-big-btn" style="background-color:var(--bg-elevated);color:var(--text-primary);border-color:var(--border-user);" onclick="quickGoogleSignIn()">
            <span style="font-weight:900;">G</span>
            <span>Sign up with Google</span>
        </button>

        <div class="divider-or">or</div>

        <label class="field-label" for="googleEmailInput">Email</label>
        <input type="email" class="field-input" id="googleEmailInput" placeholder="you@gmail.com" />

        <label class="field-label" for="googleNameInput">Name</label>
        <input type="text" class="field-input" id="googleNameInput" placeholder="Your name" />

        <label class="field-label" for="googlePassInput">Password</label>
        <input type="password" class="field-input" id="googlePassInput" placeholder="Password" />

        <button type="button" class="action-btn" onclick="saveAccountForm()">Create account</button>
    </div>
</div>

<!-- Video Modal -->
<div class="overlay-modal" id="videoModal" onclick="closeModal('videoModal')">
    <div class="modal-box" onclick="event.stopPropagation()">
        <div class="modal-head">
            <span>Pyrox Video</span>
            <button type="button" class="close-x" onclick="closeModal('videoModal')">Close</button>
        </div>
        <p style="font-size:0.94rem;color:var(--text-secondary);line-height:1.55;">
            AI Video generation module ready hai—dedicated video API connect hote hi yahan se video banegi.
        </p>
    </div>
</div>

<!-- Settings Modal -->
<div class="overlay-modal" id="settingsModal" onclick="closeModal('settingsModal')">
    <div class="modal-box" onclick="event.stopPropagation()">
        <div class="modal-head">
            <span>Settings</span>
            <button type="button" class="close-x" onclick="closeModal('settingsModal')">Close</button>
        </div>
        <label class="field-label" for="customThemeInput">Custom Theme Name</label>
        <input type="text" class="field-input" id="customThemeInput" placeholder="e.g. Pyrox, Studio Dark" />
        <button type="button" class="action-btn" onclick="saveThemeName()">Save Theme Name</button>
        <button type="button" class="action-btn" id="ttsToggleBtn" onclick="toggleTtsPreference()">Voice Reply (TTS): On</button>
        <button type="button" class="action-btn" onclick="clearSavedFolders()">Clear Library Folders</button>
    </div>
</div>

<!-- Library Modal -->
<div class="overlay-modal" id="libraryModal" onclick="closeModal('libraryModal')">
    <div class="modal-box" onclick="event.stopPropagation()">
        <div class="modal-head">
            <span>Library Folders</span>
            <button type="button" class="close-x" onclick="closeModal('libraryModal')">Close</button>
        </div>
        <div id="libraryModalBody" style="display:flex;flex-direction:column;gap:8px;font-size:0.94rem;color:var(--text-secondary);">
            No chat folders created yet.
        </div>
    </div>
</div>

<!-- Single Pyrox Pro Upgrade Modal (₹800 crossed -> ₹139) -->
<div class="overlay-modal" id="upgradeModal" onclick="closeModal('upgradeModal')">
    <div class="modal-box" onclick="event.stopPropagation()">
        <div class="modal-head">
            <div style="display:flex;align-items:center;gap:8px;">
                <svg width="26" height="26" viewBox="0 0 100 100" fill="none">
                    <path d="M50 4 C55 34, 66 45, 96 50 C66 55, 55 66, 50 96 C45 66, 34 55, 4 50 C34 45, 45 34, 50 4 Z" fill="url(#pyroxOuterGrad)" />
                    <path d="M50 20 C53 40, 60 47, 80 50 C60 53, 53 60, 50 80 C47 60, 40 53, 20 50 C40 47, 47 40, 50 20 Z" fill="url(#pyroxMidGrad)" />
                    <path d="M50 34 C51.5 44, 56 48.5, 66 50 C56 51.5, 51.5 56, 50 66 C48.5 56, 44 51.5, 34 50 C44 48.5, 48.5 44, 50 34 Z" fill="url(#pyroxCoreGrad)" />
                </svg>
                <span>Upgrade to Pyrox Pro</span>
            </div>
            <button type="button" class="close-x" onclick="closeModal('upgradeModal')">✕</button>
        </div>

        <p style="font-size:0.9rem;color:var(--text-secondary);">
            Personalized AI for study, creation, and daily work
        </p>

        <table class="compare-table">
            <thead>
                <tr>
                    <th>Features</th>
                    <th>Free</th>
                    <th>Pro</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Core model (Pyrox Only)</td>
                    <td>✓</td>
                    <td>✓</td>
                </tr>
                <tr>
                    <td>Pyrox Pro Model access</td>
                    <td>—</td>
                    <td>✓</td>
                </tr>
                <tr>
                    <td>Extended image & video creation</td>
                    <td>—</td>
                    <td>✓</td>
                </tr>
                <tr>
                    <td>Higher daily question limit</td>
                    <td>—</td>
                    <td>✓</td>
                </tr>
                <tr>
                    <td>Saved folders & library</td>
                    <td>✓</td>
                    <td>✓</td>
                </tr>
            </tbody>
        </table>

        <div class="single-price-banner">
            <div>
                <div style="font-weight:800;font-size:1.02rem;">Pyrox Pro</div>
                <div style="font-size:0.8rem;color:var(--text-secondary);">Monthly access</div>
            </div>
            <div>
                <span class="old-price">₹800</span>
                <span class="new-price">₹139/mo</span>
            </div>
        </div>

        <button type="button" class="action-btn" style="background-color:var(--accent-upgrade);border-color:var(--accent-upgrade-border);color:#ffffff;font-size:1rem;" onclick="confirmUpgrade()">
            Upgrade to Pyrox Pro
        </button>
        <div id="upgradeStatusMsg" style="font-size:0.86rem;color:var(--text-secondary);"></div>
    </div>
</div>

<!-- 70% Screen Grey Bad Response Feedback Modal -->
<div class="overlay-modal" id="feedbackModal" onclick="closeModal('feedbackModal')">
    <div class="feedback-box" onclick="event.stopPropagation()">
        <div style="display:flex;flex-direction:column;gap:14px;">
            <div class="modal-head">
                <span>Feedback</span>
                <button type="button" class="close-x" onclick="closeModal('feedbackModal')">✕</button>
            </div>
            <p style="font-size:0.92rem;color:#d4d4d8;">
                Is response mein kya dikkat aayi? Select karo:
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
            <textarea id="feedbackCustomNote" class="field-input" rows="3" placeholder="Additional note (optional)..." style="background-color:#18181b;color:#f4f4f5;border-color:#52525b;"></textarea>
        </div>

        <button type="button" class="action-btn" style="background-color:#f4f4f5;color:#09090b;font-weight:800;font-size:0.98rem;" onclick="submitBadFeedback()">
            Submit
        </button>
    </div>
</div>

<!-- 75% Camera Sheet with Round Shutter Button -->
<div class="overlay-modal camera-sheet" id="cameraModal" onclick="closeCamera()">
    <div class="modal-box" onclick="event.stopPropagation()">
        <div class="modal-head">
            <span>Camera</span>
            <button type="button" class="close-x" onclick="closeCamera()">Close</button>
        </div>
        <div class="video-frame">
            <video id="cameraVideo" autoplay playsinline muted></video>
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
    const MONTHLY_FREE_IMAGE_LIMIT = 2;

    let chatStarted = false;
    let activeAbortController = null;
    let selectedModelMode = "Pyrox Only";
    let currentFacingMode = "environment";
    let cameraStream = null;
    let flashEnabled = false;
    let ttsEnabled = true;
    let pendingAttachmentDataUrl = null;
    let pendingAttachmentName = "";
    let activeFolderId = null;
    let latestAudioPlayer = null;
    let feedbackTargetSnippet = "";
    let imageModeActive = false;

    let recognition = null;
    let isDictating = false;
    let audioCtx = null;
    let analyser = null;
    let micStream = null;
    let freqAnimId = null;

    const MIC_SVG = `
        <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
            <line x1="12" y1="19" x2="12" y2="23"></line>
        </svg>
    `;

    function syncSystemTheme() {
        const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
        document.body.classList.toggle("light-mode", !prefersDark);
    }

    if (window.matchMedia) {
        window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", syncSystemTheme);
    }

    function isUserSignedUp() {
        return Boolean(localStorage.getItem("pyrox_signed_up"));
    }

    function syncHeaderSignUpVisibility() {
        const btn = document.getElementById("headerSignUpBtn");
        if (btn) {
            btn.classList.toggle("logged-in-hide", isUserSignedUp());
        }
    }

    function runSplashAndSignUpFlow() {
        const splash = document.getElementById("splashOverlay");
        const signupScreen = document.getElementById("onboardingSignupScreen");

        setTimeout(() => {
            splash.classList.add("done");
            setTimeout(() => {
                splash.style.display = "none";
                if (!isUserSignedUp() && !sessionStorage.getItem("pyrox_skipped_signup")) {
                    signupScreen.classList.add("show");
                }
            }, 340);
        }, 950);
    }

    function skipOnboardingToWelcome() {
        sessionStorage.setItem("pyrox_skipped_signup", "1");
        document.getElementById("onboardingSignupScreen").classList.remove("show");
        refreshGreeting();
    }

    function completeOnboardingGoogle() {
        const typed = document.getElementById("obName").value.trim();
        localStorage.setItem("pyrox_user_name", typed || "Harshit");
        localStorage.setItem("pyrox_signed_up", "1");
        document.getElementById("onboardingSignupScreen").classList.remove("show");
        syncHeaderSignUpVisibility();
        refreshGreeting();
    }

    function completeOnboardingForm() {
        const nameVal = document.getElementById("obName").value.trim();
        const emailVal = document.getElementById("obEmail").value.trim();
        if (nameVal) localStorage.setItem("pyrox_user_name", nameVal);
        if (emailVal) localStorage.setItem("pyrox_user_email", emailVal);
        localStorage.setItem("pyrox_signed_up", "1");
        document.getElementById("onboardingSignupScreen").classList.remove("show");
        syncHeaderSignUpVisibility();
        refreshGreeting();
    }

    function getMonthKey() {
        const now = new Date();
        return `${now.getFullYear()}-${now.getMonth() + 1}`;
    }

    function getMonthlyImageCount() {
        const data = JSON.parse(localStorage.getItem("pyrox_monthly_images") || "{}");
        if (data.month !== getMonthKey()) {
            return 0;
        }
        return Number(data.count || 0);
    }

    function incrementMonthlyImageCount() {
        const next = getMonthlyImageCount() + 1;
        localStorage.setItem(
            "pyrox_monthly_images",
            JSON.stringify({ month: getMonthKey(), count: next })
        );
        refreshImageQuotaUI();
        return next;
    }

    function isImageLockedThisMonth() {
        return getMonthlyImageCount() >= MONTHLY_FREE_IMAGE_LIMIT;
    }

    function refreshImageQuotaUI() {
        const remaining = Math.max(0, MONTHLY_FREE_IMAGE_LIMIT - getMonthlyImageCount());
        const pill = document.getElementById("sidebarImgQuota");
        if (pill) {
            pill.textContent = isImageLockedThisMonth() ? "🔒 Locked" : `${remaining}/2`;
        }
    }

    function activateImageModeBar() {
        if (isImageLockedThisMonth()) {
            const banner = document.getElementById("imageModeBanner");
            banner.textContent = "🔒 Is mahine ki 2 free images poori ho chuki hain. Agle mahine khulega.";
            banner.classList.add("show");
            return;
        }
        imageModeActive = true;
        const banner = document.getElementById("imageModeBanner");
        banner.textContent = "Image creation active — apna prompt likh kar send karein";
        banner.classList.add("show");
        document.getElementById("promptInput").focus();
    }

    function clearImageModeBar() {
        imageModeActive = false;
        const banner = document.getElementById("imageModeBanner");
        banner.classList.remove("show");
    }

    function getTodayKey() {
        const now = new Date();
        return `${now.getFullYear()}-${now.getMonth() + 1}-${now.getDate()}`;
    }

    function getUsageToday() {
        const saved = JSON.parse(localStorage.getItem("pyrox_daily_usage") || "{}");
        if (saved.date !== getTodayKey()) {
            return { total: 0, heavy: 0 };
        }
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
            banner.textContent = "Aaj ki 40 questions ki limit khatam ho chuki hai. Kal reset hogi.";
            banner.classList.add("show");
        } else if (isHeavyContext && curr.heavy >= CODING_DAILY_LIMIT) {
            banner.textContent = "Coding/heavy questions ki aaj ki 30 limit poori ho chuki hai. Kal reset hogi.";
            banner.classList.add("show");
        } else if (remNormal <= WARNING_REMAINING_THRESHOLD || (isHeavyContext && remHeavy <= WARNING_REMAINING_THRESHOLD)) {
            const rem = isHeavyContext ? Math.min(remNormal, remHeavy) : remNormal;
            banner.textContent = `Aaj ke sirf ${rem} questions bache hain. Limit kal reset hogi.`;
            banner.classList.add("show");
        } else if (!banner.dataset.searching) {
            banner.textContent = "";
            banner.classList.remove("show");
        }
    }

    function setSearchingBanner(active) {
        const banner = document.getElementById("statusStrip");
        if (active) {
            banner.dataset.searching = "1";
            banner.textContent = "Web searching...";
            banner.classList.add("show");
        } else {
            delete banner.dataset.searching;
            updateLimitWarningBanner();
        }
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
                ? `Swagatam ${name}! Namaste, main aapki aaj kaise madad kar sakta hoon?`
                : "Swagatam! Namaste, main aapki aaj kaise madad kar sakta hoon?";
        }
        const gBtn = document.getElementById("googleAccountBtn");
        gBtn.textContent = name ? `Google: ${name}` : "Continue with Google";
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

    function selectModelMode(mode) {
        selectedModelMode = mode;
        document.getElementById("optPyroxOnly").classList.toggle("active", mode === "Pyrox Only");
    }

    function openModal(id) {
        if (id === "libraryModal") renderLibraryModal();
        document.getElementById(id).classList.add("show");
    }

    function closeModal(id) {
        document.getElementById(id).classList.remove("show");
    }

    function quickGoogleSignIn() {
        const typedName = document.getElementById("googleNameInput").value.trim();
        localStorage.setItem("pyrox_user_name", typedName || "Harshit");
        localStorage.setItem("pyrox_signed_up", "1");
        syncHeaderSignUpVisibility();
        refreshGreeting();
        closeModal("googleModal");
    }

    function saveAccountForm() {
        const name = document.getElementById("googleNameInput").value.trim();
        const email = document.getElementById("googleEmailInput").value.trim();
        if (name) localStorage.setItem("pyrox_user_name", name);
        if (email) localStorage.setItem("pyrox_user_email", email);
        localStorage.setItem("pyrox_signed_up", "1");
        syncHeaderSignUpVisibility();
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
        document.getElementById("ttsToggleBtn").textContent = `Voice Reply (TTS): ${ttsEnabled ? "On" : "Off"}`;
    }

    function confirmUpgrade() {
        document.getElementById("upgradeStatusMsg").textContent = "Pyrox Pro (₹139/mo) selected. Ready for payment integration.";
    }

    function loadFolders() {
        return JSON.parse(localStorage.getItem("pyrox_folders") || "[]");
    }

    function saveFolders(folders) {
        localStorage.setItem("pyrox_folders", JSON.stringify(folders.slice(0, 25)));
    }

    function ensureFolderForPrompt(promptText) {
        const folders = loadFolders();
        if (!activeFolderId) {
            const folderTitle = (promptText || "New Chat").slice(0, 28);
            const newFolder = {
                id: "fld_" + Date.now(),
                title: folderTitle,
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
        folders.slice(0, 8).forEach((f) => {
            const chip = document.createElement("div");
            chip.className = "folder-chip";
            chip.textContent = f.title;
            chip.onclick = () => {
                openFolderInStage(f.id);
                closeSidebar();
            };
            box.appendChild(chip);
        });
    }

    function toggleLibraryFolders() {
        document.getElementById("libraryFolders").classList.toggle("show");
    }

    function openFolderInStage(folderId) {
        const folders = loadFolders();
        const target = folders.find((f) => f.id === folderId);
        if (!target) return;
        activeFolderId = target.id;
        const stage = document.getElementById("scrollStage");
        stage.innerHTML = "";
        chatStarted = true;
        document.getElementById("upgradeBtn").classList.remove("shine-active");
        target.items.forEach((m) => {
            if (m.role === "user") {
                const row = document.createElement("div");
                row.className = "msg-row msg-user";
                row.textContent = m.content;
                stage.appendChild(row);
            } else {
                appendAIMessage(marked.parse(m.content), m.content, "");
            }
        });
        stage.scrollTop = stage.scrollHeight;
    }

    function renderLibraryModal() {
        const body = document.getElementById("libraryModalBody");
        const folders = loadFolders();
        if (!folders.length) {
            body.textContent = "No chat folders created yet.";
            return;
        }
        body.innerHTML = "";
        folders.forEach((f) => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "action-btn";
            btn.style.textAlign = "left";
            btn.textContent = `${f.title} (${f.items.length} messages)`;
            btn.onclick = () => {
                openFolderInStage(f.id);
                closeModal("libraryModal");
            };
            body.appendChild(btn);
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
        clearImageModeBar();
        activeFolderId = null;
        pendingAttachmentDataUrl = null;
        pendingAttachmentName = "";
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
            </div>
        `;
        refreshGreeting();
        chatStarted = false;
        document.getElementById("upgradeBtn").classList.add("shine-active");
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
            pendingAttachmentDataUrl = reader.result;
            const input = document.getElementById("promptInput");
            input.value = `${input.value ? input.value + " " : ""}[Attached: ${file.name}]`;
            input.focus();
        };
        reader.readAsDataURL(file);
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
        try {
            cameraStream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: currentFacingMode },
                audio: false,
            });
            document.getElementById("cameraVideo").srcObject = cameraStream;
        } catch (_) {
            alert("Camera access unavailable or denied.");
        }
    }

    function stopCameraStream() {
        if (cameraStream) {
            cameraStream.getTracks().forEach((t) => t.stop());
            cameraStream = null;
        }
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
            const caps = track.getCapabilities ? track.getCapabilities() : {};
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
        if (!video.videoWidth) return;
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext("2d").drawImage(video, 0, 0);
        pendingAttachmentDataUrl = canvas.toDataURL("image/png");
        pendingAttachmentName = "camera_photo.png";
        const input = document.getElementById("promptInput");
        input.value = `${input.value ? input.value + " " : ""}[Photo captured]`;
        closeCamera();
        input.focus();
    }

    async function startVoiceMeter() {
        const meter = document.getElementById("freqMeter");
        const inputEl = document.getElementById("promptInput");
        const bars = meter.querySelectorAll(".freq-bar");
        inputEl.classList.add("hidden-while-speaking");
        meter.classList.add("visible");

        try {
            micStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            audioCtx = new AudioCtx();
            const src = audioCtx.createMediaStreamSource(micStream);
            analyser = audioCtx.createAnalyser();
            analyser.fftSize = 64;
            src.connect(analyser);

            const arr = new Uint8Array(analyser.frequencyBinCount);
            const step = () => {
                if (!isDictating || !analyser) return;
                analyser.getByteFrequencyData(arr);
                for (let i = 0; i < bars.length; i++) {
                    const v = arr[i] || 0;
                    const h = v > 30 ? Math.max(4, Math.min(32, Math.round((v / 255) * 32))) : 3;
                    bars[i].style.height = `${h}px`;
                }
                freqAnimId = requestAnimationFrame(step);
            };
            freqAnimId = requestAnimationFrame(step);
        } catch (_) {
            bars.forEach((b) => (b.style.height = "3px"));
        }
    }

    function stopVoiceMeter() {
        if (freqAnimId) cancelAnimationFrame(freqAnimId);
        freqAnimId = null;
        if (micStream) {
            micStream.getTracks().forEach((t) => t.stop());
            micStream = null;
        }
        if (audioCtx) {
            audioCtx.close().catch(() => {});
            audioCtx = null;
        }
        const meter = document.getElementById("freqMeter");
        const inputEl = document.getElementById("promptInput");
        meter.classList.remove("visible");
        inputEl.classList.remove("hidden-while-speaking");
        meter.querySelectorAll(".freq-bar").forEach((b) => (b.style.height = "3px"));
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
            stopDictationManual();
            return;
        }

        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) {
            alert("Browser speech recognition not supported.");
            return;
        }

        recognition = new SR();
        recognition.lang = "hi-IN";
        recognition.continuous = true;
        recognition.interimResults = true;

        const baseText = document.getElementById("promptInput").value;
        let finalText = "";

        recognition.onstart = async () => {
            isDictating = true;
            setMicButtonAsStopSquare(true);
            await startVoiceMeter();
        };

        recognition.onresult = (event) => {
            let interim = "";
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const seg = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalText += seg + " ";
                } else {
                    interim += seg;
                }
            }
            document.getElementById("promptInput").value =
                `${baseText}${baseText ? " " : ""}${finalText}${interim}`.trim();
        };

        recognition.onerror = () => {
            stopDictationManual();
        };

        recognition.onend = () => {
            isDictating = false;
            setMicButtonAsStopSquare(false);
            stopVoiceMeter();
        };

        recognition.start();
    }

    function stopDictationManual() {
        isDictating = false;
        setMicButtonAsStopSquare(false);
        if (recognition) {
            try {
                recognition.stop();
            } catch (_) {}
            recognition = null;
        }
        stopVoiceMeter();
    }

    function markChatStarted() {
        if (!chatStarted) {
            chatStarted = true;
            const g = document.getElementById("greetingBox");
            if (g) g.remove();
            document.getElementById("upgradeBtn").classList.remove("shine-active");
        }
    }

    function appendUserMessage(text, imgUrl) {
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
        const span = document.createElement("div");
        span.textContent = text;
        row.appendChild(span);
        stage.appendChild(row);
        stage.scrollTop = stage.scrollHeight;
    }

    async function speakTextOnDemand(text, btnEl) {
        if (!text) return;
        btnEl.classList.add("selected-act");
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
                latestAudioPlayer.onended = () => btnEl.classList.remove("selected-act");
                latestAudioPlayer.play().catch(() => btnEl.classList.remove("selected-act"));
            } else {
                btnEl.classList.remove("selected-act");
            }
        } catch (_) {
            btnEl.classList.remove("selected-act");
        }
    }

    // Symbol-only response controls: Like, Dislike, Cycle/Redo, Listen/Audio, Copy, Share
    function buildResponseActionsBar(plainText, originalPrompt) {
        const bar = document.createElement("div");
        bar.className = "msg-actions";

        const likeBtn = document.createElement("button");
        likeBtn.type = "button";
        likeBtn.className = "icon-symbol-btn";
        likeBtn.title = "Good";
        likeBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3z"></path>
                <path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
            </svg>
        `;

        const dislikeBtn = document.createElement("button");
        dislikeBtn.type = "button";
        dislikeBtn.className = "icon-symbol-btn";
        dislikeBtn.title = "Bad";
        dislikeBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3z"></path>
                <path d="M17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path>
            </svg>
        `;

        likeBtn.onclick = () => {
            likeBtn.classList.add("selected-act");
            dislikeBtn.classList.remove("selected-act");
        };

        dislikeBtn.onclick = () => {
            dislikeBtn.classList.add("selected-act");
            likeBtn.classList.remove("selected-act");
            feedbackTargetSnippet = plainText.slice(0, 200);
            openModal("feedbackModal");
        };

        const cycleBtn = document.createElement("button");
        cycleBtn.type = "button";
        cycleBtn.className = "icon-symbol-btn";
        cycleBtn.title = "Regenerate";
        cycleBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="23 4 23 10 17 10"></polyline>
                <polyline points="1 20 1 14 7 14"></polyline>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
            </svg>
        `;
        cycleBtn.onclick = () => {
            if (originalPrompt) {
                document.getElementById("promptInput").value = originalPrompt;
                sendMessage();
            }
        };

        const listenBtn = document.createElement("button");
        listenBtn.type = "button";
        listenBtn.className = "icon-symbol-btn";
        listenBtn.title = "Listen";
        listenBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
        `;
        copyBtn.onclick = () => {
            navigator.clipboard.writeText(plainText).catch(() => {});
            copyBtn.classList.add("selected-act");
            setTimeout(() => copyBtn.classList.remove("selected-act"), 1000);
        };

        const shareBtn = document.createElement("button");
        shareBtn.type = "button";
        shareBtn.className = "icon-symbol-btn";
        shareBtn.title = "Share / Export";
        shareBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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

        document.querySelectorAll("#feedbackReasonsGrid .reason-chip").forEach((c) => c.classList.remove("active"));
        document.getElementById("feedbackCustomNote").value = "";
        closeModal("feedbackModal");
    }

    function playAudioFromUrl(url) {
        if (!ttsEnabled || !url) return;
        if (latestAudioPlayer) {
            latestAudioPlayer.pause();
        }
        latestAudioPlayer = new Audio(url);
        latestAudioPlayer.play().catch(() => {});
    }

    function setGeneratingState(generating) {
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

    function detectImageGenerationIntent(text) {
        const lower = text.toLowerCase().trim();
        if (imageModeActive) {
            return { isImage: true, prompt: text };
        }
        if (lower.startsWith("/image ")) {
            return { isImage: true, prompt: text.slice(7).trim() };
        }
        const imagePatterns = [
            /\b(generate|create|make|draw)\s+(an?\s+)?(image|photo|picture|pic|art|wallpaper)\b/i,
            /\b(image|photo|picture|tasveer)\s+(bana|banao|banade|bana\s*do|bana\s*de|generate|create)\b/i,
        ];
        if (imagePatterns.some((rx) => rx.test(text))) {
            return { isImage: true, prompt: text };
        }
        return { isImage: false, prompt: text };
    }

    async function sendMessage() {
        if (isDictating) {
            stopDictationManual();
        }

        const input = document.getElementById("promptInput");
        const raw = input.value.trim();
        if (!raw && !pendingAttachmentDataUrl) return;

        const messageToSend = raw || `Please check ${pendingAttachmentName || "this image"}`;
        const isHeavy = detectHeavyCodingIntent(messageToSend);

        if (isDailyLimitReached(isHeavy)) {
            updateLimitWarningBanner(isHeavy);
            return;
        }

        const wasImageMode = imageModeActive;
        clearImageModeBar();

        const attachmentToSend = pendingAttachmentDataUrl;
        pendingAttachmentDataUrl = null;
        pendingAttachmentName = "";

        input.value = "";
        input.blur();
        input.focus();

        ensureFolderForPrompt(messageToSend);
        appendUserMessage(messageToSend, attachmentToSend);
        appendItemToActiveFolder("user", messageToSend);
        recordQuestionUsage(isHeavy);

        const { row, bodyDiv } = appendAIMessage(
            `<div class="thinking-dots"><span></span><span></span></div>`,
            "",
            messageToSend
        );

        activeAbortController = new AbortController();
        setGeneratingState(true);

        const imgIntent = detectImageGenerationIntent(messageToSend);
        const searchLikely =
            !imgIntent.isImage &&
            /\b(aaj|kal|today|tomorrow|news|latest|festival|tyohar|weather|2026|2027|kab hai|kya chal raha)\b/i.test(
                messageToSend
            );

        if (searchLikely) {
            setSearchingBanner(true);
        }

        try {
            if (imgIntent.isImage || wasImageMode) {
                if (isImageLockedThisMonth()) {
                    bodyDiv.textContent =
                        "🔒 Is mahine ki 2 free images poori ho chuki hain. Agle mahine phir se khul jaayega.";
                } else {
                    const res = await fetch("/api/generate-image", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ prompt: imgIntent.prompt || messageToSend }),
                        signal: activeAbortController.signal,
                    });
                    const data = await res.json();
                    if (!res.ok) {
                        bodyDiv.textContent = data.detail || "Image generation failed.";
                    } else {
                        incrementMonthlyImageCount();
                        bodyDiv.innerHTML = `<img src="${data.image_data}" alt="${imgIntent.prompt || messageToSend}" />`;
                        row.appendChild(
                            buildResponseActionsBar(
                                `Generated image: ${imgIntent.prompt || messageToSend}`,
                                messageToSend
                            )
                        );
                        appendItemToActiveFolder("ai", `[Generated Image: ${imgIntent.prompt || messageToSend}]`);
                    }
                }
            } else {
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
                    }),
                    signal: activeAbortController.signal,
                });
                const data = await res.json();
                if (!res.ok) {
                    bodyDiv.textContent = data.detail || "Request failed.";
                } else {
                    const reply = data.reply || "";
                    bodyDiv.innerHTML = marked.parse(reply);
                    row.appendChild(buildResponseActionsBar(reply, messageToSend));
                    appendItemToActiveFolder("ai", reply);
                    if (data.audio_url) {
                        playAudioFromUrl(data.audio_url);
                    }
                }
            }
        } catch (err) {
            if (err.name === "AbortError") {
                bodyDiv.textContent = "Stopped.";
            } else {
                bodyDiv.textContent = "Connection error.";
            }
        } finally {
            activeAbortController = null;
            setSearchingBanner(false);
            setGeneratingState(false);
            const stage = document.getElementById("scrollStage");
            stage.scrollTop = stage.scrollHeight;
        }
    }

    syncSystemTheme();
    syncHeaderSignUpVisibility();
    runSplashAndSignUpFlow();
    refreshGreeting();
    refreshThemeLabel();
    renderLibraryFolders();
    refreshImageQuotaUI();
    updateLimitWarningBanner();
</script>
</body>
</html>
"""
    return html
