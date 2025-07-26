#!/usr/bin/env python3
"""
Test: Year Search Approaches (A vs B)

Compare explicit line-per-year vs compact systematic year instructions.
Test with Gemini to see how different AI models handle the instructions.

Approach A: Explicit line per year (verbose)
Approach B: Compact with range (efficient)
"""

import asyncio
import json
import os
import aiohttp
from typing import List, Dict

# Set API key
os.environ["GOOGLE_AI_API_KEY"] = "your-google-key-here"


class YearSearchTest:
    """Test different year search instruction approaches."""
    
    def __init__(self):
        self.test_package = "django:3.2.12"  # Known to have CVEs across multiple years
        self.num_runs = 3  # Test consistency
        
    async def call_gemini(self, prompt: str) -> str:
        """Call Gemini API."""
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
    
    def create_approach_a_prompt(self) -> str:
        """Approach A: Explicit line per year (verbose)."""
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
    
    def create_approach_b_prompt(self) -> str:
        """Approach B: Compact with range (efficient)."""
        return f"""Find ALL CVEs affecting {self.test_package}.

SYSTEMATIC YEAR-BY-YEAR SEARCH:
For EACH year from 2024 down to 2015:
- Search pattern: "CVE-[YEAR]-* affecting django:3.2.12"
- Record ALL CVEs found for that year
- Do NOT skip years even if you found CVEs in other years
- Continue through ALL 10 years: 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015

REASONING: Finding CVEs in 2023 does NOT mean you can skip 2022!
Each year may have different vulnerabilities affecting the same version.

Return ONLY JSON:
{{
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
                    "years_with_cves": sorted(years_found),
                    "total_cves": len(cve_ids),
                    "search_metadata": data.get("search_completed", {}),
                    "raw_cves": cves
                }
        except Exception as e:
            print(f"Parse error: {e}")
            return {"error": "parse_failed", "raw": response[:500]}
        
        return {"error": "no_json_found", "raw": response[:500]}
    
    async def test_approach(self, approach_name: str, prompt: str) -> List[Dict]:
        """Test an approach multiple times."""
        print(f"\n🔬 Testing {approach_name} ({self.num_runs} runs)")
        print("-" * 60)
        
        results = []
        
        for i in range(self.num_runs):
            print(f"  Run {i+1}...", end="", flush=True)
            try:
                response = await self.call_gemini(prompt)
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
    
    def analyze_approach(self, results: List[Dict], approach_name: str) -> Dict:
        """Analyze results from an approach."""
        print(f"\n📊 {approach_name} Analysis:")
        
        successful_runs = [r for r in results if "error" not in r]
        if not successful_runs:
            print("  ❌ No successful runs")
            return {"error": "no_successful_runs"}
        
        print(f"  ✅ Successful runs: {len(successful_runs)}/{len(results)}")
        
        # Collect all CVEs and years found
        all_cves = set()
        all_years = set()
        cve_lists = []
        
        for result in successful_runs:
            cves = result.get("cves", [])
            years = result.get("years_with_cves", [])
            
            all_cves.update(cves)
            all_years.update(years)
            cve_lists.append(sorted(cves))
        
        print(f"  📦 Total unique CVEs found: {len(all_cves)}")
        print(f"  📅 Years with CVEs: {sorted(list(all_years))}")
        
        # Check consistency
        unique_result_sets = set()
        for cve_list in cve_lists:
            unique_result_sets.add(frozenset(cve_list))
        
        is_consistent = len(unique_result_sets) == 1
        print(f"  🎯 Consistency: {'✅ PERFECT' if is_consistent else f'❌ VARIANT ({len(unique_result_sets)} different results)'}")
        
        if not is_consistent:
            print(f"  Variance details:")
            for i, cve_list in enumerate(cve_lists):
                print(f"    Run {i+1}: {cve_list}")
        
        # Check year coverage
        target_years = ["2024", "2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016", "2015"]
        years_searched = len(all_years)
        print(f"  📈 Year coverage: {years_searched}/10 years had CVEs")
        
        return {
            "successful_runs": len(successful_runs),
            "total_unique_cves": len(all_cves),
            "all_cves": sorted(list(all_cves)),
            "years_with_cves": sorted(list(all_years)),
            "year_coverage": years_searched,
            "is_consistent": is_consistent,
            "variance_count": len(unique_result_sets),
            "cve_lists": cve_lists,
            "raw_results": successful_runs
        }
    
    async def run_year_search_test(self):
        """Run the complete year search comparison test."""
        print("📅 YEAR SEARCH APPROACH TEST")
        print("Testing: Explicit vs Compact year search instructions with Gemini")
        print(f"Package: {self.test_package}")
        print("=" * 80)
        
        # Test Approach A (explicit line per year)
        prompt_a = self.create_approach_a_prompt()
        results_a = await self.test_approach("APPROACH A (Explicit Line Per Year)", prompt_a)
        
        # Test Approach B (compact systematic)
        prompt_b = self.create_approach_b_prompt()
        results_b = await self.test_approach("APPROACH B (Compact Systematic)", prompt_b)
        
        # Analyze results
        print("\n" + "=" * 80)
        print("📈 COMPARATIVE ANALYSIS")
        print("=" * 80)
        
        analysis_a = self.analyze_approach(results_a, "APPROACH A")
        analysis_b = self.analyze_approach(results_b, "APPROACH B")
        
        # Compare approaches
        print(f"\n🏆 HEAD-TO-HEAD COMPARISON:")
        
        if "error" not in analysis_a and "error" not in analysis_b:
            print(f"  Completeness (total unique CVEs):")
            print(f"    Approach A: {analysis_a.get('total_unique_cves', 0)} CVEs")
            print(f"    Approach B: {analysis_b.get('total_unique_cves', 0)} CVEs")
            
            print(f"  Year Coverage:")
            print(f"    Approach A: {analysis_a.get('year_coverage', 0)}/10 years")
            print(f"    Approach B: {analysis_b.get('year_coverage', 0)}/10 years")
            
            print(f"  Consistency:")
            print(f"    Approach A: {'✅ CONSISTENT' if analysis_a.get('is_consistent') else '❌ VARIANT'}")
            print(f"    Approach B: {'✅ CONSISTENT' if analysis_b.get('is_consistent') else '❌ VARIANT'}")
            
            # Determine winner
            a_cves = analysis_a.get('total_unique_cves', 0)
            b_cves = analysis_b.get('total_unique_cves', 0)
            a_years = analysis_a.get('year_coverage', 0)
            b_years = analysis_b.get('year_coverage', 0)
            a_consistent = analysis_a.get('is_consistent', False)
            b_consistent = analysis_b.get('is_consistent', False)
            
            print(f"\n🎯 VERDICT:")
            if b_cves > a_cves:
                print(f"  ✅ APPROACH B wins on completeness ({b_cves} vs {a_cves} CVEs)")
            elif a_cves > b_cves:
                print(f"  ✅ APPROACH A wins on completeness ({a_cves} vs {b_cves} CVEs)")
            else:
                print(f"  🤝 Same completeness")
                
            if b_years > a_years:
                print(f"  ✅ APPROACH B wins on year coverage ({b_years} vs {a_years} years)")
            elif a_years > b_years:
                print(f"  ✅ APPROACH A wins on year coverage ({a_years} vs {a_years} years)")
            else:
                print(f"  🤝 Same year coverage")
                
            if b_consistent and not a_consistent:
                print(f"  ✅ APPROACH B wins on consistency")
            elif a_consistent and not b_consistent:
                print(f"  ✅ APPROACH A wins on consistency")
            else:
                print(f"  🤝 Same consistency")
        
        # Save results
        with open("year_search_test_results.json", "w") as f:
            json.dump({
                "test_package": self.test_package,
                "approach_a": {
                    "name": "Explicit Line Per Year",
                    "results": results_a,
                    "analysis": analysis_a
                },
                "approach_b": {
                    "name": "Compact Systematic",
                    "results": results_b, 
                    "analysis": analysis_b
                }
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: year_search_test_results.json")


async def main():
    """Run the year search test."""
    tester = YearSearchTest()
    await tester.run_year_search_test()


if __name__ == "__main__":
    asyncio.run(main())