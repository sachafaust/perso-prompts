#!/usr/bin/env python3
"""
Analyze remaining gaps between our tool and Semgrep across all ecosystems.
"""

def analyze_gaps():
    """Compare our findings vs Semgrep to identify remaining gaps."""
    
    # Semgrep complete findings (all ecosystems)
    semgrep_packages = {
        'aiohttp', 'authlib', 'axios', 'azure-identity', 'brace-expansion',
        'certifi', 'cryptography', 'django', 'djangorestframework', 'formidable',
        'gitpython', 'h11', 'idna', 'jinja2', 'jupyter-server', 'nltk',
        'pillow', 'protobuf', 'py', 'pycares', 'pycryptodome', 'pymongo',
        'python-jose', 'requests', 'sentry-sdk', 'setuptools', 'signxml',
        'starlette', 'tar-fs', 'tornado', 'urllib3', 'zipp'
    }
    
    # Read our current findings
    try:
        with open('/tmp/our_python_packages.txt', 'r') as f:
            our_packages_raw = f.read().strip().split('\n')
    except FileNotFoundError:
        print("❌ our_python_packages.txt not found - need to run package extraction first")
        return
    
    # Clean our package names (remove version info, normalize)
    our_packages = set()
    for pkg in our_packages_raw:
        if pkg.strip():
            # Remove version constraints and normalize
            clean_name = pkg.strip().split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0].split('!=')[0].split('~=')[0]
            clean_name = clean_name.lower().strip()
            if clean_name:
                our_packages.add(clean_name)
    
    print(f"📊 Analysis Summary:")
    print(f"   Semgrep packages: {len(semgrep_packages)}")
    print(f"   Our packages: {len(our_packages)}")
    
    # Find gaps
    missing_packages = semgrep_packages - our_packages
    extra_packages = our_packages - semgrep_packages
    found_packages = semgrep_packages & our_packages
    
    print(f"\n🎯 Gap Analysis:")
    print(f"   Found by both: {len(found_packages)} ({(len(found_packages)/len(semgrep_packages))*100:.1f}%)")
    print(f"   Missing from our tool: {len(missing_packages)}")
    print(f"   Extra in our tool: {len(extra_packages)}")
    
    if missing_packages:
        print(f"\n❌ Missing packages ({len(missing_packages)}):")
        for pkg in sorted(missing_packages):
            print(f"   - {pkg}")
    
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
        print(f"   Most likely causes:")
        print(f"     - Package exclusion/filtering logic")
        print(f"     - Missing file format support")
        print(f"     - Case sensitivity issues")
        print(f"     - Transitive dependency detection")

if __name__ == "__main__":
    analyze_gaps()