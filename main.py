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
HF_API_KEY = os.environ.get("HF_API_KEY", "").strip() or os.environ.get(
    "HUGGINGFACE_API_KEY", ""
).strip()

CACHED_GROQ_MODEL: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    voice: str = "hi-IN-MadhurNeural"
    user_name: Optional[str] = None
    theme_label: str = "Charcoal Minimal"
    model_mode: str = "Pyrox Only"
    enable_tts: bool = False


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
            timeout=6,
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


def search_live_context(query: str) -> str:
    today_str = datetime.datetime.now().strftime("%A, %d %B %Y")
    base_info = f"Current Date: {today_str} (India)."
    if not SERP_API_KEY:
        return base_info

    try:
        encoded = requests.utils.quote(query)
        url = f"https://serpapi.com/search.json?q={encoded}&api_key={SERP_API_KEY}&hl=en&gl=in"
        res = requests.get(url, timeout=8)
        if res.status_code == 200:
            data = res.json()
            snippets = [
                item.get("snippet", "")
                for item in data.get("organic_results", [])[:4]
                if item.get("snippet")
            ]
            if snippets:
                return f"{base_info}\nWeb Results: {' | '.join(snippets)}"
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
        communicate = edge_tts.Communicate(cleaned[:600], voice_name, rate="+18%")
        await communicate.save(filename)
        return True
    except Exception:
        return False


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
    ]
    return any(t in q for t in triggers)


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
    if not user_msg:
        return JSONResponse(
            status_code=400, content={"detail": "Message cannot be empty."}
        )

    try:
        model_id = resolve_groq_model()
        context_block = (
            search_live_context(user_msg)
            if should_search_web(user_msg)
            else f"Current Date: {datetime.datetime.now().strftime('%A, %d %B %Y')}."
        )

        short_mode = is_short_greeting(user_msg)
        user_label = (
            req.user_name.strip()
            if req.user_name and req.user_name.strip()
            else "User"
        )

        if short_mode:
            system_prompt = (
                f"You are Pyrox ({req.model_mode} mode). {context_block} "
                f"The user is {user_label}. Reply briefly, naturally, and warmly in 1 short sentence "
                "using smooth Roman Hinglish. Do NOT use bullet points or numbered lists for a simple greeting."
            )
        else:
            system_prompt = (
                f"You are Pyrox ({req.model_mode} mode). {context_block} "
                f"The user is {user_label}. Reply fast, clearly, and naturally in smooth Roman Hinglish. "
                "Use bullet points or numbered steps ONLY when genuinely helpful for multi-step or structured info; "
                "for casual or direct questions, write normal clean paragraphs without forced bullets. "
                "Keep dates and upcoming events accurate according to the current date."
            )

        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            "temperature": 0.65,
            "max_tokens": 220 if short_mode else 650,
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

        return {"reply": reply_text, "audio_url": audio_url, "model": model_id}

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
            --text-secondary: #a1a1aa;
            --text-muted: #71717a;
            --accent-clean: #e4e4e7;
            --accent-upgrade: #2563eb;
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
        }

        .app-shell {
            display: flex;
            height: 100dvh;
            width: 100%;
            position: relative;
            overflow: hidden;
        }

        /* Sidebar */
        .sidebar {
            position: fixed;
            top: 0;
            left: 0;
            height: 100dvh;
            width: 0;
            max-width: 280px;
            background-color: var(--bg-surface);
            border-right: 1px solid transparent;
            overflow-y: auto;
            overflow-x: hidden;
            transition: width 0.22s ease, border-color 0.22s ease;
            z-index: 60;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .sidebar.open {
            width: 28vw;
            min-width: 220px;
            max-width: 280px;
            border-right-color: var(--border-subtle);
            padding: 14px 12px;
        }

        @media (max-width: 640px) {
            .sidebar.open {
                width: 34vw;
                min-width: 150px;
                padding: 12px 8px;
            }
        }

        .sidebar-top {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .sidebar-title {
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--text-primary);
            padding: 4px 8px 8px 8px;
            border-bottom: 1px solid var(--border-subtle);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .nav-item {
            padding: 10px;
            border-radius: 10px;
            font-size: 0.88rem;
            color: var(--text-secondary);
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            transition: background-color 0.15s ease, color 0.15s ease;
        }

        .nav-item:hover {
            background-color: var(--bg-elevated);
            color: var(--text-primary);
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
            padding: 8px 10px;
            border-radius: 8px;
            font-size: 0.82rem;
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

        .history-box {
            margin-top: 6px;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .history-chip {
            padding: 7px 9px;
            font-size: 0.78rem;
            color: var(--text-muted);
            background-color: rgba(255, 255, 255, 0.02);
            border-radius: 8px;
            cursor: pointer;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .history-chip:hover {
            color: var(--text-primary);
            background-color: var(--bg-elevated);
        }

        .sidebar-footer {
            border-top: 1px solid var(--border-subtle);
            padding-top: 10px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .google-pill {
            padding: 8px 10px;
            border-radius: 10px;
            border: 1px solid var(--border-subtle);
            background-color: var(--bg-elevated);
            font-size: 0.8rem;
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
            height: 54px;
            padding: 0 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            flex-shrink: 0;
            z-index: 20;
        }

        .top-left {
            display: flex;
            align-items: center;
            gap: 10px;
            min-height: 36px;
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
            transition: transform 0.12s ease, background-color 0.15s ease;
        }

        .menu-toggle-btn.hidden-burger {
            display: none;
        }

        .menu-toggle-btn:active,
        .icon-action-btn:active,
        .send-btn:active,
        .stop-btn:active {
            transform: scale(0.95);
        }

        .brand-heading {
            font-size: 1rem;
            font-weight: 700;
            letter-spacing: 0.2px;
            color: var(--text-primary);
        }

        .mode-tag {
            font-size: 0.72rem;
            color: var(--text-secondary);
            background-color: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            padding: 3px 8px;
            border-radius: 999px;
        }

        .top-right {
            display: flex;
            align-items: center;
            gap: 8px;
            position: relative;
        }

        /* Upgrade button with entry shine & bracket curve */
        .upgrade-btn {
            position: relative;
            overflow: hidden;
            background-color: var(--accent-upgrade);
            color: #ffffff;
            border: 1px solid #3b82f6;
            border-radius: 14px 4px 14px 4px;
            padding: 6px 12px;
            font-size: 0.8rem;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }

        .upgrade-btn.shine-active::after {
            content: "";
            position: absolute;
            top: -120%;
            left: -40%;
            width: 60%;
            height: 320%;
            background: linear-gradient(
                115deg,
                transparent 20%,
                rgba(255, 255, 255, 0.55) 50%,
                transparent 80%
            );
            transform: rotate(20deg);
            animation: sweepShine 2.2s ease-in-out infinite;
        }

        @keyframes sweepShine {
            0% {
                top: -120%;
                opacity: 0;
            }
            25% {
                opacity: 1;
            }
            75% {
                top: 120%;
                opacity: 1;
            }
            100% {
                top: 120%;
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
            width: 185px;
            background-color: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 6px;
            display: none;
            flex-direction: column;
            gap: 2px;
            z-index: 80;
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.65);
        }

        .dots-menu.show {
            display: flex;
        }

        .dots-item {
            padding: 9px 11px;
            border-radius: 8px;
            font-size: 0.85rem;
            color: var(--text-primary);
            cursor: pointer;
        }

        .dots-item:hover {
            background-color: var(--bg-elevated);
        }

        /* Greeting & Chat scroll container */
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
            max-width: 520px;
            padding: 20px 10px;
        }

        .greeting-center h1 {
            font-size: 1.45rem;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1.35;
        }

        .msg-row {
            display: flex;
            flex-direction: column;
            max-width: 88%;
            gap: 6px;
        }

        .msg-user {
            align-self: flex-end;
            background-color: var(--bg-elevated);
            color: var(--text-primary);
            border: 1px solid var(--border-user);
            border-radius: 14px 14px 4px 14px;
            padding: 10px 14px;
            font-size: 0.94rem;
            line-height: 1.5;
            word-break: break-word;
        }

        .msg-ai {
            align-self: flex-start;
            width: 100%;
            max-width: 100%;
            color: var(--text-primary);
            font-size: 0.95rem;
            line-height: 1.6;
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
            margin-bottom: 4px;
        }

        .msg-ai img {
            max-width: 100%;
            max-height: 360px;
            border-radius: 12px;
            border: 1px solid var(--border-subtle);
            margin-top: 6px;
        }

        .thinking-dots {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 2px;
        }

        .thinking-dots span {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: var(--text-secondary);
            animation: dotBounce 1.1s infinite ease-in-out;
        }

        .thinking-dots span:nth-child(2) {
            animation-delay: 0.2s;
        }

        @keyframes dotBounce {
            0%, 80%, 100% {
                transform: translateY(0);
                opacity: 0.45;
            }
            40% {
                transform: translateY(-5px);
                opacity: 1;
            }
        }

        /* Bottom Input Dock */
        .bottom-dock {
            flex-shrink: 0;
            width: 100%;
            padding: 6px 10px 10px 10px;
            background-color: var(--bg-main);
            border-top: 1px solid rgba(255, 255, 255, 0.06);
            position: relative;
            z-index: 30;
        }

        .plus-menu {
            position: absolute;
            bottom: 72px;
            left: 12px;
            width: 260px;
            background-color: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: 14px;
            padding: 10px;
            display: none;
            flex-direction: column;
            gap: 8px;
            z-index: 70;
            box-shadow: 0 14px 32px rgba(0, 0, 0, 0.75);
        }

        .plus-menu.show {
            display: flex;
        }

        .plus-big-btn {
            padding: 11px 12px;
            border-radius: 10px;
            background-color: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            color: var(--text-primary);
            font-size: 0.92rem;
            font-weight: 500;
            cursor: pointer;
            text-align: left;
        }

        .plus-big-btn:hover {
            background-color: #222229;
        }

        .plus-small-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 6px;
            padding-top: 4px;
            border-top: 1px solid var(--border-subtle);
        }

        .plus-small-btn {
            padding: 8px 6px;
            border-radius: 8px;
            background-color: var(--bg-main);
            border: 1px solid var(--border-subtle);
            color: var(--text-secondary);
            font-size: 0.76rem;
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
            min-height: 54px;
            background-color: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: 22px;
            padding: 6px 10px;
        }

        .icon-action-btn {
            width: 38px;
            height: 38px;
            border-radius: 12px;
            border: 1px solid var(--border-subtle);
            background-color: var(--bg-elevated);
            color: var(--text-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            flex-shrink: 0;
            font-size: 1.05rem;
            transition: transform 0.2s ease;
        }

        .icon-action-btn.open-minus {
            transform: rotate(90deg);
        }

        .prompt-input {
            flex: 1;
            min-width: 0;
            min-height: 40px;
            max-height: 110px;
            background: transparent;
            border: none;
            outline: none;
            color: var(--text-primary);
            font-size: 0.98rem;
            resize: none;
            padding: 8px 4px;
            line-height: 1.35;
        }

        /* Frequency bars: flat when silent, active only when speaking */
        .freq-meter {
            display: none;
            align-items: center;
            gap: 3px;
            height: 28px;
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
            padding: 6px 10px;
            border-radius: 10px;
            border: 1px solid var(--border-user);
            background-color: var(--bg-elevated);
            color: var(--text-primary);
            font-size: 0.75rem;
            font-weight: 600;
            cursor: pointer;
        }

        .stop-dict-btn.visible {
            display: inline-flex;
        }

        .send-btn, .stop-btn {
            width: 40px;
            height: 40px;
            border-radius: 14px;
            border: none;
            background-color: var(--text-primary);
            color: var(--bg-main);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            flex-shrink: 0;
            font-weight: 700;
        }

        .stop-btn {
            display: none;
            background-color: #27272a;
            color: var(--text-primary);
            border: 1px solid #71717a;
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
            background-color: rgba(0, 0, 0, 0.35);
            padding: 0;
        }

        .modal-box {
            width: 100%;
            max-width: 440px;
            background-color: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: 16px;
            padding: 18px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            color: var(--text-primary);
        }

        .camera-sheet .modal-box {
            max-width: 640px;
            height: 75dvh;
            border-radius: 20px 20px 0 0;
        }

        .modal-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-weight: 700;
            font-size: 1rem;
        }

        .close-x {
            background: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            color: var(--text-primary);
            border-radius: 8px;
            padding: 4px 10px;
            cursor: pointer;
            font-size: 0.85rem;
        }

        .field-input {
            width: 100%;
            background-color: var(--bg-main);
            border: 1px solid var(--border-subtle);
            color: var(--text-primary);
            border-radius: 10px;
            padding: 9px 11px;
            font-size: 0.9rem;
            outline: none;
        }

        .action-btn {
            background-color: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            color: var(--text-primary);
            border-radius: 10px;
            padding: 10px 12px;
            font-size: 0.88rem;
            cursor: pointer;
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
            padding: 12px;
            cursor: pointer;
        }

        .plan-card.selected {
            border-color: var(--accent-upgrade);
        }

        .video-frame {
            flex: 1;
            min-height: 0;
            background-color: #000000;
            border-radius: 12px;
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
            justify-content: space-between;
            gap: 8px;
        }
    </style>
</head>
<body>
<div class="app-shell" id="appShell">
    <aside class="sidebar" id="sidebar" onclick="event.stopPropagation()">
        <div class="sidebar-top">
            <div class="sidebar-title">
                <span id="sidebarThemeTitle">Pyrox</span>
                <span style="font-size:0.75rem;color:var(--text-secondary);cursor:pointer;" onclick="closeSidebar()">✕</span>
            </div>

            <div class="nav-item" onclick="newChat()">+ New Chat</div>
            <div class="nav-item" onclick="openModal('libraryModal')">Library</div>
            <div class="nav-item" onclick="toggleHistoryList()">History</div>
            <div class="history-box" id="historyList"></div>

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
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="3" y1="6" x2="21" y2="6"></line>
                        <line x1="3" y1="12" x2="21" y2="12"></line>
                        <line x1="3" y1="18" x2="21" y2="18"></line>
                    </svg>
                </button>
                <span class="brand-heading" id="headerBrandTitle">Pyrox</span>
                <span class="mode-tag" id="activeModeBadge">Pyrox Only</span>
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

            <input type="file" id="filePicker" style="display:none;" onchange="handleFileSelected(event)" />

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

<!-- Google Sign-In Modal -->
<div class="overlay-modal" id="googleModal" onclick="closeModal('googleModal')">
    <div class="modal-box" onclick="event.stopPropagation()">
        <div class="modal-head">
            <span>Google Account</span>
            <button type="button" class="close-x" onclick="closeModal('googleModal')">Close</button>
        </div>
        <p style="font-size:0.86rem;color:var(--text-secondary);">
            Apna Gmail name/account set karo taaki greeting personalize ho sake.
        </p>
        <input type="text" class="field-input" id="googleNameInput" placeholder="Enter your name (e.g. Harshit)" />
        <input type="email" class="field-input" id="googleEmailInput" placeholder="Enter Gmail (optional)" />
        <button type="button" class="action-btn" onclick="saveGoogleAccount()">Continue with Google</button>
    </div>
</div>

<!-- Settings Modal -->
<div class="overlay-modal" id="settingsModal" onclick="closeModal('settingsModal')">
    <div class="modal-box" onclick="event.stopPropagation()">
        <div class="modal-head">
            <span>Settings</span>
            <button type="button" class="close-x" onclick="closeModal('settingsModal')">Close</button>
        </div>
        <label style="font-size:0.84rem;color:var(--text-secondary);">Custom Theme Name</label>
        <input type="text" class="field-input" id="customThemeInput" placeholder="e.g. Dark Obsidian, Night Studio" />
        <button type="button" class="action-btn" onclick="saveThemeName()">Save Theme Name</button>
        <button type="button" class="action-btn" onclick="clearSavedLibrary()">Clear Saved Library</button>
    </div>
</div>

<!-- Library Modal -->
<div class="overlay-modal" id="libraryModal" onclick="closeModal('libraryModal')">
    <div class="modal-box" onclick="event.stopPropagation()">
        <div class="modal-head">
            <span>Library</span>
            <button type="button" class="close-x" onclick="closeModal('libraryModal')">Close</button>
        </div>
        <div id="libraryItemsContainer" style="max-height:280px;overflow-y:auto;display:flex;flex-direction:column;gap:8px;font-size:0.85rem;color:var(--text-secondary);">
            No saved items yet.
        </div>
    </div>
</div>

<!-- Upgrade Modal -->
<div class="overlay-modal" id="upgradeModal" onclick="closeModal('upgradeModal')">
    <div class="modal-box" onclick="event.stopPropagation()">
        <div class="modal-head">
            <span>Upgrade Pyrox</span>
            <button type="button" class="close-x" onclick="closeModal('upgradeModal')">Close</button>
        </div>
        <p style="font-size:0.85rem;color:var(--text-secondary);">
            Student-friendly plans:
        </p>
        <div class="plan-row">
            <div class="plan-card selected" id="planStarter" onclick="selectPlan('₹79 / month')">
                <div style="font-weight:700;">Starter</div>
                <div style="font-size:1.05rem;margin-top:4px;">₹79 / mo</div>
            </div>
            <div class="plan-card" id="planPlus" onclick="selectPlan('₹149 / month')">
                <div style="font-weight:700;">Plus</div>
                <div style="font-size:1.05rem;margin-top:4px;">₹149 / mo</div>
            </div>
        </div>
        <button type="button" class="action-btn" style="background-color:var(--accent-upgrade);border-color:#3b82f6;color:#fff;" onclick="confirmUpgrade()">
            Activate Selected Plan
        </button>
        <div id="upgradeStatusMsg" style="font-size:0.82rem;color:var(--text-secondary);"></div>
    </div>
</div>

<!-- 75% Camera Modal -->
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
            <button type="button" class="action-btn" id="flashToggleBtn" onclick="toggleFlash()">Flash: Off</button>
            <button type="button" class="action-btn" onclick="captureCameraPhoto()">Capture</button>
        </div>
    </div>
</div>

<script>
    let chatStarted = false;
    let activeAbortController = null;
    let selectedPlan = "₹79 / month";
    let selectedModelMode = "Pyrox Only";
    let currentFacingMode = "environment";
    let cameraStream = null;
    let flashEnabled = false;

    // Dictation & Web Audio frequency state
    let recognition = null;
    let isDictating = false;
    let audioCtx = null;
    let analyser = null;
    let micStream = null;
    let freqAnimId = null;

    function getUserName() {
        return localStorage.getItem("pyrox_user_name") || "";
    }

    function getThemeLabel() {
        return localStorage.getItem("pyrox_theme_label") || "Pyrox";
    }

    function refreshGreeting() {
        const name = getUserName().trim();
        const el = document.getElementById("greetingText");
        if (name) {
            el.textContent = `Namaste ${name}, main aapki aaj kaise madad kar sakta hoon?`;
        } else {
            el.textContent = "Namaste, main aapki aaj kaise madad kar sakta hoon?";
        }
        const gBtn = document.getElementById("googleAccountBtn");
        gBtn.textContent = name ? `Google: ${name}` : "Continue with Google";
    }

    function refreshThemeLabel() {
        const label = getThemeLabel().trim() || "Pyrox";
        document.getElementById("headerBrandTitle").textContent = label;
        document.getElementById("sidebarThemeTitle").textContent = label;
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
        document.getElementById("activeModeBadge").textContent = mode;
        document.getElementById("optPyroxOnly").classList.toggle("active", mode === "Pyrox Only");
        document.getElementById("optProModel").classList.toggle("active", mode === "Pro Model");
    }

    function openModal(id) {
        if (id === "libraryModal") renderLibrary();
        document.getElementById(id).classList.add("show");
    }

    function closeModal(id) {
        document.getElementById(id).classList.remove("show");
    }

    function saveGoogleAccount() {
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

    function selectPlan(plan) {
        selectedPlan = plan;
        document.getElementById("planStarter").classList.toggle("selected", plan.includes("79"));
        document.getElementById("planPlus").classList.toggle("selected", plan.includes("149"));
    }

    function confirmUpgrade() {
        document.getElementById("upgradeStatusMsg").textContent = `Selected ${selectedPlan}. Ready for checkout integration.`;
    }

    function saveToLibrary(entry) {
        const list = JSON.parse(localStorage.getItem("pyrox_library") || "[]");
        list.unshift(entry);
        localStorage.setItem("pyrox_library", JSON.stringify(list.slice(0, 30)));
        renderHistory();
    }

    function renderLibrary() {
        const container = document.getElementById("libraryItemsContainer");
        const list = JSON.parse(localStorage.getItem("pyrox_library") || "[]");
        if (!list.length) {
            container.textContent = "No saved items yet.";
            return;
        }
        container.innerHTML = "";
        list.forEach((item) => {
            const div = document.createElement("div");
            div.style.padding = "8px";
            div.style.border = "1px solid var(--border-subtle)";
            div.style.borderRadius = "8px";
            div.textContent = item;
            container.appendChild(div);
        });
    }

    function clearSavedLibrary() {
        localStorage.removeItem("pyrox_library");
        renderLibrary();
        renderHistory();
    }

    function renderHistory() {
        const box = document.getElementById("historyList");
        const list = JSON.parse(localStorage.getItem("pyrox_library") || "[]");
        box.innerHTML = "";
        list.slice(0, 6).forEach((item) => {
            const chip = document.createElement("div");
            chip.className = "history-chip";
            chip.textContent = item;
            chip.onclick = () => {
                document.getElementById("promptInput").value = item;
                closeSidebar();
            };
            box.appendChild(chip);
        });
    }

    function toggleHistoryList() {
        const box = document.getElementById("historyList");
        box.style.display = box.style.display === "none" ? "flex" : "none";
    }

    function newChat() {
        stopGeneration();
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
        const input = document.getElementById("promptInput");
        input.value = `${input.value ? input.value + " " : ""}[File: ${file.name}]`;
        input.focus();
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
        const modal = document.getElementById("cameraModal");
        modal.classList.add("show");
        await startCameraStream();
    }

    async function startCameraStream() {
        stopCameraStream();
        try {
            cameraStream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: currentFacingMode },
                audio: false,
            });
            const video = document.getElementById("cameraVideo");
            video.srcObject = cameraStream;
        } catch (err) {
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
        const dataUrl = canvas.toDataURL("image/png");
        appendAIMessage(`<img src="${dataUrl}" alt="Captured photo" />`);
        saveToLibrary("Captured Camera Photo");
        closeCamera();
    }

    async function startVoiceMeter() {
        const meter = document.getElementById("freqMeter");
        const bars = meter.querySelectorAll(".freq-bar");
        meter.classList.add("visible");

        try {
            micStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            audioCtx = new AudioContextClass();
            const src = audioCtx.createMediaStreamSource(micStream);
            analyser = audioCtx.createAnalyser();
            analyser.fftSize = 64;
            src.connect(analyser);

            const dataArr = new Uint8Array(analyser.frequencyBinCount);
            const tick = () => {
                if (!isDictating || !analyser) return;
                analyser.getByteFrequencyData(dataArr);
                for (let i = 0; i < bars.length; i++) {
                    const val = dataArr[i] || 0;
                    // Strictly silent/flat when voice level is below threshold
                    const h = val > 28 ? Math.max(4, Math.min(26, Math.round((val / 255) * 26))) : 3;
                    bars[i].style.height = `${h}px`;
                }
                freqAnimId = requestAnimationFrame(tick);
            };
            freqAnimId = requestAnimationFrame(tick);
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
        let finalTranscript = "";

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
                    finalTranscript += seg + " ";
                } else {
                    interim += seg;
                }
            }
            const combined = `${baseText}${baseText ? " " : ""}${finalTranscript}${interim}`.trim();
            document.getElementById("promptInput").value = combined;
        };

        recognition.onerror = () => {
            stopDictationManual();
        };

        recognition.onend = () => {
            // Never auto-send on stop/end
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

    function appendUserMessage(text) {
        markChatStarted();
        const stage = document.getElementById("scrollStage");
        const row = document.createElement("div");
        row.className = "msg-row msg-user";
        row.textContent = text;
        stage.appendChild(row);
        stage.scrollTop = stage.scrollHeight;
    }

    function appendAIMessage(htmlContent) {
        markChatStarted();
        const stage = document.getElementById("scrollStage");
        const row = document.createElement("div");
        row.className = "msg-row msg-ai";
        row.innerHTML = htmlContent;
        stage.appendChild(row);
        stage.scrollTop = stage.scrollHeight;
        return row;
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
        setGeneratingState(false);
    }

    async function sendMessage() {
        stopDictationManual();
        const input = document.getElementById("promptInput");
        const raw = input.value.trim();
        if (!raw) return;

        input.value = "";
        appendUserMessage(raw);
        saveToLibrary(raw);

        const aiRow = appendAIMessage(
            `<div class="thinking-dots"><span></span><span></span></div>`
        );

        activeAbortController = new AbortController();
        setGeneratingState(true);

        try {
            if (raw.toLowerCase().startsWith("/image ")) {
                const imgPrompt = raw.slice(7).trim();
                const res = await fetch("/api/generate-image", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ prompt: imgPrompt }),
                    signal: activeAbortController.signal,
                });
                const data = await res.json();
                if (!res.ok) {
                    aiRow.textContent = data.detail || "Image generation failed.";
                } else {
                    aiRow.innerHTML = `<img src="${data.image_data}" alt="${imgPrompt}" />`;
                }
            } else {
                const res = await fetch("/api/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        message: raw,
                        user_name: getUserName(),
                        theme_label: getThemeLabel(),
                        model_mode: selectedModelMode,
                    }),
                    signal: activeAbortController.signal,
                });
                const data = await res.json();
                if (!res.ok) {
                    aiRow.textContent = data.detail || "Request failed.";
                } else {
                    aiRow.innerHTML = marked.parse(data.reply || "");
                }
            }
        } catch (err) {
            if (err.name === "AbortError") {
                aiRow.textContent = "Stopped.";
            } else {
                aiRow.textContent = "Connection error.";
            }
        } finally {
            activeAbortController = null;
            setGeneratingState(false);
            const stage = document.getElementById("scrollStage");
            stage.scrollTop = stage.scrollHeight;
        }
    }

    refreshGreeting();
    refreshThemeLabel();
    renderHistory();
</script>
</body>
</html>
"""
    return html
    
