# Strategic Design Choice: Focus on Code, Not Infrastructure

## Core Philosophy

The AI-Powered SCA Scanner is strategically focused on **code dependency analysis**, not infrastructure vulnerability scanning. This deliberate choice positions us as the best-in-class solution for developers analyzing their application dependencies.

## What We Scan: Code Dependencies

### ✅ **IN SCOPE: Application Code Dependencies**

#### Python Ecosystem
```python
# requirements.txt
django==3.2.0
requests>=2.28.0
numpy~=1.21.0

# pyproject.toml
[project]
dependencies = [
    "fastapi>=0.104.0",
    "sqlalchemy[asyncio]>=2.0.0",
]

# setup.py
install_requires=[
    'pandas>=1.3.0',
    'scikit-learn>=1.0.0',
]

# poetry.lock, Pipfile, uv.lock, environment.yml
```

#### JavaScript/Node.js Ecosystem
```javascript
// package.json
{
  "dependencies": {
    "express": "^4.18.0",
    "react": "^18.2.0",
    "@angular/core": "^15.0.0"
  }
}

// yarn.lock, package-lock.json, pnpm-lock.yaml
```

#### Other Language Ecosystems (Future)
```go
// go.mod
require (
    github.com/gin-gonic/gin v1.9.1
    github.com/gorilla/mux v1.8.0
)

// Gemfile (Ruby)
gem 'rails', '~> 7.0.0'
gem 'devise', '>= 4.9.0'

// pom.xml (Java/Maven)
<dependency>
    <groupId>org.springframework</groupId>
    <artifactId>spring-core</artifactId>
    <version>5.3.23</version>
</dependency>
```

**Why these are in scope:**
- Developer-managed artifacts
- Clear versioning and dependency chains
- Direct remediation path (upgrade package X to version Y)
- Part of application source code
- Checked into version control

### ❌ **OUT OF SCOPE: Infrastructure & System Dependencies**

#### Docker/Container Infrastructure
```dockerfile
# Dockerfile - NOT SCANNED
FROM ubuntu:20.04                    # ❌ OS base image
RUN apt-get install -y nginx         # ❌ System packages
RUN wget https://example.com/app.tar # ❌ Manual installations

# docker-compose.yml - NOT SCANNED
services:
  web:
    image: nginx:1.21                # ❌ Container images
```

#### Operating System Packages
```bash
# System package managers - NOT SCANNED
apt-get install libssl-dev           # ❌ Debian/Ubuntu
yum install postgresql               # ❌ RHEL/CentOS
apk add redis                        # ❌ Alpine
brew install mongodb                 # ❌ macOS
```

#### Cloud/Infrastructure Configuration
```yaml
# Kubernetes manifests - NOT SCANNED
apiVersion: apps/v1
kind: Deployment
spec:
  containers:
  - image: nginx:1.21                # ❌ Container infrastructure

# Terraform - NOT SCANNED
resource "aws_instance" "web" {
  ami = "ami-0c55b159cbfafe1f0"      # ❌ Infrastructure
}
```

**Why these are out of scope:**
- Infrastructure team responsibility, not developer
- Different remediation process (rebuild/patch systems)
- Requires different scanning approach (image analysis)
- Well-served by existing tools (Trivy, Grype, etc.)
- Would dilute our core value proposition

## Clear Examples: What We Do vs. Don't Do

### Scenario 1: Python Web Application

**WE SCAN:**
```python
# requirements.txt
django==3.2.0        # ✅ Found: CVE-2023-23969 in Django
psycopg2==2.9.0      # ✅ Found: SQL injection vulnerability
requests==2.25.0     # ✅ Found: CVE-2023-32681
```

**WE DON'T SCAN:**
```dockerfile
# Dockerfile
FROM python:3.9              # ❌ Ignored: Base image vulnerabilities
RUN apt-get install postgresql-client  # ❌ Ignored: System packages
```

### Scenario 2: Node.js Microservice

**WE SCAN:**
```json
// package.json
{
  "dependencies": {
    "express": "4.17.0",     // ✅ Found: CVE-2022-24999
    "lodash": "4.17.20",     // ✅ Found: Prototype pollution
    "axios": "0.21.0"        // ✅ Found: SSRF vulnerability
  }
}
```

