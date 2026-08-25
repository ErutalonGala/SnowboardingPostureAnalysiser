import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest

# The geometry tests do not need native MediaPipe/OpenCV binaries.  Supplying
# lightweight modules keeps this compatibility test runnable in CI as well.
sys.modules.setdefault("cv2", SimpleNamespace())
sys.modules.setdefault("mediapipe", SimpleNamespace(__version__="test"))

from snowcoach import pose_engine


def test_load_solutions_uses_public_export():
    solutions = object()

    with patch.object(pose_engine.mp, "solutions", solutions, create=True):
        assert pose_engine._load_solutions() is solutions


def test_load_solutions_falls_back_to_internal_package():
    solutions = object()

    with (
        patch.object(pose_engine.mp, "solutions", None, create=True),
        patch.object(pose_engine.importlib, "import_module", return_value=solutions) as importer,
    ):
        assert pose_engine._load_solutions() is solutions

    importer.assert_called_once_with("mediapipe.python.solutions")


def test_load_solutions_reports_incompatible_version():
    with (
        patch.object(pose_engine.mp, "solutions", None, create=True),
        patch.object(pose_engine.mp, "__version__", "0.10.35", create=True),
        patch.object(pose_engine.importlib, "import_module", side_effect=ModuleNotFoundError),
        pytest.raises(RuntimeError, match=r"mediapipe 0\.10\.35.*requirements\.txt"),
    ):
        pose_engine._load_solutions()
