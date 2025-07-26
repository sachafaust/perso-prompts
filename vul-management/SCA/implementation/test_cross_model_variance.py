#!/usr/bin/env python3
"""
Cross-Model Variance Test

Tests structured vs unstructured prompts across multiple AI models:
- Grok (X.AI)  
- OpenAI GPT-4o-mini
- Gemini (baseline from previous test)

Hypothesis: Variance should occur BETWEEN models, not WITHIN same model runs.
"""

import asyncio
import json
import os
import aiohttp
from typing import Dict, List

# Set API keys
os.environ["XAI_API_KEY"] = "your-xai-key-here"
os.environ["OPENAI_API_KEY"] = "your-openai-key-here"
os.environ["GOOGLE_AI_API_KEY"] = "your-google-key-here"


class CrossModelVarianceTester:
    """Test variance across different AI models."""
    
    def __init__(self):
        self.test_package = "log4j:2.14.1"  # Known vulnerabilities
        self.num_runs = 3  # Runs per model per prompt type
        
    def get_prompts(self):
        """Get unstructured and structured prompts."""
        unstructured = f"""Find all CVEs affecting {self.test_package}. Return JSON:
{{
  "cves": ["CVE-YYYY-NNNNN", ...]
}}"""
        
        structured = f"""EXACT INSTRUCTIONS for {self.test_package}:
1. Check if CVE-2021-44228 (Log4Shell) affects version 2.14.1 → include if yes
2. Check if CVE-2021-45046 affects version 2.14.1 → include if yes  
3. Check if CVE-2021-45105 affects version 2.14.1 → include if yes
4. Search for ANY other CVE-2021-* affecting log4j 2.14.1 → include all found

Return ONLY this JSON:
{{
  "cves": ["CVE-YYYY-NNNNN", ...]
}}"""
        
        return unstructured, structured
    
    async def call_openai(self, prompt: str) -> str:
        """Call OpenAI GPT-4o-mini."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 1024
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                result = await response.json()
                if "choices" in result and result["choices"]:
                    return result["choices"][0]["message"]["content"]
                return f"ERROR: {result}"
    
    async def call_grok(self, prompt: str) -> str:
        """Call X.AI Grok."""
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {os.environ['XAI_API_KEY']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "grok-3",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 1024
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                result = await response.json()
                if "choices" in result and result["choices"]:
                    return result["choices"][0]["message"]["content"]
                return f"ERROR: {result}"
    
    async def call_gemini(self, prompt: str) -> str:
        """Call Google Gemini."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={os.environ['GOOGLE_AI_API_KEY']}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": 1024
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                result = await response.json()
                if "candidates" in result and result["candidates"]:
                    return result["candidates"][0]["content"]["parts"][0]["text"]
                return f"ERROR: {result}"
    
    def extract_cves(self, response: str) -> List[str]:
        """Extract CVE IDs from response."""
        try:
            # Try to extract JSON
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                return data.get("cves", [])
        except:
            pass
        
        # Fallback: extract CVE patterns
        import re
        cve_pattern = r'CVE-\d{4}-\d{4,7}'
        return list(set(re.findall(cve_pattern, response)))
    
    async def test_model(self, model_name: str, call_func) -> Dict:
        """Test a single model with both prompt types."""
        print(f"\n🤖 Testing {model_name}")
        print("-" * 40)
        
        unstructured_prompt, structured_prompt = self.get_prompts()
        results = {
            "model": model_name,
            "unstructured": [],
            "structured": []
        }
        
        # Test unstructured prompts
        print(f"  📝 Unstructured runs:")
        for i in range(self.num_runs):
            try:
                response = await call_func(unstructured_prompt)
                cves = self.extract_cves(response)
                results["unstructured"].append(cves)
                print(f"    Run {i+1}: {len(cves)} CVEs - {sorted(cves)}")
            except Exception as e:
                print(f"    Run {i+1}: ERROR - {e}")
                results["unstructured"].append([])
        
        # Test structured prompts
        print(f"  📋 Structured runs:")
        for i in range(self.num_runs):
            try:
                response = await call_func(structured_prompt)
                cves = self.extract_cves(response)
                results["structured"].append(cves)
                print(f"    Run {i+1}: {len(cves)} CVEs - {sorted(cves)}")
            except Exception as e:
                print(f"    Run {i+1}: ERROR - {e}")
                results["structured"].append([])
        
        return results
    
    def analyze_within_model_variance(self, results: Dict) -> Dict:
        """Analyze variance within same model runs."""
        analysis = {
            "model": results["model"],
            "unstructured_variance": False,
            "structured_variance": False,
            "unstructured_sets": [],
            "structured_sets": []
        }
        
        # Check unstructured variance
        unstructured_sets = [set(cves) for cves in results["unstructured"]]
        analysis["unstructured_sets"] = [sorted(list(s)) for s in unstructured_sets]
        analysis["unstructured_variance"] = len(set(map(frozenset, unstructured_sets))) > 1
        
        # Check structured variance
        structured_sets = [set(cves) for cves in results["structured"]]
        analysis["structured_sets"] = [sorted(list(s)) for s in structured_sets]
        analysis["structured_variance"] = len(set(map(frozenset, structured_sets))) > 1
        
        return analysis
    
    async def run_cross_model_test(self):
        """Run the complete cross-model variance test."""
        print("🔬 CROSS-MODEL VARIANCE TEST")
        print("Testing hypothesis: Variance between models, NOT within same model")
        print("=" * 80)
        
        # Test all models
        model_results = []
        
        # OpenAI
        try:
            openai_results = await self.test_model("OpenAI GPT-4o-mini", self.call_openai)
            model_results.append(openai_results)
        except Exception as e:
            print(f"❌ OpenAI failed: {e}")
        
        # Grok
        try:
            grok_results = await self.test_model("X.AI Grok-3", self.call_grok)
            model_results.append(grok_results)
        except Exception as e:
            print(f"❌ Grok failed: {e}")
        
        # Gemini
        try:
            gemini_results = await self.test_model("Google Gemini", self.call_gemini)
            model_results.append(gemini_results)
        except Exception as e:
            print(f"❌ Gemini failed: {e}")
        
        # Analyze results
        print("\n" + "=" * 80)
        print("📊 WITHIN-MODEL VARIANCE ANALYSIS")
        print("=" * 80)
        
        variance_analyses = []
        for results in model_results:
            analysis = self.analyze_within_model_variance(results)
            variance_analyses.append(analysis)
            
            print(f"\n🤖 {analysis['model']}:")
            print(f"   Unstructured variance: {'❌ YES' if analysis['unstructured_variance'] else '✅ NO'}")
            if analysis['unstructured_variance']:
                for i, cve_set in enumerate(analysis['unstructured_sets']):
                    print(f"     Run {i+1}: {cve_set}")
            
            print(f"   Structured variance: {'❌ YES' if analysis['structured_variance'] else '✅ NO'}")
            if analysis['structured_variance']:
                for i, cve_set in enumerate(analysis['structured_sets']):
                    print(f"     Run {i+1}: {cve_set}")
        
        # Cross-model comparison
        print("\n" + "=" * 80)
        print("🔄 CROSS-MODEL COMPARISON")
        print("=" * 80)
        
        if len(variance_analyses) >= 2:
            # Compare unstructured results across models
            print("\n📝 Unstructured results across models:")
            unstructured_first_runs = []
            for analysis in variance_analyses:
                if analysis['unstructured_sets']:
                    first_run = set(analysis['unstructured_sets'][0])
                    unstructured_first_runs.append((analysis['model'], sorted(list(first_run))))
            
            for model, cves in unstructured_first_runs:
                print(f"   {model}: {cves}")
            
            cross_model_unstructured_variance = len(set(map(frozenset, [set(cves) for _, cves in unstructured_first_runs]))) > 1
            print(f"\nCross-model unstructured variance: {'❌ YES' if cross_model_unstructured_variance else '✅ NO'}")
            
            # Compare structured results across models
            print("\n📋 Structured results across models:")
            structured_first_runs = []
            for analysis in variance_analyses:
                if analysis['structured_sets']:
                    first_run = set(analysis['structured_sets'][0])
                    structured_first_runs.append((analysis['model'], sorted(list(first_run))))
            
            for model, cves in structured_first_runs:
                print(f"   {model}: {cves}")
            
            cross_model_structured_variance = len(set(map(frozenset, [set(cves) for _, cves in structured_first_runs]))) > 1
            print(f"\nCross-model structured variance: {'❌ YES' if cross_model_structured_variance else '✅ NO'}")
        
        # Final hypothesis validation
        print("\n" + "=" * 80)
        print("🎯 HYPOTHESIS VALIDATION")
        print("=" * 80)
        
        within_model_variance_detected = any(
            analysis['unstructured_variance'] or analysis['structured_variance'] 
            for analysis in variance_analyses
        )
        
        if within_model_variance_detected:
            print("❌ HYPOTHESIS REJECTED: Found variance WITHIN same model runs")
            print("💡 This suggests non-deterministic behavior even with temperature=0")
        else:
            print("✅ HYPOTHESIS SUPPORTED: No variance within same model runs")
            print("💡 Variance only occurs between different models")
        
        # Save results
        with open("cross_model_variance_results.json", "w") as f:
            json.dump({
                "test_package": self.test_package,
                "model_results": model_results,
                "variance_analyses": variance_analyses,
                "hypothesis_supported": not within_model_variance_detected
            }, f, indent=2)
        
        print("\n📄 Detailed results saved to: cross_model_variance_results.json")


async def main():
    """Run the cross-model variance test."""
    tester = CrossModelVarianceTester()
    await tester.run_cross_model_test()


if __name__ == "__main__":
    asyncio.run(main())