# Product Design Requirements (PDR): AI-Powered SCA Vulnerability Analysis

---

## 📋 Overview

This Product Design Requirements (PDR) document outlines the design and implementation of an AI-powered SCA vulnerability scanner, designed with an **AI Agent First** philosophy where everything is optimized for autonomous AI agent operation. The solution enables bulk dependency analysis with balanced token efficiency, prioritizing data accuracy and usefulness while maintaining reasonable cost efficiency.

### **Proposed Solution**
AI-powered bulk vulnerability analysis designed for AI Agent First operation, with balanced token efficiency, intelligent batching, and hybrid validation for accurate, fast, and cost-effective dependency scanning.

### **Core Hypothesis: AI Agent Centric Architecture**

#### **Fundamental Shift: Context Windows vs Sequential Processing**
Traditional SCA scanning is constrained by **sequential API limitations** - analyzing one package at a time through multiple database calls. Each package requires separate requests, creating linear scaling bottlenecks.

Our core hypothesis: **Context windows are the true performance limit, not individual CVE lookups.** Modern AI models can process hundreds of packages simultaneously within a single context window, transforming vulnerability analysis from sequential operations to massive parallel processing at near-zero marginal cost increase.

#### **Context Window Performance Breakthrough**
- **Massive Parallelization**: 75+ packages analyzed in one API call vs 75+ individual database requests
- **Marginal Cost Scaling**: Adding more packages to context window costs ~5-10 additional tokens vs full API request overhead
- **Context Window Utilization**: Modern models handle 128K+ tokens - we can fit hundreds of packages in single requests
- **Zero Rate Limiting**: No sequential wait times between package analyses

#### **Cost Efficiency Through Context Window Optimization**
```
Traditional Model (Sequential):
1000 packages × 3 API calls each = 3000 individual requests
+ 6-second rate limits × 3000 = 5+ hours processing time
+ Linear cost scaling per package

AI Model (Context Window):
1000 packages ÷ 75 per context window = 13 total API calls
+ Processing time: <30 minutes (limited by AI inference, not rate limits)
+ Marginal cost per additional package: ~5-10 tokens vs full API overhead
```

**Key Insight**: Context windows enable massive parallelization at negligible marginal cost increase. The bottleneck shifts from API rate limits to AI inference speed, delivering 10x+ performance improvements.

#### **AI Agent First Consumer Model**
Traditional tools optimize for human consumption (dashboards, reports, UIs). We optimize for **AI agent consumption**:
- **Structured Data**: Machine-readable output formats
- **Actionable Intelligence**: Data that enables autonomous decision-making  
- **Composable Workflows**: Output designed for downstream AI agent processing
- **Precise Location Mapping**: File/line-level data for automated remediation

#### **Addressing Stale Data Risk: Live Web Search Integration**
A critical risk with AI model knowledge is **temporal staleness** - vulnerability databases update daily with new CVEs, but AI training data has cutoff dates. This conflicts with our quality and up-to-date data goals.

**Solution: AI Models with Live Web Search Capabilities**
- **OpenAI with Search**: Live web access for current vulnerability data
- **Anthropic Claude with Tools**: Web search tools for real-time CVE lookup
- **Google Gemini**: Live search integration for current vulnerability information

**Hybrid Approach for Data Freshness**:
1. **AI Knowledge Base**: Use model's training data for well-known, established vulnerabilities
2. **Live Web Search**: Query current vulnerability databases for recent CVEs (last 30-90 days)
3. **Traditional API Fallback**: Critical findings verification against authoritative sources

**Implementation Strategy**:
```python
async def get_vulnerabilities_with_live_data(packages: List[Package]):
    # Use AI knowledge for established vulnerabilities
    ai_results = await ai_client.bulk_analyze(packages)
    
    # Live web search for recent vulnerabilities
    recent_packages = filter_packages_needing_fresh_data(packages)
    live_results = await ai_client.search_current_vulnerabilities(recent_packages)
    
    # Merge results with recency priority
    return merge_vulnerability_data(ai_results, live_results)
```

**Cost-Benefit Analysis**:
- **Additional Cost**: ~20% increase for live search queries on recent packages
- **Quality Gain**: Current vulnerability data, no missed recent CVEs
- **Performance Impact**: Minimal - live search only for subset requiring fresh data

#### **Validation Through Hybrid Intelligence**
We maintain accuracy through **selective validation** - using traditional APIs only for critical findings verification, achieving the best of both approaches while minimizing traditional API dependency.

### **Core Design Tenets**
1. **AI Agent First**: AI agents are the primary consumers. Everything optimized for autonomous AI agent operation by default. Humans interface only via CLI.
2. **AI Agent Intelligence Pipeline**: Enable complete vulnerability intelligence workflow from input → scanning → analysis → actionable data output for specialized remediation agents
3. **Balanced Token Efficiency**: Optimize tokens while prioritizing data accuracy and usefulness for AI agent decision-making
4. **Security by Default**: Scan everything, assume nothing, exclude only by explicit approval
5. **Autonomous Operation**: AI agents self-diagnose, optimize, and produce high-quality actionable intelligence for downstream remediation agents

---

## 🎯 Objectives

### **Goals**
1. **Vulnerability Detection**: Identify all vulnerable dependencies with 95%+ accuracy
2. **Performance**: Reduce scan time from 3+ hours to <30 minutes for 1000+ dependencies  
3. **Cost Efficiency**: Achieve <$0.50 per 1000 packages analyzed
4. **Clear Data Output**: Produce structured, factual vulnerability data optimized for AI agent consumption
5. **Source Mapping**: Provide precise file/line location tracking for each vulnerable dependency

