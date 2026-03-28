"""Tests for project detection from window titles."""

import os
import pytest
from timebill.agent.detection import ProjectDetector


class TestProjectDetector:
    """Test suite for ProjectDetector class."""

    def test_vim_detection(self):
        """Test detection of Vim editor."""
        detector = ProjectDetector()

        assert detector.detect_from_title("vim - project.py") == "Vim Editing"
        assert detector.detect_from_title("Vim - main.py") == "Vim Editing"
        assert detector.detect_from_title("neovim config.lua") == "Vim Editing"
        assert detector.detect_from_title("nvim - test.txt") == "Vim Editing"

    def test_vscode_detection(self):
        """Test detection of VS Code."""
        detector = ProjectDetector()

        assert detector.detect_from_title("Visual Studio Code - main.py") == "VS Code Development"
        assert detector.detect_from_title("VS Code - project/") == "VS Code Development"
        assert detector.detect_from_title("VSCode editor") == "VS Code Development"

    def test_terminal_detection(self):
        """Test detection of terminal applications."""
        detector = ProjectDetector()

        assert detector.detect_from_title("Terminal - bash") == "Terminal Activity"
        assert detector.detect_from_title("zsh shell") == "Terminal Activity"
        assert detector.detect_from_title("PowerShell 7") == "Terminal Activity"

    def test_github_detection(self):
        """Test detection and extraction of GitHub repository names."""
        detector = ProjectDetector()

        result1 = detector.detect_from_title("GitHub - acme/api")
        assert "acme/api" in result1
        assert "GitHub" in result1

        result2 = detector.detect_from_title("github.com/user/repo - Pull Request")
        assert "user/repo" in result2

        result3 = detector.detect_from_title("GitHub: company/frontend-app")
        assert "company/frontend-app" in result3

    def test_browser_detection(self):
        """Test detection of browser applications."""
        detector = ProjectDetector()

        assert detector.detect_from_title("Google Chrome - New Tab") == "Chrome Browsing"
        assert detector.detect_from_title("Firefox Browser") == "Firefox Browsing"
        assert detector.detect_from_title("Safari - Apple") == "Safari Browsing"

    def test_empty_and_none_inputs(self):
        """Test handling of empty and None inputs."""
        detector = ProjectDetector()

        assert detector.detect_from_title("") == "Unknown Project"
        assert detector.detect_from_title("   ") == "Unknown Project"
        assert detector.detect_from_title(None) == "Unknown Project"

    def test_unknown_application(self):
        """Test fallback for unknown applications."""
        detector = ProjectDetector()

        # Should return a reasonable project name or "Unknown Project"
        result = detector.detect_from_title("Some Random App Window")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_custom_patterns_from_env(self):
        """Test loading custom patterns from environment variable."""
        # Set custom pattern
        os.environ['TIMEBILL_PROJECT_DETECTION'] = 'myapp:My Custom App,testapp:Test Application'

        detector = ProjectDetector()

        assert detector.detect_from_title("myapp - window") == "My Custom App"
        assert detector.detect_from_title("This is testapp running") == "Test Application"

        # Clean up
        del os.environ['TIMEBILL_PROJECT_DETECTION']

    def test_pattern_priority(self):
        """Test that custom patterns have priority over built-in ones."""
        # Override vim detection
        os.environ['TIMEBILL_PROJECT_DETECTION'] = 'vim:Custom Vim Project'

        detector = ProjectDetector()

        assert detector.detect_from_title("vim - test.py") == "Custom Vim Project"

        # Clean up
        del os.environ['TIMEBILL_PROJECT_DETECTION']

    def test_invalid_custom_patterns(self):
        """Test that invalid custom patterns are handled gracefully."""
        # Invalid format (no colon, invalid regex)
        os.environ['TIMEBILL_PROJECT_DETECTION'] = 'invalid,[unclosed:Project'

        # Should not crash
        detector = ProjectDetector()
        assert detector.detect_from_title("vim - test.py") == "Vim Editing"

        # Clean up
        del os.environ['TIMEBILL_PROJECT_DETECTION']

    def test_ide_detection(self):
        """Test detection of various IDEs."""
        detector = ProjectDetector()

        assert detector.detect_from_title("PyCharm - project.py") == "PyCharm Development"
        assert detector.detect_from_title("IntelliJ IDEA - Main.java") == "IntelliJ Development"
        assert detector.detect_from_title("Eclipse IDE") == "Eclipse Development"
        assert detector.detect_from_title("Sublime Text 4") == "Sublime Text Editing"

    def test_communication_apps(self):
        """Test detection of communication applications."""
        detector = ProjectDetector()

        assert detector.detect_from_title("Slack - team-channel") == "Slack Communication"
        assert detector.detect_from_title("Discord - Server Name") == "Discord Communication"
        assert detector.detect_from_title("Zoom Meeting") == "Zoom Meeting"

    def test_long_title_truncation(self):
        """Test that very long titles are handled properly."""
        detector = ProjectDetector()

        long_title = "This is a very long window title " * 10
        result = detector.detect_from_title(long_title)

        assert isinstance(result, str)
        assert len(result) > 0
        # Should either match a pattern or truncate reasonably
        assert len(result) <= 100

    def test_special_characters_in_title(self):
        """Test handling of special characters in window titles."""
        detector = ProjectDetector()

        # Should not crash on special characters
        titles = [
            "vim - file.py | /home/user",
            "VS Code — project · main.py",
            "Terminal: bash – ~/projects",
            "GitHub • user/repo",
        ]

        for title in titles:
            result = detector.detect_from_title(title)
            assert isinstance(result, str)
            assert len(result) > 0


class TestDataModels:
    """Test suite for data models."""

    def test_project_creation(self):
        """Test Project model creation."""
        from timebill.data.models import Project

        p = Project(name="Test Project")
        assert p.name == "Test Project"
        assert p.description is None
        assert p.color is None

    def test_project_with_all_fields(self):
        """Test Project model with all fields."""
        from timebill.data.models import Project

        p = Project(
            name="My Project",
            description="A test project",
            color="#FF5733"
        )
        assert p.name == "My Project"
        assert p.description == "A test project"
        assert p.color == "#FF5733"

    def test_time_entry_creation(self):
        """Test TimeEntry model creation."""
        from timebill.data.models import TimeEntry

        entry = TimeEntry(
            project_name="Test",
            start_ts=1000000,
            end_ts=2000000,
            duration_ms=1000000
        )
        assert entry.project_name == "Test"
        assert entry.start_ts == 1000000
        assert entry.end_ts == 2000000
        assert entry.duration_ms == 1000000

    def test_time_entry_with_metadata(self):
        """Test TimeEntry model with metadata."""
        from timebill.data.models import TimeEntry

        entry = TimeEntry(
            project_name="Test",
            start_ts=1000000,
            metadata={"window": "vim", "file": "main.py"}
        )
        assert entry.metadata["window"] == "vim"
        assert entry.metadata["file"] == "main.py"
