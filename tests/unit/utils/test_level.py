import builtins
from unittest.mock import patch

from waveredact.utils.level import Levels, LevelSetter

class TestLevels:
    def test_levels_labels_hierarchy(self):
        base_labels = Levels.BASE.labels
        medium_labels = Levels.MEDIUM.labels
        total_labels = Levels.TOTAL.labels

        assert len(base_labels) > 0
        assert len(medium_labels) > len(base_labels)
        assert len(total_labels) > len(medium_labels)

        assert set(base_labels).issubset(set(medium_labels))
        assert set(medium_labels).issubset(set(total_labels))

class TestLevelSetter:
    def test_level_setter_non_interactive_base(self):
        setter = LevelSetter(interactive=False, level_name="base")
        assert setter.level == Levels.BASE
        assert setter.target_labels == Levels.BASE.labels

    def test_level_setter_non_interactive_medium(self):
        setter = LevelSetter(interactive=False, level_name="MeDiUm")
        assert setter.level == Levels.MEDIUM
        assert setter.target_labels == Levels.MEDIUM.labels

    def test_level_setter_non_interactive_total(self):
        setter = LevelSetter(interactive=False, level_name="total")
        assert setter.level == Levels.TOTAL
        assert setter.target_labels == Levels.TOTAL.labels
        
    def test_level_setter_non_interactive_fallback(self):
        setter = LevelSetter(interactive=False, level_name="unknown")
        assert setter.level == Levels.TOTAL

    @patch("builtins.input", side_effect=["1"])
    def test_level_setter_interactive_base(self, mock_input):
        setter = LevelSetter(interactive=True)
        assert setter.level == Levels.BASE

    @patch("builtins.input", side_effect=["2"])
    def test_level_setter_interactive_medium(self, mock_input):
        setter = LevelSetter(interactive=True)
        assert setter.level == Levels.MEDIUM

    @patch("builtins.input", side_effect=["invalid", "3"])
    @patch("builtins.print")
    def test_level_setter_interactive_retry(self, mock_print, mock_input):
        setter = LevelSetter(interactive=True)
        assert setter.level == Levels.TOTAL
        mock_print.assert_called_once_with("Invalid input. Please enter 1,2 or 3")
