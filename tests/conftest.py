"""느린 테스트 표시(D23). 2코어에서 파일 하나가 50 s를 넘는 것들이다.

    python -m pytest -m "not slow"   빠른 검사(1–2분)
    python -m pytest                 전체
"""

import pytest

SLOW = {"test_c1_common.py", "test_c3_record_relocation.py", "test_c3_surprise_gain.py", "test_c8_selection.py",
        "test_rejudge.py", "test_ring.py"}


def pytest_collection_modifyitems(items):
    for item in items:
        if item.path.name in SLOW:
            item.add_marker(pytest.mark.slow)
