#!/usr/bin/env python3
"""
Real-World Test: Rippling Codebase Analysis

Tests unstructured vs structured prompts on real Rippling dependencies.
Focuses on completeness and consistency using Grok model.

Goals:
1. Measure if structured prompts reduce real package variance
2. Check if constraints hurt completeness (missing real CVEs)
3. Test with actual enterprise codebase scale
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Set
import aiohttp

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sca_ai_scanner.parsers.python import PythonParser
from sca_ai_scanner.parsers.javascript import JavaScriptParser

# Set API key
os.environ["XAI_API_KEY"] = "your-xai-key-here"


class RipplingRealWorldTester:
    """Test structured vs unstructured prompts on real Rippling codebase."""
    
    def __init__(self):
        self.rippling_path = Path.home() / "code" / "rippling-main"
        self.grok_api_key = os.environ["XAI_API_KEY"]
        
        # Test subset - select packages likely to have vulnerabilities
        self.target_packages = [
            # Known vulnerable packages from previous tests
            "requests:2.25.1",
            "django:3.2.0", 
            "lodash:4.17.20",
            # Will discover real versions from Rippling
        ]
        
        self.discovered_packages = []
        
    async def discover_rippling_packages(self) -> List[Dict]:
        """Discover real packages from Rippling codebase."""
        print(f"🔍 Discovering packages in {self.rippling_path}")
        
        if not self.rippling_path.exists():
            print(f"❌ Rippling path not found: {self.rippling_path}")
            return []
        
        # Parse Python packages
        python_parser = PythonParser(str(self.rippling_path))
        python_packages = await python_parser.parse_dependencies()
        
        # Parse JavaScript packages  
        js_parser = JavaScriptParser(str(self.rippling_path))
        js_packages = await js_parser.parse_dependencies()
        
        all_packages = python_packages + js_packages
        print(f"📦 Found {len(all_packages)} total packages")
        
        # Select subset for testing (focus on packages likely to have CVEs)
        vulnerable_candidates = []
        
        # Prioritize older packages and known vulnerable ones
        priority_names = {
            'requests', 'django', 'lodash', 'express', 'numpy', 'pillow', 
            'cryptography', 'pycryptodome', 'urllib3', 'lxml', 'jinja2',
            'flask', 'sqlalchemy', 'psycopg2', 'pymongo', 'redis',
            'celery', 'kombu', 'boto3', 'pyjwt', 'click'
        }
        
        for pkg in all_packages:
            if pkg.name.lower() in priority_names:
                vulnerable_candidates.append({
                    "name": pkg.name,
                    "version": pkg.version,
                    "ecosystem": pkg.ecosystem,
                    "source_files": [loc.file_path for loc in pkg.source_locations]
                })
        
        # Limit to reasonable test size
        selected = vulnerable_candidates[:15]  
        print(f"🎯 Selected {len(selected)} packages for vulnerability testing")
        
        for pkg in selected:
            print(f"  - {pkg['name']}:{pkg['version']} ({pkg['ecosystem']})")
        
        return selected
    
    async def call_grok(self, prompt: str) -> str:
        """Call Grok API."""
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.grok_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "grok-3",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 4096  # More tokens for real data
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                result = await response.json()
                if "choices" in result and result["choices"]:
                    return result["choices"][0]["message"]["content"]
                return f"ERROR: {result}"
    
    def create_unstructured_prompt(self, packages: List[Dict]) -> str:
        """Current approach - open-ended prompt."""
        pkg_list = "\n".join([f"- {pkg['name']}:{pkg['version']}" for pkg in packages])
        
        return f"""Find ALL known CVEs and security vulnerabilities for these packages from a real enterprise codebase. Be comprehensive and thorough.

Packages to analyze:
{pkg_list}

Search extensively for:
- All CVEs affecting each package version
- Security advisories and patches
- Known vulnerabilities from any source
- Supply chain and dependency issues