### **Non-Goals** 
1. **Risk Assessment Reasoning**: Analyzing business impact or providing strategic recommendations
2. **Remediation Planning**: Determining fix priorities or implementation strategies  
3. **Code Modifications**: Making any changes to source code, dependencies, or configurations
4. **Decision Making**: Choosing which vulnerabilities to fix or when to fix them
5. **Workflow Orchestration**: Managing multi-step remediation processes or testing

**Design Principle**: This scanner is a pure detection and data extraction tool. All analysis, reasoning, and implementation should be handled by specialized downstream AI agents.

### **Success Metrics**
- **Speed**: 10x faster than current implementation
- **Cost**: 5x more economical than traditional API aggregation  
- **Accuracy**: Match or exceed current CVE detection rates
- **Data Quality**: Structured output enables 90%+ automated processing by other AI agents

---

## 🏗️ Technical Architecture

### **Core Components**

#### **1. AI Vulnerability Client (Using Critique Library)**
```python
from critique import Critique

class AIVulnerabilityClient:
    def __init__(self, model: str, config: Dict, enable_live_search: bool = False):
        self.critique = Critique()
        self.model = model
        self.config = config
        self.enable_live_search = enable_live_search
        self.token_optimizer = TokenOptimizer()
        
        # Determine if model supports live search
        self.supports_live_search = self._check_live_search_support()
        
        # Configure API keys and provider settings
        self._configure_providers(config)
    
    def _check_live_search_support(self) -> bool:
        """Check if current model supports live web search"""
        live_search_models = [
            "gpt-4o-with-search", "gpt-4o-mini-with-search",
            "claude-3.5-sonnet-tools", "claude-3.5-haiku-tools", 
            "gemini-2.5-pro-search", "gemini-2.0-flash-search",
            "grok-3-web", "grok-3-mini-web"
        ]
        return any(live_model in self.model for live_model in live_search_models)
    
    def _configure_providers(self, config: Dict):
        """Configure API keys from environment variables only (never from config)"""
        import os
        # Security: API keys ONLY from environment variables
        if os.getenv('OPENAI_API_KEY'):
            self.critique.configure_openai(api_key=os.getenv('OPENAI_API_KEY'))
        if os.getenv('ANTHROPIC_API_KEY'):
            self.critique.configure_anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        if os.getenv('GOOGLE_AI_API_KEY'):
            self.critique.configure_google(api_key=os.getenv('GOOGLE_AI_API_KEY'))
        if os.getenv('XAI_API_KEY'):
            self.critique.configure_xai(api_key=os.getenv('XAI_API_KEY'))
    
    async def bulk_analyze(self, packages: List[Package]) -> VulnerabilityResults:
        """Analyze packages with optional live search for current CVE data"""
        if self.enable_live_search and self.supports_live_search:
            return await self._analyze_with_live_search(packages)
        else:
            return await self._analyze_knowledge_only(packages)
    
    async def _analyze_with_live_search(self, packages: List[Package]) -> VulnerabilityResults:
        """Analyze with live web search for current vulnerability data"""
        optimized_prompt = self.token_optimizer.create_prompt_with_live_search(packages)
        
        response = await self.critique.generate(
            model=self.model,
            prompt=optimized_prompt,
            temperature=0.1,
            max_tokens=2048,
            tools=["web_search", "cve_lookup"] if "tools" in self.model else None
        )
        
        return self._parse_response(response)
    
    async def _analyze_knowledge_only(self, packages: List[Package]) -> VulnerabilityResults:
        """Analyze using model's training knowledge only"""
        optimized_prompt = self.token_optimizer.create_prompt(packages)
        
        response = await self.critique.generate(
            model=self.model,
            prompt=optimized_prompt,
            temperature=0.1,
            max_tokens=2048
        )
        
        return self._parse_response(response)
```

#### **2. Token Optimization Engine**
```python
class TokenOptimizer:
    def create_prompt(self, packages: List[Package]) -> str:
        """Generate vulnerability analysis prompt for knowledge-only models"""
        package_list = ','.join(f'{p.name}:{p.version}' for p in packages)
        return f"""Analyze these packages for known vulnerabilities from your training data:
{package_list}

Return JSON: {{pkg: {{cves: [{{id, severity, description}}], confidence: 0.0-1.0}}}}"""
    
    def create_prompt_with_live_search(self, packages: List[Package]) -> str:
        """Generate prompt for models with live search capabilities"""
        package_list = ','.join(f'{p.name}:{p.version}' for p in packages)
        return f"""Search current vulnerability databases for these packages:
{package_list}

Use web search to find:
1. Recent CVEs and security vulnerabilities
2. Current security advisories and patches  
3. Latest vulnerability disclosures

Return JSON with current data: {{pkg: {{cves: [{{id, severity, description, publish_date}}], data_source: "live_search", confidence: 0.0-1.0}}}}"""
    
    def compress_response(self, ai_response: str) -> CompactResults:
        """Parse and validate AI response with minimal tokens"""
        pass
```

#### **3. Hybrid Validation Pipeline**
```python
class ValidationPipeline:
    def validate_findings(self, ai_results: AIResults) -> ValidatedResults:
        """Cross-check critical findings against CVE databases"""
        critical_findings = [r for r in ai_results if r.severity in ['CRITICAL', 'HIGH']]
        return self.cross_validate_with_nvd(critical_findings)
```

