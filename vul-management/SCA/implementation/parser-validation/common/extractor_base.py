"""
Base classes for test extraction from open source projects.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
import git
import tempfile
import shutil
from .test_format import StandardizedTestCase


class BaseTestExtractor(ABC):
    """Base class for extracting tests from open source repositories."""
    
    def __init__(self, repo_url: str, version: str = "main"):
        """
        Initialize the extractor.
        
        Args:
            repo_url: Git repository URL
            version: Git tag, branch, or commit to extract from
        """
        self.repo_url = repo_url
        self.version = version
        self.repo_path: Optional[Path] = None
        self.extracted_tests: List[StandardizedTestCase] = []
    
    def __enter__(self):
        """Context manager entry - clone repository."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir) / "repo"
        
        print(f"Cloning {self.repo_url} at {self.version}...")
        repo = git.Repo.clone_from(self.repo_url, str(self.repo_path))
        
        if self.version != "main":
            repo.git.checkout(self.version)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup temporary directory."""
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @abstractmethod
    def extract_tests(self) -> List[StandardizedTestCase]:
        """
        Extract test cases from the cloned repository.
        
        Returns:
            List of standardized test cases
        """
        pass
    
    @abstractmethod
    def get_test_files(self) -> List[Path]:
        """
        Get list of test files to analyze.
        
        Returns:
            List of test file paths
        """
        pass
    
    @abstractmethod
    def parse_test_file(self, file_path: Path) -> List[StandardizedTestCase]:
        """
        Parse a single test file and extract test cases.
        
        Args:
            file_path: Path to test file
            
        Returns:
            List of extracted test cases
        """
        pass
    
    def filter_relevant_tests(self, tests: List[StandardizedTestCase]) -> List[StandardizedTestCase]:
        """
        Filter tests to only include those relevant to dependency parsing.
        
        Args:
            tests: All extracted tests
            
        Returns:
            Filtered list of relevant tests
        """
        # Override in subclasses for project-specific filtering
        return tests
    
    def save_tests_to_yaml(self, output_dir: Path, tests: List[StandardizedTestCase]) -> None:
        """
        Save extracted tests to YAML files organized by category.
        
        Args:
            output_dir: Directory to save test files
            tests: Test cases to save
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Group tests by category
        by_category = {}
        for test in tests:
            category = test.category.value
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(test)
        
        # Save each category to its own file
        for category, category_tests in by_category.items():
            category_file = output_dir / f"{category}.yaml"
            
            with open(category_file, 'w') as f:
                f.write(f"# {category.replace('_', ' ').title()} Test Cases\n")
                f.write(f"# Extracted from {self.repo_url} at {self.version}\n")
                f.write(f"# Total tests: {len(category_tests)}\n\n")
                
                for test in category_tests:
                    f.write(test.to_yaml())
                    f.write("\n---\n\n")
        
        print(f"Saved {len(tests)} tests to {output_dir}")
        for category, category_tests in by_category.items():
            print(f"  {category}: {len(category_tests)} tests")


class SourceProjectInfo:
    """Information about a source project for test extraction."""
    
    def __init__(self, name: str, repo_url: str, test_directories: List[str], 
                 stable_version: str, description: str):
        self.name = name
        self.repo_url = repo_url
        self.test_directories = test_directories
        self.stable_version = stable_version
        self.description = description


# Common source projects for different languages
PYTHON_SOURCES = {
    "pip-tools": SourceProjectInfo(
        name="pip-tools",
        repo_url="https://github.com/jazzband/pip-tools.git",
        test_directories=["tests"],
        stable_version="7.4.1",
        description="Requirements.txt parsing and compilation"
    ),
    "poetry": SourceProjectInfo(
        name="poetry",
        repo_url="https://github.com/python-poetry/poetry.git", 
        test_directories=["tests"],
        stable_version="1.8.3",
        description="pyproject.toml parsing and dependency resolution"
    ),
    "setuptools": SourceProjectInfo(
        name="setuptools",
        repo_url="https://github.com/pypa/setuptools.git",
        test_directories=["tests"],
        stable_version="70.0.0",
        description="setup.py and setup.cfg parsing"
    )
}

JAVASCRIPT_SOURCES = {
    "npm": SourceProjectInfo(
        name="npm",
        repo_url="https://github.com/npm/npm.git",
        test_directories=["test"],
        stable_version="10.8.1",
        description="package.json parsing"
    ),
    "yarn": SourceProjectInfo(
        name="yarn",
        repo_url="https://github.com/yarnpkg/yarn.git",
        test_directories=["__tests__"],
        stable_version="1.22.19",
        description="yarn.lock parsing"
    )
}