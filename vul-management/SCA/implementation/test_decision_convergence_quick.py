#!/usr/bin/env python3
"""
Quick Decision Convergence Test - Focused Version

Based on partial results from the full test, we saw significant differences.
This focused test uses fewer packages to get complete results faster.
"""

import asyncio
import json
import os
import time
from typing import Dict, List, Any
import aiohttp

# Set API keys
os.environ["OPENAI_API_KEY"] = "your-openai-key-here"


class QuickConvergenceTest:
    """Quick test with fewer packages to see pattern."""
    
    def __init__(self):
        # Use just 5 packages based on what we saw in partial results
        self.test_packages = [
            {"name": "django", "version": "3.2.12"},      # MATCH: 10 vs 3 CVEs
            {"name": "requests", "version": "2.27.1"},    # DIFFER: 2 vs 0 CVEs
            {"name": "cryptography", "version": "3.4.6"}, # MATCH: 0 vs 0 CVEs
            {"name": "pillow", "version": "8.1.0"},       # DIFFER: 2 vs 0 CVEs
            {"name": "urllib3", "version": "1.26.3"}      # MATCH: 10 vs 2 CVEs
        ]
        
        self.model = "gpt-4o-mini"
        self.test_results = []
    
    def create_complete_scan_prompt(self, package: Dict) -> str:
        """Create our optimized complete scan prompt (2015-2024)."""
        pkg_str = f"{package['name']}:{package['version']}"
        
        return f"""Find ALL CVEs affecting {pkg_str}.

CRITICAL: Each CVE ID represents a DISTINCT vulnerability. NEVER consolidate or choose between CVEs.

YEAR-BY-YEAR REASONING CHECKLIST (Execute each step):
1. Search CVE-2024-* affecting {pkg_str} → Record ALL found
2. Search CVE-2023-* affecting {pkg_str} → Record ALL found  
3. Search CVE-2022-* affecting {pkg_str} → Record ALL found
4. Search CVE-2021-* affecting {pkg_str} → Record ALL found
5. Search CVE-2020-* affecting {pkg_str} → Record ALL found
6. Search CVE-2019-* affecting {pkg_str} → Record ALL found
7. Search CVE-2018-* affecting {pkg_str} → Record ALL found
8. Search CVE-2017-* affecting {pkg_str} → Record ALL found
9. Search CVE-2016-* affecting {pkg_str} → Record ALL found
10. Search CVE-2015-* affecting {pkg_str} → Record ALL found

Return ONLY JSON:
{{
  "scan_type": "complete",
  "package": "{pkg_str}",
  "cves": [
    {{
      "id": "CVE-YYYY-NNNNN",
      "year": "YYYY",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "description": "Brief description"
    }}
  ]
}}

If NO vulnerabilities: {{"scan_type": "complete", "package": "{pkg_str}", "cves": []}}"""
    
    def create_simplified_scan_prompt(self, package: Dict) -> str:
        """Create simplified scan prompt (2022-2024 + critical older)."""
        pkg_str = f"{package['name']}:{package['version']}"
        
        return f"""Find ACTIONABLE vulnerabilities affecting {pkg_str} for remediation decisions.

SIMPLIFIED APPROACH - Focus on:
1. Recent vulnerabilities (2022-2024) that need immediate attention
2. Critical/High severity older vulnerabilities that still matter

SEARCH STRATEGY:
1. Search CVE-2024-* affecting {pkg_str} → Record ALL found
2. Search CVE-2023-* affecting {pkg_str} → Record ALL found  
3. Search CVE-2022-* affecting {pkg_str} → Record ALL found
4. Search CVE-2021-* and older CRITICAL/HIGH affecting {pkg_str} → Record only major risks

Return ONLY JSON:
{{
  "scan_type": "simplified",
  "package": "{pkg_str}",
  "cves": [
    {{
      "id": "CVE-YYYY-NNNNN",
      "year": "YYYY",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "description": "Brief description"
    }}
  ]
}}

If NO vulnerabilities: {{"scan_type": "simplified", "package": "{pkg_str}", "cves": []}}"""
    
    def create_remediation_prompt(self, scan_data: Dict) -> str:
        """Create remediation decision prompt."""
        package = scan_data.get("package", "unknown")
        cves = scan_data.get("cves", [])
        
        if cves:
            cve_summary = f"Found {len(cves)} vulnerabilities:\n"
            for cve in cves[:5]:  # Top 5
                cve_summary += f"- {cve['id']}: {cve['severity']} - {cve['description']}\n"
            if len(cves) > 5:
                cve_summary += f"... and {len(cves) - 5} more"
        else:
            cve_summary = "No vulnerabilities found"
        
        return f"""You are a security engineer. Based on this vulnerability scan, what should the development team do?

PACKAGE: {package}
SCAN RESULTS:
{cve_summary}

Provide your recommendation in JSON:
{{
  "action": "upgrade|patch|investigate|no_action",
  "priority": "immediate|high|medium|low", 
  "reasoning": "brief explanation",
  "urgency_score": 1-10
}}"""
    
    async def call_openai(self, prompt: str) -> str:
        """Call OpenAI API with shorter timeout."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 2048
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.post(url, headers=headers, json=payload) as response:
                result = await response.json()
                if "choices" in result and result["choices"]:
                    return result["choices"][0]["message"]["content"]
                return f"ERROR: {result}"
    
    def extract_json(self, response: str) -> Dict:
        """Extract JSON from response."""
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
            return {"error": "no_json", "raw": response[:200]}
        except Exception as e:
            return {"error": "parse_failed", "exception": str(e)}
    
    async def test_package(self, package: Dict) -> Dict:
        """Test single package with both approaches."""
        pkg_str = f"{package['name']}:{package['version']}"
        print(f"\n📦 {pkg_str}")
        
        try:
            # Scan with both approaches
            print("  Complete scan...", end="")
            complete_prompt = self.create_complete_scan_prompt(package)
            complete_response = await self.call_openai(complete_prompt)
            complete_scan = self.extract_json(complete_response)
            complete_cves = len(complete_scan.get("cves", []))
            print(f" {complete_cves} CVEs")
            
            print("  Simplified scan...", end="")
            simplified_prompt = self.create_simplified_scan_prompt(package)
            simplified_response = await self.call_openai(simplified_prompt)
            simplified_scan = self.extract_json(simplified_response)
            simplified_cves = len(simplified_scan.get("cves", []))
            print(f" {simplified_cves} CVEs")
            
            # Get remediation decisions
            print("  Complete remediation...", end="")
            complete_rem_prompt = self.create_remediation_prompt(complete_scan)
            complete_rem_response = await self.call_openai(complete_rem_prompt)
            complete_remediation = self.extract_json(complete_rem_response)
            complete_action = complete_remediation.get("action", "unknown")
            print(f" {complete_action}")
            
            print("  Simplified remediation...", end="")
            simplified_rem_prompt = self.create_remediation_prompt(simplified_scan)
            simplified_rem_response = await self.call_openai(simplified_rem_prompt)
            simplified_remediation = self.extract_json(simplified_rem_response)
            simplified_action = simplified_remediation.get("action", "unknown")
            print(f" {simplified_action}")
            
            # Compare decisions
            actions_match = complete_action == simplified_action
            complete_priority = complete_remediation.get("priority", "unknown")
            simplified_priority = simplified_remediation.get("priority", "unknown")
            priorities_match = complete_priority == simplified_priority
            
            overall_match = actions_match and priorities_match
            
            print(f"  Decision: {'✅ MATCH' if overall_match else '❌ DIFFER'}")
            if not overall_match:
                print(f"    Complete: {complete_action} ({complete_priority})")
                print(f"    Simplified: {simplified_action} ({simplified_priority})")
            
            return {
                "package": pkg_str,
                "cve_counts": {"complete": complete_cves, "simplified": simplified_cves},
                "decisions": {
                    "complete": {"action": complete_action, "priority": complete_priority},
                    "simplified": {"action": simplified_action, "priority": simplified_priority}
                },
                "match": overall_match,
                "cve_reduction": complete_cves - simplified_cves
            }
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return {"package": pkg_str, "error": str(e)}
    
    async def run_quick_test(self):
        """Run quick convergence test."""
        print("🎯 QUICK DECISION CONVERGENCE TEST")
        print("Testing hypothesis with 5 packages for faster results")
        print("=" * 60)
        
        start_time = time.time()
        
        for package in self.test_packages:
            result = await self.test_package(package)
            self.test_results.append(result)
            await asyncio.sleep(0.5)  # Small delay
        
        # Analysis
        print("\n" + "=" * 60)
        print("📊 QUICK ANALYSIS")
        print("=" * 60)
        
        successful = [r for r in self.test_results if "error" not in r]
        
        if successful:
            matches = len([r for r in successful if r.get("match")])
            convergence_rate = (matches / len(successful)) * 100
            
            total_complete_cves = sum(r["cve_counts"]["complete"] for r in successful)
            total_simplified_cves = sum(r["cve_counts"]["simplified"] for r in successful)
            reduction = ((total_complete_cves - total_simplified_cves) / max(total_complete_cves, 1)) * 100
            
            print(f"\n🎯 Decision Convergence: {convergence_rate:.1f}% ({matches}/{len(successful)})")
            print(f"📊 CVE Reduction: {reduction:.1f}% ({total_complete_cves} → {total_simplified_cves})")
            
            # Show differences
            differences = [r for r in successful if not r.get("match")]
            if differences:
                print(f"\n⚠️  Different decisions ({len(differences)} packages):")
                for diff in differences:
                    pkg = diff["package"]
                    comp = diff["decisions"]["complete"]
                    simp = diff["decisions"]["simplified"]
                    print(f"  {pkg}:")
                    print(f"    Complete: {comp['action']} ({comp['priority']})")
                    print(f"    Simplified: {simp['action']} ({simp['priority']})")
            
            # Hypothesis conclusion
            print(f"\n🧪 HYPOTHESIS EVALUATION:")
            if convergence_rate >= 80:
                print(f"   ✅ HYPOTHESIS SUPPORTED ({convergence_rate:.1f}% convergence)")
                print(f"   Simplified approach works for most packages")
            elif convergence_rate >= 60:
                print(f"   🤔 HYPOTHESIS PARTIALLY SUPPORTED ({convergence_rate:.1f}% convergence)")
                print(f"   Some important differences exist")
            else:
                print(f"   ❌ HYPOTHESIS NOT SUPPORTED ({convergence_rate:.1f}% convergence)")
                print(f"   Significant differences in remediation decisions")
            
            print(f"\n📋 Key Finding: Simplified approach reduces CVE processing by {reduction:.1f}%")
            if differences:
                print(f"    But changes decisions for {len(differences)} out of {len(successful)} packages")
        
        # Save results
        with open("quick_convergence_results.json", "w") as f:
            json.dump({
                "test_summary": {
                    "convergence_rate": convergence_rate if successful else 0,
                    "packages_tested": len(successful),
                    "cve_reduction_percent": reduction if successful else 0
                },
                "detailed_results": self.test_results
            }, f, indent=2)
        
        duration = time.time() - start_time
        print(f"\n📄 Results saved to quick_convergence_results.json")
        print(f"⏱️  Completed in {duration:.1f} seconds")


async def main():
    """Run quick test."""
    tester = QuickConvergenceTest()
    await tester.run_quick_test()


if __name__ == "__main__":
    asyncio.run(main())