from pathlib import Path

from bookfriend.utils import session_utils

TEST_PATH = "test_session.json"

def test_save_and_load_session():
    data ={"food":"bar", "count": 124}
    session_utils.save_session(data, TEST_PATH)

    assert Path(TEST_PATH).exists()    #old school way os.path.exists(TEST_PATH)

    loaded = session_utils.load_session(TEST_PATH)

    assert loaded == data

    Path(TEST_PATH).unlink()