### **Data Flow Architecture**
```
Dependencies → Security-First Filtering → AI Batching → Bulk Analysis → Validation → Enhanced Reporting
     ↓              ↓                      ↓            ↓            ↓            ↓
   1000+ pkgs   →  950+ pkgs    →  13 batches  →  AI Results → Validate  →  Final Report
```

---

## 🎯 Scope & Boundaries

### **In Scope: Vulnerability Analysis & Detection**
- **Dependency Discovery**: Parse and identify all dependencies across multiple languages
- **Vulnerability Detection**: AI-powered bulk analysis of security vulnerabilities  
- **Risk Assessment**: Contextual analysis of business impact and exploitability
- **Actionable Intelligence**: Structured vulnerability data optimized for AI agent consumption
- **Source Location Tracking**: Precise file/line mapping for each vulnerable dependency
- **Multi-Provider Support**: Flexible AI model selection across providers

### **Out of Scope: Remediation Implementation**
The following capabilities are **explicitly out of scope** and should be handled by specialized remediation AI agents:

- **Dependency Updates**: Automatically updating package versions in files
- **Code Modifications**: Making actual changes to source code or configuration files  
- **Build System Changes**: Modifying CI/CD pipelines or build configurations
- **Testing Execution**: Running tests to validate fixes
- **Git Operations**: Creating commits, branches, or pull requests
- **Environment Management**: Installing packages or managing virtual environments

**Design Principle**: This scanner produces comprehensive, actionable vulnerability intelligence that empowers other AI agents to implement fixes safely and effectively.

---

## 💡 Feature Specifications

### **AI-Powered Vulnerability Analysis**

#### **Security-First Filtering**
- **Default Behavior**: Scan all packages (zero exclusions for maximum security)
- **Cache Optimization**: Skip only recently analyzed packages (6-hour TTL maximum)
- **User-Controlled Exclusions**: Optional config file for explicitly approved safe packages
- **Audit Trail**: Complete record of filtering decisions with security justification
- **No Assumptions**: Never filter based on package age, source, or perceived safety

#### **Intelligent Batching**
- **Batch Size**: 75 packages per API call (balanced efficiency with context preservation)
- **Smart Grouping**: Group by ecosystem and risk profile  
- **Parallel Processing**: Multiple batches processed concurrently
- **Rate Limiting**: Respect AI provider rate limits

#### **Balanced Token Efficiency**
```
Balanced Input Format (AI Agent Optimized):
"Analyze these packages for vulnerabilities:
requests==2.25.1, django==3.2.1, numpy==1.20.0

Return JSON with complete security context:
{package: {cves: [{id, severity, description}], risk_score, remediation, confidence}}"

Estimated Token Usage:
- Base prompt: 45 tokens (includes context for accuracy)
- Per package: 4-6 tokens (full version info)
- Response: 15-30 tokens per package (detailed security context)
- Total cost: ~$0.0008-0.0012 per package
- **Principle**: Data Accuracy & Usefulness > Token Cost Savings
```

#### **AI Agent Optimized Response Schema**
```json
{
  "requests:2.25.1": {
    "cves": [{
      "id": "CVE-2023-32681",
      "severity": "HIGH",
      "description": "Certificate verification bypass in requests",
      "cvss_score": 8.5
    }],
    "risk_assessment": {
      "score": 8.5,
      "business_impact": "Data exposure risk",
      "exploitability": "Remote exploitation possible"
    },
    "remediation": {
      "action": "upgrade",
      "target_version": ">=2.31.0",
      "urgency": "high",
      "estimated_effort": "low"
    },
    "confidence": 0.95
  },
  "django:3.2.1": {
    "cves": [],
    "risk_assessment": {
      "score": 2.0,
      "status": "secure"
    },
    "remediation": {
      "action": "none",
      "recommendation": "Monitor for updates"
    },
    "confidence": 0.99
  }
}
```

### **Hybrid Validation System**

#### **Validation Rules**
1. **CRITICAL/HIGH Findings**: Always validate against NVD/OSV databases
2. **Medium Findings**: Spot-check 20% against traditional databases
3. **Low/No Issues**: Accept AI assessment with confidence >0.9
4. **Confidence <0.8**: Report low confidence with explicit error details

#### **Confidence Scoring**
- **High Confidence (0.9+)**: AI provides specific CVE IDs that exist in databases
- **Medium Confidence (0.7-0.9)**: AI identifies vulnerability patterns without specific CVEs
- **Low Confidence (<0.7)**: Contradictory information or vague responses

### **Enhanced Reporting**

#### **AI Agent Consumable Output Format**
```json
{
  "ai_agent_metadata": {
    "workflow_stage": "remediation_ready",
    "confidence_level": "high",
    "autonomous_action_recommended": true
  },
  "vulnerability_analysis": {
    "requests==2.25.1": {
      "source_locations": [
        {
          "file_path": "./requirements.txt",
          "line_number": 15,
          "declaration": "requests==2.25.1",
          "file_type": "requirements"
        },
        {
          "file_path": "./backend/pyproject.toml", 
          "line_number": 23,
          "declaration": "requests = \"^2.25.1\"",
          "file_type": "pyproject_toml"
        }
      ],
      "cves": [{
        "id": "CVE-2023-32681",
        "severity": "HIGH", 
        "business_impact": "Customer data exposure risk",
        "exploitability": "Remote code execution possible",
        "ai_agent_urgency": "immediate"
      }],
      "remediation_intelligence": {
        "recommended_action": "dependency_upgrade",
        "target_version": ">=2.31.0",
        "fix_complexity": "low",
        "affected_files": [
          "./requirements.txt:15",
          "./backend/pyproject.toml:23"
        ],
        "upgrade_path": {
          "current": "2.25.1",
          "safe_minimum": "2.31.0",
          "latest_stable": "2.32.3"
        }
      }
    }
  },
  "vulnerability_summary": {
    "total_packages_analyzed": 950,
    "vulnerable_packages": 23,
    "severity_breakdown": {
      "critical": 3,
      "high": 8, 
      "medium": 10,
      "low": 2
    },
    "recommended_next_steps": [
      "Forward vulnerability data to remediation AI agent",
      "Prioritize critical and high severity fixes first",
      "Re-scan after remediation to verify fixes"
    ]
  }
}
```

