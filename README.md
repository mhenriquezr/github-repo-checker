# GitHub Repository Checker

Tool to verify and search GitHub repositories based on quality criteria.

## Requirements

- Python 3.8+
- GitHub Personal Access Token with `public_repo` scope
  - Get one here: https://github.com/settings/tokens/new

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure your GitHub token
echo "GITHUB_TOKEN=your_token_here" > .env

# Optional: Configure custom approved repositories (comma-separated)
echo "APPROVED_REPOS=https://github.com/user/repo1,https://github.com/user/repo2" >> .env
```

## Usage

### CLI

```bash
# Verify a repository
python main.py verify https://github.com/owner/repo

# Search repositories
python main.py search --language Python --min-stars 100

# Fast search without verification
python main.py search --language Rust --no-verify
```

### Web Interface

```bash
# Start the web server
python web_app.py

# Open browser at http://localhost:5000
```

## Evaluation Criteria

Repositories are scored 0-100 based on these requirements:

| Criterion | Weight | Description |
|-----------|--------|-------------|
| **Git Repository** | Critical | Must be a valid git repository |
| **Primary Language** | Critical | Must have a detected primary language |
| **Open License** | Critical | Must have open source license |
| **Multiple Contributors** | Critical | At least 3 contributors (1 = fails) |
| **Build Instructions** | Critical | Clear setup documentation (README, etc) |
| **Project Complexity** | Critical | Minimum 30 files and 8 directories |
| **Quality Project** | Critical | Not vibe-coded (proper commits, description, README) |
| **Repository Size** | Critical | Maximum 500 MB |
| **Testing Practices** | Warning | Has test files/directories (recommended) |
| **Recent Activity** | Warning | Activity in last 6 months |
| **Code Quality** | Warning | Linters/formatters or 50+ stars |
| **Network Usage** | Warning | Minimal network dependencies |

**Minimum Requirements:**
- Stars: 3+
- Contributors: 3+ (solo projects rejected)
- Files: 30+
- Directories: 8+
- Size: ≤ 500 MB

**Pass Threshold:** 75/100

**Scoring:**
- Critical requirements: 10 points each
- Warning requirements: 5 points each

## Output

### CLI Verification

Shows:
- Repository information (name, stars, language, license)
- Overall score and pass/fail
- Only failed checks and warnings
- Concise summary

### Web Interface

Features:
- Clean, modern UI
- Real-time verification
- Detailed results with color coding
- Visual score display
- Failed checks and warnings highlighted

## GitHub API

**Token Required:** Personal Access Token
**Permissions:** `public_repo` (read access to public repositories)
**Rate Limits:** 
- Authenticated: 5000 requests/hour
- Unauthenticated: 60 requests/hour

## Examples

```bash
# CLI: Quick check
python main.py verify https://github.com/pallets/flask

# CLI: Find quality Python projects
python main.py search --language Python --min-stars 50 --has-tests

# Web: Start server
python web_app.py
# Then open http://localhost:5000 in your browser
```
