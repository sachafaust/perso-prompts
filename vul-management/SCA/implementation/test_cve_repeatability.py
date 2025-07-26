#!/usr/bin/env python3
"""
CVE Mapping Repeatability Test

Tests whether the same packages produce consistent CVE detection
and severity assignments across multiple runs with the same AI model.

Focus: Measure variance in CVE IDs detected and severity levels assigned.
"""

import asyncio
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sca_ai_scanner.core.client import AIVulnerabilityClient
from sca_ai_scanner.core.models import ScanConfig, Package, SourceLocation, FileType


class CVERepeatabilityTester:
    """Test CVE mapping consistency across multiple runs."""
    
    def __init__(self):
        self.config = ScanConfig(
            model="grok-3",
            enable_live_search=True,
            confidence_threshold=0.7
        )
        
        # Test packages with known vulnerabilities
        self.test_packages = [
            "requests:2.25.1",    # Known CVE-2023-32681 (HIGH)
            "django:3.2.0",       # Multiple known CVEs
            "lodash:4.17.20",     # Known prototype pollution
            "numpy:1.19.0",       # Should be relatively clean
            "express:4.17.0"      # Known CVEs
        ]
        
        self.results = []
    
    async def run_single_scan(self, run_number: int) -> Dict:
        """Run a single vulnerability scan and capture results."""
        print(f"🔄 Running scan #{run_number + 1}")
        
        # Create Package objects from package strings
        packages = []
        for pkg_str in self.test_packages:
            name, version = pkg_str.split(":")
            pkg = Package(
                name=name,
                version=version,
                ecosystem="test",
                source_locations=[
                    SourceLocation(
                        file_path="/test/requirements.txt",
                        line_number=1,
                        declaration=f"{name}=={version}",
                        file_type=FileType.REQUIREMENTS
                    )
                ]
            )
            packages.append(pkg)
        
        async with AIVulnerabilityClient(self.config) as client:
            # Analyze packages using bulk_analyze method
            results = await client.bulk_analyze(packages)
        
            # Extract just CVE IDs and severities for comparison
            scan_result = {
                "run_number": run_number + 1,
                "timestamp": datetime.utcnow().isoformat(),
                "packages": {}
            }
            
            for pkg_id, analysis in results.vulnerability_analysis.items():
                cve_data = []
                for cve in analysis.cves:
                    cve_data.append({
                        "id": cve.id,
                        "severity": cve.severity.value
                    })
                
                scan_result["packages"][pkg_id] = {
                    "cve_count": len(cve_data),
                    "cves": cve_data,
                    "confidence": analysis.confidence
                }
            
            return scan_result
    
    async def run_repeatability_test(self, num_runs: int = 5):
        """Run multiple scans to test repeatability."""
        print(f"🧪 Starting CVE Repeatability Test")
        print(f"📦 Testing packages: {', '.join(self.test_packages)}")
        print(f"🤖 Model: {self.config.model}")
        print(f"🔄 Runs: {num_runs}")
        print()
        
        # Set API key
        os.environ["XAI_API_KEY"] = "your-xai-key-here"
        
        # Run multiple scans
        for run in range(num_runs):
            try:
                result = await self.run_single_scan(run)
                self.results.append(result)
                print(f"✅ Completed run #{run + 1}")
            except Exception as e:
                print(f"❌ Run #{run + 1} failed: {e}")
                continue
        
        print(f"\n📊 Completed {len(self.results)} successful runs")
    
    def analyze_variance(self):
        """Analyze variance in CVE detection and severity assignment."""
        if len(self.results) < 2:
            print("❌ Need at least 2 successful runs to analyze variance")
            return
        
        print("\n" + "="*60)
        print("📈 CVE MAPPING VARIANCE ANALYSIS")
        print("="*60)
        
        variance_report = {
            "summary": {
                "total_runs": len(self.results),
                "packages_tested": len(self.test_packages),
                "variance_detected": False
            },
            "package_variance": {}
        }
        
        # Analyze each package across all runs
        for package in self.test_packages:
            print(f"\n📦 PACKAGE: {package}")
            print("-" * 40)
            
            # Collect CVE data across all runs
            all_cves_by_run = []
            all_severities_by_run = []
            
            for run_result in self.results:
                pkg_data = run_result["packages"].get(package, {"cves": []})
                cves_this_run = set(cve["id"] for cve in pkg_data["cves"])
                severities_this_run = {cve["id"]: cve["severity"] for cve in pkg_data["cves"]}
                
                all_cves_by_run.append(cves_this_run)
                all_severities_by_run.append(severities_this_run)
            
            # Check CVE detection consistency
            all_unique_cves = set()
            for cve_set in all_cves_by_run:
                all_unique_cves.update(cve_set)
            
            cve_consistent = len(set(map(frozenset, all_cves_by_run))) == 1
            
            print(f"CVE Detection Consistent: {'✅ YES' if cve_consistent else '❌ NO'}")
            
            if not cve_consistent:
                variance_report["summary"]["variance_detected"] = True
                print("  📋 CVE Detection Variance:")
                for i, cve_set in enumerate(all_cves_by_run):
                    print(f"    Run {i+1}: {sorted(list(cve_set)) if cve_set else 'No CVEs'}")
            
            # Check severity consistency for each CVE found
            severity_issues = []
            for cve_id in all_unique_cves:
                severities_for_cve = []
                for sev_dict in all_severities_by_run:
                    if cve_id in sev_dict:
                        severities_for_cve.append(sev_dict[cve_id])
                
                if len(set(severities_for_cve)) > 1:
                    severity_issues.append((cve_id, severities_for_cve))
            
            severity_consistent = len(severity_issues) == 0
            print(f"Severity Assignment Consistent: {'✅ YES' if severity_consistent else '❌ NO'}")
            
            if severity_issues:
                variance_report["summary"]["variance_detected"] = True
                print("  🚨 Severity Variance:")
                for cve_id, severities in severity_issues:
                    print(f"    {cve_id}: {severities}")
            
            # Store package-level variance data
            variance_report["package_variance"][package] = {
                "cve_detection_consistent": cve_consistent,
                "severity_assignment_consistent": severity_consistent,
                "unique_cves_found": sorted(list(all_unique_cves)),
                "cve_sets_by_run": [sorted(list(cve_set)) for cve_set in all_cves_by_run]
            }
        
        # Overall summary
        print(f"\n🎯 OVERALL RESULTS")
        print("-" * 40)
        if variance_report["summary"]["variance_detected"]:
            print("❌ VARIANCE DETECTED: CVE mapping is NOT consistent across runs")
            print("⚠️  This confirms the hypothesis - AI models produce non-deterministic results")
        else:
            print("✅ NO VARIANCE: CVE mapping appears consistent across runs")
            print("📊 This would suggest deterministic behavior (unexpected for AI models)")
        
        # Save detailed results
        output_file = Path("cve_repeatability_analysis.json")
        with open(output_file, 'w') as f:
            json.dump({
                "test_config": {
                    "model": self.config.model,
                    "packages": self.test_packages,
                    "num_runs": len(self.results)
                },
                "raw_results": self.results,
                "variance_analysis": variance_report
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {output_file}")


async def main():
    """Run the CVE repeatability test."""
    tester = CVERepeatabilityTester()
    
    # Run the test with 5 iterations
    await tester.run_repeatability_test(num_runs=5)
    
    # Analyze the results
    tester.analyze_variance()


if __name__ == "__main__":
    asyncio.run(main())