### **AI Model Configuration**

#### **AI Configuration File Format**
```yaml
# ~/.sca_ai_config.yml - AI model and API configuration
# Single model configuration with explicit error handling

# Note: API keys are NEVER stored in config files for security
# All API keys must be provided via environment variables only

# Model selection (single model, no fallbacks)
model: "gpt-4o-mini-with-search"        # Selected model for all analysis

# Provider-specific settings
providers:
  openai:
    organization: "org-xxxxxxxxxxxxx"   # Optional organization ID
    base_url: "https://api.openai.com/v1"  # Custom endpoint if needed
    
  anthropic:
    version: "2023-06-01"               # API version
    
  google:
    project_id: "your-project-id"       # Google Cloud project
    
  xai:
    base_url: "https://api.x.ai/v1"     # X AI endpoint

# Analysis settings
analysis:
  batch_size: 75                        # Packages per AI call
  confidence_threshold: 0.8             # Minimum confidence for results
  max_retries: 3                        # Retry failed requests
  timeout_seconds: 30                   # Request timeout
  
# Cost management
budget:
  daily_limit: 50.00                    # USD daily spending limit
  monthly_limit: 1000.00                # USD monthly spending limit
  alert_threshold: 0.8                  # Alert at 80% of budget
  
# Model-specific optimization
optimization:
  gpt-4o-mini:
    temperature: 0.1                    # Low temperature for consistent results
    max_tokens: 2048                    # Response length limit
    
  claude-3.5-haiku:
    temperature: 0.0                    # Deterministic responses
    max_tokens: 4096
    
  gemini-2.0-flash:
    temperature: 0.1
    top_p: 0.9
```

#### **Environment Variables (Required for Security)**

**Security Principle**: API keys are ONLY provided via environment variables. No CLI flags or config file storage of secrets to prevent exposure in command history, process lists, or log files.

```bash
# API Keys (Required - never passed via CLI)
export OPENAI_API_KEY="sk-..."              # For gpt-4o models (with or without search)
export ANTHROPIC_API_KEY="sk-ant-..."       # For claude models (with or without tools)
export GOOGLE_AI_API_KEY="AIza..."          # For gemini models (with or without search)
export XAI_API_KEY="xai-..."                # For grok models (with or without web access)

# Model defaults (live search enabled by default)
export SCA_DEFAULT_MODEL="gpt-4o-mini-with-search"
```

**Security Requirements**:
- ✅ API keys via environment variables only
- ✅ No API keys in CLI arguments or config files
- ✅ No API keys in logs, telemetry, or output files
- ✅ Automatic redaction of secrets in error messages
- ✅ Process isolation prevents key exposure in process lists

### **Security-First Exclusion Configuration**

#### **Exclusion Config File Format**
```yaml
# ~/.sca_exclusions.yml - User-controlled security exclusions
# Default: Empty (scan everything for maximum security)

safe_packages:
  - "internal-build-tool"     # Security team approved 2024-07-15
  - "company-test-utils"      # Internal testing utility, approved by CISO

# Required: Security team approval documentation
exclusion_metadata:
  internal-build-tool:
    approved_by: "security-team@company.com"
    approval_date: "2024-07-15"
    review_date: "2024-10-15"
    reason: "Internal build utility, source code audited"
    
  company-test-utils:
    approved_by: "security-team@company.com" 
    approval_date: "2024-07-10"
    review_date: "2024-10-10"
    reason: "Test-only package, not in production"

# Security policy
policy:
  max_exclusions: 50          # Limit number of exclusions
  require_approval: true      # All exclusions need security approval
  review_interval_days: 90    # Regular review cycle
```

#### **Exclusion Validation Rules**
- **Approval Required**: All exclusions must have security team approval
- **Review Cycle**: Maximum 90-day review intervals
- **Audit Trail**: Complete logging of exclusion decisions
- **Principle**: Security by default, exclusions by exception

---

## 🛡️ Risk Management

### **Technical Risks**

#### **AI Hallucination**
- **Risk**: AI generates non-existent CVE IDs
- **Mitigation**: Validate all CRITICAL/HIGH findings against authoritative databases
- **Error Handling**: Explicit validation failure messages with specific next steps

#### **Cost Overrun**
- **Risk**: Unexpected token usage spikes
- **Mitigation**: Implement usage monitoring and rate limiting
- **Safeguards**: Daily spending caps and alert thresholds

#### **Accuracy Degradation**
- **Risk**: AI misses real vulnerabilities
- **Mitigation**: Continuous validation against known vulnerable packages
- **Quality Assurance**: Regular accuracy benchmarking

### **Operational Risks**

#### **API Dependency**
- **Risk**: AI service outages
- **Error Handling**: Clear failure messages with specific provider/API key issues
- **Monitoring**: Health checks with explicit error reporting

#### **Token Cost Management**
- **Risk**: Runaway costs from inefficient usage
- **Mitigation**: Token usage budgets and optimization monitoring
- **Controls**: Pre-scan cost estimation and approval workflows

