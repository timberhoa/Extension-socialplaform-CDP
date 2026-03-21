"""
Project Manager - Handles project selection and creation for capture sessions.
Provides interactive CLI for managing capture projects.
"""

import os
from pathlib import Path
from datetime import datetime


def get_projects_dir() -> Path:
    """Get the projects directory path."""
    return Path("./captures/projects")


def list_projects() -> list[str]:
    """List all existing projects."""
    projects_dir = get_projects_dir()
    if not projects_dir.exists():
        return []

    projects = []
    for item in sorted(projects_dir.iterdir()):
        if item.is_dir() and not item.name.startswith('.'):
            projects.append(item.name)
    return projects


def get_project_info(project_name: str) -> dict:
    """Get info about a project (session count, last modified)."""
    project_dir = get_projects_dir() / project_name
    if not project_dir.exists():
        return {}

    sessions = []
    for item in project_dir.iterdir():
        if item.is_dir() and item.name.startswith('session-'):
            sessions.append(item.name)

    # Get last modified
    jsonl_files = list(project_dir.glob('**/requests.jsonl'))
    last_modified = None
    if jsonl_files:
        last_modified = max(f.stat().st_mtime for f in jsonl_files)

    return {
        'sessions': len(sessions),
        'last_modified': datetime.fromtimestamp(last_modified).strftime('%Y-%m-%d %H:%M') if last_modified else 'N/A',
        'has_analysis': (project_dir / 'reverse-web-api-skill-result').exists()
    }


def create_project(name: str) -> Path:
    """Create a new project directory."""
    project_dir = get_projects_dir() / name
    project_dir.mkdir(parents=True, exist_ok=True)
    return project_dir


def select_project_interactive() -> str | None:
    """Interactive project selection menu."""
    projects = list_projects()

    print("\n" + "=" * 60)
    print("  PROJECT SELECTION")
    print("=" * 60)

    if projects:
        print("\n  Existing projects:\n")
        for i, name in enumerate(projects, 1):
            info = get_project_info(name)
            status = "✓" if info.get('has_analysis') else " "
            print(f"    [{i}] {name}")
            print(f"        Sessions: {info.get('sessions', 0)} | Last: {info.get('last_modified', 'N/A')} | Analyzed: {status}")
        print()
    else:
        print("\n  No existing projects found.\n")

    print(f"    [N] Create NEW project")
    print(f"    [Q] Quit\n")

    while True:
        choice = input("  Select option: ").strip()

        if choice.upper() == 'Q':
            return None

        if choice.upper() == 'N':
            return create_project_interactive()

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(projects):
                return projects[idx]
            print("  Invalid selection. Try again.")
        except ValueError:
            print("  Invalid input. Enter number, N, or Q.")


def create_project_interactive() -> str | None:
    """Interactive project creation."""
    print("\n  CREATE NEW PROJECT")
    print("  " + "-" * 40)

    while True:
        name = input("  Project name (or Q to cancel): ").strip()

        if name.upper() == 'Q':
            return None

        if not name:
            print("  Name cannot be empty.")
            continue

        # Sanitize name
        safe_name = "".join(c if c.isalnum() or c in '-_ ' else '_' for c in name)
        safe_name = safe_name.replace(' ', '-')

        if safe_name != name:
            print(f"  Name sanitized to: {safe_name}")

        # Check if exists
        if (get_projects_dir() / safe_name).exists():
            overwrite = input(f"  Project '{safe_name}' exists. Continue with it? [Y/n]: ").strip()
            if overwrite.upper() != 'N':
                return safe_name
            continue

        create_project(safe_name)
        print(f"  Created project: {safe_name}")
        return safe_name


def get_project_output_dir(project_name: str) -> Path:
    """Get the output directory for a project's captures."""
    return get_projects_dir() / project_name


def get_project_analysis_dir(project_name: str) -> Path:
    """Get the analysis results directory for a project."""
    return get_projects_dir() / project_name / "reverse-web-api-skill-result"


if __name__ == "__main__":
    # Test interactive selection
    selected = select_project_interactive()
    if selected:
        print(f"\nSelected project: {selected}")
        print(f"Output dir: {get_project_output_dir(selected)}")
    else:
        print("\nCancelled.")
