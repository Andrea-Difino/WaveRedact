import builtins
from unittest.mock import patch

from waveredact.config.level import Levels, LevelSetter

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

    @patch("waveredact.config.level.questionary.select")
    def test_level_setter_interactive_base(self, mock_select):
        mock_select.return_value.ask.return_value = Levels.BASE
        setter = LevelSetter(interactive=True)
        assert setter.level == Levels.BASE

    @patch("waveredact.config.level.questionary.select")
    def test_level_setter_interactive_medium(self, mock_select):
        mock_select.return_value.ask.return_value = Levels.MEDIUM
        setter = LevelSetter(interactive=True)
        assert setter.level == Levels.MEDIUM