### **Explicit Error Handling (No Fallbacks)**

**Design Principle**: Fail fast with clear, actionable error messages rather than hiding problems with fallback mechanisms.

#### **Common Failure Scenarios**
```bash
# API Key Missing
❌ Error: OPENAI_API_KEY not found in environment
   → Set your API key: export OPENAI_API_KEY="sk-..."
   → Or use different provider: --model claude-3.5-haiku-tools

# Model Not Supported
❌ Error: Model 'gpt-4o-mini' does not support live search
   → Use: --model gpt-4o-mini-with-search
   → Or disable live search: --knowledge-only

# Rate Limit Exceeded
❌ Error: OpenAI rate limit exceeded (requests: 3000/min)
   → Wait 60 seconds and retry
   → Or reduce batch size: --batch-size 25
   → Current usage: 2847/3000 requests this minute

# Invalid API Key
❌ Error: OpenAI API key invalid (HTTP 401)
   → Check API key format: sk-...
   → Verify key has not expired
   → Test key: curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models

# Budget Exceeded
❌ Error: Daily budget limit reached ($50.00)
   → Current spend: $52.30
   → Increase budget: --budget 100.00
   → Or continue tomorrow
```

#### **Error Message Structure**
- **Problem**: Clear description of what failed
- **Root Cause**: Specific technical reason  
- **Action Items**: Exact commands to resolve the issue
- **Context**: Current state/usage information when relevant

---

## 📊 Cost Analysis

### **Traditional vs AI-Powered Scanning**

| Metric | Traditional | AI-Powered | Improvement |
|--------|-------------|------------|-------------|
| **Time per 1000 packages** | 180 minutes | 20 minutes | 9x faster |
| **API calls required** | 3000+ calls | 14 calls | 200x fewer |
| **Rate limit delays** | 18,000 seconds | 0 seconds | Eliminated |
| **Cost per 1000 packages** | $2.50 (API costs) | $0.75 (AI tokens) | 3.3x cheaper |
| **Infrastructure complexity** | High | Medium | Simplified |
| **Security coverage** | 100% | 100% | No compromise |

### **Token Economics**
```
Per Package Breakdown (AI Agent First with Balanced Efficiency):
- Input tokens: 5 tokens average (includes security context)
- Output tokens: 25 tokens average (vulnerable packages with detailed context)
- Output tokens: 8 tokens average (clean packages with confidence data)
- Cost per package: $0.0010 (comprehensive analysis, 95% packages scanned)
- **Design Principle**: Never sacrifice security accuracy for token savings

Monthly Costs (10,000 packages):
- AI Analysis: $70/month (analyzing 95% vs 50% of packages)
- Validation Calls: $15/month
- Total: $85/month vs $250/month traditional
- Security: 100% coverage with zero assumptions
```

---

## 🔧 Technical Requirements

### **Infrastructure**

#### **AI Provider Integration**
Multiple AI providers supported via unified interface, allowing users to choose based on cost, performance, and preference:

**OpenAI Models:**
- **With Live Search**: `gpt-4o-with-search`, `gpt-4o-mini-with-search` (current CVE data)
- **Knowledge Only**: `gpt-4o`, `gpt-4o-mini`, `o1`, `o1-mini` (training data cutoff)
- **Legacy**: `gpt-4`, `gpt-3.5-turbo` (knowledge only)

**Anthropic Models:**
- **With Tool Use**: `claude-3.5-sonnet-tools`, `claude-3.5-haiku-tools` (live CVE lookup)
- **Knowledge Only**: `claude-3.5-sonnet`, `claude-3.5-haiku`, `claude-3-opus`

**Google Models:**
- **With Live Search**: `gemini-2.5-pro-search`, `gemini-2.0-flash-search`
- **Knowledge Only**: `gemini-2.5-pro`, `gemini-2.0-flash`, `gemini-pro`


**X AI Models:**
- **With Web Access**: `grok-3-web`, `grok-3-mini-web` (current vulnerability data)
- **Knowledge Only**: `grok-3`, `grok-3-mini`, `grok-beta`

#### **Model Selection Guide**

| Model | Cost | Speed | Accuracy | Live Data | Best For |
|-------|------|-------|----------|-----------|----------|
| `gpt-4o-mini-with-search` | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | **Recommended for current CVEs** |
| `claude-3.5-haiku-tools` | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ | Fast with live CVE lookup |
| `gemini-2.0-flash-search` | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ | Ultra-fast with live search |
| `claude-3.5-sonnet-tools` | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | High accuracy with current data |
| `grok-3-mini-web` | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ | Alternative with web access |
| `gpt-4o-mini` | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ | Cost-effective, knowledge only |
| `claude-3.5-haiku` | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ | High-speed, knowledge only |

**Recommendations:**
- **Current Vulnerability Detection**: `gpt-4o-mini-with-search` (default)
- **High-Speed Live Scanning**: `claude-3.5-haiku-tools` or `gemini-2.0-flash-search`
- **Enterprise/Critical with Live Data**: `claude-3.5-sonnet-tools`
- **Cost-Optimized (older CVEs acceptable)**: `gpt-4o-mini` or `claude-3.5-haiku`
- **Development/Testing**: Knowledge-only models sufficient

#### **Enhanced Caching**
- **AI Results Cache**: 12-hour TTL (shorter due to potential variance)
- **Validated Results Cache**: 24-hour TTL (longer for cross-confirmed findings)
- **Batch Results Cache**: Store complete batch analysis for reuse

#### **AI Agent First Telemetry & Observability**

**Design Principle**: Telemetry optimized for AI agent consumption and autonomous optimization

