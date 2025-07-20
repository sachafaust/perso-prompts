"""
Docker dependency parser for Dockerfile and docker-compose files.
Extracts base images and package installations for vulnerability analysis.
"""

import re
from pathlib import Path
from typing import List, Set, Dict, Any, Optional
import logging

from .base import DependencyParser
from ..core.models import Package, SourceLocation, FileType
from ..exceptions import ParsingError

logger = logging.getLogger(__name__)


class DockerParser(DependencyParser):
    """
    Docker dependency parser for container security analysis.
    Handles Dockerfile, docker-compose.yml, and related container configuration files.
    """
    
    def get_supported_files(self) -> Set[str]:
        """Return set of supported Docker configuration files."""
        return {
            'Dockerfile', 'dockerfile', 'Dockerfile.dev', 'Dockerfile.prod',
            'docker-compose.yml', 'docker-compose.yaml',
            'docker-compose.dev.yml', 'docker-compose.prod.yml',
            'docker-compose.override.yml'
        }
    
    def get_ecosystem_name(self) -> str:
        """Return ecosystem name for Docker packages."""
        return "docker"
    
    def parse_file(self, file_path: Path) -> List[Package]:
        """Parse a Docker configuration file and extract dependencies."""
        if not file_path.exists():
            raise ParsingError(f"File not found: {file_path}", str(file_path))
        
        file_name = file_path.name.lower()
        
        if file_name.startswith('dockerfile'):
            return self._parse_dockerfile(file_path)
        elif 'docker-compose' in file_name and file_name.endswith(('.yml', '.yaml')):
            return self._parse_docker_compose(file_path)
        else:
            logger.warning(f"Unsupported Docker file type: {file_name}")
            return []
    
    def _parse_dockerfile(self, file_path: Path) -> List[Package]:
        """Parse Dockerfile and extract base images and installed packages."""
        packages = []
        lines = self.read_file_lines(file_path)
        
        # Handle line continuations
        processed_lines = self._process_line_continuations(lines)
        
        for line_info in processed_lines:
            line = line_info['line'].strip()
            line_num = line_info['line_num']
            original_line = line_info['original']
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Parse FROM instructions (base images)
            if line.upper().startswith('FROM '):
                from_packages = self._parse_from_instruction(
                    line, file_path, line_num, original_line
                )
                packages.extend(from_packages)
            
            # Parse RUN instructions that install packages
            elif line.upper().startswith('RUN '):
                run_packages = self._parse_run_instruction(
                    line, file_path, line_num, original_line
                )
                packages.extend(run_packages)
            
            # Parse COPY/ADD instructions for dependency files
            elif line.upper().startswith(('COPY ', 'ADD ')):
                copy_packages = self._parse_copy_instruction(
                    line, file_path, line_num, original_line
                )
                packages.extend(copy_packages)
        
        return packages
    
    def _process_line_continuations(self, lines: List[str]) -> List[dict]:
        """Process line continuations (backslashes) in Dockerfile."""
        processed = []
        current_line = ""
        current_line_num = 1
        current_original = ""
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # If this is a continuation of the previous line
            if current_line and stripped:
                current_line += " " + stripped.rstrip('\\').strip()
                current_original += " " + line.rstrip()
            else:
                # If we have an accumulated line, process it
                if current_line:
                    processed.append({
                        'line': current_line,
                        'line_num': current_line_num,
                        'original': current_original
                    })
                
                # Start new line
                current_line = stripped.rstrip('\\').strip()
                current_line_num = line_num
                current_original = line.rstrip()
            
            # If line doesn't end with backslash, complete the instruction
            if not stripped.endswith('\\'):
                if current_line:
                    processed.append({
                        'line': current_line,
                        'line_num': current_line_num,
                        'original': current_original
                    })
                current_line = ""
                current_original = ""
        
        # Handle final line if exists
        if current_line:
            processed.append({
                'line': current_line,
                'line_num': current_line_num,
                'original': current_original
            })
        
        return processed
    
    def _parse_from_instruction(
        self, 
        line: str, 
        file_path: Path, 
        line_num: int, 
        original_line: str
    ) -> List[Package]:
        """Parse FROM instruction to extract base image."""
        packages = []
        
        # Parse FROM instruction: FROM image:tag [AS name]
        from_match = re.match(r'^FROM\s+([^\s]+)', line, re.IGNORECASE)
        if from_match:
            image_spec = from_match.group(1)
            
            # Skip multi-stage build references
            if image_spec.startswith('--'):
                return packages
            
            # Parse image name and tag
            image_name, image_tag = self._parse_image_spec(image_spec)
            
            if image_name and self.should_include_docker_image(image_name, image_tag):
                source_location = self.create_source_location(
                    file_path, line_num, original_line.strip(), FileType.DOCKERFILE
                )
                
                package = Package(
                    name=self.normalize_package_name(image_name),
                    version=image_tag or "latest",
                    source_locations=[source_location],
                    ecosystem="docker"
                )
                
                packages.append(package)
        
        return packages
    
    def _parse_image_spec(self, image_spec: str) -> tuple[str, Optional[str]]:
        """Parse Docker image specification into name and tag."""
        # Handle registry prefix
        if '/' in image_spec and '.' in image_spec.split('/')[0]:
            # Has registry (e.g., registry.example.com/image:tag)
            registry_and_image = image_spec
        else:
            registry_and_image = image_spec
        
        # Split image and tag
        if ':' in registry_and_image:
            image_name, tag = registry_and_image.rsplit(':', 1)
            # Handle digest format (image@sha256:...)
            if '@' in tag:
                tag = tag.split('@')[0] or "latest"
        else:
            image_name = registry_and_image
            tag = "latest"
        
        return image_name, tag
    
    def _parse_run_instruction(
        self, 
        line: str, 
        file_path: Path, 
        line_num: int, 
        original_line: str
    ) -> List[Package]:
        """Parse RUN instruction to extract installed packages."""
        packages = []
        
        # Remove RUN prefix
        run_command = line[4:].strip()
        
        # Parse different package managers
        packages.extend(self._parse_apt_packages(run_command, file_path, line_num, original_line))
        packages.extend(self._parse_yum_packages(run_command, file_path, line_num, original_line))
        packages.extend(self._parse_apk_packages(run_command, file_path, line_num, original_line))
        packages.extend(self._parse_pip_packages(run_command, file_path, line_num, original_line))
        packages.extend(self._parse_npm_packages(run_command, file_path, line_num, original_line))
        
        return packages
    
    def _parse_apt_packages(
        self, 
        command: str, 
        file_path: Path, 
        line_num: int, 
        original_line: str
    ) -> List[Package]:
        """Parse apt/apt-get package installations."""
        packages = []
        
        # Look for apt install commands (with optional environment variables)
        apt_patterns = [
            r'(?:[A-Z_]+=\S+\s+)?apt-get\s+install\s+(.+)',
            r'(?:[A-Z_]+=\S+\s+)?apt\s+install\s+(.+)',
            r'(?:[A-Z_]+=\S+\s+)?aptitude\s+install\s+(.+)'
        ]
        
        for pattern in apt_patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                package_list = match.group(1)
                
                # Clean up package list - remove common flags but preserve package names
                package_list = re.sub(r'\s*-(y|yes|q|quiet|f|force)\s*', ' ', package_list)  # Remove short flags
                package_list = re.sub(r'\s*--no-install-recommends\s*', ' ', package_list)  # Remove long flags
                package_list = re.sub(r'\s*&&\s*.*', '', package_list)  # Remove chained commands
                
                # Split packages
                package_names = package_list.split()
                
                for pkg_name in package_names:
                    # Skip flags and common utilities
                    if pkg_name.startswith('-') or pkg_name in ['sudo', 'curl', 'wget', 'ca-certificates']:
                        continue
                    
                    # Parse package with version
                    name, version = self._parse_deb_package(pkg_name)
                    
                    if name and self.should_include_package(name, version):
                        source_location = self.create_source_location(
                            file_path, line_num, original_line.strip(), FileType.DOCKERFILE
                        )
                        
                        package = Package(
                            name=self.normalize_package_name(name),
                            version=version,
                            source_locations=[source_location],
                            ecosystem="debian"
                        )
                        
                        packages.append(package)
        
        return packages
    
    def _parse_deb_package(self, pkg_spec: str) -> tuple[str, str]:
        """Parse Debian package specification."""
        # Handle version specification: package=version
        if '=' in pkg_spec:
            name, version = pkg_spec.split('=', 1)
        else:
            name = pkg_spec
            version = "latest"
        
        return name.strip(), version.strip()
    
    def _parse_yum_packages(
        self, 
        command: str, 
        file_path: Path, 
        line_num: int, 
        original_line: str
    ) -> List[Package]:
        """Parse yum/dnf package installations."""
        packages = []
        
        yum_patterns = [
            r'yum\s+install\s+(.+)',
            r'dnf\s+install\s+(.+)',
            r'zypper\s+install\s+(.+)'
        ]
        
        for pattern in yum_patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                package_list = match.group(1)
                
                # Clean up package list
                package_list = re.sub(r'\s*-[a-zA-Z]\s*', ' ', package_list)
                package_list = re.sub(r'\s*&&\s*.*', '', package_list)
                
                package_names = package_list.split()
                
                for pkg_name in package_names:
                    if pkg_name.startswith('-') or pkg_name in ['sudo', 'curl', 'wget']:
                        continue
                    
                    name, version = self._parse_rpm_package(pkg_name)
                    
                    if name and self.should_include_package(name, version):
                        source_location = self.create_source_location(
                            file_path, line_num, original_line.strip(), FileType.DOCKERFILE
                        )
                        
                        package = Package(
                            name=self.normalize_package_name(name),
                            version=version,
                            source_locations=[source_location],
                            ecosystem="rpm"
                        )
                        
                        packages.append(package)
        
        return packages
    
    def _parse_rpm_package(self, pkg_spec: str) -> tuple[str, str]:
        """Parse RPM package specification."""
        # Handle version specification: package-version
        if '-' in pkg_spec and not pkg_spec.startswith('-'):
            # Try to split on last dash (version separator)
            parts = pkg_spec.rsplit('-', 1)
            if len(parts) == 2 and re.match(r'[\d\.]', parts[1]):
                return parts[0], parts[1]
        
        return pkg_spec, "latest"
    
    def _parse_apk_packages(
        self, 
        command: str, 
        file_path: Path, 
        line_num: int, 
        original_line: str
    ) -> List[Package]:
        """Parse apk (Alpine) package installations."""
        packages = []
        
        apk_pattern = r'apk\s+add\s+(.+)'
        match = re.search(apk_pattern, command, re.IGNORECASE)
        
        if match:
            package_list = match.group(1)
            
            # Clean up package list
            package_list = re.sub(r'\s*--[a-zA-Z-]+\s*', ' ', package_list)  # Remove flags
            package_list = re.sub(r'\s*&&\s*.*', '', package_list)
            
            package_names = package_list.split()
            
            for pkg_name in package_names:
                if pkg_name.startswith('-') or pkg_name in ['sudo', 'curl', 'wget']:
                    continue
                
                name, version = self._parse_apk_package(pkg_name)
                
                if name and self.should_include_package(name, version):
                    source_location = self.create_source_location(
                        file_path, line_num, original_line.strip(), FileType.DOCKERFILE
                    )
                    
                    package = Package(
                        name=self.normalize_package_name(name),
                        version=version,
                        source_locations=[source_location],
                        ecosystem="alpine"
                    )
                    
                    packages.append(package)
        
        return packages
    
    def _parse_apk_package(self, pkg_spec: str) -> tuple[str, str]:
        """Parse Alpine package specification."""
        # Handle version specification: package=version
        if '=' in pkg_spec:
            name, version = pkg_spec.split('=', 1)
        else:
            name = pkg_spec
            version = "latest"
        
        return name.strip(), version.strip()
    
    def _parse_pip_packages(
        self, 
        command: str, 
        file_path: Path, 
        line_num: int, 
        original_line: str
    ) -> List[Package]:
        """Parse pip package installations."""
        packages = []
        
        pip_patterns = [
            r'pip\s+install\s+(.+)',
            r'pip3\s+install\s+(.+)',
            r'python\s+-m\s+pip\s+install\s+(.+)',
            r'python3\s+-m\s+pip\s+install\s+(.+)'
        ]
        
        for pattern in pip_patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                package_list = match.group(1)
                
                # Handle requirements file
                if '-r ' in package_list:
                    continue  # Skip requirements file installations
                
                # Clean up package list - remove common pip flags
                package_list = re.sub(r'\s*--no-cache-dir\b', ' ', package_list)
                package_list = re.sub(r'\s*--user\b', ' ', package_list)
                package_list = re.sub(r'\s*--upgrade\b', ' ', package_list)
                package_list = re.sub(r'\s*--force-reinstall\b', ' ', package_list)
                package_list = re.sub(r'\s*&&\s*.*', '', package_list)
                
                package_names = package_list.split()
                
                for pkg_name in package_names:
                    if pkg_name.startswith('-'):
                        continue
                    
                    # Parse pip package specification
                    name, version = self._parse_pip_package(pkg_name)
                    
                    if name and self.should_include_package(name, version):
                        source_location = self.create_source_location(
                            file_path, line_num, original_line.strip(), FileType.DOCKERFILE
                        )
                        
                        package = Package(
                            name=self.normalize_package_name(name),
                            version=version,
                            source_locations=[source_location],
                            ecosystem="pypi"
                        )
                        
                        packages.append(package)
        
        return packages
    
    def _parse_pip_package(self, pkg_spec: str) -> tuple[str, str]:
        """Parse pip package specification."""
        # Remove extras like [standard] from package name
        if '[' in pkg_spec:
            pkg_spec = pkg_spec.split('[')[0]
        
        # Handle version operators
        version_operators = ['>=', '<=', '==', '!=', '~=', '>', '<']
        
        for operator in sorted(version_operators, key=len, reverse=True):
            if operator in pkg_spec:
                name, version = pkg_spec.split(operator, 1)
                return name.strip(), version.strip()
        
        return pkg_spec.strip(), "latest"
    
    def _parse_npm_packages(
        self, 
        command: str, 
        file_path: Path, 
        line_num: int, 
        original_line: str
    ) -> List[Package]:
        """Parse npm package installations."""
        packages = []
        
        npm_patterns = [
            r'npm\s+install\s+(.+)',
            r'npm\s+i\s+(.+)',
            r'yarn\s+add\s+(.+)',
            r'pnpm\s+add\s+(.+)'
        ]
        
        for pattern in npm_patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                package_list = match.group(1)
                
                # Clean up package list
                package_list = re.sub(r'\s*--[a-zA-Z-]+\s*', ' ', package_list)
                package_list = re.sub(r'\s*&&\s*.*', '', package_list)
                
                package_names = package_list.split()
                
                for pkg_name in package_names:
                    if pkg_name.startswith('-'):
                        continue
                    
                    name, version = self._parse_npm_package(pkg_name)
                    
                    if name and self.should_include_package(name, version):
                        source_location = self.create_source_location(
                            file_path, line_num, original_line.strip(), FileType.DOCKERFILE
                        )
                        
                        package = Package(
                            name=self.normalize_package_name(name),
                            version=version,
                            source_locations=[source_location],
                            ecosystem="npm"
                        )
                        
                        packages.append(package)
        
        return packages
    
    def _parse_npm_package(self, pkg_spec: str) -> tuple[str, str]:
        """Parse npm package specification."""
        if '@' in pkg_spec and not pkg_spec.startswith('@'):
            # Handle version: package@version
            name, version = pkg_spec.rsplit('@', 1)
        elif pkg_spec.startswith('@') and pkg_spec.count('@') > 1:
            # Handle scoped package with version: @scope/package@version
            parts = pkg_spec.rsplit('@', 1)
            name, version = parts[0], parts[1]
        else:
            name = pkg_spec
            version = "latest"
        
        return name.strip(), version.strip()
    
    def _parse_copy_instruction(
        self, 
        line: str, 
        file_path: Path, 
        line_num: int, 
        original_line: str
    ) -> List[Package]:
        """Parse COPY/ADD instructions for dependency files."""
        # This could be extended to detect when dependency files are copied
        # and potentially parse them if they're available
        return []
    
    def _parse_docker_compose(self, file_path: Path) -> List[Package]:
        """Parse docker-compose.yml files."""
        packages = []
        
        try:
            import yaml
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # Parse services
            if 'services' in data:
                for service_name, service_config in data['services'].items():
                    if isinstance(service_config, dict):
                        # Parse image specification
                        if 'image' in service_config:
                            image_packages = self._parse_compose_image(
                                service_config['image'], file_path, service_name
                            )
                            packages.extend(image_packages)
                        
                        # Parse build context (could contain Dockerfile)
                        if 'build' in service_config:
                            build_packages = self._parse_compose_build(
                                service_config['build'], file_path, service_name
                            )
                            packages.extend(build_packages)
            
        except ImportError:
            logger.warning(f"PyYAML not available, skipping {file_path}")
        except Exception as e:
            raise ParsingError(f"Failed to parse docker-compose file: {e}", str(file_path))
        
        return packages
    
    def _parse_compose_image(
        self, 
        image_spec: str, 
        file_path: Path, 
        service_name: str
    ) -> List[Package]:
        """Parse image specification from docker-compose."""
        packages = []
        
        image_name, image_tag = self._parse_image_spec(image_spec)
        
        if image_name and self.should_include_docker_image(image_name, image_tag):
            source_location = self.create_source_location(
                file_path, 1, f"services.{service_name}.image: {image_spec}", FileType.DOCKERFILE
            )
            
            package = Package(
                name=self.normalize_package_name(image_name),
                version=image_tag or "latest",
                source_locations=[source_location],
                ecosystem="docker"
            )
            
            packages.append(package)
        
        return packages
    
    def _parse_compose_build(
        self, 
        build_config: Any, 
        file_path: Path, 
        service_name: str
    ) -> List[Package]:
        """Parse build configuration from docker-compose."""
        # Could be extended to parse referenced Dockerfiles
        return []
    
    def should_include_docker_image(self, image_name: str, tag: str) -> bool:
        """Determine if Docker image should be included."""
        # Skip scratch and empty base images
        if image_name in ['scratch', 'busybox']:
            return False
        
        # Include official images and versioned images
        return True
    
    def should_include_package(self, name: str, version: str) -> bool:
        """Override with Docker-specific exclusions."""
        if not super().should_include_package(name, version):
            return False
        
        # Docker-specific exclusions for common utilities
        excluded_packages = {
            'curl', 'wget', 'ca-certificates', 'gnupg', 'lsb-release',
            'apt-transport-https', 'software-properties-common',
            'build-essential', 'make', 'gcc', 'g++', 'git'
        }
        
        if name.lower() in excluded_packages:
            logger.debug(f"Excluding common utility package: {name}")
            return False
        
        return True