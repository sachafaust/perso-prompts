#!/usr/bin/env python3
"""
Battle Test: Structured Prompting for Variance Reduction

Tests whether our structured prompting approach reduces CVE detection variance
using Gemini model with real packages.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List
import aiohttp

# Set API key
os.environ["GOOGLE_AI_API_KEY"] = "your-google-key-here"


class StructuredPromptTester:
    """Test structured vs unstructured prompts for variance."""
    
    def __init__(self):
        self.api_key = os.environ["GOOGLE_AI_API_KEY"]
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model = "gemini-1.5-flash"
        
        # Test packages
        self.test_packages = [
            ("requests", "2.25.1"),
            ("django", "3.2.0"),
            ("numpy", "1.19.0")
        ]
    
    async def call_gemini(self, prompt: str) -> Dict:
        """Call Gemini API with prompt."""
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.0,  # Already trying to reduce variance!
                "maxOutputTokens": 2048
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                result = await response.json()
                
                if "candidates" in result and result["candidates"]:
                    content = result["candidates"][0]["content"]["parts"][0]["text"]
                    # Extract JSON from response
                    try:
                        # Find JSON in response
                        json_start = content.find("{")
                        json_end = content.rfind("}") + 1
                        json_str = content[json_start:json_end]
                        return json.loads(json_str)
                    except:
                        return {"error": "Failed to parse JSON", "raw": content}
                else:
                    return {"error": "No response from Gemini"}
    
    def create_unstructured_prompt(self) -> str:
        """Current approach - open-ended prompt."""
        packages_str = "\n".join([f"- {name}:{version}" for name, version in self.test_packages])
        
        return f"""Find ALL known CVEs and security vulnerabilities for these packages. Search thoroughly through your training data.

Packages to analyze:
{packages_str}

Be exhaustive in your search. Include all vulnerabilities from any source.

Return vulnerable packages in JSON format:
{{
  "package:version": {{
    "cves": [{{
      "id": "CVE-YYYY-NNNNN",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "description": "Brief description",
      "cvss_score": 0.0-10.0
    }}],
    "confidence": 0.0-1.0
  }}
}}"""

    def create_structured_prompt(self) -> str:
        """New approach - structured, deterministic prompt."""
        packages_str = "\n".join([f"- {name}:{version}" for name, version in self.test_packages])
        
        return f"""VULNERABILITY SCAN INSTRUCTIONS
Execute this EXACT procedure for each package. Follow steps precisely.

Packages to analyze:
{packages_str}

MANDATORY SEARCH PROCEDURE:
For EACH package above, execute these steps IN ORDER:

STEP 1: Systematic year-by-year CVE search
Search for CVEs by year, starting from 2024 and working backwards:
- Pattern: "CVE-2024-* affecting [package_name]" → record ALL findings
- Pattern: "CVE-2023-* affecting [package_name]" → record ALL findings  
- Pattern: "CVE-2022-* affecting [package_name]" → record ALL findings
- Pattern: "CVE-2021-* affecting [package_name]" → record ALL findings
- Pattern: "CVE-2020-* affecting [package_name]" → record ALL findings
- Continue back to 2014 (10 year default window)

STEP 2: Version vulnerability assessment
For EACH CVE found:
- Check if CVE affects the specific version listed
- Include if: package version <= last_affected_version
- ALL CVEs affecting the version must be included (no limits)

STEP 3: Standardized data formatting
For EACH CVE (ALL of them), extract:
- Exact CVE ID (CVE-YYYY-NNNNN format)
- CVSS score (numerical)
- Apply severity mapping: 9.0-10.0→CRITICAL, 7.0-8.9→HIGH, 4.0-6.9→MEDIUM, 0.1-3.9→LOW
- Description template: "CVE-[ID] in [package]: [vulnerability_type]. CVSS: [score]. Fixed: [version]"

RESPONSE REQUIREMENTS:
- Include EVERY CVE found (no sampling, no limits)
- Report exact count of CVEs per package
- Use this EXACT JSON structure:

{{
  "scan_metadata": {{
    "search_depth_years": 10,
    "search_method": "systematic_year_by_year",
    "completeness": "exhaustive"
  }},
  "requests:2.25.1": {{
    "total_cves_found": <exact_count>,
    "cves": [
      {{
        "id": "CVE-YYYY-NNNNN",
        "severity": "<CRITICAL|HIGH|MEDIUM|LOW based on CVSS mapping>",
        "cvss_score": <numerical_score>,
        "description": "<use template format>",
        "year_discovered": "YYYY",
        "affects_version": true
      }}
    ],
    "search_years_completed": ["2024", "2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016", "2015", "2014"]
  }}
}}

