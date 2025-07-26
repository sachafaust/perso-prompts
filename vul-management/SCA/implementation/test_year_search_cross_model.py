#!/usr/bin/env python3
"""
Test: Year Search Across Models (OpenAI vs Grok vs Gemini)

Test if different AI models have different knowledge cutoffs or biases
for CVE discovery across years.

Hypothesis: Gemini's 2021-2022 limitation might be knowledge cutoff,
while OpenAI/Grok might find CVEs in different years.
"""

import asyncio
import json
import os
import aiohttp
from typing import List, Dict

# Set API keys
os.environ["XAI_API_KEY"] = "your-xai-key-here"
os.environ["OPENAI_API_KEY"] = "your-openai-key-here"
os.environ["GOOGLE_AI_API_KEY"] = "your-google-key-here"


class CrossModelYearTest:
    """Test year search across different AI models."""
    
    def __init__(self):
        self.test_package = "django:3.2.12"  # Known to have CVEs across multiple years
        self.num_runs = 2  # Fewer runs since we're testing across models
        
    def create_test_prompt(self) -> str:
        """Use Approach A (explicit) since it performed better."""
        return f"""Find ALL CVEs affecting {self.test_package}.

YEAR-BY-YEAR REASONING CHECKLIST (Execute each step):
1. Search CVE-2024-* affecting django:3.2.12 → Record ALL found
2. Search CVE-2023-* affecting django:3.2.12 → Record ALL found  
3. Search CVE-2022-* affecting django:3.2.12 → Record ALL found
4. Search CVE-2021-* affecting django:3.2.12 → Record ALL found
5. Search CVE-2020-* affecting django:3.2.12 → Record ALL found
6. Search CVE-2019-* affecting django:3.2.12 → Record ALL found
7. Search CVE-2018-* affecting django:3.2.12 → Record ALL found
8. Search CVE-2017-* affecting django:3.2.12 → Record ALL found
9. Search CVE-2016-* affecting django:3.2.12 → Record ALL found
10. Search CVE-2015-* affecting django:3.2.12 → Record ALL found

CRITICAL: Complete ALL 10 steps even if you find CVEs in early years.
Each year may contain different vulnerabilities affecting version 3.2.12.

Return ONLY JSON:
{{
  "model_info": "Identify which model you are",
  "search_completed": {{
    "years_searched": ["2024", "2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016", "2015"]
  }},
  "cves": [
    {{
      "id": "CVE-YYYY-NNNNN",
      "year": "YYYY", 
      "description": "Brief description"
    }}
  ]
}}"""
    
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
            "max_tokens": 3072
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
            "max_tokens": 3072
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                result = await response.json()
                if "choices" in result and result["choices"]:
                    return result["choices"][0]["message"]["content"]
                return f"ERROR: {result}"
    
    async def call_gemini(self, prompt: str) -> str:
        """Call Google Gemini."""
        api_key = os.environ["GOOGLE_AI_API_KEY"]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": 3072
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                result = await response.json()
                if "candidates" in result and result["candidates"]:
                    return result["candidates"][0]["content"]["parts"][0]["text"]
                return f"ERROR: {result}"
    
    def extract_results(self, response: str) -> Dict:
        """Extract CVE data and metadata from response."""
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                # Extract CVE IDs and years
                cves = data.get("cves", [])
                cve_ids = [cve.get("id", "") for cve in cves if cve.get("id")]
                years_found = list(set([cve.get("year", "") for cve in cves if cve.get("year")]))
                
                return {
                    "cves": cve_ids,
                    "years_with_cves": sorted([y for y in years_found if y]),
                    "total_cves": len(cve_ids),
                    "model_info": data.get("model_info", "Unknown"),
                    "search_metadata": data.get("search_completed", {}),
                    "raw_cves": cves
                }
        except Exception as e:
            print(f"Parse error: {e}")
            return {"error": "parse_failed", "raw": response[:500]}
        
        return {"error": "no_json_found", "raw": response[:500]}
    
    async def test_model(self, model_name: str, call_func) -> List[Dict]:
        """Test a model multiple times."""
        print(f"\n🤖 Testing {model_name} ({self.num_runs} runs)")
        print("-" * 60)
        
        prompt = self.create_test_prompt()
        results = []
        
        for i in range(self.num_runs):
            print(f"  Run {i+1}...", end="", flush=True)
            try:
                response = await call_func(prompt)
                result = self.extract_results(response)
                results.append(result)
                
                if "error" not in result:
                    cve_count = result.get("total_cves", 0)
                    years = result.get("years_with_cves", [])
                    print(f" ✓ {cve_count} CVEs across {len(years)} years: {years}")
                else:
                    print(f" ❌ {result['error']}")
                    
            except Exception as e:
                print(f" ❌ Exception: {e}")
                results.append({"error": "exception", "details": str(e)})
        
        return results
    
    def analyze_model_results(self, results: List[Dict], model_name: str) -> Dict:
        """Analyze results from a model."""
        print(f"\n📊 {model_name} Analysis:")
        
        successful_runs = [r for r in results if "error" not in r]
        if not successful_runs:
            print("  ❌ No successful runs")
            return {"error": "no_successful_runs"}
        
        print(f"  ✅ Successful runs: {len(successful_runs)}/{len(results)}")
        
        # Collect all CVEs and years found
        all_cves = set()
        all_years = set()
        
        for result in successful_runs:
            cves = result.get("cves", [])
            years = result.get("years_with_cves", [])
            
            all_cves.update(cves)
            all_years.update(years)
        
        print(f"  📦 Total unique CVEs found: {len(all_cves)}")
        print(f"  📅 Years with CVEs: {sorted(list(all_years))}")
        print(f"  🎯 Year span: {min(all_years) if all_years else 'N/A'} to {max(all_years) if all_years else 'N/A'}")
        
        # Show some example CVEs
        if all_cves:
            sample_cves = sorted(list(all_cves))[:5]
            print(f"  🔍 Sample CVEs: {sample_cves}")
        
        return {
            "model_name": model_name,
            "successful_runs": len(successful_runs),
            "total_unique_cves": len(all_cves),
            "all_cves": sorted(list(all_cves)),
            "years_with_cves": sorted(list(all_years)),
            "year_span": {"min": min(all_years) if all_years else None, "max": max(all_years) if all_years else None},
            "year_coverage": len(all_years),
            "raw_results": successful_runs
        }
    
    async def run_cross_model_test(self):
        """Run the complete cross-model year test."""
        print("🌐 CROSS-MODEL YEAR SEARCH TEST")
        print("Testing: Do different AI models have different year coverage/knowledge cutoffs?")
        print(f"Package: {self.test_package}")
        print("=" * 80)
        
        # Test all models
        model_analyses = []
        
        # OpenAI
        try:
            openai_results = await self.test_model("OpenAI GPT-4o-mini", self.call_openai)
            openai_analysis = self.analyze_model_results(openai_results, "OpenAI")
            model_analyses.append(openai_analysis)
        except Exception as e:
            print(f"❌ OpenAI failed: {e}")
        
        # Grok
        try:
            grok_results = await self.test_model("X.AI Grok-3", self.call_grok)
            grok_analysis = self.analyze_model_results(grok_results, "Grok")
            model_analyses.append(grok_analysis)
        except Exception as e:
            print(f"❌ Grok failed: {e}")
        
        # Gemini (for comparison)
        try:
            gemini_results = await self.test_model("Google Gemini", self.call_gemini)
            gemini_analysis = self.analyze_model_results(gemini_results, "Gemini")
            model_analyses.append(gemini_analysis)
        except Exception as e:
            print(f"❌ Gemini failed: {e}")
        
        # Cross-model comparison
        print("\n" + "=" * 80)
        print("🔄 CROSS-MODEL COMPARISON")
        print("=" * 80)
        
        if len(model_analyses) >= 2:
            print(f"\n📊 Model Performance Summary:")
            for analysis in model_analyses:
                if "error" not in analysis:
                    model = analysis["model_name"]
                    cves = analysis["total_unique_cves"]
                    years = analysis["years_with_cves"]
                    span = analysis["year_span"]
                    print(f"  {model}:")
                    print(f"    CVEs found: {cves}")
                    print(f"    Years covered: {len(years)}/10 → {years}")
                    print(f"    Year span: {span['min']} to {span['max']}" if span['min'] else "    Year span: No CVEs found")
            
            # Check for knowledge cutoff patterns
            print(f"\n🕐 Knowledge Cutoff Analysis:")
            all_models_years = set()
            for analysis in model_analyses:
                if "error" not in analysis:
                    all_models_years.update(analysis["years_with_cves"])
            
            print(f"  Combined years across all models: {sorted(list(all_models_years))}")
            
            # Check if models find different year ranges
            year_sets_by_model = []
            for analysis in model_analyses:
                if "error" not in analysis:
                    year_sets_by_model.append(set(analysis["years_with_cves"]))
            
            if len(set(map(frozenset, year_sets_by_model))) > 1:
                print(f"  ❗ DIFFERENT YEAR COVERAGE detected across models")
                for i, analysis in enumerate(model_analyses):
                    if "error" not in analysis:
                        print(f"    {analysis['model_name']}: {analysis['years_with_cves']}")
            else:
                print(f"  ✅ All models found CVEs in same years")
            
            # Check for 2023-2024 coverage (recent years)
            recent_years = {"2023", "2024"}
            models_with_recent = []
            for analysis in model_analyses:
                if "error" not in analysis:
                    model_years = set(analysis["years_with_cves"])
                    if recent_years.intersection(model_years):
                        models_with_recent.append(analysis["model_name"])
            
            if models_with_recent:
                print(f"  🚀 Models finding 2023-2024 CVEs: {models_with_recent}")
            else:
                print(f"  📅 NO models found 2023-2024 CVEs (possible knowledge cutoff)")
        
        # Save results
        with open("cross_model_year_test_results.json", "w") as f:
            json.dump({
                "test_package": self.test_package,
                "model_analyses": model_analyses,
                "summary": {
                    "total_models_tested": len(model_analyses),
                    "combined_unique_cves": len(set().union(*[set(a.get("all_cves", [])) for a in model_analyses if "error" not in a])),
                    "combined_years": sorted(list(set().union(*[set(a.get("years_with_cves", [])) for a in model_analyses if "error" not in a])))
                }
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: cross_model_year_test_results.json")


async def main():
    """Run the cross-model year test."""
    tester = CrossModelYearTest()
    await tester.run_cross_model_test()


if __name__ == "__main__":
    asyncio.run(main())