from groq import Groq

client = Groq(
    api_key="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"
)
response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[
        {"role": "user", "content": "Hello"}
    ]
)

print(response.choices[0].message.content)