```python
class TelemetryEngine:
    """AI Agent First telemetry with structured, machine-readable output"""
    
    def log_scan_event(self, event_type: str, data: Dict, context: Dict):
        """Structured logging optimized for AI agent analysis"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "session_id": self.session_id,
            "data": data,
            "context": context,
            "ai_agent_metadata": {
                "optimization_opportunities": self._detect_optimization_opportunities(data),
                "performance_indicators": self._extract_performance_indicators(data),
                "error_patterns": self._identify_error_patterns(data)
            }
        }
        self._write_structured_log(log_entry)
```

**Core Telemetry Categories**:

1. **Performance & Optimization Detection**
   - Token efficiency metrics with optimization suggestions
   - Batch size performance analysis with AI-guided recommendations
   - Model performance comparison data for autonomous model selection
   - Cache hit/miss patterns with predictive optimization hints

2. **Cost & Efficiency Tracking**
   - Real-time cost tracking with predictive budget warnings
   - Token usage patterns with efficiency improvement suggestions
   - ROI analysis comparing AI vs traditional scanning methods
   - Provider cost comparison data for autonomous provider switching

3. **Quality & Accuracy Monitoring**
   - Confidence score distributions with quality trend analysis
   - Validation success rates with accuracy improvement recommendations
   - False positive/negative detection with pattern recognition
   - AI model accuracy benchmarking with autonomous model tuning

4. **Error Classification & Diagnostics**
   - Structured error taxonomy for AI agent troubleshooting
   - Root cause analysis data with automated resolution suggestions
   - Retry pattern analysis with optimal retry strategy recommendations
   - Provider-specific error patterns with failover optimization

**AI Agent Autonomous Optimization Features**:
- **Predictive Alerts**: Warn before hitting rate limits, budget thresholds, or quality degradation
- **Autonomous Reporting**: Generate actionable insights for both AI agents and human operators

### **CLI Integration**

#### **New Command Line Options**
```bash
# AI Agent First Operation (Default Behavior)
--model MODEL_NAME           # AI model for analysis (default: gpt-4o-mini-with-search)
--knowledge-only             # Disable live search, use training data only (opt-out from default)
--provider openai|anthropic|google|xai  # AI provider (auto-detected from model)
--config CONFIG_FILE         # YAML config with model preferences (API keys via environment only)

# AI Agent Optimization (Always Active)
--batch-size 75             # Batch size for AI analysis optimization
--budget 50.00              # Daily spending limit in USD
--telemetry-file FILE       # AI agent telemetry output (default: ./sca_telemetry.jsonl)
--telemetry-level info|debug|trace  # AI agent telemetry verbosity

# AI Agent Data Output Options
--vulnerability-data FILE  # Export structured vulnerability data for other AI agents

# Security and Validation (AI Agent Focused)
--exclusions CONFIG_FILE    # User-controlled exclusions (security team approved)
--force-fresh              # Ignore caches, full AI agent analysis
--audit-trail FILE         # Complete audit trail for AI agent review
--validate-critical        # Always validate CRITICAL/HIGH findings

# Legacy Options (for testing/comparison only)
--traditional-scan          # Use traditional database scanning for comparison testing
--hybrid-validation         # Use both AI and traditional validation for verification

# Note: API keys are provided via environment variables only for security
# No CLI flags for API keys to prevent exposure in command history or process lists
```

#### **Usage Examples (AI Agent First by Default)**
```bash
# Basic AI agent operation (live search enabled by default)
export OPENAI_API_KEY="sk-..."
sca_scanner_cli.py ~/code/project

# Knowledge-only model (opt-out from live search for cost savings)
sca_scanner_cli.py ~/code/project --model gpt-4o-mini --knowledge-only

# High-speed scanning with live CVE lookup (default behavior)
export ANTHROPIC_API_KEY="sk-ant-..."
sca_scanner_cli.py ~/code/project --model claude-3.5-haiku-tools

# Ultra-fast scanning with live search
export GOOGLE_AI_API_KEY="AIza..."
sca_scanner_cli.py ~/code/project --model gemini-2.0-flash-search

# Cost-optimized scanning (disable live search for development)
sca_scanner_cli.py ~/code/project --model claude-3.5-haiku --knowledge-only --budget 10.00

# Export structured vulnerability data with current CVE information (default)
sca_scanner_cli.py ~/code/project --vulnerability-data vulns.json

# AI agent with detailed telemetry for autonomous optimization
sca_scanner_cli.py ~/code/project --telemetry-level debug --telemetry-file detailed_analysis.jsonl

```

