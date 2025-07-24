"""
Test JavaScript parser on real-world project (Rippling codebase).
Validate production-level parsing capability.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sca_ai_scanner.parsers.javascript import JavaScriptParser

def test_javascript_parser_on_rippling():
    """Test JavaScript parser on Rippling codebase."""
    
    # Use Rippling codebase directory
    rippling_path = "/Users/sacha/code/rippling-main"
    parser = JavaScriptParser(rippling_path)
    
    print("🔍 Testing JavaScript Parser on Rippling Codebase")
    print("=" * 50)
    
    # Discover JavaScript dependency files
    js_files = parser.discover_dependency_files()
    
    print(f"📁 Found {len(js_files)} JavaScript dependency files:")
    
    total_packages = 0
    successful_parses = 0
    failed_parses = 0
    parse_errors = []
    
    # Sample a few files to test (don't process all to save time)
    sample_files = list(js_files)[:10]  # Test first 10 files
    
    for file_path in sample_files:
        try:
            print(f"\n📦 Parsing: {file_path}")
            packages = parser.parse_file(file_path)
            
            print(f"   ✅ Found {len(packages)} packages")
            if len(packages) > 0:
                print(f"   📋 Sample packages: {', '.join([pkg.name for pkg in packages[:5]])}")
                if len(packages) > 5:
                    print(f"      ... and {len(packages) - 5} more")
            
            total_packages += len(packages)
            successful_parses += 1
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            failed_parses += 1
            parse_errors.append(f"{file_path}: {e}")
    
    # Summary
    print(f"\n📊 Parsing Results:")
    print(f"   Files tested: {len(sample_files)}")
    print(f"   Successful: {successful_parses}")
    print(f"   Failed: {failed_parses}")
    print(f"   Total packages found: {total_packages}")
    print(f"   Success rate: {(successful_parses/len(sample_files)*100):.1f}%")
    
    if parse_errors:
        print(f"\n❌ Parse Errors:")
        for error in parse_errors[:3]:  # Show first 3 errors
            print(f"   • {error}")
        if len(parse_errors) > 3:
            print(f"   ... and {len(parse_errors) - 3} more errors")
    
    # Test some specific interesting files
    interesting_files = [
        "/Users/sacha/code/rippling-main/app/grc/modules/client_bindings/package.json",
        "/Users/sacha/code/rippling-main/tools/typescript/disco/package.json"
    ]
    
    print(f"\n🎯 Testing Specific Complex Files:")
    for file_path in interesting_files:
        file_obj = Path(file_path)
        if file_obj.exists():
            try:
                print(f"\n📦 {file_obj.name} ({file_obj.parent}):")
                packages = parser.parse_file(file_obj)
                print(f"   📋 {len(packages)} packages found")
                
                # Show package breakdown by type
                production_pkgs = []
                scoped_pkgs = []
                for pkg in packages:
                    if pkg.name.startswith('@'):
                        scoped_pkgs.append(pkg.name)
                    else:
                        production_pkgs.append(pkg.name)
                
                print(f"   🏷️  Scoped packages: {len(scoped_pkgs)}")
                if scoped_pkgs:
                    print(f"      Examples: {', '.join(scoped_pkgs[:3])}")
                print(f"   📦 Regular packages: {len(production_pkgs)}")
                if production_pkgs:
                    print(f"      Examples: {', '.join(production_pkgs[:3])}")
                
            except Exception as e:
                print(f"   ❌ Error parsing {file_obj.name}: {e}")
    
    print(f"\n🎯 JavaScript Parser Real-World Validation {'PASSED' if successful_parses > failed_parses else 'NEEDS IMPROVEMENT'}")
    
    return {
        "total_files_tested": len(sample_files),
        "successful_parses": successful_parses,
        "failed_parses": failed_parses,
        "total_packages": total_packages,
        "success_rate": (successful_parses/len(sample_files)*100) if sample_files else 0,
        "errors": parse_errors
    }


if __name__ == "__main__":
    results = test_javascript_parser_on_rippling()
    
    print(f"\n📈 Final Score: {results['success_rate']:.1f}% success rate")
    print(f"🎯 Status: {'PRODUCTION READY' if results['success_rate'] >= 90 else 'NEEDS IMPROVEMENT'}")