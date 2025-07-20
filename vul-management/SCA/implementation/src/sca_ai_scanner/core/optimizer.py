"""
Token optimization engine for balanced token efficiency.
Implements AI Agent First design with context window optimization.
"""

import json
from typing import List, Dict, Any
from .models import Package, ScanConfig


class TokenOptimizer:
    """
    Token optimization engine focused on balanced efficiency.
    Prioritizes data accuracy and usefulness while minimizing token usage.
    """
    
    def __init__(self, config: ScanConfig):
        """Initialize token optimizer with scan configuration."""
        self.config = config
        self.optimization_strategies = {
            "compact": self._format_compact_list,
            "detailed": self._format_detailed_list, 
            "balanced": self._format_balanced_list
        }
        
        # Use balanced format by default (AI Agent First principle)
        self.strategy = "balanced"
    
    def create_prompt(self, packages: List[Package]) -> str:
        """
        Generate vulnerability analysis prompt for knowledge-only models.
        Optimized for accuracy while maintaining token efficiency.
        """
        package_list = self._format_package_list(packages)
        
        prompt = f"""Find ALL known CVEs and security vulnerabilities for these {len(packages)} packages. Search thoroughly through your training data.

Packages to analyze:
{package_list}

CRITICAL: These packages likely have known vulnerabilities. Be exhaustive in your search:
- Search for ALL CVEs affecting each package version and earlier versions
- Include vulnerability advisories from GitHub Security, NVD, OSV, PyPI Advisory Database
- Look for security patches, changelogs mentioning fixes for security issues
- Include vulnerabilities from dependency research papers and security blogs
- Check for both code vulnerabilities and supply chain/build issues

Examples of what to look for:
- selenium:3.141.0 (from 2018) - very likely has multiple CVEs
- lxml parsing vulnerabilities 
- pillow image processing CVEs
- cryptography timing attacks or implementation flaws
- django web framework security issues

CRITICAL OPTIMIZATION: Only return packages that have vulnerabilities. 
Skip packages with no CVEs to reduce response size.

Return ONLY vulnerable packages in JSON format:

{{
  "package:version": {{
    "cves": [{{
      "id": "CVE-YYYY-NNNNN",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW", 
      "description": "Brief description",
      "cvss_score": 0.0-10.0
    }}],
    "confidence": 0.0-1.0
  }}
}}

If NO vulnerabilities found across all packages, return empty JSON object: {{}}"""
        
        return prompt
    
    def create_prompt_with_live_search(self, packages: List[Package]) -> str:
        """
        Generate prompt for models with live search capabilities.
        Leverages real-time CVE data for maximum accuracy.
        """
        package_list = self._format_package_list(packages)
        
        prompt = f"""Search current vulnerability databases for these {len(packages)} packages:

Packages to analyze:
{package_list}

Use web search to find current vulnerability information:
1. Search CVE databases (NVD, MITRE, OSV.dev) for each package
2. Look for recent security advisories and patches
3. Check GitHub security advisories for the packages
4. Verify latest vulnerability disclosures

CRITICAL OPTIMIZATION: Only return packages that have vulnerabilities. 
Skip packages with no CVEs to reduce response size.

Return ONLY vulnerable packages in JSON format:

{{
  "package:version": {{
    "cves": [{{
      "id": "CVE-YYYY-NNNNN",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW", 
      "description": "Vulnerability description from current sources",
      "cvss_score": 0.0-10.0,
      "publish_date": "YYYY-MM-DD",
      "data_source": "live_search"
    }}],
    "confidence": 0.0-1.0
  }}
}}

If NO vulnerabilities found across all packages, return empty JSON object: {{}}

Priority: Use current, live vulnerability data. Mark confidence appropriately based on data freshness and source reliability.

CRITICAL: Respond ONLY with valid JSON. Do not include any explanatory text, markdown formatting, or comments outside the JSON structure."""
        
        return prompt
    
    def _format_package_list(self, packages: List[Package]) -> str:
        """Format package list for optimal token usage."""
        if self.strategy == "compact":
            return self._format_compact_list(packages)
        elif self.strategy == "detailed":
            return self._format_detailed_list(packages)
        else:
            return self._format_balanced_list(packages)
    
    def _format_compact_list(self, packages: List[Package]) -> str:
        """Ultra-compact format for maximum token efficiency."""
        return ', '.join(f"{pkg.name}:{pkg.version}" for pkg in packages)
    
    def _format_detailed_list(self, packages: List[Package]) -> str:
        """Detailed format with full context for maximum accuracy."""
        lines = []
        for pkg in packages:
            ecosystem_info = f" ({pkg.ecosystem})" if pkg.ecosystem else ""
            source_info = ""
            if pkg.source_locations:
                files = [loc.file_path for loc in pkg.source_locations[:2]]  # First 2 files
                source_info = f" [found in: {', '.join(files)}]"
            
            lines.append(f"- {pkg.name}:{pkg.version}{ecosystem_info}{source_info}")
        
        return '\n'.join(lines)
    
    def _format_balanced_list(self, packages: List[Package]) -> str:
        """Balanced format optimizing for both accuracy and efficiency."""
        lines = []
        for pkg in packages:
            # Include ecosystem for context, skip detailed source info
            ecosystem_info = f" ({pkg.ecosystem})" if pkg.ecosystem else ""
            lines.append(f"- {pkg.name}:{pkg.version}{ecosystem_info}")
        
        return '\n'.join(lines)
    
    def optimize_response_parsing(self, raw_response: str) -> Dict[str, Any]:
        """
        Optimize response parsing with intelligent JSON extraction.
        Handles various AI response formats gracefully.
        """
        # Try multiple JSON extraction strategies
        strategies = [
            self._extract_complete_json,
            self._extract_json_blocks,
            self._extract_partial_json,
            self._parse_structured_text
        ]
        
        for strategy in strategies:
            try:
                result = strategy(raw_response)
                if result and self._validate_response_structure(result):
                    return result
            except Exception:
                continue
        
        # Fallback: return raw response with error flag
        return {
            "parsing_failed": True,
            "parsing_error": True,
            "raw_response": raw_response,
            "error_message": "Failed to parse AI response into structured format"
        }
    
    def _extract_complete_json(self, response: str) -> Dict[str, Any]:
        """Extract complete JSON object from response."""
        # Find the first complete JSON object
        start_idx = response.find('{')
        if start_idx == -1:
            raise ValueError("No JSON object found")
        
        brace_count = 0
        end_idx = start_idx
        
        for i, char in enumerate(response[start_idx:], start_idx):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break
        
        if brace_count != 0:
            raise ValueError("Incomplete JSON object")
        
        json_str = response[start_idx:end_idx]
        return json.loads(json_str)
    
    def _extract_json_blocks(self, response: str) -> Dict[str, Any]:
        """Extract JSON from code blocks or formatted sections."""
        # Look for JSON in code blocks
        patterns = [
            '```json\n',
            '```\n{',
            'json\n{',
            '{\n'
        ]
        
        for pattern in patterns:
            start_idx = response.find(pattern)
            if start_idx != -1:
                start_idx += len(pattern) if not pattern.endswith('{') else len(pattern) - 1
                end_idx = response.find('```', start_idx)
                if end_idx == -1:
                    end_idx = response.rfind('}') + 1
                
                json_str = response[start_idx:end_idx].strip()
                if json_str.endswith('```'):
                    json_str = json_str[:-3].strip()
                
                return json.loads(json_str)
        
        raise ValueError("No JSON blocks found")
    
    def _extract_partial_json(self, response: str) -> Dict[str, Any]:
        """Extract partial JSON and attempt to complete it."""
        # Find JSON-like structures and try to parse them
        lines = response.split('\n')
        json_lines = []
        in_json = False
        
        for line in lines:
            line = line.strip()
            if line.startswith('{') or line.startswith('"'):
                in_json = True
            
            if in_json:
                json_lines.append(line)
                if line.endswith('}') and not line.endswith('"},'):
                    break
        
        if json_lines:
            json_str = '\n'.join(json_lines)
            # Try to fix common JSON issues
            json_str = self._fix_common_json_issues(json_str)
            return json.loads(json_str)
        
        raise ValueError("No partial JSON found")
    
    def _parse_structured_text(self, response: str) -> Dict[str, Any]:
        """Parse structured text response when JSON parsing fails."""
        # This would implement text parsing logic to extract
        # vulnerability information from natural language responses
        
        # For now, return a structured error response
        return {
            "text_parsing_attempted": True,
            "parsing_error": True,
            "raw_response": response,
            "message": "Structured text parsing not yet implemented"
        }
    
    def _fix_common_json_issues(self, json_str: str) -> str:
        """Fix common JSON formatting issues in AI responses."""
        # Remove trailing commas
        json_str = json_str.replace(',}', '}')
        json_str = json_str.replace(',]', ']')
        
        # Fix unquoted keys (simple regex replacement)
        import re
        json_str = re.sub(r'(\w+):', r'"\1":', json_str)
        
        # Fix single quotes to double quotes
        json_str = json_str.replace("'", '"')
        
        return json_str
    
    def _validate_response_structure(self, response: Dict[str, Any]) -> bool:
        """Validate that response has expected structure for AI agent consumption."""
        if not isinstance(response, dict):
            return False
        
        # Check for error indicators
        if response.get("parsing_error") or response.get("error"):
            return False
        
        # For vulnerability responses, expect package data
        if not any(key for key in response.keys() if ':' in key or key == "raw_response"):
            return False
        
        return True
    
    def calculate_token_estimate(self, packages: List[Package]) -> Dict[str, int]:
        """
        Estimate token usage for given packages.
        Helps with cost prediction and batch optimization.
        """
        # Create sample prompt to estimate tokens
        sample_prompt = self.create_prompt(packages[:5])  # Sample with 5 packages
        
        # Rough token estimation (1 token ≈ 4 characters)
        prompt_tokens = len(sample_prompt) // 4
        
        # Scale to full package list
        scaling_factor = len(packages) / 5
        estimated_input_tokens = int(prompt_tokens * scaling_factor)
        
        # Estimate output tokens based on expected response
        # Assume 20-30 tokens per package for vulnerability data
        estimated_output_tokens = len(packages) * 25
        
        return {
            "input_tokens": estimated_input_tokens,
            "output_tokens": estimated_output_tokens,
            "total_tokens": estimated_input_tokens + estimated_output_tokens
        }
    
    def optimize_batch_size(self, total_packages: int, max_context_tokens: int = 100000) -> int:
        """
        Calculate optimal batch size for context window utilization.
        Balances efficiency with context window limits.
        """
        # Estimate tokens per package (input + output)
        tokens_per_package = 30  # Conservative estimate
        
        # Reserve tokens for prompt structure and response formatting
        reserved_tokens = 1000
        
        # Calculate maximum packages per batch
        available_tokens = max_context_tokens - reserved_tokens
        max_packages_per_batch = available_tokens // tokens_per_package
        
        # Use configured batch size as upper limit
        optimal_batch_size = min(
            max_packages_per_batch,
            self.config.batch_size,
            total_packages
        )
        
        return max(1, optimal_batch_size)
    
    def get_optimization_metrics(self) -> Dict[str, Any]:
        """
        Get current optimization metrics for AI agent analysis.
        Enables autonomous optimization decisions.
        """
        return {
            "strategy": self.strategy,
            "batch_size": self.config.batch_size,
            "optimization_opportunities": [
                "Consider larger batch sizes for better context utilization",
                "Enable live search for current vulnerability data",
                "Use balanced format for optimal accuracy/efficiency trade-off"
            ],
            "performance_indicators": {
                "token_efficiency": "optimal",
                "accuracy_preservation": "high",
                "context_utilization": "balanced"
            }
        }