#### **AI Agent First Output (Default)**
```bash
🤖 AI Agent First SCA Scanner v3.0
   🎯 Model: gpt-4o-mini-with-search (OpenAI) - Live CVE data enabled by default
   🔍 Data Source: AI Knowledge + Live Web Search (current vulnerability databases)
   🔄 Agentic workflow: INPUT → SCAN → ANALYSIS → REMEDIATION
   💰 Cost: $0.82 for 950 packages analyzed (includes live search)
   📊 Data Freshness: Current as of scan time (live lookup enabled by default)

🔍 AI Agent Analysis Results:
   📦 Packages analyzed: 950/1000 (AI agent decision: 50 cached, secure)
   🚨 Vulnerabilities: 23 findings requiring AI agent remediation
   ⚡ Batch efficiency: 75 packages/call (AI agent optimized)
   ✅ Validation: 23 findings cross-verified for AI agent confidence

📊 AI Agent Telemetry (Always Active):
   📁 Structured logs: ./sca_telemetry.jsonl (machine-readable)
   🔧 Optimization opportunities: 3 detected for autonomous improvement
   📈 Performance trend: Improving (AI agent learning)
   🎯 Remediation data: Ready for AI agent implementation

🛠️ AI Agent Intelligence Output:
   📋 Vulnerability data: 23 packages with structured intelligence
   🤖 Remediation-ready: Data optimized for specialized remediation AI agents
   📊 Risk breakdown: Critical (3), High (8), Medium (10), Low (2)
   🔒 Source mapping: All vulnerabilities traced to exact file locations

# Comparison: Knowledge-Only Model Output
🤖 AI Agent First SCA Scanner v3.0 (Knowledge-Only Mode)
   🎯 Model: gpt-4o-mini (OpenAI) - Training data only
   📚 Data Source: AI Training Knowledge (cutoff: April 2024)
   💰 Cost: $0.68 for 950 packages analyzed (no live search)
   ⚠️  Data Freshness: Training cutoff date - may miss recent CVEs
   
   📋 Recommendation: Use live search models for production scanning
```

---

## 🧪 Testing Strategy

### **Unit Testing Framework**
```python
# Core testing structure with pytest
tests/
├── unit/
│   ├── test_dependency_parser.py      # Test all dependency file parsers
│   ├── test_vulnerability_clients.py  # Mock AI provider responses
│   ├── test_batch_optimizer.py        # Token optimization logic
│   └── test_output_formatter.py       # JSON schema validation
├── integration/
│   ├── test_ai_providers.py          # Real API integration tests
│   ├── test_end_to_end.py            # Full pipeline validation
│   └── test_performance.py           # Speed and cost benchmarks
└── fixtures/
    ├── sample_dependencies/           # Test dependency files
    ├── mock_vulnerabilities/          # Known CVE test data
    └── expected_outputs/              # Validated JSON schemas
```


### **Rapid Testing Setup**
```python
# tests/conftest.py - Fast test configuration
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_ai_client():
    """Mock AI client for fast unit tests"""
    client = Mock()
    client.analyze.return_value = {
        "requests==2.25.1": {
            "cves": [{"id": "CVE-2023-32681", "severity": "HIGH"}],
            "confidence": 0.95
        }
    }
    return client

@pytest.fixture
def sample_dependencies():
    """Sample dependency data for testing"""
    return [
        {"name": "requests", "version": "2.25.1", "file": "requirements.txt", "line": 15},
        {"name": "django", "version": "3.2.1", "file": "pyproject.toml", "line": 23}
    ]

# Fast test execution with mocked external calls
pytest.main([
    "tests/unit/",
    "-v",
    "--tb=short",
    "--cache-clear",
    "--maxfail=1"  # Fail fast for rapid feedback
])
```

### **Validation Testing**
1. **Known Vulnerable Packages**: Test against NIST NVD confirmed CVEs
2. **False Positive Detection**: Ensure AI doesn't hallucinate non-existent vulnerabilities  
3. **Schema Validation**: Verify JSON output matches expected structure
4. **Edge Cases**: Malformed package names, version conflicts, network failures

### **Performance Testing**
1. **Load Testing**: 1000+ package batches under various conditions
2. **Token Optimization**: Measure actual vs. estimated token usage
3. **Cost Tracking**: Real-world cost analysis across different AI providers
4. **Latency Benchmarking**: End-to-end timing for CLI execution

### **Test Coverage Requirements**
- **Unit Tests**: 90%+ code coverage for core logic
- **Integration Tests**: All AI providers and vulnerability databases  
- **Performance Tests**: Sub-30 minute execution for 1000+ packages
- **Local Development**: Fast test execution for rapid iteration cycles

---

## 📖 Documentation Strategy

### **Documentation Standards**
Provide comprehensive, AI agent-optimized documentation with clear examples and getting started guides that enable AI agents to understand and leverage the tool effectively within minutes. Human accessibility is secondary to AI agent comprehension.

### **Core Documentation Structure**

#### **README.md (Primary Entry Point)**
```markdown
# AI-Powered SCA Scanner

Fast, accurate vulnerability scanning powered by AI agents for multi-language codebases.

## ✨ Features

- 🚀 **10x Faster**: Scan 1000+ dependencies in <30 minutes vs 3+ hours
- 🤖 **AI-Powered**: Bulk vulnerability analysis using OpenAI, Anthropic, Google, X AI
- 🔍 **Multi-Language**: Python, JavaScript, Docker dependency detection
- 💰 **Cost Efficient**: $0.75 per 1000 packages vs $2.50 traditional methods
- 🎯 **AI Agent Ready**: Structured output optimized for downstream AI automation
- 🔒 **Security First**: Environment-only API keys, comprehensive audit trails

## 🚀 Quick Start

### Installation

pip install sca-ai-scanner

### Basic Usage

# Set your API key
export OPENAI_API_KEY="sk-..."

# Scan your project
sca-scanner /path/to/project

# Export structured data for AI agents
sca-scanner /path/to/project --vulnerability-data vulns.json

### Example Output

📦 Scanned 847 dependencies in 18 minutes
🚨 Found 23 vulnerabilities (3 critical, 8 high, 10 medium, 2 low)
💾 Exported structured data to vulns.json
```

#### **Installation Guide (docs/installation.md)**
```markdown
# Installation Guide

## Requirements
- Python 3.9+
- API key for at least one AI provider (OpenAI, Anthropic, Google, X AI)

## Installation Methods

### PyPI (Recommended)
pip install sca-ai-scanner

### From Source
git clone https://github.com/your-org/sca-ai-scanner
cd sca-ai-scanner
pip install -e .

### Development Setup
git clone https://github.com/your-org/sca-ai-scanner
cd sca-ai-scanner
pip install -e ".[dev,test]"
pytest tests/
```

