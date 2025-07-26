#!/usr/bin/env python3
"""
Test: Reasoning Guidance for CVE Completeness

Hypothesis: AI applies implicit selection logic rather than true inclusion.
Solution: Add explicit reasoning guidance about why to include "similar" CVEs.

Test Design:
- Use cryptography:36.0.1 (known to have temporally close CVEs)
- Compare current approach vs reasoning-enhanced approach
- Run multiple times to measure consistency improvement
"""

import asyncio
import json
import os
import aiohttp
from typing import List, Dict

# Set API key
os.environ["XAI_API_KEY"] = "your-xai-key-here"


class ReasoningGuidanceTest:
    """Test reasoning guidance to improve CVE completeness."""
    
    def __init__(self):
        self.test_package = "cryptography:36.0.1"  # Known to have multiple 2023 CVEs
        self.num_runs = 5  # More runs to see patterns
        
    async def call_grok(self, prompt: str) -> str:
        """Call Grok API."""
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {os.environ['XAI_API_KEY']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "grok-3",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 2048
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                result = await response.json()
                if "choices" in result and result["choices"]:
                    return result["choices"][0]["message"]["content"]
                return f"ERROR: {result}"
    
    def create_current_prompt(self) -> str:
        """Current approach - basic 'include all' instruction."""
        return f"""Find ALL known CVEs affecting {self.test_package}.

Search systematically:
1. Check CVE-2024-* affecting cryptography
2. Check CVE-2023-* affecting cryptography  
3. Check CVE-2022-* affecting cryptography
4. Include ALL CVEs that affect version 36.0.1

Return ONLY JSON:
{{
  "cves": [
    {{
      "id": "CVE-YYYY-NNNNN",
      "year": "YYYY",
      "description": "Brief description"
    }}
  ]
}}"""
    
    def create_reasoning_enhanced_prompt(self) -> str:
        """Enhanced approach with explicit reasoning guidance."""
        return f"""Find ALL known CVEs affecting {self.test_package}.

CRITICAL REASONING GUIDANCE:
Each CVE ID represents a DISTINCT vulnerability. NEVER consolidate or choose between CVEs.

WHY YOU MUST INCLUDE ALL CVEs:
1. CVE-2023-0286 ≠ CVE-2023-50782 even if both affect cryptography in 2023
2. Different CVEs = different attack vectors, patches, impacts  
3. Security teams need the COMPLETE vulnerability surface
4. "Similar" CVEs often have different version ranges or conditions

REASONING CHECKLIST for each CVE found:
- Does this CVE ID affect version 36.0.1? → If YES, include it
- Is this a different CVE ID than others I found? → If YES, include it
- Does it matter if this CVE seems similar to another? → NO, include both
- Should I pick the "more important" one? → NO, include all

EXAMPLES of what to include:
- If you find CVE-2023-0286 (timing attack) AND CVE-2023-50782 (DoS) → Include BOTH
- If you find CVE-2022-3602 (buffer overflow) AND CVE-2022-XXXXX (other) → Include BOTH
- Never think "these look similar, I'll pick one"

Search systematically:
1. Check CVE-2024-* affecting cryptography → include ALL found
2. Check CVE-2023-* affecting cryptography → include ALL found
3. Check CVE-2022-* affecting cryptography → include ALL found

Return ONLY JSON with ALL distinct CVE IDs found:
{{
  "cves": [
    {{
      "id": "CVE-YYYY-NNNNN", 
      "year": "YYYY",
      "description": "Brief description"
    }}
  ]
}}"""
    
    def extract_cves(self, response: str) -> List[Dict]:
        """Extract CVE data from response."""
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                return data.get("cves", [])
        except Exception as e:
            print(f"Parse error: {e}")
            return []
        return []
    
    async def test_approach(self, approach_name: str, prompt: str) -> List[List[str]]:
        """Test an approach multiple times."""
        print(f"\n🔬 Testing {approach_name} ({self.num_runs} runs)")
        print("-" * 50)
        
        results = []
        cve_id_lists = []
        
        for i in range(self.num_runs):
            print(f"  Run {i+1}...", end="", flush=True)
            try:
                response = await self.call_grok(prompt)
                cves = self.extract_cves(response)
                cve_ids = [cve.get("id", "") for cve in cves if cve.get("id")]
                cve_ids = [cve_id for cve_id in cve_ids if cve_id]  # Remove empty strings
                
                results.append(cves)
                cve_id_lists.append(sorted(cve_ids))
                
                print(f" ✓ {len(cve_ids)} CVEs: {sorted(cve_ids)}")
                
            except Exception as e:
                print(f" ❌ Error: {e}")
                results.append([])
                cve_id_lists.append([])
        
        return cve_id_lists
    
    def analyze_consistency(self, cve_lists: List[List[str]], approach_name: str) -> Dict:
        """Analyze consistency across runs."""
        print(f"\n📊 {approach_name} Analysis:")
        
        if not cve_lists:
            return {"error": "No results"}
        
        # Get all unique CVEs found across all runs
        all_cves = set()
        for cve_list in cve_lists:
            all_cves.update(cve_list)
        
        print(f"  Total unique CVEs found: {len(all_cves)}")
        if all_cves:
            print(f"  CVEs: {sorted(list(all_cves))}")
        
        # Check consistency
        unique_sets = set()
        for cve_list in cve_lists:
            unique_sets.add(frozenset(cve_list))
        
        is_consistent = len(unique_sets) == 1
        print(f"  Consistency: {'✅ PERFECT' if is_consistent else f'❌ VARIANT ({len(unique_sets)} different results)'}")
        
        # Show variance details if inconsistent
        if not is_consistent:
            print(f"  Variance details:")
            for i, cve_list in enumerate(cve_lists):
                print(f"    Run {i+1}: {cve_list}")
        
        # Calculate completeness metrics
        max_cves = max(len(cve_list) for cve_list in cve_lists) if cve_lists else 0
        min_cves = min(len(cve_list) for cve_list in cve_lists) if cve_lists else 0
        avg_cves = sum(len(cve_list) for cve_list in cve_lists) / len(cve_lists) if cve_lists else 0
        
        return {
            "unique_cves_found": len(all_cves),
            "all_cves": sorted(list(all_cves)),
            "is_consistent": is_consistent,
            "variance_count": len(unique_sets),
            "max_cves_per_run": max_cves,
            "min_cves_per_run": min_cves,
            "avg_cves_per_run": avg_cves,
            "run_details": cve_lists
        }
    
    async def run_reasoning_test(self):
        """Run the complete reasoning guidance test."""
        print("🧠 REASONING GUIDANCE TEST")
        print("Testing: Does explicit reasoning improve CVE completeness?")
        print(f"Package: {self.test_package}")
        print("=" * 70)
        
        # Test current approach
        current_prompt = self.create_current_prompt()
        current_results = await self.test_approach("CURRENT APPROACH", current_prompt)
        
        # Test reasoning-enhanced approach  
        reasoning_prompt = self.create_reasoning_enhanced_prompt()
        reasoning_results = await self.test_approach("REASONING ENHANCED", reasoning_prompt)
        
        # Analyze results
        print("\n" + "=" * 70)
        print("📈 COMPARATIVE ANALYSIS")
        print("=" * 70)
        
        current_analysis = self.analyze_consistency(current_results, "CURRENT")
        reasoning_analysis = self.analyze_consistency(reasoning_results, "REASONING ENHANCED")
        
        # Compare approaches
        print(f"\n🏆 COMPARISON:")
        print(f"  Completeness (unique CVEs found):")
        print(f"    Current: {current_analysis.get('unique_cves_found', 0)} CVEs")
        print(f"    Reasoning: {reasoning_analysis.get('unique_cves_found', 0)} CVEs")
        
        print(f"  Consistency:")
        print(f"    Current: {'✅ CONSISTENT' if current_analysis.get('is_consistent') else '❌ VARIANT'}")
        print(f"    Reasoning: {'✅ CONSISTENT' if reasoning_analysis.get('is_consistent') else '❌ VARIANT'}")
        
        print(f"  Average CVEs per run:")
        print(f"    Current: {current_analysis.get('avg_cves_per_run', 0):.1f}")
        print(f"    Reasoning: {reasoning_analysis.get('avg_cves_per_run', 0):.1f}")
        
        # Determine if reasoning guidance helped
        reasoning_improvement = reasoning_analysis.get('unique_cves_found', 0) > current_analysis.get('unique_cves_found', 0)
        consistency_improvement = reasoning_analysis.get('is_consistent', False) and not current_analysis.get('is_consistent', False)
        
        print(f"\n🎯 VERDICT:")
        if reasoning_improvement:
            print(f"  ✅ REASONING ENHANCED found more CVEs ({reasoning_analysis.get('unique_cves_found', 0)} vs {current_analysis.get('unique_cves_found', 0)})")
        elif reasoning_analysis.get('unique_cves_found', 0) == current_analysis.get('unique_cves_found', 0):
            print(f"  🤝 Same completeness between approaches")
        else:
            print(f"  ❌ Current approach found more CVEs")
            
        if consistency_improvement:
            print(f"  ✅ REASONING ENHANCED improved consistency")
        elif reasoning_analysis.get('is_consistent') == current_analysis.get('is_consistent'):
            print(f"  🤝 Same consistency between approaches")
        else:
            print(f"  ❌ Reasoning guidance didn't improve consistency")
        
        # Check for CVEs that appear inconsistently  
        current_cves = set(current_analysis.get('all_cves', []))
        reasoning_cves = set(reasoning_analysis.get('all_cves', []))
        
        only_current = current_cves - reasoning_cves
        only_reasoning = reasoning_cves - current_cves
        
        if only_current:
            print(f"  📝 Only found by current: {sorted(list(only_current))}")
        if only_reasoning:
            print(f"  🧠 Only found by reasoning: {sorted(list(only_reasoning))}")
        
        # Save results
        with open("reasoning_guidance_test_results.json", "w") as f:
            json.dump({
                "test_package": self.test_package,
                "current_approach": {
                    "results": current_results,
                    "analysis": current_analysis
                },
                "reasoning_enhanced": {
                    "results": reasoning_results,
                    "analysis": reasoning_analysis
                },
                "hypothesis_validated": reasoning_improvement or consistency_improvement
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: reasoning_guidance_test_results.json")


async def main():
    """Run the reasoning guidance test."""
    tester = ReasoningGuidanceTest()
    await tester.run_reasoning_test()


if __name__ == "__main__":
    asyncio.run(main())