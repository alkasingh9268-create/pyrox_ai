import os
import json
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

app = FastAPI(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)

# Groq API Key ko environment variable se uthayega (jo Render me dala hai)
API_KEY = os.environ.get("GROQ_API_KEY")
