#!/usr/bin/env python3
"""Analyze a project directory and output a structured JSON brief.

Detects languages, frameworks, config files, directory structure,
test patterns, and CI presence to inform the cadre debate team.

Usage:
    python analyze_project.py [project_dir]

Outputs JSON to stdout:
    {
        "project_name": "my-project",
        "languages": ["TypeScript", "Python"],
        "frameworks": ["React", "Express"],
        "package_managers": ["npm"],
        "directories": {"src/": "source code", ...},
        "test_patterns": ["vitest", "**/*.test.ts"],
        "ci": "github-actions",
        "config_files": ["package.json", "tsconfig.json"],
        "monorepo": false,
        "iac": ["Terraform", "Helm"],
        "description": ""
    }
"""

import json
import sys
from pathlib import Path


# Config file → language/framework mapping
CONFIG_SIGNALS = {
    "package.json": {"lang": "TypeScript/JavaScript", "pm": "npm"},
    "yarn.lock": {"pm": "yarn"},
    "pnpm-lock.yaml": {"pm": "pnpm"},
    "bun.lockb": {"pm": "bun"},
    "go.mod": {"lang": "Go", "pm": "go"},
    "Cargo.toml": {"lang": "Rust", "pm": "cargo"},
    "pyproject.toml": {"lang": "Python", "pm": "uv/pip"},
    "requirements.txt": {"lang": "Python", "pm": "pip"},
    "Pipfile": {"lang": "Python", "pm": "pipenv"},
    "Gemfile": {"lang": "Ruby", "pm": "bundler"},
    "build.gradle": {"lang": "Java/Kotlin", "pm": "gradle"},
    "build.gradle.kts": {"lang": "Kotlin", "pm": "gradle"},
    "pom.xml": {"lang": "Java", "pm": "maven"},
    "composer.json": {"lang": "PHP", "pm": "composer"},
    "mix.exs": {"lang": "Elixir", "pm": "mix"},
    "CMakeLists.txt": {"lang": "C/C++", "pm": "cmake"},
    "Makefile": {"pm": "make"},
    "Dockerfile": {"tool": "docker"},
    "docker-compose.yml": {"tool": "docker-compose"},
    "docker-compose.yaml": {"tool": "docker-compose"},
    # IaC config files
    "azure.yaml": {"tool": "azd"},
    "Pulumi.yaml": {"tool": "pulumi", "lang": "Pulumi"},
    "Pulumi.yml": {"tool": "pulumi", "lang": "Pulumi"},
    "Chart.yaml": {"tool": "helm"},
    "terragrunt.hcl": {"tool": "terragrunt", "lang": "HCL"},
    "bicepconfig.json": {"tool": "bicep"},
    "skaffold.yaml": {"tool": "skaffold"},
    "kustomization.yaml": {"tool": "kustomize"},
    "kustomization.yml": {"tool": "kustomize"},
    "crossplane.yaml": {"tool": "crossplane"},
    "ansible.cfg": {"tool": "ansible", "lang": "YAML/Ansible"},
}

# Framework detection from package.json dependencies
NPM_FRAMEWORK_SIGNALS = {
    "react": "React",
    "next": "Next.js",
    "vue": "Vue",
    "nuxt": "Nuxt",
    "svelte": "Svelte",
    "angular": "Angular",
    "@angular/core": "Angular",
    "express": "Express",
    "fastify": "Fastify",
    "hono": "Hono",
    "koa": "Koa",
    "nestjs": "NestJS",
    "@nestjs/core": "NestJS",
    "prisma": "Prisma",
    "@prisma/client": "Prisma",
    "drizzle-orm": "Drizzle",
    "typeorm": "TypeORM",
    "sequelize": "Sequelize",
    "tailwindcss": "Tailwind CSS",
    "vitest": "Vitest",
    "jest": "Jest",
    "mocha": "Mocha",
    "playwright": "Playwright",
    "cypress": "Cypress",
    "storybook": "Storybook",
    "@storybook/react": "Storybook",
}

