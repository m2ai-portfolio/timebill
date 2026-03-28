"""Project detection module for TimeBill.

This module provides the ProjectDetector class that infers project names
from window titles, IDE status bars, and browser tab names.
"""

import re
from typing import Optional


class ProjectDetector:
    """Detects active project from window titles and process names."""

    # Default patterns for common IDEs and tools
    DEFAULT_PATTERNS = {
        # IDE patterns - extract filename/path information
        'vim': [
            r'vim.*?[\\/]([^\\/]+)[\\/]',  # vim - /path/to/project/file.py
            r'vim.*?-\s*([^\\/\s]+)[\\/]',  # vim - project/file.py
        ],
        'vscode': [
            r'Visual Studio Code.*?[\\/]([^\\/]+)[\\/]',  # VSCode - /path/project/
            r'VSCode.*?[\\/]([^\\/]+)[\\/]',
            r'Code.*?[\\/]([^\\/]+)[\\/]',
        ],
        'intellij': [
            r'IntelliJ IDEA.*?\[([^\]]+)\]',  # IntelliJ IDEA - [project]
            r'PyCharm.*?\[([^\]]+)\]',
            r'WebStorm.*?\[([^\]]+)\]',
        ],
        'sublime': [
            r'Sublime Text.*?[\\/]([^\\/]+)[\\/]',
        ],
        'atom': [
            r'Atom.*?[\\/]([^\\/]+)[\\/]',
        ],

        # Browser patterns - extract repo/org information
        'github': [
            r'GitHub.*?[\\/]([^\\/\s]+)[\\/]([^\\/\s]+)',  # GitHub - org/repo
            r'github\.com[\\/]([^\\/\s]+)[\\/]([^\\/\s]+)',
        ],
        'gitlab': [
            r'GitLab.*?[\\/]([^\\/\s]+)[\\/]([^\\/\s]+)',
            r'gitlab\.com[\\/]([^\\/\s]+)[\\/]([^\\/\s]+)',
        ],
        'bitbucket': [
            r'Bitbucket.*?[\\/]([^\\/\s]+)[\\/]([^\\/\s]+)',
            r'bitbucket\.org[\\/]([^\\/\s]+)[\\/]([^\\/\s]+)',
        ],
    }

    def __init__(self, custom_patterns: dict = None):
        """Initialize ProjectDetector.

        Args:
            custom_patterns: Optional dict mapping project names to list of
                           pattern strings to match against window titles.
                           Example: {'myapp': ['myapp', 'MyApp']}
        """
        self.custom_patterns = custom_patterns or {}

    def detect_project(self, window_title: str) -> Optional[str]:
        """Detect project name from window title.

        Args:
            window_title: The foreground window title string

        Returns:
            Detected project name or None if no match found
        """
        if not window_title:
            return None

        # Try custom patterns first (highest priority)
        project_name = self._match_custom_patterns(window_title)
        if project_name:
            return project_name

        # Try default IDE patterns
        project_name = self._match_ide_patterns(window_title)
        if project_name:
            return project_name

        # Try browser patterns
        project_name = self._match_browser_patterns(window_title)
        if project_name:
            return project_name

        return None

    def _match_custom_patterns(self, window_title: str) -> Optional[str]:
        """Match against user-defined custom patterns.

        Args:
            window_title: The window title to match

        Returns:
            Project name if match found, None otherwise
        """
        for project_name, patterns in self.custom_patterns.items():
            for pattern in patterns:
                # Support both regex patterns and simple string matching
                if pattern.lower() in window_title.lower():
                    return project_name
                try:
                    if re.search(pattern, window_title, re.IGNORECASE):
                        return project_name
                except re.error:
                    # If pattern is invalid regex, we already did string match above
                    continue
        return None

    def _match_ide_patterns(self, window_title: str) -> Optional[str]:
        """Match against IDE-specific patterns.

        Args:
            window_title: The window title to match

        Returns:
            Extracted project name if match found, None otherwise
        """
        # Common directory names to skip when looking for project names
        SKIP_DIRS = {'src', 'lib', 'bin', 'test', 'tests', 'docs', 'examples',
                     'home', 'user', 'users', 'var', 'www', 'projects', 'workspace',
                     'agent', 'data', 'config', 'public', 'static'}

        # Check for vim patterns
        if 'vim' in window_title.lower():
            # Extract path component from vim window title
            # Patterns:
            # - vim - myproject/main.py
            # - vim /home/user/projects/webapp/index.html
            # - vim - ~/projects/timebill/agent/detection.py
            # We want to extract the project name (part before the filename)

            # Look for path with slashes
            path_match = re.search(r'vim\s+[~\-\s]*(.+?)[\\/]([^\\/]+)$', window_title, re.IGNORECASE)
            if path_match:
                full_path = path_match.group(1)
                # Extract directory components, skip common ones, get the best match
                parts = re.split(r'[\\/]', full_path)
                parts = [p for p in parts if p and p not in ['~', '.', '..']]

                # First try to find a non-skip directory
                for part in reversed(parts):
                    if part.lower() not in SKIP_DIRS:
                        return part

                # If all are skip dirs, return the last one anyway
                if parts:
                    return parts[-1]

            # Fallback: simple pattern like "vim - myproject/file"
            match = re.search(r'vim.*?[\s\-]+(~[\\/])?([a-zA-Z0-9_\-]+)[\\/]', window_title)
            if match:
                return match.group(2)

        # Check for VSCode patterns
        if 'visual studio code' in window_title.lower() or 'vscode' in window_title.lower():
            # VSCode patterns:
            # - Visual Studio Code - myproject/src/main.js
            # - index.tsx - myapp - Visual Studio Code
            # - VSCode - /home/dev/api/server.py

            # Try pattern: filename - project - Visual Studio Code
            match = re.search(r'[\w\.]+\s*-\s*([a-zA-Z0-9_\-]+)\s*-\s*Visual Studio Code', window_title, re.IGNORECASE)
            if match:
                return match.group(1)

            # Try pattern: Visual Studio Code - /path/to/project/file
            # Extract the full path and parse it
            match = re.search(r'(?:Visual Studio Code|VSCode)\s*-\s*(.+)', window_title, re.IGNORECASE)
            if match:
                full_path = match.group(1).strip()
                # Extract all directory parts
                # Split by / or \ and remove the filename (last part)
                parts = re.split(r'[\\/]', full_path)
                # Remove empty parts and the filename (last part if it has an extension)
                if parts and '.' in parts[-1]:
                    parts = parts[:-1]
                parts = [p for p in parts if p]

                # Find first non-skip directory from the end
                for part in reversed(parts):
                    if part.lower() not in SKIP_DIRS:
                        return part
                # Fallback to last part if all are skip dirs
                if parts:
                    return parts[-1]

        # Also check for just "Code" in the title
        elif 'code' in window_title.lower() and 'visual studio' not in window_title.lower():
            match = re.search(r'[\\/]([a-zA-Z0-9_\-]+)[\\/]', window_title)
            if match:
                return match.group(1)

        # Check for IntelliJ/PyCharm/WebStorm patterns
        for ide in ['intellij', 'pycharm', 'webstorm', 'idea']:
            if ide in window_title.lower():
                match = re.search(r'\[([^\]]+)\]', window_title)
                if match:
                    return match.group(1)

        # Check for other IDEs
        for ide in ['sublime', 'atom', 'emacs']:
            if ide in window_title.lower():
                match = re.search(r'[\\/]([a-zA-Z0-9_\-]+)[\\/]', window_title)
                if match:
                    return match.group(1)

        return None

    def _match_browser_patterns(self, window_title: str) -> Optional[str]:
        """Match against browser/web patterns.

        Args:
            window_title: The window title to match

        Returns:
            Extracted project name if match found, None otherwise
        """
        # GitHub patterns
        if 'github' in window_title.lower():
            # Pattern: GitHub - org/repo or github.com/org/repo
            # Also: Pull Request #42 - acme/api-server - GitHub
            # We want to extract the repo name (second part)

            # First try to match site.com/org/repo pattern (3 parts)
            match = re.search(r'(?:github\.)?[a-zA-Z0-9_\-]+\.(?:com|org|io|net)/([a-zA-Z0-9_\-]+)/([a-zA-Z0-9_\-]+)', window_title, re.IGNORECASE)
            if match:
                return match.group(2)  # repo name

            # Fall back to simple org/repo pattern
            match = re.search(r'([a-zA-Z0-9_\-]+)/([a-zA-Z0-9_\-]+)', window_title)
            if match and match.group(1).lower() not in ['com', 'org', 'io', 'net']:
                return match.group(2)

        # GitLab patterns
        if 'gitlab' in window_title.lower():
            # Pattern: GitLab - org/repo or gitlab.com/org/repo
            match = re.search(r'(?:gitlab\.)?[a-zA-Z0-9_\-]+\.(?:com|org|io|net)/([a-zA-Z0-9_\-]+)/([a-zA-Z0-9_\-]+)', window_title, re.IGNORECASE)
            if match:
                return match.group(2)

            match = re.search(r'([a-zA-Z0-9_\-]+)/([a-zA-Z0-9_\-]+)', window_title)
            if match and match.group(1).lower() not in ['com', 'org', 'io', 'net']:
                return match.group(2)

        # Bitbucket patterns
        if 'bitbucket' in window_title.lower():
            # Pattern: Bitbucket - org/repo or bitbucket.org/org/repo
            match = re.search(r'(?:bitbucket\.)?[a-zA-Z0-9_\-]+\.(?:com|org|io|net)/([a-zA-Z0-9_\-]+)/([a-zA-Z0-9_\-]+)', window_title, re.IGNORECASE)
            if match:
                return match.group(2)

            match = re.search(r'([a-zA-Z0-9_\-]+)/([a-zA-Z0-9_\-]+)', window_title)
            if match and match.group(1).lower() not in ['com', 'org', 'io', 'net']:
                return match.group(2)

        return None
