<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pyrox AI</title>
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

        /* Sidebar Styles */
        .sidebar {
            width: 80px;
            background-color: #050505;
            border-right: 1px solid #1a1a1a;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px 0;
            justify-content: space-between;
            z-index: 10;
        }

        .menu-top, .menu-bottom {
            display: flex;
            flex-direction: column;
            gap: 25px;
            align-items: center;
        }

        .menu-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
            color: #888888;
            font-size: 10px;
            cursor: pointer;
            transition: color 0.2s;
            text-decoration: none;
        }

        .menu-item:hover {
            color: #ffffff;
        }

        .menu-icon {
            width: 22px;
            height: 22px;
            stroke: currentColor;
            fill: none;
            stroke-width: 2;
        }

        /* Main Workspace Area */
        .main-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: space-between;
            padding: 20px;
            position: relative;
            height: 100vh;
        }

        /* Top Header Logo */
        .top-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-top: 10px;
        }

        .pyrox-logo-small {
            width: 38px;
            height: 38px;
        }

        .app-title {
            font-size: 1.4rem;
            font-weight: 700;
            letter-spacing: 1px;
            color: #ffffff;
        }

        /* Chat Messages Box */
        .chat-container {
            width: 100%;
            max-width: 720px;
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
            padding: 20px 10px;
            margin: 10px 0;
        }

        .message {
            display: flex;
            flex-direction: column;
            max-width: 82%;
            line-height: 1.5;
            font-size: 0.95rem;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .user-message {
            align-self: flex-end;
            background-color: #1a1a1a;
            color: #ffffff;
            padding: 12px 18px;
            border-radius: 20px 20px 4px 20px;
            border: 1px solid #333;
        }

        .ai-message {
            align-self: flex-start;
            background-color: #0d0d0d;
            color: #e0e0e0;
            padding: 14px 20px;
            border-radius: 20px 20px 20px 4px;
            border: 1px solid #222;
        }

        .ai-message .sender-name {
            font-size: 0.75rem;
            color: #888;
            margin-bottom: 6px;
            font-weight: 600;
        }

        /* Input Bar */
        .input-container {
            width: 100%;
            max-width: 720px;
            background-color: #0a0a0a;
            border: 1px solid #222222;
            border-radius: 28px;
            padding: 10px 18px;
            display: flex;
            align-items: center;
            gap: 12px;
            position: relative;
            margin-bottom: 10px;
        }

        .star-icon {
            width: 24px;
            height: 24px;
            cursor: pointer;
            flex-shrink: 0;
        }

        .chat-input {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: #ffffff;
            font-size: 1rem;
            padding: 8px 0;
        }

        .chat-input::placeholder {
            color: #555555;
        }

        .input-actions {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .action-btn {
            background: transparent;
            border: none;
            color: #aaaaaa;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }

        .action-btn.recording {
            color: #ff4d4d;
            transform: scale(1.15);
        }

        .send-btn {
            width: 32px;
            height: 32px;
            background-color: #ffffff;
            border-radius: 50%;
            color: #000000;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            border: none;
            transition: opacity 0.2s;
        }

        /* Audio Frequency Animation */
        .frequency-visualizer {
            position: absolute;
            bottom: -22px;
            right: 60px;
            display: none;
            align-items: flex-end;
            gap: 3px;
            height: 14px;
        }

        .frequency-visualizer.active {
            display: flex;
        }

        .freq-bar {
            width: 2px;
            background-color: #00e5ff;
            border-radius: 2px;
            animation: pulse 1.2s infinite ease-in-out;
        }

        .freq-bar:nth-child(1) { height: 60%; animation-delay: 0.1s; }
        .freq-bar:nth-child(2) { height: 100%; animation-delay: 0.3s; }
        .freq-bar:nth-child(3) { height: 40%; animation-delay: 0.2s; }
        .freq-bar:nth-child(4) { height: 80%; animation-delay: 0.4s; }

        @keyframes pulse {
            0%, 100% { transform: scaleY(0.4); }
            50% { transform: scaleY(1); }
        }
    </style>
</head>
<body>

    <!-- Navigation Bar -->
    <div class="sidebar">
        <div class="menu-top">
            <div class="menu-item" onclick="clearChat()">
                <svg class="menu-icon" viewBox="0 0 24 24"><path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                <span>History</span>
            </div>
            <div class="menu-item" onclick="clearChat()">
                <svg class="menu-icon" viewBox="0 0 24 24"><path d="M12 4v16m8-8H4"></path></svg>
                <span>New Chat</span>
            </div>
            <div class="menu-item">
                <svg class="menu-icon" viewBox="0 0 24 24"><path d="M12 14l9-5-9-5-9 5 9 5z"></path><path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0112 20.055a11.952 11.952 0 01-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z"></path></svg>
                <span>For Students</span>
            </div>
            <div class="menu-item">
                <svg class="menu-icon" viewBox="0 0 24 24"><path d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
                <span>For Business</span>
            </div>
        </div>
        <div class="menu-bottom">
            <div class="menu-item">
                <svg class="menu-icon" viewBox="0 0 24 24"><path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
                <span>Profile</span>
            </div>
        </div>
    </div>

    <!-- Main Workspace Area -->
    <div class="main-container">
        
        <div class="top-header">
            <svg class="pyrox-logo-small" viewBox="0 0 200 200">
                <circle cx="100" cy="100" r="80" fill="none" stroke="#ffffff" stroke-width="4" />
                <path d="M 100 20 L 70 80 L 110 80 L 90 120 L 130 120 L 100 180" fill="none" stroke="#ffffff" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M 20 100 L 70 80 M 180 100 L 130 120" stroke="#ffffff" stroke-width="3" stroke-linecap="round"/>
            </svg>
            <h1 class="app-title">Pyrox AI</h1>
        </div>

        <div class="chat-container" id="chatContainer">
            <div class="message ai-message">
                <span class="sender-name">Pyrox AI</span>
                Hello! Main Pyrox AI hoon. Aap bolkar ya type karke mujhse kuch bhi pooch sakte hain!
            </div>
        </div>

        <div class="input-container">
            <svg class="star-icon" viewBox="0 0 24 24">
                <defs>
                    <linearGradient id="starGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stop-color="#9C27B0"/>
                        <stop offset="30%" stop-color="#E91E63"/>
                        <stop offset="70%" stop-color="#FF9800"/>
                        <stop offset="100%" stop-color="#03A9F4"/>
                    </linearGradient>
                </defs>
                <path d="M12 0C12 6.627 6.627 12 0 12C6.627 12 12 17.373 12 24C12 17.373 17.373 12 24 12C17.373 12 12 6.627 12 0Z" fill="url(#starGrad)"/>
            </svg>

            <input type="text" id="chatInput" class="chat-input" placeholder="Type or speak your question..." onkeypress="handleKeyPress(event)" />

            <div class="input-actions">
                <button class="action-btn" id="micBtn" title="Voice Input" onclick="toggleVoiceInput()">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                        <line x1="12" y1="19" x2="12" y2="23"></line>
                        <line x1="8" y1="23" x2="16" y2="23"></line>
                    </svg>
                </button>
                <button class="send-btn" title="Send Message" onclick="sendMessage()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                        <line x1="5" y1="12" x2="19" y2="12"></line>
                        <polyline points="12 5 19 12 12 19"></polyline>
                    </svg>
                </button>
            </div>

            <div class="frequency-visualizer" id="visualizer">
                <div class="freq-bar"></div>
                <div class="freq-bar"></div>
                <div class="freq-bar"></div>
                <div class="freq-bar"></div>
            </div>
        </div>
    </div>

    <!-- JAVASCRIPT: Professional Speech & Messaging Logic -->
    <script>
        const inputField = document.getElementById('chatInput');
        const chatContainer = document.getElementById('chatContainer');
        const micBtn = document.getElementById('micBtn');
        const visualizer = document.getElementById('visualizer');

        // Professional Voice Speech Recognition Setup
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        let recognition = null;
        let isListening = false;

        if (SpeechRecognition) {
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.lang = 'hi-IN'; // Hindi/English auto input support

            recognition.onstart = () => {
                isListening = true;
                micBtn.classList.add('recording');
                visualizer.classList.add('active');
            };

            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                inputField.value = transcript;
                sendMessage(); // Auto send after speaking
            };

            recognition.onerror = () => {
                stopListening();
            };

            recognition.onend = () => {
                stopListening();
            };
        }

        function toggleVoiceInput() {
            if (!recognition) {
                alert('Aapke browser mein Voice feature support nahi karta. Please Chrome browser use kariye.');
                return;
            }

            if (isListening) {
                recognition.stop();
            } else {
                recognition.start();
            }
        }

        function stopListening() {
            isListening = false;
            micBtn.classList.remove('recording');
            visualizer.classList.remove('active');
        }

        async function sendMessage() {
            const text = inputField.value.trim();
            if (text === '') return;

            // User Message Display
            const userMsgDiv = document.createElement('div');
            userMsgDiv.className = 'message user-message';
            userMsgDiv.innerText = text;
            chatContainer.appendChild(userMsgDiv);

            inputField.value = '';
            chatContainer.scrollTop = chatContainer.scrollHeight;

            // Placeholder AI Response
            const aiMsgDiv = document.createElement('div');
            aiMsgDiv.className = 'message ai-message';
            aiMsgDiv.innerHTML = `<span class="sender-name">Pyrox AI</span>Thinking...`;
            chatContainer.appendChild(aiMsgDiv);

            // Backend Fetch Request (Change URL with Streamlit / FastAPI link)
            try {
                /* 
                // UNCOMMENT THIS WHEN BACKEND IS READY:
                const response = await fetch('http://localhost:5000/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                const data = await response.json();
                aiMsgDiv.innerHTML = `<span class="sender-name">Pyrox AI</span>${data.reply}`;
                */

                setTimeout(() => {
                    aiMsgDiv.innerHTML = `<span class="sender-name">Pyrox AI</span>Aapka sawaal mil gaya: "${text}". Abhi Streamlit API link hote hi ye real Python AI response dene lagega!`;
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }, 600);

            } catch (err) {
                aiMsgDiv.innerHTML = `<span class="sender-name">Pyrox AI</span>Backend connection Error. Please try again!`;
            }
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }

        function clearChat() {
            chatContainer.innerHTML = `
                <div class="message ai-message">
                    <span class="sender-name">Pyrox AI</span>
                    Nayi chat shuru ho chuki hai. Bolie, main aapki kya madad karoon?
                </div>
            `;
        }
    </script>
</body>
</html>
