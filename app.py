import os
import streamlit as st
from groq import Groq

# Streamlit Page Config
st.set_page_config(
    page_title="Pyrox",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Streamlit Hide Default UI Elements
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    #MainMenu, header, footer { visibility: hidden; }
    .block-container { padding: 0rem; margin: 0rem; }
    </style>
""", unsafe_allow_html=True)

# Fetch API Key
api_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")

# HTML + CSS + JS Complete Studio UI
full_app_html = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        body {
            background-color: #000000;
            color: #ffffff;
            display: flex;
            height: 100vh;
            overflow: hidden;
        }
        /* Sidebar */
        .sidebar {
            width: 75px;
            background-color: #050505;
            border-right: 1px solid #1a1a1a;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px 0;
            justify-content: space-between;
        }
        .menu-top, .menu-bottom {
            display: flex;
            flex-direction: column;
            gap: 24px;
            align-items: center;
        }
        .menu-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 5px;
            color: #888888;
            font-size: 10px;
            cursor: pointer;
            transition: color 0.2s;
        }
        .menu-item:hover { color: #ffffff; }
        .menu-icon { width: 22px; height: 22px; stroke: currentColor; fill: none; stroke-width: 2; }

        /* Main Workspace */
        .main-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: space-between;
            padding: 20px;
            height: 100vh;
            position: relative;
        }

        /* Header with Dual Color Logo (Black & Red) */
        .top-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-top: 5px;
        }
        .pyrox-logo {
            width: 42px;
            height: 42px;
        }
        .app-title {
            font-size: 1.6rem;
            font-weight: 800;
            letter-spacing: 0.5px;
            color: #ffffff;
        }

        /* Chat Workspace */
        .chat-container {
            width: 100%;
            max-width: 800px;
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 18px;
            padding: 20px 10px;
        }
        .message {
            display: flex;
            flex-direction: column;
            max-width: 80%;
            line-height: 1.6;
            font-size: 1rem;
        }
        .user-message {
            align-self: flex-end;
            background-color: #1c1c1e;
            color: #ffffff;
            padding: 14px 20px;
            border-radius: 20px 20px 4px 20px;
            border: 1px solid #333;
        }
        .ai-message {
            align-self: flex-start;
            background-color: #0d0d0d;
            color: #f1f1f1;
            padding: 16px 22px;
            border-radius: 20px 20px 20px 4px;
            border: 1px solid #222;
        }
        .ai-message .sender-name {
            font-size: 0.75rem;
            color: #ff3333;
            margin-bottom: 6px;
            font-weight: 700;
        }

        /* Bottom Input Bar Wrapper */
        .input-wrapper {
            width: 100%;
            max-width: 800px;
            position: relative;
            margin-bottom: 15px;
        }
        .input-container {
            width: 100%;
            background-color: #0a0a0a;
            border: 1px solid #262626;
            border-radius: 32px;
            padding: 10px 18px;
            display: flex;
            align-items: center;
            gap: 12px;
            position: relative;
            transition: border-color 0.3s, box-shadow 0.3s;
        }
        .input-container.active-listening {
            border-color: #ff3333;
            box-shadow: 0 0 15px rgba(255, 51, 51, 0.25);
        }

        .star-icon {
            width: 24px;
            height: 24px;
            flex-shrink: 0;
            cursor: pointer;
        }

        /* Long Audio Wave Visualizer Line next to Mic */
        .long-wave-line {
            display: flex;
            align-items: center;
            gap: 3px;
            height: 20px;
            width: 100px;
            opacity: 0.2;
            transition: opacity 0.3s;
        }
        .long-wave-line.active {
            opacity: 1;
        }
        .wave-bar {
            flex: 1;
            background-color: #ff3333;
            border-radius: 2px;
            height: 20%;
            transition: height 0.1s ease;
        }
        .long-wave-line.active .wave-bar {
            animation: wavePulse 0.8s infinite ease-in-out alternate;
        }
        .long-wave-line.active .wave-bar:nth-child(1) { animation-delay: 0.0s; }
        .long-wave-line.active .wave-bar:nth-child(2) { animation-delay: 0.1s; }
        .long-wave-line.active .wave-bar:nth-child(3) { animation-delay: 0.2s; }
        .long-wave-line.active .wave-bar:nth
