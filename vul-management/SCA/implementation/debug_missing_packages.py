#!/usr/bin/env python3
"""
Debug why specific packages are missing from our detection.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sca_ai_scanner.parsers.python import PythonParser
from sca_ai_scanner.parsers.javascript import JavaScriptParser
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

def debug_python_packages():
    """Debug missing Python packages."""
    print("🐍 Debugging Python package detection...")
    
    missing_packages = ['h11', 'jupyter-server', 'py', 'tornado']
    rippling_path = Path.home() / 'code' / 'rippling-main'
    
    if not rippling_path.exists():
        print(f"❌ Rippling codebase not found at {rippling_path}")
        return
    
    parser = PythonParser(str(rippling_path))
    all_packages = parser.parse_all_files()
    
    found_packages = {pkg.name.lower() for pkg in all_packages}
    
    print(f"📊 Found {len(all_packages)} Python packages total")
    
    for missing_pkg in missing_packages:
        if missing_pkg.lower() in found_packages:
            print(f"✅ {missing_pkg} - FOUND")
        else:
            print(f"❌ {missing_pkg} - MISSING")
            
            # Check for variations
            variations = [
                missing_pkg.replace('-', '_'),
                missing_pkg.replace('_', '-'),
                missing_pkg.replace('-', ''),
                missing_pkg.upper(),
                missing_pkg.capitalize()
            ]
            
            found_variations = [v for v in variations if v.lower() in found_packages]
            if found_variations:
                print(f"   🔍 Found variations: {found_variations}")
            
            # Check if it's being filtered out
            print(f"   🔍 Testing exclusion logic...")
            parser_instance = PythonParser(str(rippling_path))
            should_include = parser_instance.should_include_package(missing_pkg, "1.0.0")
            print(f"   🔍 should_include_package('{missing_pkg}', '1.0.0'): {should_include}")

def debug_javascript_packages():
    """Debug missing JavaScript packages."""
    print("\n📦 Debugging JavaScript package detection...")
    
    missing_packages = ['formidable']
    rippling_path = Path.home() / 'code' / 'rippling-main'
    
    if not rippling_path.exists():
        print(f"❌ Rippling codebase not found at {rippling_path}")
        return
    
    parser = JavaScriptParser(str(rippling_path))
    all_packages = parser.parse_all_files()
    
    found_packages = {pkg.name.lower() for pkg in all_packages}
    
    print(f"📊 Found {len(all_packages)} JavaScript packages total")
    
    for missing_pkg in missing_packages:
        if missing_pkg.lower() in found_packages:
            print(f"✅ {missing_pkg} - FOUND")
        else:
            print(f"❌ {missing_pkg} - MISSING")
            
            # Check for variations
            variations = [
                missing_pkg.replace('-', '_'),
                missing_pkg.replace('_', '-'),
                missing_pkg.replace('-', ''),
                missing_pkg.upper(),
                missing_pkg.capitalize()
            ]
            
            found_variations = [v for v in variations if v.lower() in found_packages]
            if found_variations:
                print(f"   🔍 Found variations: {found_variations}")
            
            # Check if it's being filtered out
            print(f"   🔍 Testing exclusion logic...")
            parser_instance = JavaScriptParser(str(rippling_path))
            should_include = parser_instance.should_include_package(missing_pkg, "1.0.0")
            print(f"   🔍 should_include_package('{missing_pkg}', '1.0.0'): {should_include}")

def main():
    """Debug missing packages."""
    print("🔍 Debugging Missing Packages")
    print("Investigating why 5 packages are not detected by our parsers")
    
    debug_python_packages()
    debug_javascript_packages()
    
    print("\n💡 Next steps based on findings:")
    print("   - Check if packages are in different file formats")
    print("   - Verify exclusion logic isn't too aggressive")
    print("   - Look for case sensitivity issues")
    print("   - Check transitive dependency detection")

if __name__ == "__main__":
    main()