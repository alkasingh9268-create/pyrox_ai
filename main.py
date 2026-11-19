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
        communicate = edge_tts.Communicate(cleaned[:550], voice_name, rate="+20%")
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
        if req.image_data_url and not "vision" in model_id.lower():
            effective_prompt = (
                f"{effective_prompt}\n[Note: User attached an image from camera/file. "
                "If image pixels are not passed directly to text-only model, politely let the user know "
                "you received the attachment note and ask what specific detail they want help with.]"
            )

        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": effective_prompt},
            ],
            "temperature": 0.65,
            "max_tokens": 200 if short_mode else 650,
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


@app.post("/api/generate-image")
async def generate_image_endpoint(req: ImageRequest):
    if not HF_API_KEY:
        return JSONResponse(
            status_code=400,
            content={
                "detail": "HF_API_KEY missing in environment variables. Set HF_API_KEY first."
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
        resp = requests.post(router_url, headers=headers, json=body, timeout=60)
        if resp.status_code == 404:
            resp = requests.post(legacy_url, headers=headers, json=body, timeout=60)

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
            --bg-surface: #111114;
            --bg-elevated: #18181d;
            --border-subtle: #27272a;
            --border-user: #52525b;
            --text-primary: #f4f4f5;
            --text-secondary: #b4b4bc;
            --text-muted: #71717a;
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
            --text-secondary: #334155;
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
            z-index: 500;
            overflow: hidden;
            transition: opacity 0.35s ease, transform 0.35s ease;
        }

        .splash-overlay.done {
            opacity: 0;
            transform: scale(1.06);
            pointer-events: none;
        }

        .splash-stage {
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
        }

        .splash-star-wrap {
            z-index: 3;
            animation: pogoStarPop 0.78s cubic-bezier(0.22, 1.45, 0.36, 1) forwards;
        }

        .splash-word-flash {
            font-size: 2.35rem;
            font-weight: 800;
            letter-spacing: 0.6px;
            color: var(--text-primary);
            opacity: 0;
            transform: translateX(-28px) skewX(-12deg);
            animation: flashRevealPyrox 0.78s cubic-bezier(0.16, 1, 0.3, 1) 0.14s forwards;
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
                transform: translateX(-30px) skewX(-16deg);
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

        .app-shell {
            display: flex;
            height: 100dvh;
            width: 100%;
            position: relative;
            overflow: hidden;
        }

        /* Expandable Sidebar (~40% width on mobile) */
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
            width: 40vw;
            min-width: 175px;
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
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--text-primary);
            padding: 4px 8px 10px 8px;
            border-bottom: 1px solid var(--border-subtle);
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 6px;
        }

        .nav-item {
            padding: 12px 11px;
            border-radius: 10px;
            font-size: 0.98rem;
            font-weight: 600;
            color: var(--text-primary);
            cursor: pointer;
            display: flex;
            align-items: center;
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
            padding: 9px 10px;
            border-radius: 8px;
            font-size: 0.88rem;
            color: var(--text-secondary);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .model-option.active {
            background-color: var(--bg-elevated);
            color: var(--text-primary);
            font-weight: 600;
        }

        .library-folders {
            display: none;
            flex-direction: column;
            gap: 6px;
            margin-top: 4px;
            padding-left: 6px;
        }

        .library-folders.show {
            display: flex;
        }

        .folder-chip {
            padding: 8px 10px;
            font-size: 0.84rem;
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
            padding: 10px 10px;
            border-radius: 10px;
            border: 1px solid var(--border-subtle);
            background-color: var(--bg-elevated);
            font-size: 0.88rem;
            font-weight: 600;
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
            height: 56px;
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
            gap: 8px;
            min-height: 36px;
            min-width: 0;
        }

        .menu-toggle-btn {
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

        .brand-title-wrap {
            display: flex;
            align-items: center;
            gap: 7px;
            min-width: 0;
        }

        .brand-heading {
            font-size: 1.05rem;
            font-weight: 700;
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

        /* Upgrade button: entry shine before chat starts, stops once chat starts */
        .upgrade-btn {
            position: relative;
            overflow: hidden;
            background-color: var(--accent-upgrade);
            color: #ffffff;
            border: 1px solid var(--accent-upgrade-border);
            border-radius: 14px 4px 14px 4px;
            padding: 7px 12px;
            font-size: 0.82rem;
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
            width: 34px;
            height: 34px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
        }

        .dots-menu {
            position: absolute;
            top: 42px;
            right: 0;
            width: 190px;
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
            font-size: 0.9rem;
            color: var(--text-primary);
            cursor: pointer;
        }

        .dots-item:hover {
            background-color: var(--bg-elevated);
        }

        /* Status banner for Web Search or Limit Warning */
        .status-strip {
            display: none;
            padding: 6px 14px;
            font-size: 0.84rem;
            font-weight: 600;
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
            padding: 16px 14px;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }

        .greeting-center {
            margin: auto;
            text-align: center;
            max-width: 540px;
            padding: 20px 10px;
        }

        .greeting-center h1 {
            font-size: 1.55rem;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1.38;
        }

        .msg-row {
            display: flex;
            flex-direction: column;
            max-width: 88%;
            gap: 8px;
        }

        .msg-user {
            align-self: flex-end;
            background-color: var(--bg-elevated);
            color: var(--text-primary);
            border: 1px solid var(--border-user);
            border-radius: 14px 14px 4px 14px;
            padding: 11px 15px;
            font-size: 1rem;
            line-height: 1.55;
            word-break: break-word;
        }

        .msg-ai {
            align-self: flex-start;
            width: 100%;
            max-width: 100%;
            color: var(--text-primary);
            font-size: 1.02rem;
            line-height: 1.65;
            padding: 4px 2px;
        }

        .msg-ai p {
            margin-bottom: 8px;
        }

        .msg-ai ul, .msg-ai ol {
            padding-left: 20px;
            margin: 6px 0 10px 0;
        }

        .msg-ai li {
            margin-bottom: 5px;
        }

        .msg-ai img {
            max-width: 100%;
            max-height: 360px;
            border-radius: 12px;
            border: 1px solid var(--border-subtle);
            margin-top: 6px;
        }

        .msg-actions {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 2px;
        }

        .mini-action-btn {
            background-color: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            color: var(--text-secondary);
            border-radius: 8px;
            padding: 4px 10px;
            font-size: 0.78rem;
            font-weight: 600;
            cursor: pointer;
        }

        .mini-action-btn:hover {
            color: var(--text-primary);
        }

        /* Two-dot thinking indicator */
        .thinking-dots {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 6px 2px;
        }

        .thinking-dots span {
            width: 9px;
            height: 9px;
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

        /* Bottom Dock - Large & clean for mobile */
        .bottom-dock {
            flex-shrink: 0;
            width: 100%;
            padding: 8px 10px 10px 10px;
            background-color: var(--bg-main);
            border-top: 1px solid var(--border-subtle);
            position: relative;
            z-index: 30;
        }

        .plus-menu {
            position: absolute;
            bottom: 82px;
            left: 12px;
            width: 268px;
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
            font-size: 0.96rem;
            font-weight: 600;
            cursor: pointer;
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
            padding: 8px 6px;
            border-radius: 8px;
            background-color: var(--bg-main);
            border: 1px solid var(--border-subtle);
            color: var(--text-secondary);
            font-size: 0.78rem;
            font-weight: 600;
            cursor: pointer;
            text-align: center;
        }

        .plus-small-btn:hover {
            color: var(--text-primary);
        }

        .input-shell {
            display: flex;
            align-items: center;
            gap: 8px;
            min-height: 62px;
            background-color: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: 24px;
            padding: 8px 10px;
        }

        .icon-action-btn {
            width: 42px;
            height: 42px;
            border-radius: 13px;
            border: 1px solid var(--border-subtle);
            background-color: var(--bg-elevated);
            color: var(--text-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            flex-shrink: 0;
            font-size: 1.15rem;
            transition: transform 0.18s ease;
        }

        .icon-action-btn.open-minus {
            transform: rotate(90deg);
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
            font-size: 1.02rem;
            resize: none;
            padding: 9px 4px;
            line-height: 1.38;
        }

        /* Silent-until-voice frequency bars */
        .freq-meter {
            display: none;
            align-items: center;
            gap: 3px;
            height: 30px;
            padding: 0 4px;
        }

        .freq-meter.visible {
            display: flex;
        }

        .freq-bar {
            width: 3px;
            height: 3px;
            border-radius: 2px;
            background-color: var(--text-primary);
            transition: height 0.07s linear;
        }

        .stop-dict-btn {
            display: none;
            align-items: center;
            justify-content: center;
            padding: 7px 10px;
            border-radius: 10px;
            border: 1px solid var(--border-user);
            background-color: var(--bg-elevated);
            color: var(--text-primary);
            font-size: 0.78rem;
            font-weight: 700;
            cursor: pointer;
        }

        .stop-dict-btn.visible {
            display: inline-flex;
        }

        .send-btn, .stop-btn {
            width: 44px;
            height: 44px;
            border-radius: 15px;
            border: none;
            background-color: var(--text-primary);
            color: var(--bg-main);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            flex-shrink: 0;
            font-size: 1.25rem;
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
            max-width: 450px;
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

        .camera-sheet .modal-box {
            max-width: 640px;
            height: 75dvh;
            border-radius: 22px 22px 0 0;
        }

        .modal-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-weight: 700;
            font-size: 1.05rem;
        }

        .close-x {
            background: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            color: var(--text-primary);
            border-radius: 8px;
            padding: 5px 10px;
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 600;
        }

        /* GitHub-inspired Sign-Up modal with larger Continue with Google button */
        .google-big-btn {
            width: 100%;
            padding: 14px 16px;
            border-radius: 12px;
            border: 1px solid var(--border-user);
            background-color: var(--bg-elevated);
            color: var(--text-primary);
            font-size: 1.04rem;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }

        .google-big-btn:hover {
            border-color: var(--accent-upgrade-border);
        }

        .divider-or {
            text-align: center;
            font-size: 0.82rem;
            color: var(--text-muted);
            margin: 2px 0;
        }

        .field-label {
            font-size: 0.84rem;
            font-weight: 600;
            color: var(--text-secondary);
        }

        .field-input {
            width: 100%;
            background-color: var(--bg-main);
            border: 1px solid var(--border-subtle);
            color: var(--text-primary);
            border-radius: 10px;
            padding: 10px 12px;
            font-size: 0.94rem;
            outline: none;
        }

        .action-btn {
            background-color: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            color: var(--text-primary);
            border-radius: 10px;
            padding: 11px 13px;
            font-size: 0.92rem;
            font-weight: 600;
            cursor: pointer;
        }

        /* ChatGPT-style Upgrade Feature Comparison Modal */
        .compare-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.88rem;
        }

        .compare-table th,
        .compare-table td {
            padding: 9px 6px;
            border-bottom: 1px solid var(--border-subtle);
            text-align: left;
        }

        .compare-table th:nth-child(2),
        .compare-table td:nth-child(2),
        .compare-table th:nth-child(3),
        .compare-table td:nth-child(3) {
            text-align: center;
            width: 64px;
        }

        .plan-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        }

        .plan-card {
            border: 1px solid var(--border-subtle);
            background-color: var(--bg-elevated);
            border-radius: 12px;
            padding: 11px;
            cursor: pointer;
        }

        .plan-card.selected {
            border-color: var(--accent-upgrade-border);
        }

        /* Camera sheet with round shutter button */
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
            width: 58px;
            height: 58px;
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
            width: 42px;
            height: 42px;
            border-radius: 50%;
            background-color: var(--text-primary);
        }
    </style>
</head>
<body>
<!-- Pogo-style Flashy Star + Pyrox Splash Entry -->
<div class="splash-overlay" id="splashOverlay">
    <div class="splash-stage">
        <div class="splash-star-wrap">
            <svg width="46" height="46" viewBox="0 0 100 100" fill="none">
                <polygon points="50,6 63,36 95,39 71,60 78,92 50,75 22,92 29,60 5,39 37,36" stroke="#ef4444" stroke-width="5" fill="rgba(239,68,68,0.12)"/>
                <polygon points="50,20 59,41 81,43 64,58 69,80 50,68 31,80 36,58 19,43 41,41" stroke="#3b82f6" stroke-width="4" fill="rgba(59,130,246,0.14)"/>
                <polygon points="50,33 56,47 70,48 59,58 62,72 50,64 38,72 41,58 30,48 44,47" stroke="#1d4ed8" stroke-width="3" fill="#60a5fa"/>
            </svg>
        </div>
        <div class="splash-word-flash" id="splashWord">Pyrox</div>
    </div>
</div>

<div class="app-shell" id="appShell">
    <aside class="sidebar" id="sidebar" onclick="event.stopPropagation()">
        <div class="sidebar-top">
            <div class="sidebar-title">
                <span id="sidebarThemeTitle">Pyrox</span>
                <span style="font-size:0.82rem;color:var(--text-secondary);cursor:pointer;" onclick="closeSidebar()">✕</span>
            </div>

            <div class="nav-item" onclick="newChat(); closeSidebar();">+ New Chat</div>
            <div class="nav-item" onclick="toggleLibraryFolders()">Library</div>
            <div class="library-folders" id="libraryFolders"></div>

            <div class="nav-item" onclick="toggleModelSublist()">Pyrox Only ▾</div>
            <div class="model-sublist" id="modelSublist">
                <div class="model-option active" id="optPyroxOnly" onclick="selectModelMode('Pyrox Only')">
                    <span>Pyrox Only</span>
                    <span>Active</span>
                </div>
                <div class="model-option" id="optProModel" onclick="selectModelMode('Pro Model')">
                    <span>Pro Model</span>
                    <span>Soon</span>
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
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                        <line x1="3" y1="6" x2="21" y2="6"></line>
                        <line x1="3" y1="12" x2="21" y2="12"></line>
                        <line x1="3" y1="18" x2="21" y2="18"></line>
                    </svg>
                </button>

                <div class="brand-title-wrap">
                    <svg width="24" height="24" viewBox="0 0 100 100" fill="none">
                        <polygon points="50,6 63,36 95,39 71,60 78,92 50,75 22,92 29,60 5,39 37,36" stroke="#ef4444" stroke-width="6"/>
                        <polygon points="50,21 59,41 81,43 64,58 69,80 50,68 31,80 36,58 19,43 41,41" stroke="#3b82f6" stroke-width="5"/>
                        <polygon points="50,34 56,47 70,48 59,58 62,72 50,64 38,72 41,58 30,48 44,47" stroke="#60a5fa" stroke-width="4" fill="#60a5fa"/>
                    </svg>
                    <span class="brand-heading" id="headerBrandTitle">Pyrox</span>
                </div>
            </div>

            <div class="top-right" onclick="event.stopPropagation()">
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
                <h1 id="greetingText">Namaste, main aapki aaj kaise madad kar sakta hoon?</h1>
            </div>
        </section>

        <footer class="bottom-dock" id="bottomDock" onclick="event.stopPropagation()">
            <div class="plus-menu" id="plusMenu">
                <button type="button" class="plus-big-btn" onclick="triggerFilePicker()">File</button>
                <button type="button" class="plus-big-btn" onclick="openCamera()">Camera</button>
                <button type="button" class="plus-big-btn" onclick="openModal('libraryModal')">Drive</button>
                <div class="plus-small-grid">
                    <button type="button" class="plus-small-btn" onclick="promptImageCreation()">Image Creation</button>
                    <button type="button" class="plus-small-btn" onclick="promptCanvasMode()">Canvas</button>
                </div>
            </div>

            <input type="file" id="filePicker" accept="image/*,.pdf,.txt,.doc,.docx" style="display:none;" onchange="handleFileSelected(event)" />

            <div class="input-shell">
                <button type="button" class="icon-action-btn" id="plusBtn" onclick="togglePlusMenu(event)" title="More actions">+</button>

                <button type="button" class="icon-action-btn" id="micBtn" onclick="toggleDictation(event)" title="Voice input">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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
                </div>

                <button type="button" class="stop-dict-btn" id="stopDictBtn" onclick="stopDictationManual()">Stop</button>

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
        </footer>
    </main>
</div>

<!-- GitHub-inspired Sign-Up Modal with Large Continue with Google -->
<div class="overlay-modal" id="googleModal" onclick="closeModal('googleModal')">
    <div class="modal-box" onclick="event.stopPropagation()">
        <div class="modal-head">
            <span>Sign up for Pyrox</span>
            <button type="button" class="close-x" onclick="closeModal('googleModal')">✕</button>
        </div>

        <button type="button" class="google-big-btn" onclick="quickGoogleSignIn()">
            <span>G</span>
            <span>Continue with Google</span>
        </button>

        <div class="divider-or">or</div>

        <label class="field-label" for="googleEmailInput">Email</label>
        <input type="email" class="field-input" id="googleEmailInput" placeholder="you@gmail.com" />

        <label class="field-label" for="googleNameInput">Username / Name</label>
        <input type="text" class="field-input" id="googleNameInput" placeholder="Your name" />

        <label class="field-label" for="googlePassInput">Password</label>
        <input type="password" class="field-input" id="googlePassInput" placeholder="Password" />

        <button type="button" class="action-btn" onclick="saveAccountForm()">Create account</button>
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
        <input type="text" class="field-input" id="customThemeInput" placeholder="e.g. Pyrox Dark, Studio White" />
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
        <div id="libraryModalBody" style="display:flex;flex-direction:column;gap:8px;font-size:0.9rem;color:var(--text-secondary);">
            No chat folders created yet.
        </div>
    </div>
</div>

<!-- ChatGPT-style Upgrade Modal -->
<div class="overlay-modal" id="upgradeModal" onclick="closeModal('upgradeModal')">
    <div class="modal-box" onclick="event.stopPropagation()">
        <div class="modal-head">
            <span>Upgrade Pyrox</span>
            <button type="button" class="close-x" onclick="closeModal('upgradeModal')">✕</button>
        </div>
        <p style="font-size:0.86rem;color:var(--text-secondary);">
            Student-friendly plans (₹79–₹149) for extended access and perks.
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
                    <td>Fast core model & daily limit</td>
                    <td>✓</td>
                    <td>✓</td>
                </tr>
                <tr>
                    <td>Higher image creation quota</td>
                    <td>—</td>
                    <td>✓</td>
                </tr>
                <tr>
                    <td>Pro Model & priority tools</td>
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

        <div class="plan-row">
            <div class="plan-card selected" id="planStarter" onclick="selectPlan('₹79 / month')">
                <div style="font-weight:700;">Starter</div>
                <div style="font-size:1rem;margin-top:3px;">₹79 / mo</div>
            </div>
            <div class="plan-card" id="planPlus" onclick="selectPlan('₹149 / month')">
                <div style="font-weight:700;">Pro</div>
                <div style="font-size:1rem;margin-top:3px;">₹149 / mo</div>
            </div>
        </div>

        <button type="button" class="action-btn" style="background-color:var(--accent-upgrade);border-color:var(--accent-upgrade-border);color:#ffffff;" onclick="confirmUpgrade()">
            Upgrade Plan
        </button>
        <div id="upgradeStatusMsg" style="font-size:0.84rem;color:var(--text-secondary);"></div>
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
    const DAILY_QUESTION_LIMIT = 40;
    const WARNING_REMAINING_THRESHOLD = 5;

    let chatStarted = false;
    let activeAbortController = null;
    let selectedPlan = "₹79 / month";
    let selectedModelMode = "Pyrox Only";
    let currentFacingMode = "environment";
    let cameraStream = null;
    let flashEnabled = false;
    let ttsEnabled = true;
    let pendingAttachmentDataUrl = null;
    let pendingAttachmentName = "";
    let activeFolderId = null;
    let latestAudioPlayer = null;

    let recognition = null;
    let isDictating = false;
    let audioCtx = null;
    let analyser = null;
    let micStream = null;
    let freqAnimId = null;

    // Sync theme strictly with system dark/light preference
    function syncSystemTheme() {
        const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
        document.body.classList.toggle("light-mode", !prefersDark);
    }

    if (window.matchMedia) {
        window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", syncSystemTheme);
    }

    function runSplashEntry() {
        const splash = document.getElementById("splashOverlay");
        setTimeout(() => {
            splash.classList.add("done");
            setTimeout(() => {
                splash.style.display = "none";
            }, 380);
        }, 980);
    }

    function getTodayKey() {
        const now = new Date();
        return `${now.getFullYear()}-${now.getMonth() + 1}-${now.getDate()}`;
    }

    function getUsedQuestionsToday() {
        const saved = JSON.parse(localStorage.getItem("pyrox_daily_usage") || "{}");
        if (saved.date !== getTodayKey()) {
            return 0;
        }
        return Number(saved.count || 0);
    }

    function incrementUsedQuestionsToday() {
        const nextCount = getUsedQuestionsToday() + 1;
        localStorage.setItem(
            "pyrox_daily_usage",
            JSON.stringify({ date: getTodayKey(), count: nextCount })
        );
        updateLimitWarningBanner();
        return nextCount;
    }

    function updateLimitWarningBanner() {
        const used = getUsedQuestionsToday();
        const remaining = Math.max(0, DAILY_QUESTION_LIMIT - used);
        const banner = document.getElementById("statusStrip");
        if (used >= DAILY_QUESTION_LIMIT) {
            banner.textContent = "Aaj ki 40 questions ki limit khatam ho chuki hai. Kal reset hogi ya Upgrade karein.";
            banner.classList.add("show");
        } else if (remaining <= WARNING_REMAINING_THRESHOLD) {
            banner.textContent = `Aaj ke sirf ${remaining} questions bache hain. Limit khatam hone par kal reset hogi.`;
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
                ? `Namaste ${name}, main aapki aaj kaise madad kar sakta hoon?`
                : "Namaste, main aapki aaj kaise madad kar sakta hoon?";
        }
        const gBtn = document.getElementById("googleAccountBtn");
        gBtn.textContent = name ? `Google: ${name}` : "Continue with Google";
    }

    function refreshThemeLabel() {
        const label = getThemeLabel().trim() || "Pyrox";
        document.getElementById("headerBrandTitle").textContent = label;
        document.getElementById("sidebarThemeTitle").textContent = label;
        document.getElementById("splashWord").textContent = label;
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
        document.getElementById("optProModel").classList.toggle("active", mode === "Pro Model");
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
        const chosen = typedName || "Harshit";
        localStorage.setItem("pyrox_user_name", chosen);
        refreshGreeting();
        closeModal("googleModal");
    }

    function saveAccountForm() {
        const name = document.getElementById("googleNameInput").value.trim();
        const email = document.getElementById("googleEmailInput").value.trim();
        if (name) localStorage.setItem("pyrox_user_name", name);
        if (email) localStorage.setItem("pyrox_user_email", email);
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

    function selectPlan(plan) {
        selectedPlan = plan;
        document.getElementById("planStarter").classList.toggle("selected", plan.includes("79"));
        document.getElementById("planPlus").classList.toggle("selected", plan.includes("149"));
    }

    function confirmUpgrade() {
        document.getElementById("upgradeStatusMsg").textContent = `Selected ${selectedPlan}. Ready for payment flow.`;
    }

    // Folder-based Library (named after first prompt in that chat)
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
            target.items.push({ role, content: content.slice(0, 500) });
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
            chip.textContent = `📁 ${f.title}`;
            chip.onclick = () => {
                openFolderInStage(f.id);
                closeSidebar();
            };
            box.appendChild(chip);
        });
    }

    function toggleLibraryFolders() {
        const box = document.getElementById("libraryFolders");
        box.classList.toggle("show");
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
                const row = document.createElement("div");
                row.className = "msg-row msg-ai";
                row.innerHTML = marked.parse(m.content);
                stage.appendChild(row);
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
            btn.textContent = `📁 ${f.title} (${f.items.length} entries)`;
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
        activeFolderId = null;
        pendingAttachmentDataUrl = null;
        pendingAttachmentName = "";
        const stage = document.getElementById("scrollStage");
        stage.innerHTML = "";
        const greetingDiv = document.createElement("div");
        greetingDiv.className = "greeting-center";
        greetingDiv.id = "greetingBox";
        const h1 = document.createElement("h1");
        h1.id = "greetingText";
        greetingDiv.appendChild(h1);
        stage.appendChild(greetingDiv);
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

    function promptImageCreation() {
        closePlusMenu();
        const input = document.getElementById("promptInput");
        input.value = "/image ";
        input.focus();
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
        const bars = meter.querySelectorAll(".freq-bar");
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
                    const h = v > 30 ? Math.max(4, Math.min(28, Math.round((v / 255) * 28))) : 3;
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
        meter.classList.remove("visible");
        meter.querySelectorAll(".freq-bar").forEach((b) => (b.style.height = "3px"));
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
            document.getElementById("stopDictBtn").classList.add("visible");
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
            // Do not auto-submit when dictation ends
            isDictating = false;
            document.getElementById("stopDictBtn").classList.remove("visible");
            stopVoiceMeter();
        };

        recognition.start();
    }

    function stopDictationManual() {
        isDictating = false;
        document.getElementById("stopDictBtn").classList.remove("visible");
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

    function appendAIMessage(htmlContent, plainTextForCopy) {
        markChatStarted();
        const stage = document.getElementById("scrollStage");
        const row = document.createElement("div");
        row.className = "msg-row msg-ai";

        const bodyDiv = document.createElement("div");
        bodyDiv.innerHTML = htmlContent;
        row.appendChild(bodyDiv);

        if (plainTextForCopy) {
            const bar = document.createElement("div");
            bar.className = "msg-actions";
            const copyBtn = document.createElement("button");
            copyBtn.type = "button";
            copyBtn.className = "mini-action-btn";
            copyBtn.textContent = "Copy";
            copyBtn.onclick = () => {
                navigator.clipboard.writeText(plainTextForCopy).catch(() => {});
                copyBtn.textContent = "Copied";
                setTimeout(() => (copyBtn.textContent = "Copy"), 1200);
            };
            bar.appendChild(copyBtn);
            row.appendChild(bar);
        }

        stage.appendChild(row);
        stage.scrollTop = stage.scrollHeight;
        return { row, bodyDiv };
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

    async function sendMessage() {
        stopDictationManual();

        if (getUsedQuestionsToday() >= DAILY_QUESTION_LIMIT) {
            updateLimitWarningBanner();
            return;
        }

        const input = document.getElementById("promptInput");
        const raw = input.value.trim();
        if (!raw && !pendingAttachmentDataUrl) return;

        const messageToSend = raw || `Please check ${pendingAttachmentName || "this image"}`;
        const attachmentToSend = pendingAttachmentDataUrl;
        pendingAttachmentDataUrl = null;
        pendingAttachmentName = "";
        input.value = "";

        ensureFolderForPrompt(messageToSend);
        appendUserMessage(messageToSend, attachmentToSend);
        appendItemToActiveFolder("user", messageToSend);
        incrementUsedQuestionsToday();

        const { bodyDiv } = appendAIMessage(
            `<div class="thinking-dots"><span></span><span></span></div>`,
            ""
        );

        activeAbortController = new AbortController();
        setGeneratingState(true);

        const searchLikely = /\b(aaj|kal|today|tomorrow|news|latest|festival|tyohar|weather|2026|2027|kab hai|kya chal raha)\b/i.test(
            messageToSend
        );
        if (searchLikely) {
            setSearchingBanner(true);
        }

        try {
            if (messageToSend.toLowerCase().startsWith("/image ")) {
                const imgPrompt = messageToSend.slice(7).trim();
                const res = await fetch("/api/generate-image", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ prompt: imgPrompt }),
                    signal: activeAbortController.signal,
                });
                const data = await res.json();
                if (!res.ok) {
                    bodyDiv.textContent = data.detail || "Image generation failed.";
                } else {
                    bodyDiv.innerHTML = `<img src="${data.image_data}" alt="${imgPrompt}" />`;
                    appendItemToActiveFolder("ai", `[Generated Image: ${imgPrompt}]`);
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
    runSplashEntry();
    refreshGreeting();
    refreshThemeLabel();
    renderLibraryFolders();
    updateLimitWarningBanner();
</script>
</body>
</html>
"""
    return html
