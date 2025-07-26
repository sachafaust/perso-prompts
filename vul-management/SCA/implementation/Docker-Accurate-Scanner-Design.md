# Docker Accurate Scanner Design

## Core Principle: No Guessing

For high-accuracy vulnerability detection in Docker, we must analyze actual image layers, not Dockerfile text.

## Implementation Architecture

### 1. Dual-Mode Scanner

```python
class DockerScanner:
    def __init__(self):
        self.mode = "accurate"  # or "fast"
    
    def scan(self, target):
        if self.mode == "fast":
            # Current implementation - static parsing
            # Clearly marked as "estimates only"
            return self.static_scan(target)
        else:
            # Accurate mode - image analysis
            return self.accurate_scan(target)
    
    def accurate_scan(self, target):
        """High accuracy scanning via image analysis."""
        
        # Step 1: Ensure we have an image
        if is_dockerfile(target):
            image = self.safe_build(target)
        elif is_image_reference(target):
            image = self.pull_image(target)
        else:
            raise ValueError("Invalid target")
        
        # Step 2: Extract without running
        packages = self.extract_packages_from_layers(image)
        
        # Step 3: Map to CVEs with confidence
        return self.map_to_cves(packages, confidence=1.0)
```

### 2. Safe Building Strategy

```python
class SafeDockerBuilder:
    """Build Dockerfiles safely for analysis."""
    
    def build_for_analysis(self, dockerfile_path):
        # Option 1: Use BuildKit security features
        build_opts = {
            "network": "none",  # No network during build
            "security_opt": ["no-new-privileges"],
            "target": "final",  # Stop at final stage
            "no_cache": True   # Fresh build
        }
        
        # Option 2: Build in isolated environment
        with IsolatedBuildEnvironment() as env:
            image_id = env.build(dockerfile_path, **build_opts)
            return image_id
    
    def extract_without_running(self, image_id):
        """Extract package info without creating container."""
        
        # Save image as tar
        image_tar = docker.save(image_id)
        
        # Extract filesystem layers
        with tarfile.open(image_tar) as tar:
            # Look for package databases in each layer
            package_files = {
                "debian": "var/lib/dpkg/status",
                "alpine": "lib/apk/db/installed", 
                "rhel": "var/lib/rpm/Packages"
            }
            
            packages = []
            for member in tar.getmembers():
                for distro, db_path in package_files.items():
                    if db_path in member.name:
                        content = tar.extractfile(member).read()
                        packages.extend(
                            self.parse_package_db(content, distro)
                        )
            
            return packages
```

### 3. Image Layer Analysis

```python
class ImageLayerAnalyzer:
    """Analyze Docker images without running containers."""
    
    def analyze_image(self, image_reference):
        # Pull image metadata only
        manifest = self.get_image_manifest(image_reference)
        
        # For each layer
        all_packages = []
        for layer in manifest.layers:
            # Download layer
            layer_data = self.download_layer(layer.digest)
            
            # Extract filesystem changes
            with self.extract_layer(layer_data) as fs:
                # Parse package databases
                packages = self.parse_all_package_formats(fs)
                all_packages.extend(packages)
        
        # Deduplicate and resolve final state
        return self.resolve_package_state(all_packages)
    
    def parse_all_package_formats(self, filesystem):
        """Parse all package manager databases."""
        
        parsers = {
            "/var/lib/dpkg/status": self.parse_dpkg,
            "/lib/apk/db/installed": self.parse_apk,
            "/var/lib/rpm/Packages": self.parse_rpm,
            # Also check for language packages
            "/usr/local/lib/python*/site-packages": self.parse_python,
            "/usr/lib/node_modules": self.parse_node,
        }
        
        packages = []
        for path, parser in parsers.items():
            if filesystem.exists(path):
                packages.extend(parser(filesystem.read(path)))
        
        return packages
```

### 4. CVE Mapping with Certainty

```python
class AccurateCVEMapper:
    """Map exact package versions to CVEs."""
    
    def map_packages_to_cves(self, packages, source="image_analysis"):
        vulnerabilities = []
        
        for package in packages:
            # We have exact versions now!
            cves = self.query_vulnerability_db(
                name=package.name,
                version=package.version,  # e.g., "1.18.0-0ubuntu1.2"
                distro=package.distro,    # e.g., "ubuntu:20.04"
                architecture=package.arch  # e.g., "amd64"
            )
            
            for cve in cves:
                vulnerabilities.append({
                    "package": package.name,
                    "installed_version": package.version,
                    "cve": cve.id,
                    "severity": cve.severity,
                    "fixed_version": cve.fixed_version,
                    "confidence": 1.0,  # We KNOW this is accurate
                    "source": source
                })
        
        return vulnerabilities
```

## Implementation Phases

### Phase 1: Image Analysis Core
1. Implement layer extraction
2. Parse dpkg/rpm/apk databases
3. Test with common base images

### Phase 2: Safe Building
1. BuildKit integration
2. Sandbox environment
3. Resource limits

### Phase 3: Performance Optimization
1. Layer caching
2. Parallel analysis
3. Incremental updates

### Phase 4: Integration
1. CLI support for both modes
2. Clear accuracy indicators
3. Performance benchmarks

## Performance Considerations

```python
class OptimizedImageScanner:
    def __init__(self):
        self.layer_cache = {}  # digest -> packages
        self.base_image_cache = {}  # image:tag -> packages
    
    def scan_with_cache(self, image):
        """Use caching for performance."""
        
        manifest = self.get_manifest(image)
        cached_packages = []
        layers_to_analyze = []
        
        # Check cache for each layer
        for layer in manifest.layers:
            if layer.digest in self.layer_cache:
                cached_packages.extend(self.layer_cache[layer.digest])
            else:
                layers_to_analyze.append(layer)
        
        # Analyze only new layers
        new_packages = self.analyze_layers(layers_to_analyze)
        
        # Update cache
        for layer, packages in zip(layers_to_analyze, new_packages):
            self.layer_cache[layer.digest] = packages
        
        return cached_packages + new_packages
```

## Conclusion

For high-accuracy Docker vulnerability scanning:

1. **Accept the reality**: We must analyze actual images, not Dockerfiles
2. **Build safely**: Use sandboxing and security controls
3. **Extract smartly**: Analyze layers without running containers
4. **Cache aggressively**: Many layers are reused across images
5. **Be transparent**: Always indicate accuracy level

This approach matches what production-grade tools (Trivy, Grype, Clair) actually do.