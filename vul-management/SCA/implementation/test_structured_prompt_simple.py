#!/usr/bin/env python3
"""
Simple test to check if structured prompts improve consistency.
Uses a single package with known vulnerabilities.
"""

import asyncio
import json
import os
import aiohttp

# Set API key
os.environ["GOOGLE_AI_API_KEY"] = "your-google-key-here"


async def call_gemini_simple(prompt: str) -> str:
    """Call Gemini and return raw response."""
    api_key = os.environ["GOOGLE_AI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": 2048
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            result = await response.json()
            if "candidates" in result and result["candidates"]:
                return result["candidates"][0]["content"]["parts"][0]["text"]
            return "ERROR: No response"


async def test_variance():
    """Test variance with simple prompts."""
    
    # Test package known to have CVEs
    test_package = "log4j:2.14.1"  # Known Log4Shell vulnerability
    
    print("🔬 TESTING PROMPT VARIANCE")
    print("Package:", test_package)
    print("="*60)
    
    # Unstructured prompt
    unstructured_prompt = f"""Find all CVEs for {test_package}. Return only JSON with format:
{{
  "cves": ["CVE-YYYY-NNNNN", ...]
}}"""
    
    # Structured prompt
    structured_prompt = f"""INSTRUCTIONS:
1. List CVEs for {test_package} starting from 2021
2. Include CVE-2021-44228 (Log4Shell) if it affects version 2.14.1
3. Include CVE-2021-45046 if it affects version 2.14.1
4. Include CVE-2021-45105 if it affects version 2.14.1
5. Return ONLY this exact JSON structure:

{{
  "cves": ["CVE-YYYY-NNNNN", ...]
}}"""
    
    print("\n📊 UNSTRUCTURED PROMPT RESULTS:")
    for i in range(3):
        result = await call_gemini_simple(unstructured_prompt)
        print(f"\nRun {i+1}:")
        print(result[:200] + "..." if len(result) > 200 else result)
    
    print("\n" + "="*60)
    print("\n📊 STRUCTURED PROMPT RESULTS:")
    for i in range(3):
        result = await call_gemini_simple(structured_prompt)
        print(f"\nRun {i+1}:")
        print(result[:200] + "..." if len(result) > 200 else result)


if __name__ == "__main__":
    asyncio.run(test_variance())