# Python framework detection from pyproject.toml
PYTHON_FRAMEWORK_SIGNALS = {
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "pytest": "pytest",
    "sqlalchemy": "SQLAlchemy",
    "pydantic": "Pydantic",
    "celery": "Celery",
}

# IaC file extension → tool mapping (detected via directory scan)
IAC_EXTENSIONS = {
    ".tf": "Terraform",
    ".tfvars": "Terraform",
    ".bicep": "Bicep",
    ".bicepparam": "Bicep",
}

# IaC-specific config files that confirm the IaC tool
IAC_CONFIG_SIGNALS = {
    "main.tf": "Terraform",
    "main.bicep": "Bicep",
    "provider.tf": "Terraform",
    "providers.tf": "Terraform",
    "backend.tf": "Terraform",
    "variables.tf": "Terraform",
    "terraform.tfvars": "Terraform",
    "terraform.tfstate": "Terraform",
    ".terraform.lock.hcl": "Terraform",
    "values.yaml": "Helm",
    "values.yml": "Helm",
    "helmfile.yaml": "Helmfile",
    "helmfile.yml": "Helmfile",
    "azure.yaml": "Azure Developer CLI",
    "Pulumi.yaml": "Pulumi",
    "Pulumi.yml": "Pulumi",
    "serverless.yml": "Serverless Framework",
    "serverless.yaml": "Serverless Framework",
    "sam-template.yaml": "AWS SAM",
    "template.yaml": "AWS SAM/CloudFormation",
    "cdk.json": "AWS CDK",
    "cdktf.json": "CDKTF",
}

# Test pattern detection
TEST_SIGNALS = {
    "vitest.config.ts": "vitest",
    "vitest.config.js": "vitest",
    "jest.config.ts": "jest",
    "jest.config.js": "jest",
    "jest.config.json": "jest",
    "pytest.ini": "pytest",
    "setup.cfg": "pytest",
    "conftest.py": "pytest",
    ".mocharc.yml": "mocha",
    "cypress.config.ts": "cypress",
    "cypress.config.js": "cypress",
    "playwright.config.ts": "playwright",
    # IaC testing/linting tools
    ".tflint.hcl": "tflint",
    ".checkov.yml": "checkov",
    ".checkov.yaml": "checkov",
    "tflint.hcl": "tflint",
}

# CI detection
CI_SIGNALS = {
    ".github/workflows": "github-actions",
    ".gitlab-ci.yml": "gitlab-ci",
    "Jenkinsfile": "jenkins",
    ".circleci": "circleci",
    ".travis.yml": "travis",
    "azure-pipelines.yml": "azure-devops",
    "bitbucket-pipelines.yml": "bitbucket",
}

# Monorepo signals
MONOREPO_SIGNALS = [
    "lerna.json",
    "nx.json",
    "turbo.json",
    "rush.json",
    "pnpm-workspace.yaml",
]


