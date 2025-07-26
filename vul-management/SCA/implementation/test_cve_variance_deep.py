#!/usr/bin/env python3
"""
Deep CVE Variance Test

More aggressive test to detect variance in AI CVE detection:
1. Add randomness to prompts
2. Test different package versions  
3. Use temperature/sampling settings
4. Add timestamp variations
"""

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sca_ai_scanner.core.client import AIVulnerabilityClient
from sca_ai_scanner.core.models import ScanConfig, Package, SourceLocation, FileType


class DeepVarianceTester:
    """Test for AI variance with more aggressive techniques."""
    
    def __init__(self):
        # Set API key
        os.environ["XAI_API_KEY"] = "your-xai-key-here"
        
    async def test_single_package_variance(self, package_str: str, num_runs: int = 5):
        """Test variance for a single package across multiple runs."""
        print(f"🔬 Testing variance for: {package_str}")
        
        results = []
        
        for run in range(num_runs):
            # Create unique config for each run to avoid any potential caching
            config = ScanConfig(
                model="grok-3",
                enable_live_search=True,
                confidence_threshold=0.7
            )
            
            # Add some randomness to the package declaration to avoid caching
            random_suffix = str(uuid.uuid4())[:8]
            name, version = package_str.split(":")
            
            # Create package with slightly different metadata each time
            pkg = Package(
                name=name,
                version=version,
                ecosystem="test",
                source_locations=[
                    SourceLocation(
                        file_path=f"/test_{random_suffix}/requirements.txt",
                        line_number=1 + run,  # Different line numbers
                        declaration=f"{name}=={version}  # Run {run+1}",
                        file_type=FileType.REQUIREMENTS
                    )
                ]
            )
            
            try:
                async with AIVulnerabilityClient(config) as client:
                    results_obj = await client.bulk_analyze([pkg])
                    
                    # Extract CVE data
                    pkg_key = f"{name}:{version}"
                    if pkg_key in results_obj.vulnerability_analysis:
                        analysis = results_obj.vulnerability_analysis[pkg_key]
                        cve_data = []
                        for cve in analysis.cves:
                            cve_data.append({
                                "id": cve.id,
                                "severity": cve.severity.value,
                                "description": cve.description[:100] + "..." if len(cve.description) > 100 else cve.description
                            })
                        
                        run_result = {
                            "run": run + 1,
                            "cve_count": len(cve_data),
                            "cves": cve_data,
                            "confidence": analysis.confidence,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        results.append(run_result)
                        print(f"  Run {run+1}: {len(cve_data)} CVEs found")
                    else:
                        print(f"  Run {run+1}: No analysis data found")
                        
            except Exception as e:
                print(f"  Run {run+1}: FAILED - {e}")
                
        return results
    
    def analyze_single_package_variance(self, package_str: str, results: List[Dict]):
        """Analyze variance for a single package."""
        if len(results) < 2:
            print(f"❌ Need at least 2 results for {package_str}")
            return
            
        print(f"\n📊 VARIANCE ANALYSIS: {package_str}")
        print("=" * 50)
        
        # Check CVE count variance
        cve_counts = [r["cve_count"] for r in results]
        count_variance = len(set(cve_counts)) > 1
        print(f"CVE Count Variance: {'❌ YES' if count_variance else '✅ NO'}")
        if count_variance:
            print(f"  Counts: {cve_counts}")
        
        # Check specific CVE IDs
        all_cve_sets = []
        for r in results:
            cve_ids = set(cve["id"] for cve in r["cves"])
            all_cve_sets.append(cve_ids)
        
        cve_id_variance = len(set(map(frozenset, all_cve_sets))) > 1
        print(f"CVE ID Variance: {'❌ YES' if cve_id_variance else '✅ NO'}")
        if cve_id_variance:
            for i, cve_set in enumerate(all_cve_sets):
                print(f"  Run {i+1}: {sorted(list(cve_set))}")
        
        # Check severity variance
        severity_variance = False
        all_unique_cves = set()
        for cve_set in all_cve_sets:
            all_unique_cves.update(cve_set)
        
        for cve_id in all_unique_cves:
            severities_for_cve = []
            for r in results:
                for cve in r["cves"]:
                    if cve["id"] == cve_id:
                        severities_for_cve.append(cve["severity"])
            
            if len(set(severities_for_cve)) > 1:
                severity_variance = True
                print(f"  {cve_id}: {severities_for_cve}")
        
        print(f"Severity Variance: {'❌ YES' if severity_variance else '✅ NO'}")
        
        # Check description variance
        description_variance = False
        for cve_id in all_unique_cves:
            descriptions_for_cve = []
            for r in results:
                for cve in r["cves"]:
                    if cve["id"] == cve_id:
                        descriptions_for_cve.append(cve["description"])
            
            if len(set(descriptions_for_cve)) > 1:
                description_variance = True
                print(f"  {cve_id}: Different descriptions")
        
        print(f"Description Variance: {'❌ YES' if description_variance else '✅ NO'}")
        
        # Overall assessment
        any_variance = count_variance or cve_id_variance or severity_variance or description_variance
        print(f"\n🎯 OVERALL: {'❌ VARIANCE DETECTED' if any_variance else '✅ NO VARIANCE'}")
        
        return any_variance
    
    async def run_comprehensive_test(self):
        """Run comprehensive variance testing."""
        print("🧪 DEEP CVE VARIANCE TEST")
        print("Testing for AI model non-determinism\n")
        
        test_packages = [
            "requests:2.25.1",    # Known vulnerable
            "django:3.2.0",       # Multiple CVEs
            "numpy:1.19.0"        # Should be clean
        ]
        
        all_results = {}
        variance_detected = False
        
        for package in test_packages:
            results = await self.test_single_package_variance(package, num_runs=5)
            all_results[package] = results
            
            package_variance = self.analyze_single_package_variance(package, results)
            if package_variance:
                variance_detected = True
        
        print("\n" + "="*60)
        print("🎯 FINAL CONCLUSIONS")
        print("="*60)
        
        if variance_detected:
            print("❌ VARIANCE CONFIRMED: AI model produces non-deterministic results")
            print("💡 This means CVE detection is not repeatable across runs")
            print("⚠️  Enterprise implications: Same scan could yield different results")
        else:
            print("✅ NO VARIANCE DETECTED: Results appear consistent")
            print("🤔 This is unexpected for AI models - may indicate:")
            print("   - Provider-level response caching")
            print("   - Model determinism (unlikely)")
            print("   - Insufficient test variation")
        
        # Save detailed results
        output_file = Path("deep_cve_variance_analysis.json")
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        print(f"\n📄 Detailed results: {output_file}")


async def main():
    """Run the deep variance test."""
    tester = DeepVarianceTester()
    await tester.run_comprehensive_test()


if __name__ == "__main__":
    asyncio.run(main())