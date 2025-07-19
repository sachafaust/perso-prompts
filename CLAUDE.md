# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a collection of work-related prompts and documentation focused on security analysis and vulnerability management. The repository contains specialized prompts for analyzing security data and implementing security tools.

## Repository Structure

```
perso-prompts/
├── README.md                           # Basic repository description
└── vul-management/                     # Vulnerability management documentation
    ├── Rippling-Vuln-Dashboard.md     # Jira vulnerability analysis prompt
    └── SCA-Scanner.md                  # SCA scanner implementation guide
```

## Content Focus Areas

### Vulnerability Management Analysis
- **Location**: `vul-management/Rippling-Vuln-Dashboard.md`
- **Purpose**: Comprehensive prompt for analyzing Jira vulnerability management data
- **Key Features**: 
  - SLA compliance calculation methods
  - Team performance analysis
  - Security impact assessment
  - Triage bottleneck identification

### SCA Scanner Implementation
- **Location**: `vul-management/SCA-Scanner.md`
- **Purpose**: Evolution documentation for Software Composition Analysis scanner
- **Key Features**:
  - Multi-language dependency scanning (Python, JavaScript, Docker)
  - Live vulnerability database integration (OSV.dev, NVD, GitHub)
  - Parallel processing architecture
  - Production-ready implementation lessons

## Development Notes

- This repository contains documentation and prompts only - no executable code
- No build, test, or lint commands are required
- Content focuses on defensive security analysis and vulnerability management
- Documents are written in Markdown format for easy reading and reference

## Usage Patterns

When working with this repository:
1. Review existing prompts before creating new ones
2. Follow the established structure for vulnerability management content
3. Maintain the detailed specification format used in existing documents
4. Focus on defensive security applications only