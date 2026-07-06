import requests

url = "http://localhost:8080/v1/chat/completions"

payload = {
    "model": "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
    "messages": [
        {"role": "user", "content": "I have chest tightness and breathlessness"}
    ]
}

r = requests.post(url, json=payload)
print(r.json())
