"""Tests for project detection module."""

import pytest
from agent.detection import ProjectDetector


class TestProjectDetector:
    """Test suite for ProjectDetector class."""

    def test_init_without_custom_patterns(self):
        """Test initialization without custom patterns."""
        detector = ProjectDetector()
        assert detector.custom_patterns == {}

    def test_init_with_custom_patterns(self):
        """Test initialization with custom patterns."""
        patterns = {'myapp': ['myapp', 'MyApp']}
        detector = ProjectDetector(patterns)
        assert detector.custom_patterns == patterns

    def test_detect_project_empty_title(self):
        """Test detection with empty window title."""
        detector = ProjectDetector()
        assert detector.detect_project('') is None
        assert detector.detect_project(None) is None

    # VIM pattern tests
    def test_detect_vim_simple_path(self):
        """Test detection from vim with simple project path."""
        detector = ProjectDetector()
        result = detector.detect_project('vim - myproject/main.py')
        assert result == 'myproject'

    def test_detect_vim_full_path(self):
        """Test detection from vim with full path."""
        detector = ProjectDetector()
        result = detector.detect_project('vim /home/user/projects/webapp/index.html')
        assert result == 'webapp'

    def test_detect_vim_nested_path(self):
        """Test detection from vim with nested path."""
        detector = ProjectDetector()
        result = detector.detect_project('vim - /var/www/ecommerce/src/app.py')
        assert result == 'ecommerce'

    # VSCode pattern tests
    def test_detect_vscode_simple(self):
        """Test detection from VSCode."""
        detector = ProjectDetector()
        result = detector.detect_project('Visual Studio Code - myproject/src/main.js')
        assert result == 'myproject'

    def test_detect_vscode_abbreviated(self):
        """Test detection from VSCode abbreviated name."""
        detector = ProjectDetector()
        result = detector.detect_project('VSCode - /home/dev/api/server.py')
        assert result == 'api'

    # IntelliJ pattern tests
    def test_detect_intellij_project_name(self):
        """Test detection from IntelliJ with project name in brackets."""
        detector = ProjectDetector()
        result = detector.detect_project('IntelliJ IDEA - [my-awesome-project]')
        assert result == 'my-awesome-project'

    def test_detect_pycharm_project(self):
        """Test detection from PyCharm."""
        detector = ProjectDetector()
        result = detector.detect_project('PyCharm - [data-pipeline]')
        assert result == 'data-pipeline'

    # GitHub pattern tests
    def test_detect_github_org_repo(self):
        """Test detection from GitHub with org/repo pattern."""
        detector = ProjectDetector()
        result = detector.detect_project('GitHub - acme/api')
        assert result == 'api'

    def test_detect_github_url_pattern(self):
        """Test detection from GitHub URL pattern."""
        detector = ProjectDetector()
        result = detector.detect_project('github.com/myorg/myrepo - Pull Request')
        assert result == 'myrepo'

    def test_detect_github_case_insensitive(self):
        """Test GitHub detection is case insensitive."""
        detector = ProjectDetector()
        result = detector.detect_project('GITHUB - testorg/testapp')
        assert result == 'testapp'

    # GitLab pattern tests
    def test_detect_gitlab_repo(self):
        """Test detection from GitLab."""
        detector = ProjectDetector()
        result = detector.detect_project('GitLab - company/backend')
        assert result == 'backend'

    def test_detect_gitlab_url(self):
        """Test detection from GitLab URL."""
        detector = ProjectDetector()
        result = detector.detect_project('gitlab.com/team/frontend - Merge Request')
        assert result == 'frontend'

    # Bitbucket pattern tests
    def test_detect_bitbucket_repo(self):
        """Test detection from Bitbucket."""
        detector = ProjectDetector()
        result = detector.detect_project('Bitbucket - startup/mobile-app')
        assert result == 'mobile-app'

    # Custom pattern tests
    def test_custom_pattern_simple_string_match(self):
        """Test custom pattern with simple string matching."""
        detector = ProjectDetector({'myapp': ['myapp', 'MyApp']})
        result = detector.detect_project('MyApp - editor')
        assert result == 'myapp'

    def test_custom_pattern_case_insensitive(self):
        """Test custom pattern matching is case insensitive."""
        detector = ProjectDetector({'myapp': ['myapp']})
        result = detector.detect_project('MYAPP - Something')
        assert result == 'myapp'

    def test_custom_pattern_regex(self):
        """Test custom pattern with regex."""
        detector = ProjectDetector({'webapp': [r'web.*app', 'WebApplication']})
        result = detector.detect_project('My WebApp Interface')
        assert result == 'webapp'

    def test_custom_pattern_multiple_patterns(self):
        """Test custom pattern with multiple pattern strings."""
        detector = ProjectDetector({
            'project-a': ['proj-a', 'project-a'],
            'project-b': ['proj-b', 'project-b']
        })
        result = detector.detect_project('Working on proj-a files')
        assert result == 'project-a'

    def test_custom_pattern_priority_over_default(self):
        """Test that custom patterns take priority over default patterns."""
        detector = ProjectDetector({'custom-project': ['github']})
        result = detector.detect_project('github.com/org/repo')
        assert result == 'custom-project'

    # Edge cases
    def test_no_match_returns_none(self):
        """Test that no match returns None."""
        detector = ProjectDetector()
        result = detector.detect_project('Random Window Title Without Project Info')
        assert result is None

    def test_multiple_slashes_in_path(self):
        """Test handling of multiple slashes in paths."""
        detector = ProjectDetector()
        result = detector.detect_project('vim - /home/user/projects/my-project/src/main.py')
        assert result == 'my-project'

    def test_special_characters_in_project_name(self):
        """Test project names with special characters."""
        detector = ProjectDetector()
        result = detector.detect_project('IntelliJ IDEA - [my_project-v2]')
        assert result == 'my_project-v2'

    def test_whitespace_handling(self):
        """Test handling of various whitespace patterns."""
        detector = ProjectDetector()
        result = detector.detect_project('vim  -  myproject/file.py')
        assert result == 'myproject'

    # Integration tests
    def test_realistic_vim_scenario(self):
        """Test realistic vim window title."""
        detector = ProjectDetector()
        result = detector.detect_project('vim - ~/projects/timebill/agent/detection.py')
        assert result == 'timebill'

    def test_realistic_vscode_scenario(self):
        """Test realistic VSCode window title."""
        detector = ProjectDetector()
        result = detector.detect_project('index.tsx - myapp - Visual Studio Code')
        assert result == 'myapp'

    def test_realistic_github_scenario(self):
        """Test realistic GitHub tab title."""
        detector = ProjectDetector()
        result = detector.detect_project('Pull Request #42 - acme/api-server - GitHub')
        assert result == 'api-server'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
