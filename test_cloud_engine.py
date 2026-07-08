#!/usr/bin/env python
import os
import asyncio
os.environ['GOOGLE_AI_API_KEY'] = 'AIzaSyC1P_wfSs1bSZCnimdo_DvVcX3KQgt1ZcQ'

from services.services_llm_engine import CloudModelEngine

async def main():
    engine = CloudModelEngine()
    print("Available providers:")
    for provider in engine.get_available_providers():
        print(f"  {provider}")
    
    print(f"\nGemini available: {engine.is_available('gemini')}")
    
    # Test streaming
    if engine.is_available('gemini'):
        print("\nTesting Gemini stream...")
        tokens = []
        async for token in engine.generate_response_stream(
            provider='gemini',
            message='Hello',
            history=[],
            patient_id='test',
            temperature=0.7,
            max_tokens=100,
            extra_context='',
        ):
            tokens.append(token)
            print(f"Token: {token[:50]}", end="...")
        
        print(f"\nTotal tokens: {len(tokens)}")
        print(f"Full response: {''.join(tokens)[:200]}")

if __name__ == '__main__':
    asyncio.run(main())
