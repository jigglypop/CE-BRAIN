import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pytest

HERE = Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/allen_synphys'
sys.path.insert(0,str(HERE))
spec = importlib.util.spec_from_file_location('vc20hz_source_inputs',HERE/'vc20hz_source_inputs.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture_cache(tmp_path):
    base,overlay = tmp_path/'base',tmp_path/'overlay'
    base.mkdir()
    value = bytes(range(256))*256
    record = dict(bytes=len(value),sha256=hashlib.sha256(value).hexdigest())
    manifest = dict(remote=dict(url='https://example.invalid/test',bytes=2*module.raw.BLOCK,etag='fixed'),
                    block_size=module.raw.BLOCK,blocks={'0':record})
    (base/'000000000000.bin').write_bytes(value)
    (base/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
    return base,overlay,module.sha(base/'manifest.json'),value


def test_offline_reuse_and_missing_block_preserve_base(tmp_path):
    base,overlay,digest,value = fixture_cache(tmp_path)
    with module.LayeredRanges(base,overlay,expected_base_sha=digest) as reader:
        reader.seek(123)
        assert reader.read(37)==value[123:160]
        reader.seek(module.raw.BLOCK)
        with pytest.raises(OSError,match='Offline missing'):
            reader.read(1)
    assert not overlay.exists()
    assert module.sha(base/'manifest.json')==digest


def test_corrupt_block_rejected(tmp_path):
    base,overlay,digest,value = fixture_cache(tmp_path)
    (base/'000000000000.bin').write_bytes(b'bad')
    with module.LayeredRanges(base,overlay,expected_base_sha=digest) as reader:
        with pytest.raises(ValueError,match='Corrupt'):
            reader.read(1)


def test_overlay_version_mismatch_rejected(tmp_path):
    base,overlay,digest,_ = fixture_cache(tmp_path)
    overlay.mkdir()
    (overlay/'manifest.json').write_text('{}',encoding='utf-8')
    with pytest.raises(ValueError,match='identity'):
        module.LayeredRanges(base,overlay,expected_base_sha=digest)


def test_range_validation_precedes_writes(tmp_path,monkeypatch):
    base,overlay,digest,_ = fixture_cache(tmp_path)
    class Response:
        status = 200
        headers = {}
        def __enter__(self): return self
        def __exit__(self,*args): pass
    monkeypatch.setattr(module.urllib.request,'urlopen',lambda *args,**kwargs:Response())
    with module.LayeredRanges(base,overlay,True,digest) as reader:
        reader.remote_verified = True
        with pytest.raises(ValueError,match='ranged'):
            reader.block(module.raw.BLOCK)
    assert not overlay.exists()


def test_command_intervals_keep_negative_test_pulses_and_end_boundary():
    command = np.array([-.07,-.08,-.08,-.07,-.01,-.01,-.07,-.08])
    intervals = module.command_intervals(command,1000)
    assert [(r['start_index'],r['stop_index']) for r in intervals]==[(1,3),(4,6),(7,8)]
    assert intervals[0]['delta_min_V']==pytest.approx(-.01)
    assert intervals[1]['delta_max_V']==pytest.approx(.06)
    assert intervals[-1]['duration_s']==pytest.approx(.001)
