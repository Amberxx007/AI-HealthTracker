#!/usr/bin/env python
import asyncio
import httpx
import json
import os

api_key = os.environ.get("GROQ_API_KEY", "").strip()
if not api_key:
    raise SystemExit("Missing env var GROQ_API_KEY")

async def test_groq():
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    messages = [{"role": "user", "content": "Hello"}]
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 100,
        "stream": True,
    }
    
    print(f"URL: {url}")
    print(f"API Key prefix: {api_key[:20]}...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("\nStreaming response:")
    
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", url, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json=payload) as resp:
                print(f"Status: {resp.status_code}")
                print(f"Headers: {dict(resp.headers)}")
                line_count = 0
                async for line in resp.aiter_lines():
                    line_count += 1
                    if line_count <= 10 or line.startswith("data: "):
                        print(f"Line {line_count}: {line[:100]}")
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    try:
                        chunk = json.loads(data)
                        token = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if token:
                            print(f"  TOKEN: {token}")
                    except (json.JSONDecodeError, KeyError, IndexError) as e:
                        print(f"  Error parsing: {e}")
                print(f"\nTotal lines received: {line_count}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_groq())
