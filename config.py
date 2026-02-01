"""Configuration module for GitHub API access."""
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Supported languages (removed restriction - all languages accepted)
SUPPORTED_LANGUAGES = None  # Accept all languages

# Minimum requirements
MIN_STARS = 200
MIN_CONTRIBUTORS = 3  # Minimum 3 contributors (1 solo = fails)
ACTIVITY_DAYS = 180  # Check for activity in last 6 months

# Complexity requirements
MIN_FILES = 30  # Minimum number of files in repository
MIN_DIRECTORIES = 8  # Minimum number of directories
MAX_SIZE_MB = 500  # Maximum repository size in MB

# Pass threshold
PASS_THRESHOLD = 75  # Minimum score percentage to pass (0-100)

# File patterns to check
TESTING_FILES = [
    "test/", "tests/", "__tests__/", "spec/",
    "pytest.ini", "jest.config.js", "cargo.toml"
]

BUILD_FILES = [
    "README.md", "README", "INSTALL.md",
    "Makefile", "package.json", "setup.py", "pyproject.toml",
    "Cargo.toml", "build.rs", "CMakeLists.txt"
]

LINTER_FILES = [
    ".eslintrc", ".pylintrc", ".flake8", "clippy.toml",
    "rustfmt.toml", ".prettierrc", "tslint.json"
]

# Network/port indicators (to avoid)
NETWORK_INDICATORS = [
    "server.py", "app.py", "main.py:.*app.run",
    "express()", "http.createServer", "actix_web", "rocket"
]