Return vulnerable packages in JSON format:
{{
  "package:version": {{
    "cves": [{{
      "id": "CVE-YYYY-NNNNN",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "description": "Vulnerability description",
      "cvss_score": 0.0-10.0
    }}],
    "confidence": 0.0-1.0
  }}
}}

If no vulnerabilities found for a package, omit it from response."""
    
    def create_structured_prompt(self, packages: List[Dict]) -> str:
        """Structured approach with systematic search."""
        pkg_list = "\n".join([f"- {pkg['name']}:{pkg['version']}" for pkg in packages])
        
        return f"""SYSTEMATIC VULNERABILITY ANALYSIS
Execute this EXACT procedure for the following real enterprise packages:

Packages to analyze:
{pkg_list}

MANDATORY SEARCH PROCEDURE:
For EACH package, execute these steps systematically:

STEP 1: Year-by-year CVE search (complete coverage)
- Search pattern: "CVE-2024-* affecting [package_name]" → record ALL findings
- Search pattern: "CVE-2023-* affecting [package_name]" → record ALL findings
- Search pattern: "CVE-2022-* affecting [package_name]" → record ALL findings  
- Search pattern: "CVE-2021-* affecting [package_name]" → record ALL findings
- Search pattern: "CVE-2020-* affecting [package_name]" → record ALL findings
- Continue back to 2019, 2018, 2017, 2016, 2015 (10-year window)

STEP 2: Version impact assessment
For each CVE found:
- Determine if the specific version is vulnerable
- Include if: package_version <= last_vulnerable_version
- Include ALL CVEs that affect the version (no limits)

STEP 3: Severity standardization
For each CVE:
- Extract exact CVSS score
- Apply mapping: 9.0-10.0→CRITICAL, 7.0-8.9→HIGH, 4.0-6.9→MEDIUM, 0.1-3.9→LOW
- Use template: "CVE-[ID] in [package] [version]: [vulnerability_type]. CVSS: [score]"

RESPONSE REQUIREMENTS:
- Include EVERY vulnerable package found
- Include EVERY CVE affecting each package version  
- NO arbitrary limits or sampling
- Use this EXACT JSON structure:

{{
  "scan_summary": {{
    "packages_analyzed": {len(packages)},
    "search_years": ["2024", "2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016", "2015"],
    "methodology": "systematic_year_by_year"
  }},
  "package:version": {{
    "total_cves": <exact_count>,
    "cves": [
      {{
        "id": "CVE-YYYY-NNNNN",
        "severity": "CRITICAL|HIGH|MEDIUM|LOW",
        "cvss_score": <number>,
        "description": "<standardized_description>",
        "affects_version": true,
        "year_published": "YYYY"
      }}
    ],
    "confidence": <0.0-1.0>,
    "search_completed": true
  }}
}}

