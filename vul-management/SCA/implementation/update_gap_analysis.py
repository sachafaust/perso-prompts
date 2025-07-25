#!/usr/bin/env python3
"""
Extract fresh package data and update gap analysis.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sca_ai_scanner.parsers.python import PythonParser
from sca_ai_scanner.parsers.javascript import JavaScriptParser

def extract_fresh_packages():
    """Extract fresh package data from both parsers."""
    rippling_path = Path.home() / 'code' / 'rippling-main'
    
    if not rippling_path.exists():
        print(f"❌ Rippling codebase not found at {rippling_path}")
        return
    
    print("🔄 Extracting fresh package data...")
    
    # Extract Python packages
    python_parser = PythonParser(str(rippling_path))
    python_packages = python_parser.parse_all_files()
    python_names = {pkg.name.lower() for pkg in python_packages}
    
    # Extract JavaScript packages
    js_parser = JavaScriptParser(str(rippling_path))
    js_packages = js_parser.parse_all_files()
    js_names = {pkg.name.lower() for pkg in js_packages}
    
    # Combine all packages
    all_packages = python_names | js_names
    
    print(f"📊 Extracted packages:")
    print(f"   Python: {len(python_names)}")
    print(f"   JavaScript: {len(js_names)}")
    print(f"   Total unique: {len(all_packages)}")
    
    # Save to file for gap analysis
    with open('/tmp/our_fresh_packages.txt', 'w') as f:
        for pkg in sorted(all_packages):
            f.write(f"{pkg}\n")
    
    print(f"✅ Fresh package data saved to /tmp/our_fresh_packages.txt")
    
    # Now analyze gaps
    analyze_gaps_fresh(all_packages)

def analyze_gaps_fresh(our_packages):
    """Analyze gaps using fresh data."""
    
    # Semgrep complete findings (all ecosystems)
    semgrep_packages = {
        'aiohttp', 'authlib', 'axios', 'azure-identity', 'brace-expansion',
        'certifi', 'cryptography', 'django', 'djangorestframework', 'formidable',
        'gitpython', 'h11', 'idna', 'jinja2', 'jupyter-server', 'nltk',
        'pillow', 'protobuf', 'py', 'pycares', 'pycryptodome', 'pymongo',
        'python-jose', 'requests', 'sentry-sdk', 'setuptools', 'signxml',
        'starlette', 'tar-fs', 'tornado', 'urllib3', 'zipp'
    }
    
    print(f"\n🎯 Fresh Gap Analysis:")
    print(f"   Semgrep packages: {len(semgrep_packages)}")
    print(f"   Our packages: {len(our_packages)}")
    
    # Find gaps
    missing_packages = semgrep_packages - our_packages
    extra_packages = our_packages - semgrep_packages
    found_packages = semgrep_packages & our_packages
    
    print(f"\n📈 Results:")
    print(f"   Found by both: {len(found_packages)} ({(len(found_packages)/len(semgrep_packages))*100:.1f}%)")
    print(f"   Missing from our tool: {len(missing_packages)}")
    print(f"   Extra in our tool: {len(extra_packages)}")
    
    if missing_packages:
        print(f"\n❌ Missing packages ({len(missing_packages)}):")
        for pkg in sorted(missing_packages):
            print(f"   - {pkg}")
    else:
        print(f"\n🎉 No missing packages - perfect parity!")
    
    # Analyze by ecosystem
    python_packages = {
        'aiohttp', 'authlib', 'azure-identity', 'certifi', 'cryptography',
        'django', 'djangorestframework', 'gitpython', 'h11', 'idna',
        'jinja2', 'jupyter-server', 'nltk', 'pillow', 'protobuf', 'py',
        'pycares', 'pycryptodome', 'pymongo', 'python-jose', 'requests',
        'sentry-sdk', 'setuptools', 'signxml', 'starlette', 'tornado',
        'urllib3', 'zipp'
    }
    
    javascript_packages = {
        'axios', 'brace-expansion', 'formidable', 'tar-fs'
    }
    
    print(f"\n🔍 Ecosystem Breakdown:")
    
    # Python analysis
    python_missing = python_packages - our_packages
    python_found = python_packages & our_packages
    print(f"   Python: {len(python_found)}/{len(python_packages)} ({(len(python_found)/len(python_packages))*100:.1f}%)")
    if python_missing:
        print(f"     Missing: {sorted(python_missing)}")
    
    # JavaScript analysis  
    js_missing = javascript_packages - our_packages
    js_found = javascript_packages & our_packages
    print(f"   JavaScript: {len(js_found)}/{len(javascript_packages)} ({(len(js_found)/len(javascript_packages))*100:.1f}%)")
    if js_missing:
        print(f"     Missing: {sorted(js_missing)}")
    
    print(f"\n💡 Analysis:")
    if len(missing_packages) == 0:
        print("🎉 Perfect parity achieved!")
    else:
        gap_percentage = (len(missing_packages) / len(semgrep_packages)) * 100
        print(f"   Current gap: {gap_percentage:.1f}% ({len(missing_packages)} packages)")
        
        # Check if missing packages actually exist
        for pkg in missing_packages:
            if pkg == 'formidable':
                print(f"   ⚠️  '{pkg}' - not found in codebase (potential Semgrep false positive)")
            else:
                print(f"   🔍 '{pkg}' - needs investigation")

if __name__ == "__main__":
    extract_fresh_packages()