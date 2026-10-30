import os
from groq import Groq

# Yahan apni poori ki poori API key daal de bina kisi cheez ke
client = Groq(api_key="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")

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Hello!",
        }
    ],
    model="llama3-8b-8192",
)

print(chat_completion.choices[0].message.content)