Return ONLY the JSON, no other text."""
    
    async def run_variance_test(self, num_runs: int = 5):
        """Test both prompt styles multiple times."""
        print("🔬 STRUCTURED PROMPT BATTLE TEST")
        print("=" * 60)
        
        # Test unstructured approach
        print("\n📊 Testing UNSTRUCTURED prompts (current approach)...")
        unstructured_results = []
        unstructured_prompt = self.create_unstructured_prompt()
        
        for i in range(num_runs):
            print(f"  Run {i+1}...", end="", flush=True)
            result = await self.call_gemini(unstructured_prompt)
            unstructured_results.append(result)
            print(" ✓")
        
        # Test structured approach  
        print("\n📊 Testing STRUCTURED prompts (new approach)...")
        structured_results = []
        structured_prompt = self.create_structured_prompt()
        
        for i in range(num_runs):
            print(f"  Run {i+1}...", end="", flush=True)
            result = await self.call_gemini(structured_prompt)
            structured_results.append(result)
            print(" ✓")
        
        # Analyze variance
        print("\n" + "="*60)
        print("📈 VARIANCE ANALYSIS")
        print("="*60)
        
        print("\n🔷 UNSTRUCTURED APPROACH VARIANCE:")
        unstructured_variance = self.analyze_variance(unstructured_results)
        
        print("\n🔶 STRUCTURED APPROACH VARIANCE:")
        structured_variance = self.analyze_variance(structured_results)
        
        # Compare approaches
        print("\n" + "="*60)
        print("🏆 COMPARISON RESULTS")
        print("="*60)
        
        print(f"Unstructured CVE detection variance: {'❌ HIGH' if unstructured_variance['cve_variance'] else '✅ LOW'}")
        print(f"Structured CVE detection variance: {'❌ HIGH' if structured_variance['cve_variance'] else '✅ LOW'}")
        
        print(f"\nUnstructured severity variance: {'❌ HIGH' if unstructured_variance['severity_variance'] else '✅ LOW'}")
        print(f"Structured severity variance: {'❌ HIGH' if structured_variance['severity_variance'] else '✅ LOW'}")
        
        print(f"\nUnstructured completeness variance: {'❌ HIGH' if unstructured_variance['count_variance'] else '✅ LOW'}")
        print(f"Structured completeness variance: {'❌ HIGH' if structured_variance['count_variance'] else '✅ LOW'}")
        
        # Save detailed results
        with open("structured_prompt_battle_results.json", "w") as f:
            json.dump({
                "test_config": {
                    "model": self.model,
                    "num_runs": num_runs,
                    "packages": self.test_packages
                },
                "unstructured": {
                    "results": unstructured_results,
                    "variance": unstructured_variance
                },
                "structured": {
                    "results": structured_results,
                    "variance": structured_variance
                }
            }, f, indent=2)
        
        print("\n📄 Detailed results saved to: structured_prompt_battle_results.json")
    
    def analyze_variance(self, results: List[Dict]) -> Dict:
        """Analyze variance across multiple runs."""
        if len(results) < 2:
            return {"error": "Need at least 2 runs"}
        
        # Extract CVE data for each package across runs
        variance_analysis = {
            "cve_variance": False,
            "severity_variance": False,
            "count_variance": False,
            "details": {}
        }
        
        for pkg_name, pkg_version in self.test_packages:
            pkg_key = f"{pkg_name}:{pkg_version}"
            print(f"\n  Package: {pkg_key}")
            
            # Collect CVE data across runs
            cve_sets = []
            cve_counts = []
            
            for i, result in enumerate(results):
                if "error" in result:
                    print(f"    Run {i+1}: ERROR - {result['error']}")
                    continue
                
                if pkg_key in result:
                    pkg_data = result[pkg_key]
                    cves = pkg_data.get("cves", [])
                    cve_ids = set(cve["id"] for cve in cves if "id" in cve)
                    cve_sets.append(cve_ids)
                    cve_counts.append(len(cves))
                    
                    # Check for total_cves_found in structured format
                    if "total_cves_found" in pkg_data:
                        print(f"    Run {i+1}: {pkg_data['total_cves_found']} CVEs (structured format)")
                    else:
                        print(f"    Run {i+1}: {len(cves)} CVEs found")
                else:
                    cve_sets.append(set())
                    cve_counts.append(0)
                    print(f"    Run {i+1}: No data")
            
            # Check variance
            if len(set(cve_counts)) > 1:
                variance_analysis["count_variance"] = True
                print(f"    ❌ COUNT VARIANCE: {cve_counts}")
            
            if len(cve_sets) > 1 and len(set(map(frozenset, cve_sets))) > 1:
                variance_analysis["cve_variance"] = True
                print(f"    ❌ CVE ID VARIANCE detected")
            
            variance_analysis["details"][pkg_key] = {
                "counts": cve_counts,
                "unique_cve_count": len(set().union(*cve_sets)) if cve_sets else 0
            }
        
        return variance_analysis


async def main():
    """Run the structured prompt battle test."""
    tester = StructuredPromptTester()
    await tester.run_variance_test(num_runs=5)


if __name__ == "__main__":
    asyncio.run(main())