**WE DON'T SCAN:**
```yaml
# docker-compose.yml
services:
  app:
    image: node:16-alpine    # ❌ Ignored: Container image
  db:
    image: postgres:13       # ❌ Ignored: Database image
```

### Scenario 3: Full Stack Application

**WE SCAN:**
- `/backend/requirements.txt` - Python dependencies ✅
- `/frontend/package.json` - JavaScript dependencies ✅
- `/api/go.mod` - Go dependencies ✅

**WE DON'T SCAN:**
- `/Dockerfile` - Container configuration ❌
- `/k8s/deployment.yaml` - Kubernetes manifests ❌
- `/.github/workflows/ci.yml` - CI/CD infrastructure ❌

## Competitive Positioning

### Why This Focus Matters

1. **Clear Value Proposition**
   - "AI-powered code dependency scanning"
   - Not "yet another container scanner"

2. **Developer-Centric**
   - Fits into developer workflows
   - Actionable results developers can fix
   - Integrated with code, not operations

3. **Best-in-Class, Not Jack-of-All-Trades**
   - Excel at code dependency analysis
   - Let Trivy/Grype handle infrastructure
   - Clean integration boundaries

4. **Following Successful Examples**
   - Semgrep: Focused on code, not containers
   - Dependabot: Only code dependencies
   - Snyk: Separate products for code vs. containers

## User Communication

### Clear Messaging

```yaml
# In documentation and CLI output
AI-Powered SCA Scanner
Focus: Application code dependencies
Supported: Python, JavaScript, Go, Ruby, Java packages
Not Supported: Docker images, OS packages, infrastructure

For infrastructure scanning, we recommend:
- Trivy for container images
- OWASP Dependency-Check for broader coverage
```

### CLI Behavior

```bash
$ sca-scanner .
Scanning for code dependencies...
✓ Found: requirements.txt
✓ Found: package.json
✓ Found: go.mod
⚠ Skipped: Dockerfile (infrastructure not scanned)

# Clear error if user expects Docker scanning
$ sca-scanner Dockerfile
Error: Docker/infrastructure scanning not supported.
This tool scans application code dependencies only.
For Docker scanning, consider using Trivy or Grype.
```

## Benefits of This Focus

1. **Faster Development**
   - No complex image building/extraction
   - No OS package manager knowledge needed
   - Simpler codebase to maintain

2. **Better Performance**
   - Scan in seconds, not minutes
   - No large image downloads
   - Efficient for CI/CD pipelines

3. **Clearer Mental Model**
   - Users know exactly what we scan
   - No confusion about coverage
   - Predictable, consistent results

4. **Higher Quality**
   - Deep expertise in code dependencies
   - Better AI models for specific domain
   - More accurate vulnerability detection

## Integration Strategy

### Working with Infrastructure Scanners

```bash
# Recommended workflow for complete coverage
# Step 1: Code dependencies (our tool)
sca-scanner . --output code-vulns.json

# Step 2: Infrastructure (other tools)
trivy image myapp:latest --output infra-vulns.json

# Step 3: Combine results
security-dashboard --code code-vulns.json --infra infra-vulns.json
```

### Clear Boundaries

| Concern | Tool | Responsibility |
|---------|------|----------------|
| Code Dependencies | SCA Scanner (us) | Find vulnerabilities in application packages |
| Container Images | Trivy/Grype | Find vulnerabilities in OS and system packages |
| Infrastructure | Terraform/CloudFormation scanners | Find misconfigurations |
| Secrets | GitLeaks/TruffleHog | Find exposed credentials |

## Conclusion

By focusing exclusively on code dependencies and explicitly excluding infrastructure scanning, we:

1. **Build a better product** - Excellence through focus
2. **Serve developers better** - Clear, actionable results
3. **Differentiate clearly** - Not another "me too" scanner
4. **Ship faster** - Less complexity to build and maintain

This strategic choice aligns with successful precedents (Semgrep, Dependabot) and creates a cleaner, more valuable product for our target users: developers who need fast, accurate analysis of their application dependencies.