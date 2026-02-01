from pathlib import Path

from bookfriend.utils import session_utils

TEST_PATH = "test_session.json"



def test_reset_session_removes_file(tmp_path):
    # Arrange: create a fake session file
    test_file = tmp_path / "session.json"
    test_file.write_text('{"foo": "bar"}', encoding="utf-8")
    assert test_file.exists()

    # Act: reset_session should delete it
    session_utils.reset_session(test_file)

    # Assert: file should not exist anymore
    assert not test_file.exists()

