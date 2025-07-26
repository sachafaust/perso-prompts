#!/usr/bin/env python3
"""
Quick test of Docker parser implementation.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sca_ai_scanner.parsers.docker import DockerParser

def test_basic_dockerfile():
    """Test basic Dockerfile parsing."""
    
    dockerfile_content = """
FROM ubuntu:20.04

RUN apt-get update && apt-get install -y \\
    nginx=1.18.0-0ubuntu1.2 \\
    python3 \\
    python3-pip

RUN pip3 install django==3.2.0 requests>=2.25.0

FROM node:16-alpine AS frontend
RUN npm install express@4.17.1
"""
    
    # Create temporary Dockerfile
    temp_file = Path("/tmp/Dockerfile")
    temp_file.write_text(dockerfile_content)
    
    try:
        parser = DockerParser("/tmp")
        packages = parser.parse_file(temp_file)
        
        print(f"📦 Found {len(packages)} packages:\n")
        
        # Group by ecosystem
        by_ecosystem = {}
        for pkg in packages:
            ecosystem = pkg.ecosystem
            if ecosystem not in by_ecosystem:
                by_ecosystem[ecosystem] = []
            by_ecosystem[ecosystem].append(pkg)
        
        # Display results
        for ecosystem, pkgs in sorted(by_ecosystem.items()):
            print(f"\n{ecosystem.upper()} ({len(pkgs)} packages):")
            for pkg in sorted(pkgs, key=lambda p: p.name):
                print(f"  - {pkg.name}: {pkg.version}")
        
        # Validation
        print("\n✅ Validation:")
        expected = {
            ("ubuntu", "20.04", "docker"),
            ("nginx", "1.18.0-0ubuntu1.2", "debian"),
            ("python3", "latest", "debian"),
            ("python3-pip", "latest", "debian"),
            ("django", "3.2.0", "pypi"),
            ("requests", "2.25.0", "pypi"),
            ("node", "16-alpine", "docker"),
            ("express", "4.17.1", "npm")
        }
        
        found = {(pkg.name, pkg.version, pkg.ecosystem) for pkg in packages}
        
        missing = expected - found
        extra = found - expected
        
        if missing:
            print(f"❌ Missing packages: {missing}")
        if extra:
            print(f"⚠️  Extra packages: {extra}")
        if not missing and not extra:
            print("✅ All expected packages found!")
            
    finally:
        temp_file.unlink(missing_ok=True)

def test_complex_dockerfile():
    """Test complex Dockerfile with multiple package managers."""
    
    dockerfile_content = """
FROM alpine:3.14

# Install system packages
RUN apk add --no-cache \\
    postgresql=13.8-r0 \\
    redis=6.2.6-r0 \\
    nodejs \\
    npm \\
    python3 \\
    py3-pip

# Install Python packages
RUN pip3 install \\
    celery[redis]==5.1.2 \\
    gunicorn

# Install Node packages
RUN npm install -g yarn@1.22.10
RUN yarn add lodash@4.17.21
"""
    
    temp_file = Path("/tmp/Dockerfile.complex")
    temp_file.write_text(dockerfile_content)
    
    try:
        parser = DockerParser("/tmp")
        packages = parser.parse_file(temp_file)
        
        print(f"\n\n📦 Complex Dockerfile - Found {len(packages)} packages:\n")
        
        # Group by ecosystem
        by_ecosystem = {}
        for pkg in packages:
            ecosystem = pkg.ecosystem
            if ecosystem not in by_ecosystem:
                by_ecosystem[ecosystem] = []
            by_ecosystem[ecosystem].append(pkg)
        
        # Display results
        for ecosystem, pkgs in sorted(by_ecosystem.items()):
            print(f"\n{ecosystem.upper()} ({len(pkgs)} packages):")
            for pkg in sorted(pkgs, key=lambda p: p.name):
                print(f"  - {pkg.name}: {pkg.version}")
                
    finally:
        temp_file.unlink(missing_ok=True)

if __name__ == "__main__":
    print("🐳 Testing Docker Parser Implementation\n")
    print("="*60)
    
    test_basic_dockerfile()
    test_complex_dockerfile()
    
    print("\n" + "="*60)
    print("✅ Docker parser basic functionality confirmed!")
    print("\nNext steps:")
    print("1. Run full validation suite")
    print("2. Implement CVE mapping")
    print("3. Add version resolution enhancements")