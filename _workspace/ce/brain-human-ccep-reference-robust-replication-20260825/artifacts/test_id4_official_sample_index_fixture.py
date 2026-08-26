import hashlib
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("fixture", HERE / "id4_official_sample_index_fixture.py")
fixture = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(fixture)


def test_official_paths_are_frozen_and_cross_subject_safe():
    paths = fixture._paths()
    assert set(paths) == {"tmet", "tidx", "tdat"}
    assert all(path.startswith("sub-1/ses-ieeg01/ieeg/sub-1_ses-ieeg01_task-ccep_run-01_ieeg.mefd/LV1.timd/")
               for path in paths.values())
    assert all(path.endswith("." + extension) for extension, path in paths.items())
    assert fixture._sha(b"known") == hashlib.sha256(b"known").hexdigest()


def test_receipt_schema_preserves_both_full_toc_rows():
    source = (HERE / "id4_official_sample_index_fixture.py").read_text(encoding="utf-8")
    assert '"first_toc_row": first' in source
    assert '"second_toc_row": second' in source