#### **Configuration Guide (docs/configuration.md)**
```markdown
# Configuration Guide

## API Keys (Required)

### Environment Variables (Secure Method)
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

### Supported Providers
- **OpenAI**: gpt-4o-mini-with-search (recommended), gpt-4o-with-search, o1-mini (with web search for current data)
- **Anthropic**: claude-3.5-haiku-tools, claude-3.5-sonnet-tools (with tool use for live CVE lookup)
- **Google**: gemini-2.0-flash-search, gemini-2.5-pro-search (with live search integration)
- **X AI**: grok-3-mini-web, grok-3-web (with live web access capabilities)

## Model Selection
# Use fastest, most cost-effective model with live search (default)
sca-scanner --model gpt-4o-mini-with-search

# Use knowledge-only model (opt-out from live search)
sca-scanner --model gpt-4o-mini --knowledge-only

# Use highest accuracy model with live CVE lookup
sca-scanner --model claude-3.5-sonnet-tools

## Configuration File (~/.sca_ai_config.yml)
models:
  primary: "gpt-4o-mini-with-search"        # Live search enabled by default

analysis:
  batch_size: 75
  timeout_seconds: 30

budget:
  daily_limit: 50.00
```

#### **Usage Examples (docs/examples.md)**
```markdown
# Usage Examples

## Basic Scanning
# Scan current directory
sca-scanner .

# Scan specific project
sca-scanner /path/to/project

## AI Model Selection
# Cost-optimized scanning
sca-scanner . --model gpt-4o-mini --budget 10.00

# High-accuracy scanning
sca-scanner . --model claude-3.5-sonnet

## Output Formats
# Export for AI agents
sca-scanner . --vulnerability-data output.json

# Detailed telemetry
sca-scanner . --telemetry-level debug --telemetry-file scan.jsonl

## Advanced Options
# Force fresh scan (ignore cache)
sca-scanner . --force-fresh

# Custom batch size for performance tuning
sca-scanner . --batch-size 100

# With exclusions file
sca-scanner . --exclusions ~/.sca_exclusions.yml
```

#### **AI Agent Integration Guide (docs/ai-agents.md)**
```markdown
# AI Agent Integration

## Structured Output Format

The scanner produces JSON output optimized for AI agent consumption:

{
  "vulnerability_analysis": {
    "package-name==version": {
      "source_locations": [
        {
          "file_path": "./requirements.txt",
          "line_number": 15,
          "declaration": "requests==2.25.1"
        }
      ],
      "cves": [...],
      "remediation_intelligence": {
        "recommended_action": "dependency_upgrade",
        "target_version": ">=2.31.0",
        "affected_files": ["./requirements.txt:15"]
      }
    }
  }
}

## Integration Example

import json
import subprocess

# Run scanner
result = subprocess.run([
    "sca-scanner", "/path/to/project", 
    "--vulnerability-data", "vulns.json"
], capture_output=True)

# Load structured data
with open("vulns.json") as f:
    vuln_data = json.load(f)

# Forward to remediation AI agent
remediation_agent.process_vulnerabilities(vuln_data)
```

#### **Troubleshooting Guide (docs/troubleshooting.md)**
```markdown
# Troubleshooting

## Common Issues

### API Key Not Found
Error: No API key found for provider
Solution: Export your API key: export OPENAI_API_KEY="sk-..."

### Rate Limiting
Error: Rate limit exceeded
Solution: 
- Use --batch-size 50 to reduce concurrent requests
- Set --budget to control spending

### Large Project Timeouts
Error: Scan timeout after 30 minutes
Solution:
- Use --force-fresh to skip cache validation
- Increase batch size: --batch-size 100

## Performance Optimization

### Speed
- Use gpt-4o-mini or claude-3.5-haiku
- Increase --batch-size to 100-150
- Enable caching (default)

### Cost
- Set daily budget: --budget 25.00
- Use gpt-4o-mini model
- Exclude test dependencies with config file

### Accuracy
- Use claude-3.5-sonnet or o1-mini
- Enable hybrid validation (default for critical findings)
- Review exclusions file regularly

## Debug Mode
sca-scanner . --telemetry-level debug --telemetry-file debug.jsonl
```

### **Documentation Quality Standards**

#### **Content Requirements**
- **AI Agent Examples**: Every feature has working code examples optimized for AI agent understanding
- **Programmatic Guides**: Installation, configuration, usage progression for automated execution
- **Error Handling**: Common issues with specific programmatic solutions AI agents can implement
- **Performance Tuning**: Optimization guides for speed, cost, accuracy with measurable parameters
- **Security Best Practices**: API key handling, output safety for automated systems

#### **Structure Standards**
- **Progressive Disclosure**: Basic → Advanced usage patterns for AI agent learning
- **Machine-Readable Content**: Structured headings, consistent formatting for AI parsing
- **Cross-References**: Clear links between related sections for AI agent navigation
- **Version Compatibility**: Explicit Python/dependency version requirements for automated setup
- **Code Validation**: All examples tested and working for reliable AI agent execution

#### **Maintenance Requirements**
- **Living Documentation**: Updated with each feature release for AI agent compatibility
- **Example Validation**: Automated testing of documentation examples for reliable AI execution
- **AI Agent Feedback Integration**: Regular updates based on AI agent usage patterns and errors
- **Machine Readability**: Structured, consistent language optimized for AI agent comprehension


