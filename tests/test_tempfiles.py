from pathlib import Path
from unittest.mock import patch

from snowcoach.tempfiles import remove_temp_file


def test_remove_temp_file_removes_existing_file(tmp_path):
    temporary_file = tmp_path / "video.mp4"
    temporary_file.write_bytes(b"video")

    assert remove_temp_file(temporary_file)
    assert not temporary_file.exists()


def test_remove_temp_file_retries_permission_error():
    path = Path("locked.mp4")

    with (
        patch.object(Path, "unlink", side_effect=[PermissionError, None]) as unlink,
        patch("snowcoach.tempfiles.gc.collect") as collect,
        patch("snowcoach.tempfiles.time.sleep") as sleep,
    ):
        assert remove_temp_file(path, attempts=2, delay=0.1)

    assert unlink.call_count == 2
    collect.assert_called_once_with()
    sleep.assert_called_once_with(0.1)


def test_remove_temp_file_gives_up_without_raising():
    with (
        patch.object(Path, "unlink", side_effect=PermissionError) as unlink,
        patch("snowcoach.tempfiles.gc.collect"),
        patch("snowcoach.tempfiles.time.sleep"),
    ):
        assert not remove_temp_file("locked.mp4", attempts=3, delay=0)

    assert unlink.call_count == 3
