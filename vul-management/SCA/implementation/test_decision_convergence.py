#!/usr/bin/env python3
"""
Decision Convergence Test: Complete vs Simplified CVE Data

Test the hypothesis: Do complete CVE datasets vs simplified datasets
lead to different remediation decisions?

This test scans packages with two approaches:
1. Complete: All CVEs 2015-2024 (our optimized prompt)
2. Simplified: CVEs 2022-2024 + critical older findings

Then feeds both to a remediation AI and compares decisions.
"""

import asyncio
import json
import os
import time
from typing import Dict, List, Any
import aiohttp

# Set API keys from previous tests
os.environ["OPENAI_API_KEY"] = "your-openai-key-here"


class DecisionConvergenceTest:
    """Test if complete vs simplified CVE data leads to different remediation decisions."""
    
    def __init__(self):
        # Use packages from Rippling test that we know have vulnerabilities
        self.test_packages = [
            {"name": "django", "version": "3.2.12"},
            {"name": "requests", "version": "2.27.1"},
            {"name": "cryptography", "version": "3.4.6"},
            {"name": "pillow", "version": "8.1.0"},
            {"name": "urllib3", "version": "1.26.3"},
            {"name": "psycopg2", "version": "2.9.1"},
            {"name": "celery", "version": "5.2.0"},
            {"name": "redis", "version": "3.5.3"},
            {"name": "numpy", "version": "1.21.0"},
            {"name": "flask", "version": "2.0.1"}
        ]
        
        self.model = "gpt-4o-mini"
        self.test_results = []
    
    def create_complete_scan_prompt(self, package: Dict) -> str:
        """Create our optimized complete scan prompt (2015-2024)."""
        pkg_str = f"{package['name']}:{package['version']}"
        
        return f"""Find ALL CVEs affecting {pkg_str}.

CRITICAL: Each CVE ID represents a DISTINCT vulnerability. NEVER consolidate or choose between CVEs.

WHY YOU MUST INCLUDE ALL CVEs:
1. CVE-2023-0286 ≠ CVE-2023-50782 even if both affect same package/year
2. Different CVEs = different attack vectors, patches, impacts
3. Security teams need the COMPLETE vulnerability surface
4. "Similar" CVEs often have different version ranges or conditions

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

CRITICAL: Complete ALL 10 steps even if you find CVEs in early years.

Return ONLY JSON:
{{
  "scan_type": "complete",
  "package": "{pkg_str}",
  "cves": [
    {{
      "id": "CVE-YYYY-NNNNN",
      "year": "YYYY",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "description": "Brief description",
      "cvss_score": 0.0
    }}
  ],
  "confidence": 0.0
}}

If NO vulnerabilities found, return: {{"scan_type": "complete", "package": "{pkg_str}", "cves": [], "confidence": 0.9}}"""
    
    def create_simplified_scan_prompt(self, package: Dict) -> str:
        """Create simplified scan prompt (2022-2024 + critical older)."""
        pkg_str = f"{package['name']}:{package['version']}"
        
        return f"""Find ACTIONABLE vulnerabilities affecting {pkg_str} for remediation decisions.

SIMPLIFIED APPROACH - Focus on:
1. Recent vulnerabilities (2022-2024) that need immediate attention
2. Critical/High severity older vulnerabilities that still matter for remediation

YEAR-BY-YEAR SEARCH (RECENT FOCUS):
1. Search CVE-2024-* affecting {pkg_str} → Record ALL found
2. Search CVE-2023-* affecting {pkg_str} → Record ALL found  
3. Search CVE-2022-* affecting {pkg_str} → Record ALL found
4. Search CVE-2021-* and older CRITICAL/HIGH severity affecting {pkg_str} → Record significant findings only

OPTIMIZATION: Skip low/medium severity CVEs from 2015-2020 unless they represent major security risks.

Return ONLY JSON:
{{
  "scan_type": "simplified",
  "package": "{pkg_str}",
  "cves": [
    {{
      "id": "CVE-YYYY-NNNNN",
      "year": "YYYY",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "description": "Brief description",
      "cvss_score": 0.0,
      "remediation_priority": "immediate|high|medium|low"
    }}
  ],
  "confidence": 0.0
}}

If NO vulnerabilities found, return: {{"scan_type": "simplified", "package": "{pkg_str}", "cves": [], "confidence": 0.9}}"""
    
    def create_remediation_analysis_prompt(self, scan_data: Dict) -> str:
        """Create prompt for remediation decision analysis."""
        scan_type = scan_data.get("scan_type", "unknown")
        package = scan_data.get("package", "unknown")
        cves = scan_data.get("cves", [])
        
        cve_summary = ""
        if cves:
            cve_summary = "\n".join([
                f"- {cve['id']}: {cve['severity']} ({cve.get('cvss_score', 'N/A')}) - {cve['description']}"
                for cve in cves[:10]  # Limit to top 10 for readability
            ])
            if len(cves) > 10:
                cve_summary += f"\n... and {len(cves) - 10} more CVEs"
        else:
            cve_summary = "No vulnerabilities found"
        
        return f"""You are a security remediation expert. Based on the vulnerability scan data below, provide actionable remediation recommendations.

PACKAGE: {package}
SCAN TYPE: {scan_type}
VULNERABILITIES FOUND: {len(cves)}

CVE DETAILS:
{cve_summary}

Provide your analysis and recommendations in JSON format:

{{
  "package": "{package}",
  "scan_type": "{scan_type}",
  "remediation_decision": {{
    "action": "upgrade|patch|mitigate|no_action|investigate",
    "priority": "immediate|high|medium|low",
    "recommended_version": "X.Y.Z or null",
    "reasoning": "Brief explanation of decision",
    "urgency_score": 1-10,
    "effort_estimate": "trivial|low|medium|high|complex"
  }},
  "risk_assessment": {{
    "current_risk_level": "critical|high|medium|low",
    "business_impact": "high|medium|low",
    "exploitability": "high|medium|low"
  }},
  "implementation_notes": {{
    "breaking_changes_expected": true/false,
    "testing_required": "minimal|moderate|extensive",
    "rollback_complexity": "easy|moderate|difficult"
  }},
  "confidence": 0.0-1.0
}}

Focus on practical, actionable recommendations that a development team can implement."""
    
    async def call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
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
    
    def extract_json_from_response(self, response: str) -> Dict:
        """Extract JSON data from AI response."""
        try:
            # Find JSON in response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            
            return {"error": "no_json_found", "raw": response[:500]}
        except Exception as e:
            return {"error": "parse_failed", "exception": str(e), "raw": response[:500]}
    
    async def scan_package_complete(self, package: Dict) -> Dict:
        """Scan package with complete approach."""
        print(f"    Complete scan...", end="", flush=True)
        
        prompt = self.create_complete_scan_prompt(package)
        response = await self.call_openai(prompt)
        result = self.extract_json_from_response(response)
        
        if "error" not in result:
            cve_count = len(result.get("cves", []))
            print(f" ✓ {cve_count} CVEs")
        else:
            print(f" ❌ {result['error']}")
        
        return result
    
    async def scan_package_simplified(self, package: Dict) -> Dict:
        """Scan package with simplified approach."""
        print(f"    Simplified scan...", end="", flush=True)
        
        prompt = self.create_simplified_scan_prompt(package)
        response = await self.call_openai(prompt)
        result = self.extract_json_from_response(response)
        
        if "error" not in result:
            cve_count = len(result.get("cves", []))
            print(f" ✓ {cve_count} CVEs")
        else:
            print(f" ❌ {result['error']}")
        
        return result
    
    async def analyze_remediation(self, scan_data: Dict) -> Dict:
        """Get remediation recommendations for scan data."""
        scan_type = scan_data.get("scan_type", "unknown")
        print(f"    {scan_type.title()} remediation analysis...", end="", flush=True)
        
        prompt = self.create_remediation_analysis_prompt(scan_data)
        response = await self.call_openai(prompt)
        result = self.extract_json_from_response(response)
        
        if "error" not in result:
            action = result.get("remediation_decision", {}).get("action", "unknown")
            priority = result.get("remediation_decision", {}).get("priority", "unknown")
            print(f" ✓ {action} ({priority})")
        else:
            print(f" ❌ {result['error']}")
        
        return result
    
    def compare_decisions(self, complete_remediation: Dict, simplified_remediation: Dict, package: Dict) -> Dict:
        """Compare remediation decisions between complete and simplified approaches."""
        
        def extract_decision_key_points(remediation_data: Dict) -> Dict:
            """Extract key decision points for comparison."""
            if "error" in remediation_data:
                return {"error": True}
            
            decision = remediation_data.get("remediation_decision", {})
            risk = remediation_data.get("risk_assessment", {})
            
            return {
                "action": decision.get("action", "unknown"),
                "priority": decision.get("priority", "unknown"),
                "urgency_score": decision.get("urgency_score", 0),
                "current_risk_level": risk.get("current_risk_level", "unknown"),
                "recommended_version": decision.get("recommended_version"),
                "confidence": remediation_data.get("confidence", 0.0)
            }
        
        complete_key_points = extract_decision_key_points(complete_remediation)
        simplified_key_points = extract_decision_key_points(simplified_remediation)
        
        # Check if both have errors
        if complete_key_points.get("error") or simplified_key_points.get("error"):
            return {
                "package": f"{package['name']}:{package['version']}",
                "comparison_result": "error",
                "decisions_match": False,
                "error": "One or both scans failed"
            }
        
        # Compare key decision points
        action_match = complete_key_points["action"] == simplified_key_points["action"]
        priority_match = complete_key_points["priority"] == simplified_key_points["priority"]
        risk_match = complete_key_points["current_risk_level"] == simplified_key_points["current_risk_level"]
        
        # Calculate urgency score difference
        urgency_diff = abs(complete_key_points["urgency_score"] - simplified_key_points["urgency_score"])
        urgency_close = urgency_diff <= 2  # Within 2 points considered "close"
        
        # Overall decision match
        decisions_match = action_match and priority_match and urgency_close
        
        return {
            "package": f"{package['name']}:{package['version']}",
            "comparison_result": "success",
            "decisions_match": decisions_match,
            "detailed_comparison": {
                "action_match": action_match,
                "priority_match": priority_match,
                "risk_level_match": risk_match,
                "urgency_score_close": urgency_close,
                "urgency_difference": urgency_diff
            },
            "complete_decision": complete_key_points,
            "simplified_decision": simplified_key_points,
            "confidence_difference": abs(complete_key_points["confidence"] - simplified_key_points["confidence"])
        }
    
    async def test_package(self, package: Dict) -> Dict:
        """Test a single package with both approaches and compare decisions."""
        pkg_str = f"{package['name']}:{package['version']}"
        print(f"\n📦 Testing {pkg_str}")
        print("-" * 60)
        
        # Step 1: Scan with both approaches
        complete_scan = await self.scan_package_complete(package)
        simplified_scan = await self.scan_package_simplified(package)
        
        # Step 2: Get remediation analysis for both
        complete_remediation = await self.analyze_remediation(complete_scan)
        simplified_remediation = await self.analyze_remediation(simplified_scan)
        
        # Step 3: Compare decisions
        comparison = self.compare_decisions(complete_remediation, simplified_remediation, package)
        
        # Step 4: Calculate cost difference (rough estimate)
        complete_cves = len(complete_scan.get("cves", []))
        simplified_cves = len(simplified_scan.get("cves", []))
        
        result = {
            "package": pkg_str,
            "scans": {
                "complete": complete_scan,
                "simplified": simplified_scan
            },
            "remediations": {
                "complete": complete_remediation,
                "simplified": simplified_remediation
            },
            "comparison": comparison,
            "metrics": {
                "complete_cves_found": complete_cves,
                "simplified_cves_found": simplified_cves,
                "cve_reduction": complete_cves - simplified_cves,
                "cve_reduction_percent": ((complete_cves - simplified_cves) / max(complete_cves, 1)) * 100
            }
        }
        
        # Print summary
        match_status = "✅ MATCH" if comparison.get("decisions_match") else "❌ DIFFER"
        print(f"    Decision comparison: {match_status}")
        print(f"    CVEs: Complete={complete_cves}, Simplified={simplified_cves}")
        
        return result
    
    async def run_convergence_test(self):
        """Run the complete decision convergence test."""
        print("🎯 DECISION CONVERGENCE TEST")
        print("Testing: Do complete vs simplified CVE scans lead to different remediation decisions?")
        print("=" * 80)
        
        start_time = time.time()
        
        # Test all packages
        for package in self.test_packages:
            try:
                result = await self.test_package(package)
                self.test_results.append(result)
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ Failed to test {package['name']}:{package['version']}: {e}")
                self.test_results.append({
                    "package": f"{package['name']}:{package['version']}",
                    "error": str(e)
                })
        
        # Analysis
        print("\n" + "=" * 80)
        print("📊 CONVERGENCE ANALYSIS")
        print("=" * 80)
        
        successful_tests = [r for r in self.test_results if "error" not in r]
        failed_tests = [r for r in self.test_results if "error" in r]
        
        print(f"\n✅ Successful tests: {len(successful_tests)}/{len(self.test_results)}")
        if failed_tests:
            print(f"❌ Failed tests: {len(failed_tests)}")
        
        if successful_tests:
            # Decision convergence analysis
            matching_decisions = [r for r in successful_tests if r["comparison"].get("decisions_match")]
            differing_decisions = [r for r in successful_tests if not r["comparison"].get("decisions_match")]
            
            convergence_rate = len(matching_decisions) / len(successful_tests) * 100
            
            print(f"\n🎯 Decision Convergence Rate: {convergence_rate:.1f}%")
            print(f"   Matching decisions: {len(matching_decisions)}/{len(successful_tests)}")
            print(f"   Differing decisions: {len(differing_decisions)}/{len(successful_tests)}")
            
            # CVE reduction analysis
            total_complete_cves = sum(r["metrics"]["complete_cves_found"] for r in successful_tests)
            total_simplified_cves = sum(r["metrics"]["simplified_cves_found"] for r in successful_tests)
            
            if total_complete_cves > 0:
                overall_reduction = ((total_complete_cves - total_simplified_cves) / total_complete_cves) * 100
                print(f"\n📊 CVE Data Reduction:")
                print(f"   Complete approach: {total_complete_cves} total CVEs")
                print(f"   Simplified approach: {total_simplified_cves} total CVEs")
                print(f"   Reduction: {overall_reduction:.1f}%")
            
            # Show differing decisions
            if differing_decisions:
                print(f"\n⚠️  Packages with differing decisions:")
                for result in differing_decisions:
                    pkg = result["package"]
                    comp = result["comparison"]["complete_decision"]
                    simp = result["comparison"]["simplified_decision"]
                    print(f"   {pkg}:")
                    print(f"     Complete: {comp['action']} ({comp['priority']})")
                    print(f"     Simplified: {simp['action']} ({simp['priority']})")
        
        # Save detailed results
        end_time = time.time()
        test_duration = end_time - start_time
        
        final_results = {
            "test_metadata": {
                "test_type": "decision_convergence",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_seconds": test_duration,
                "packages_tested": len(self.test_packages),
                "model_used": self.model
            },
            "summary": {
                "successful_tests": len(successful_tests),
                "failed_tests": len(failed_tests),
                "convergence_rate": convergence_rate if successful_tests else 0,
                "total_complete_cves": total_complete_cves if successful_tests else 0,
                "total_simplified_cves": total_simplified_cves if successful_tests else 0,
                "cve_reduction_percent": overall_reduction if successful_tests and total_complete_cves > 0 else 0
            },
            "detailed_results": self.test_results
        }
        
        with open("decision_convergence_test_results.json", "w") as f:
            json.dump(final_results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: decision_convergence_test_results.json")
        print(f"⏱️  Test completed in {test_duration:.1f} seconds")
        
        # Hypothesis conclusion
        print(f"\n🧪 HYPOTHESIS TESTING CONCLUSION:")
        if successful_tests:
            if convergence_rate >= 80:
                print(f"   ✅ HYPOTHESIS SUPPORTED: {convergence_rate:.1f}% decision convergence")
                print(f"      Simplified approach leads to same decisions in most cases")
                print(f"      CVE reduction: {overall_reduction:.1f}% fewer CVEs to process")
            elif convergence_rate >= 60:
                print(f"   🤔 HYPOTHESIS PARTIALLY SUPPORTED: {convergence_rate:.1f}% convergence")
                print(f"      Significant agreement but some important differences")
            else:
                print(f"   ❌ HYPOTHESIS NOT SUPPORTED: Only {convergence_rate:.1f}% convergence")
                print(f"      Complete and simplified approaches lead to different decisions")
        else:
            print(f"   ❓ INCONCLUSIVE: Test failures prevented proper analysis")


async def main():
    """Run the decision convergence test."""
    tester = DecisionConvergenceTest()
    await tester.run_convergence_test()


if __name__ == "__main__":
    asyncio.run(main())