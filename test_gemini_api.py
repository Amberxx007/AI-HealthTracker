#!/usr/bin/env python
import asyncio
import httpx
import json
import os

api_key = 'AIzaSyC1P_wfSs1bSZCnimdo_DvVcX3KQgt1ZcQ'

async def test_gemini():
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:streamGenerateContent?alt=sse&key={api_key}"
    
    messages = [{"role": "user", "content": "Hello, how are you?"}]
    
    # Convert OpenAI-style messages to Gemini format
    system_text = ""
    contents = []
    for m in messages:
        if m["role"] == "system":
            system_text = m["content"]
        elif m["role"] == "user":
            contents.append({"role": "user", "parts": [{"text": m["content"]}]})
        elif m["role"] == "assistant":
            contents.append({"role": "model", "parts": [{"text": m["content"]}]})
    
    payload = {
        "contents": contents,
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 100},
    }
    if system_text:
        payload["systemInstruction"] = {"parts": [{"text": system_text}]}
    
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("\nStreaming response:")
    
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", url, json=payload) as resp:
                print(f"Status: {resp.status_code}")
                print(f"Headers: {dict(resp.headers)}")
                line_count = 0
                async for line in resp.aiter_lines():
                    line_count += 1
                    print(f"Line {line_count}: {line[:100]}")
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    try:
                        chunk = json.loads(data)
                        print(f"  Parsed: {json.dumps(chunk, indent=2)[:200]}")
                        parts = chunk.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                        for part in parts:
                            text = part.get("text", "")
                            if text:
                                print(f"  TEXT: {text}")
                    except (json.JSONDecodeError, KeyError, IndexError) as e:
                        print(f"  Error parsing: {e}")
                print(f"\nTotal lines received: {line_count}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_gemini())