def _read_package_json(project_dir: Path) -> dict | None:
    """Read and parse package.json, returning None if missing or invalid."""
    pkg_json = project_dir / "package.json"
    if pkg_json.exists():
        try:
            return json.loads(pkg_json.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return None


def detect_languages_and_frameworks(project_dir: Path, pkg_data: dict | None) -> dict:
    """Scan for config files and detect languages, frameworks, package managers."""
    languages = set()
    frameworks = set()
    package_managers = set()
    config_files = []
    tools = set()

    for config_file, signals in CONFIG_SIGNALS.items():
        if (project_dir / config_file).exists():
            config_files.append(config_file)
            if "lang" in signals:
                languages.add(signals["lang"])
            if "pm" in signals:
                package_managers.add(signals["pm"])
            if "tool" in signals:
                tools.add(signals["tool"])

    # Deep scan package.json for frameworks
    if pkg_data is not None:
        all_deps = {}
        all_deps.update(pkg_data.get("dependencies", {}))
        all_deps.update(pkg_data.get("devDependencies", {}))
        for dep, framework in NPM_FRAMEWORK_SIGNALS.items():
            if dep in all_deps:
                frameworks.add(framework)
        # Check for TypeScript
        has_ts = "typescript" in all_deps or (project_dir / "tsconfig.json").exists()
        if has_ts:
            languages.discard("TypeScript/JavaScript")
            languages.add("TypeScript")
        elif "TypeScript/JavaScript" in languages:
            languages.discard("TypeScript/JavaScript")
            languages.add("JavaScript")
        # Check for monorepo workspaces
        if "workspaces" in pkg_data:
            tools.add("npm-workspaces")

    # Deep scan pyproject.toml for frameworks
    pyproject = project_dir / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text()
            for dep, framework in PYTHON_FRAMEWORK_SIGNALS.items():
                if dep in content.lower():
                    frameworks.add(framework)
        except OSError:
            pass

    return {
        "languages": sorted(languages),
        "frameworks": sorted(frameworks),
        "package_managers": sorted(package_managers),
        "config_files": sorted(config_files),
        "tools": sorted(tools),
    }


def scan_directories(project_dir: Path) -> dict:
    """Scan top-level directories and categorize them."""
    dirs = {}
    skip = {".git", "node_modules", ".next", "__pycache__", ".venv", "venv",
            "dist", "build", ".cache", "coverage", ".claude", "target", ".tox"}

    for entry in sorted(project_dir.iterdir()):
        if entry.is_dir() and entry.name not in skip and not entry.name.startswith("."):
            # Try to categorize
            name = entry.name
            dirs[f"{name}/"] = _categorize_dir(name, entry)

    return dirs


def _categorize_dir(name: str, path: Path) -> str:
    """Heuristic categorization of a directory."""
    categories = {
        "src": "source code",
        "lib": "library code",
        "app": "application code",
        "api": "API code",
        "server": "server code",
        "client": "client code",
        "frontend": "frontend code",
        "backend": "backend code",
        "web": "web application",
        "packages": "monorepo packages",
        "apps": "monorepo applications",
        "test": "tests",
        "tests": "tests",
        "__tests__": "tests",
        "spec": "test specs",
        "e2e": "end-to-end tests",
        "docs": "documentation",
        "scripts": "scripts and tooling",
        "config": "configuration",
        "public": "static assets",
        "static": "static assets",
        "assets": "assets",
        "migrations": "database migrations",
        "prisma": "Prisma schema and migrations",
        "components": "UI components",
        "pages": "page components",
        "routes": "route handlers",
        "middleware": "middleware",
        "utils": "utilities",
        "helpers": "helper functions",
        "types": "type definitions",
        "hooks": "hooks",
        "services": "service layer",
        "models": "data models",
        "controllers": "controllers",
        "views": "views",
        "templates": "templates",
        "cmd": "CLI commands (Go)",
        "internal": "internal packages (Go)",
        "pkg": "public packages (Go)",
        # IaC directories
        "infra": "infrastructure as code",
        "infrastructure": "infrastructure as code",
        "terraform": "Terraform infrastructure",
        "bicep": "Bicep infrastructure",
        "helm": "Helm charts",
        "charts": "Helm charts",
        "deploy": "deployment configuration",
        "deployment": "deployment configuration",
        "k8s": "Kubernetes manifests",
        "kubernetes": "Kubernetes manifests",
        "manifests": "Kubernetes manifests",
        "modules": "IaC/code modules",
        "environments": "environment configurations",
        "envs": "environment configurations",
        "stacks": "IaC stacks (Pulumi/CDK)",
        "playbooks": "Ansible playbooks",
        "roles": "Ansible roles",
        "policies": "policy definitions (OPA/Sentinel)",
    }
    return categories.get(name, "project directory")


def detect_tests(project_dir: Path) -> list:
    """Detect test frameworks and patterns."""
    patterns = []
    for test_file, framework in TEST_SIGNALS.items():
        if (project_dir / test_file).exists():
            patterns.append(framework)
    return sorted(set(patterns))


def detect_ci(project_dir: Path) -> str:
    """Detect CI/CD system."""
    for ci_path, ci_name in CI_SIGNALS.items():
        if (project_dir / ci_path).exists():
            return ci_name
    return ""


def detect_iac(project_dir: Path) -> list:
    """Detect Infrastructure as Code tools and frameworks."""
    iac_tools = set()

    # Check for IaC config files with fixed names
    for config_file, tool in IAC_CONFIG_SIGNALS.items():
        if (project_dir / config_file).exists():
            iac_tools.add(tool)

    # Scan top-level and common IaC directories for extension-based detection
    scan_dirs = [project_dir]
    for subdir in ("infra", "infrastructure", "terraform", "bicep", "deploy",
                   "deployment", "modules", "environments", "envs", "stacks"):
        candidate = project_dir / subdir
        if candidate.is_dir():
            scan_dirs.append(candidate)

    for scan_dir in scan_dirs:
        try:
            for entry in scan_dir.iterdir():
                if entry.is_file():
                    ext = entry.suffix
                    if ext in IAC_EXTENSIONS:
                        iac_tools.add(IAC_EXTENSIONS[ext])
        except OSError:
            continue

    # Check for Helm chart structure (Chart.yaml + templates/)
    if (project_dir / "Chart.yaml").exists() and (project_dir / "templates").is_dir():
        iac_tools.add("Helm")

    # Check for Kubernetes manifests (YAML files with apiVersion)
    for subdir in ("k8s", "kubernetes", "manifests"):
        k8s_dir = project_dir / subdir
        if k8s_dir.is_dir():
            iac_tools.add("Kubernetes")
            break

    return sorted(iac_tools)


def detect_monorepo(project_dir: Path, pkg_data: dict | None) -> bool:
    """Detect if this is a monorepo."""
    for signal in MONOREPO_SIGNALS:
        if (project_dir / signal).exists():
            return True
    # Check for npm/yarn/pnpm workspaces in package.json
    if pkg_data is not None and "workspaces" in pkg_data:
        return True
    # Check for packages/ or apps/ directories
    if (project_dir / "packages").is_dir() or (project_dir / "apps").is_dir():
        return True
    return False


def get_project_name(project_dir: Path, pkg_data: dict | None) -> str:
    """Get project name from config or directory name."""
    if pkg_data is not None:
        name = pkg_data.get("name", "")
        if name:
            return name.split("/")[-1]  # strip scope

    pyproject = project_dir / "pyproject.toml"
    if pyproject.exists():
        try:
            for line in pyproject.read_text().splitlines():
                if line.strip().startswith("name"):
                    # Simple parse: name = "foo"
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        return parts[1].strip().strip('"').strip("'")
        except OSError:
            pass

    return project_dir.name


def analyze(project_dir: str) -> dict:
    """Run full project analysis and return structured brief."""
    project_path = Path(project_dir).resolve()

    if not project_path.is_dir():
        return {"error": f"Not a directory: {project_dir}"}

    # Parse package.json once and share across detectors
    pkg_data = _read_package_json(project_path)
    detection = detect_languages_and_frameworks(project_path, pkg_data)

    return {
        "project_name": get_project_name(project_path, pkg_data),
        "languages": detection["languages"],
        "frameworks": detection["frameworks"],
        "package_managers": detection["package_managers"],
        "directories": scan_directories(project_path),
        "test_patterns": detect_tests(project_path),
        "ci": detect_ci(project_path),
        "config_files": detection["config_files"],
        "monorepo": detect_monorepo(project_path, pkg_data),
        "iac": detect_iac(project_path),
        "description": "",
    }


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    result = analyze(target)
    print(json.dumps(result, indent=2))
