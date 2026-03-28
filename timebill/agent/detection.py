"""Project detection from window titles and process names."""

import os
import re
from typing import Dict, List, Tuple


class ProjectDetector:
    """Detects active project from window titles, IDE status, and browser tabs."""

    def __init__(self):
        """Initialize the project detector with built-in and custom patterns."""
        # Built-in patterns: (pattern, project_name_template)
        self.patterns: List[Tuple[re.Pattern, str]] = [
            # IDE patterns
            (re.compile(r'\bvim\b', re.IGNORECASE), "Vim Editing"),
            (re.compile(r'\bneovim\b', re.IGNORECASE), "Vim Editing"),
            (re.compile(r'\bnvim\b', re.IGNORECASE), "Vim Editing"),
            (re.compile(r'\bvs\s*code\b', re.IGNORECASE), "VS Code Development"),
            (re.compile(r'\bvisual\s*studio\s*code\b', re.IGNORECASE), "VS Code Development"),
            (re.compile(r'\bpycharm\b', re.IGNORECASE), "PyCharm Development"),
            (re.compile(r'\bintellij\b', re.IGNORECASE), "IntelliJ Development"),
            (re.compile(r'\beclipse\b', re.IGNORECASE), "Eclipse Development"),
            (re.compile(r'\bsublime\b', re.IGNORECASE), "Sublime Text Editing"),
            (re.compile(r'\batom\b', re.IGNORECASE), "Atom Editing"),

            # Terminal patterns
            (re.compile(r'\bterminal\b', re.IGNORECASE), "Terminal Activity"),
            (re.compile(r'\bbash\b', re.IGNORECASE), "Terminal Activity"),
            (re.compile(r'\bzsh\b', re.IGNORECASE), "Terminal Activity"),
            (re.compile(r'\bfish\b', re.IGNORECASE), "Terminal Activity"),
            (re.compile(r'\bcmd\b', re.IGNORECASE), "Terminal Activity"),
            (re.compile(r'\bpowershell\b', re.IGNORECASE), "Terminal Activity"),

            # GitHub patterns - extract repo name
            (re.compile(r'github[:\s\-]+([a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-]+)', re.IGNORECASE), r"GitHub: \1"),
            (re.compile(r'github\.com/([a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-]+)', re.IGNORECASE), r"GitHub: \1"),

            # GitLab patterns
            (re.compile(r'gitlab[:\s\-]+([a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-]+)', re.IGNORECASE), r"GitLab: \1"),

            # Browser patterns
            (re.compile(r'\bchrome\b', re.IGNORECASE), "Chrome Browsing"),
            (re.compile(r'\bfirefox\b', re.IGNORECASE), "Firefox Browsing"),
            (re.compile(r'\bsafari\b', re.IGNORECASE), "Safari Browsing"),
            (re.compile(r'\bedge\b', re.IGNORECASE), "Edge Browsing"),

            # Documentation
            (re.compile(r'\bdocs\b', re.IGNORECASE), "Documentation"),
            (re.compile(r'\breadme\b', re.IGNORECASE), "Documentation"),

            # Communication
            (re.compile(r'\bslack\b', re.IGNORECASE), "Slack Communication"),
            (re.compile(r'\bdiscord\b', re.IGNORECASE), "Discord Communication"),
            (re.compile(r'\bzoom\b', re.IGNORECASE), "Zoom Meeting"),
            (re.compile(r'\bmeet\b', re.IGNORECASE), "Video Meeting"),
        ]

        # Load custom patterns from environment variable
        self._load_custom_patterns()

    def _load_custom_patterns(self):
        """Load custom detection patterns from TIMEBILL_PROJECT_DETECTION env var."""
        custom_patterns_str = os.environ.get('TIMEBILL_PROJECT_DETECTION', '')
        if not custom_patterns_str:
            return

        # Format: "pattern1:ProjectName1,pattern2:ProjectName2"
        pattern_pairs = custom_patterns_str.split(',')
        for pair in pattern_pairs:
            pair = pair.strip()
            if not pair or ':' not in pair:
                continue

            pattern_str, project_name = pair.split(':', 1)
            pattern_str = pattern_str.strip()
            project_name = project_name.strip()

            if pattern_str and project_name:
                try:
                    # Add custom pattern at the beginning (higher priority)
                    self.patterns.insert(0, (re.compile(pattern_str, re.IGNORECASE), project_name))
                except re.error:
                    # Skip invalid regex patterns
                    continue

    def detect_from_title(self, title: str) -> str:
        """
        Detect project name from window title.

        Args:
            title: Window title string

        Returns:
            Project name string (never empty, defaults to "Unknown Project")
        """
        if not title or not isinstance(title, str):
            return "Unknown Project"

        title = title.strip()
        if not title:
            return "Unknown Project"

        # Try to match against all patterns
        for pattern, project_template in self.patterns:
            match = pattern.search(title)
            if match:
                # If template contains group references, substitute them
                if '\\' in project_template and match.groups():
                    try:
                        project_name = pattern.sub(project_template, title)
                        # Extract just the substituted part if possible
                        if project_template.startswith(r"GitHub: \1"):
                            return f"GitHub: {match.group(1)}"
                        elif project_template.startswith(r"GitLab: \1"):
                            return f"GitLab: {match.group(1)}"
                        return project_name
                    except:
                        return project_template
                else:
                    return project_template

        # If no pattern matches, create a project name from the title
        # Take the first few meaningful words
        words = title.split()
        if words:
            # Take up to first 3 words, or until we hit common separators
            meaningful_words = []
            for word in words[:5]:
                if word in ['-', '|', '—', '–', ':', '•']:
                    break
                meaningful_words.append(word)

            if meaningful_words:
                project_name = ' '.join(meaningful_words[:3])
                return project_name if len(project_name) <= 50 else project_name[:47] + "..."

        return "Unknown Project"