Return ONLY the JSON, no explanatory text."""
    
    def extract_vulnerability_data(self, response: str) -> Dict:
        """Extract vulnerability data from response."""
        try:
            # Find JSON in response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            print(f"Failed to parse JSON: {e}")
            return {"error": "parse_failed", "raw": response[:500]}
        
        return {"error": "no_json_found", "raw": response[:500]}
    
    def analyze_consistency(self, results: List[Dict], prompt_type: str) -> Dict:
        """Analyze consistency across multiple runs."""
        print(f"\n📊 {prompt_type.upper()} CONSISTENCY ANALYSIS:")
        
        if len(results) < 2:
            print("  ⚠️  Need at least 2 runs for consistency analysis")
            return {"error": "insufficient_runs"}
        
        # Track variance per package
        all_packages = set()
        for result in results:
            if "error" not in result:
                all_packages.update(key for key in result.keys() 
                                  if ":" in key and key != "scan_summary")
        
        consistency_report = {
            "total_packages_found": len(all_packages),
            "consistent_packages": 0,
            "variant_packages": 0,
            "package_details": {}
        }
        
        for package in all_packages:
            print(f"\n  📦 {package}:")
            
            # Collect CVE data across runs
            package_cves_by_run = []
            package_counts_by_run = []
            
            for i, result in enumerate(results):
                if "error" in result:
                    print(f"    Run {i+1}: ERROR")
                    package_cves_by_run.append(set())
                    package_counts_by_run.append(0)
                elif package in result:
                    pkg_data = result[package]
                    if "cves" in pkg_data:
                        cve_ids = set(cve["id"] for cve in pkg_data["cves"] if "id" in cve)
                        package_cves_by_run.append(cve_ids)
                        package_counts_by_run.append(len(cve_ids))
                        print(f"    Run {i+1}: {len(cve_ids)} CVEs - {sorted(list(cve_ids))}")
                    else:
                        package_cves_by_run.append(set())
                        package_counts_by_run.append(0)
                        print(f"    Run {i+1}: No CVE data")
                else:
                    package_cves_by_run.append(set())
                    package_counts_by_run.append(0)
                    print(f"    Run {i+1}: Package not found")
            
            # Check consistency
            unique_cve_sets = set(map(frozenset, package_cves_by_run))
            is_consistent = len(unique_cve_sets) == 1
            
            if is_consistent:
                consistency_report["consistent_packages"] += 1
                print(f"    ✅ CONSISTENT")
            else:
                consistency_report["variant_packages"] += 1
                print(f"    ❌ VARIANT - {len(unique_cve_sets)} different results")
            
            consistency_report["package_details"][package] = {
                "consistent": is_consistent,
                "cve_counts": package_counts_by_run,
                "unique_results": len(unique_cve_sets)
            }
        
        consistency_percentage = (consistency_report["consistent_packages"] / 
                                len(all_packages) * 100) if all_packages else 0
        
        print(f"\n  🎯 Overall consistency: {consistency_percentage:.1f}% ({consistency_report['consistent_packages']}/{len(all_packages)} packages)")
        
        return consistency_report
    
    async def run_real_world_test(self):
        """Run the complete real-world test."""
        print("🔬 REAL-WORLD TEST: Rippling Codebase")
        print("Testing structured vs unstructured prompts on enterprise dependencies")
        print("=" * 80)
        
        # Discover real packages
        packages = await self.discover_rippling_packages()
        if not packages:
            print("❌ No packages discovered")
            return
        
        # Create prompts
        unstructured_prompt = self.create_unstructured_prompt(packages)
        structured_prompt = self.create_structured_prompt(packages)
        
        print(f"\n📏 Prompt sizes:")
        print(f"  Unstructured: {len(unstructured_prompt)} characters")
        print(f"  Structured: {len(structured_prompt)} characters")
        
        # Test unstructured approach (3 runs)
        print(f"\n🔄 Testing UNSTRUCTURED approach (3 runs)...")
        unstructured_results = []
        for i in range(3):
            print(f"  Run {i+1}...", end="", flush=True)
            try:
                response = await self.call_grok(unstructured_prompt)
                result = self.extract_vulnerability_data(response)
                unstructured_results.append(result)
                
                if "error" not in result:
                    vulnerable_count = len([k for k in result.keys() if ":" in k])
                    print(f" ✓ ({vulnerable_count} vulnerable packages)")
                else:
                    print(f" ❌ ({result['error']})")
            except Exception as e:
                print(f" ❌ (exception: {e})")
                unstructured_results.append({"error": "exception", "details": str(e)})
        
        # Test structured approach (3 runs)
        print(f"\n🔄 Testing STRUCTURED approach (3 runs)...")
        structured_results = []
        for i in range(3):
            print(f"  Run {i+1}...", end="", flush=True)
            try:
                response = await self.call_grok(structured_prompt)
                result = self.extract_vulnerability_data(response)
                structured_results.append(result)
                
                if "error" not in result:
                    vulnerable_count = len([k for k in result.keys() if ":" in k and k != "scan_summary"])
                    print(f" ✓ ({vulnerable_count} vulnerable packages)")
                else:
                    print(f" ❌ ({result['error']})")
            except Exception as e:
                print(f" ❌ (exception: {e})")
                structured_results.append({"error": "exception", "details": str(e)})
        
        # Analyze results
        print("\n" + "=" * 80)
        print("📈 CONSISTENCY & COMPLETENESS ANALYSIS")
        print("=" * 80)
        
        unstructured_analysis = self.analyze_consistency(unstructured_results, "unstructured")
        structured_analysis = self.analyze_consistency(structured_results, "structured")
        
        # Completeness comparison
        print(f"\n🎯 COMPLETENESS COMPARISON:")
        
        # Extract all unique packages found across all runs
        all_unstructured_packages = set()
        all_structured_packages = set()
        
        for result in unstructured_results:
            if "error" not in result:
                all_unstructured_packages.update(key for key in result.keys() if ":" in key)
        
        for result in structured_results:
            if "error" not in result:
                all_structured_packages.update(key for key in result.keys() if ":" in key and key != "scan_summary")
        
        print(f"  Unstructured found: {len(all_unstructured_packages)} vulnerable packages")
        print(f"  Structured found: {len(all_structured_packages)} vulnerable packages")
        
        # Packages found by one approach but not the other
        only_unstructured = all_unstructured_packages - all_structured_packages
        only_structured = all_structured_packages - all_unstructured_packages
        
        if only_unstructured:
            print(f"  📝 Only unstructured found: {sorted(list(only_unstructured))}")
        if only_structured:
            print(f"  📋 Only structured found: {sorted(list(only_structured))}")
        
        # Final assessment
        print(f"\n" + "=" * 80)
        print("🏆 FINAL ASSESSMENT")
        print("=" * 80)
        
        unstructured_consistency = unstructured_analysis.get("consistent_packages", 0) / max(unstructured_analysis.get("total_packages_found", 1), 1) * 100
        structured_consistency = structured_analysis.get("consistent_packages", 0) / max(structured_analysis.get("total_packages_found", 1), 1) * 100
        
        print(f"Consistency:")
        print(f"  Unstructured: {unstructured_consistency:.1f}%")
        print(f"  Structured: {structured_consistency:.1f}%")
        
        print(f"\nCompleteness (unique packages found):")
        print(f"  Unstructured: {len(all_unstructured_packages)} packages")
        print(f"  Structured: {len(all_structured_packages)} packages")
        
        if structured_consistency > unstructured_consistency + 10:
            print(f"\n✅ STRUCTURED WINS on consistency ({structured_consistency:.1f}% vs {unstructured_consistency:.1f}%)")
        elif unstructured_consistency > structured_consistency + 10:
            print(f"\n❌ UNSTRUCTURED WINS on consistency ({unstructured_consistency:.1f}% vs {structured_consistency:.1f}%)")
        else:
            print(f"\n🤝 SIMILAR consistency between approaches")
        
        if len(all_structured_packages) > len(all_unstructured_packages):
            print(f"✅ STRUCTURED WINS on completeness ({len(all_structured_packages)} vs {len(all_unstructured_packages)} packages)")
        elif len(all_unstructured_packages) > len(all_structured_packages):
            print(f"❌ UNSTRUCTURED WINS on completeness ({len(all_unstructured_packages)} vs {len(all_structured_packages)} packages)")
        else:
            print(f"🤝 SIMILAR completeness between approaches")
        
        # Save detailed results
        with open("rippling_real_world_test_results.json", "w") as f:
            json.dump({
                "test_config": {
                    "packages_tested": packages,
                    "model": "grok-3",
                    "rippling_path": str(self.rippling_path)
                },
                "unstructured": {
                    "results": unstructured_results,
                    "analysis": unstructured_analysis
                },
                "structured": {
                    "results": structured_results,
                    "analysis": structured_analysis
                },
                "comparison": {
                    "unstructured_consistency": unstructured_consistency,
                    "structured_consistency": structured_consistency,
                    "unstructured_packages": len(all_unstructured_packages),
                    "structured_packages": len(all_structured_packages)
                }
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: rippling_real_world_test_results.json")


async def main():
    """Run the real-world Rippling test."""
    tester = RipplingRealWorldTester()
    await tester.run_real_world_test()


if __name__ == "__main__":
    asyncio.run(main())