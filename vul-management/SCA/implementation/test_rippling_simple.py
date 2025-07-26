#!/usr/bin/env python3
"""
Simplified Real-World Test: Rippling Packages

Quick test using manually selected packages that we know exist in Rippling.
Tests structured vs unstructured prompts for consistency and completeness.
"""

import asyncio
import json
import os
from typing import Dict, List
import aiohttp

# Set API key
os.environ["XAI_API_KEY"] = "your-xai-key-here"


class RipplingSimpleTest:
    """Simplified test with known Rippling-style packages."""
    
    def __init__(self):
        # Common enterprise packages likely to be in Rippling
        self.test_packages = [
            {"name": "django", "version": "3.2.12"},
            {"name": "requests", "version": "2.27.1"},
            {"name": "psycopg2", "version": "2.9.1"},
            {"name": "celery", "version": "5.2.3"},
            {"name": "redis", "version": "4.1.4"},
            {"name": "boto3", "version": "1.21.21"},
            {"name": "flask", "version": "2.0.3"},
            {"name": "sqlalchemy", "version": "1.4.32"},
            {"name": "pyjwt", "version": "2.3.0"},
            {"name": "cryptography", "version": "36.0.1"}
        ]
        
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
            "max_tokens": 4096
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                result = await response.json()
                if "choices" in result and result["choices"]:
                    return result["choices"][0]["message"]["content"]
                return f"ERROR: {result}"
    
    def create_unstructured_prompt(self) -> str:
        """Current open-ended approach."""
        pkg_list = "\n".join([f"- {pkg['name']}:{pkg['version']}" for pkg in self.test_packages])
        
        return f"""Find ALL known CVEs and security vulnerabilities for these enterprise Python packages. Be comprehensive.

Packages to analyze:
{pkg_list}

Search thoroughly for all vulnerabilities affecting each package version. Include:
- All CVEs from any source
- Security advisories and patches  
- Known vulnerabilities from vulnerability databases
- Supply chain issues

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
}}

Omit packages with no vulnerabilities."""
    
    def create_structured_prompt(self) -> str:
        """Structured systematic approach."""
        pkg_list = "\n".join([f"- {pkg['name']}:{pkg['version']}" for pkg in self.test_packages])
        
        return f"""SYSTEMATIC CVE ANALYSIS for enterprise Python packages.

Packages to analyze:
{pkg_list}

EXECUTE THIS EXACT SEARCH PROCEDURE:

For EACH package above:
1. Search CVE-2024-* affecting [package_name] → record ALL
2. Search CVE-2023-* affecting [package_name] → record ALL  
3. Search CVE-2022-* affecting [package_name] → record ALL
4. Search CVE-2021-* affecting [package_name] → record ALL
5. Search CVE-2020-* affecting [package_name] → record ALL
6. Continue to 2019, 2018, 2017, 2016, 2015

For each CVE found:
- Check if it affects the specific version listed
- Apply CVSS mapping: 9.0-10.0→CRITICAL, 7.0-8.9→HIGH, 4.0-6.9→MEDIUM, 0.1-3.9→LOW
- Use description format: "CVE-[ID] in [package]: [type]. CVSS: [score]"

Include ALL vulnerable packages with ALL their CVEs (no limits).

Return ONLY this JSON:
{{
  "search_metadata": {{
    "packages_analyzed": {len(self.test_packages)},
    "search_years": ["2024", "2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016", "2015"],
    "method": "systematic"
  }},
  "package:version": {{
    "total_cves": <count>,
    "cves": [
      {{
        "id": "CVE-YYYY-NNNNN",
        "severity": "CRITICAL|HIGH|MEDIUM|LOW",
        "cvss_score": <number>,
        "description": "<formatted_description>",
        "year": "YYYY"
      }}
    ],
    "confidence": 0.0-1.0
  }}
}}"""
    
    def extract_vulnerability_data(self, response: str) -> Dict:
        """Extract JSON from response."""
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            return {"error": "parse_failed", "details": str(e), "raw": response[:300]}
        
        return {"error": "no_json", "raw": response[:300]}
    
    def analyze_run_results(self, results: List[Dict], approach_name: str):
        """Analyze results from multiple runs."""
        print(f"\n📊 {approach_name.upper()} ANALYSIS:")
        
        if not results:
            print("  ❌ No results to analyze")
            return {"error": "no_results"}
        
        # Count successful runs
        successful_runs = [r for r in results if "error" not in r]
        print(f"  ✅ Successful runs: {len(successful_runs)}/{len(results)}")
        
        if len(successful_runs) < 2:
            print("  ⚠️  Need at least 2 successful runs for variance analysis")
            return {"successful_runs": len(successful_runs)}
        
        # Extract all packages found across runs
        all_packages_found = set()
        for result in successful_runs:
            for key in result.keys():
                if ":" in key and key not in ["search_metadata"]:
                    all_packages_found.add(key)
        
        print(f"  📦 Unique packages found: {len(all_packages_found)}")
        
        # Check consistency for each package
        consistent_packages = 0
        variant_packages = 0
        
        for package in all_packages_found:
            print(f"\n    📦 {package}:")
            
            # Get CVE data across runs
            cve_sets_by_run = []
            for i, result in enumerate(successful_runs):
                if package in result and "cves" in result[package]:
                    cves = result[package]["cves"]
                    cve_ids = set(cve["id"] for cve in cves if "id" in cve)
                    cve_sets_by_run.append(cve_ids)
                    print(f"      Run {i+1}: {len(cve_ids)} CVEs {sorted(list(cve_ids))}")
                else:
                    cve_sets_by_run.append(set())
                    print(f"      Run {i+1}: Not found")
            
            # Check if all runs produced same CVEs
            unique_cve_sets = set(map(frozenset, cve_sets_by_run))
            if len(unique_cve_sets) == 1:
                consistent_packages += 1
                print(f"      ✅ CONSISTENT")
            else:
                variant_packages += 1
                print(f"      ❌ VARIANT ({len(unique_cve_sets)} different results)")
        
        consistency_percentage = (consistent_packages / len(all_packages_found) * 100) if all_packages_found else 0
        
        return {
            "successful_runs": len(successful_runs),
            "total_packages": len(all_packages_found),
            "consistent_packages": consistent_packages,
            "variant_packages": variant_packages,
            "consistency_percentage": consistency_percentage,
            "packages_found": sorted(list(all_packages_found))
        }
    
    async def run_test(self):
        """Run the simplified real-world test."""
        print("🔬 SIMPLIFIED RIPPLING-STYLE TEST")
        print("Testing with enterprise Python packages likely in production")
        print("=" * 70)
        
        print(f"📦 Testing {len(self.test_packages)} packages:")
        for pkg in self.test_packages:
            print(f"  - {pkg['name']}:{pkg['version']}")
        
        unstructured_prompt = self.create_unstructured_prompt()
        structured_prompt = self.create_structured_prompt()
        
        # Test unstructured (3 runs)
        print(f"\n🔄 UNSTRUCTURED APPROACH (3 runs):")
        unstructured_results = []
        for i in range(3):
            print(f"  Run {i+1}...", end="", flush=True)
            try:
                response = await self.call_grok(unstructured_prompt)
                result = self.extract_vulnerability_data(response)
                unstructured_results.append(result)
                
                if "error" not in result:
                    vuln_count = len([k for k in result.keys() if ":" in k])
                    print(f" ✓ ({vuln_count} vulnerable packages)")
                else:
                    print(f" ❌ ({result['error']})")
                    
            except Exception as e:
                print(f" ❌ (Exception: {e})")
                unstructured_results.append({"error": "exception", "details": str(e)})
        
        # Test structured (3 runs)
        print(f"\n🔄 STRUCTURED APPROACH (3 runs):")
        structured_results = []
        for i in range(3):
            print(f"  Run {i+1}...", end="", flush=True)
            try:
                response = await self.call_grok(structured_prompt)
                result = self.extract_vulnerability_data(response)
                structured_results.append(result)
                
                if "error" not in result:
                    vuln_count = len([k for k in result.keys() if ":" in k and k != "search_metadata"])
                    print(f" ✓ ({vuln_count} vulnerable packages)")
                else:
                    print(f" ❌ ({result['error']})")
                    
            except Exception as e:
                print(f" ❌ (Exception: {e})")
                structured_results.append({"error": "exception", "details": str(e)})
        
        # Analyze results
        print("\n" + "=" * 70)
        print("📈 RESULTS ANALYSIS")
        print("=" * 70)
        
        unstructured_analysis = self.analyze_run_results(unstructured_results, "unstructured")
        structured_analysis = self.analyze_run_results(structured_results, "structured")
        
        # Compare approaches
        print(f"\n🏆 COMPARISON:")
        print(f"  Consistency:")
        print(f"    Unstructured: {unstructured_analysis.get('consistency_percentage', 0):.1f}%")
        print(f"    Structured: {structured_analysis.get('consistency_percentage', 0):.1f}%")
        
        print(f"  Completeness (packages with vulnerabilities):")
        print(f"    Unstructured: {unstructured_analysis.get('total_packages', 0)} packages")
        print(f"    Structured: {structured_analysis.get('total_packages', 0)} packages")
        
        # Determine winner
        u_consistency = unstructured_analysis.get('consistency_percentage', 0)
        s_consistency = structured_analysis.get('consistency_percentage', 0)
        u_completeness = unstructured_analysis.get('total_packages', 0)
        s_completeness = structured_analysis.get('total_packages', 0)
        
        print(f"\n🎯 VERDICT:")
        if s_consistency > u_consistency + 10:
            print(f"  ✅ STRUCTURED WINS on consistency ({s_consistency:.1f}% vs {u_consistency:.1f}%)")
        elif u_consistency > s_consistency + 10:
            print(f"  ❌ UNSTRUCTURED WINS on consistency ({u_consistency:.1f}% vs {s_consistency:.1f}%)")
        else:
            print(f"  🤝 Similar consistency")
        
        if s_completeness > u_completeness:
            print(f"  ✅ STRUCTURED WINS on completeness ({s_completeness} vs {u_completeness} packages)")
        elif u_completeness > s_completeness:
            print(f"  ❌ UNSTRUCTURED WINS on completeness ({u_completeness} vs {s_completeness} packages)")
        else:
            print(f"  🤝 Similar completeness")
        
        # Save results
        with open("rippling_simple_test_results.json", "w") as f:
            json.dump({
                "test_packages": self.test_packages,
                "unstructured": {
                    "results": unstructured_results,
                    "analysis": unstructured_analysis
                },
                "structured": {
                    "results": structured_results,
                    "analysis": structured_analysis
                }
            }, f, indent=2)
        
        print(f"\n📄 Results saved to: rippling_simple_test_results.json")


async def main():
    """Run the test."""
    tester = RipplingSimpleTest()
    await tester.run_test()


if __name__ == "__main__":
    asyncio.run(main())