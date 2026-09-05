"""공개 SGSG 배포본을 실행하지 않고 무결성과 입력 계약을 확인한다."""
import ast
import hashlib
import json
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
archive = ROOT / "data/external/sgsg_v1/local_connectivity_model-v1.0.0.zip"
raw = archive.read_bytes()
assert len(raw) == 2119453
assert hashlib.md5(raw).hexdigest() == "d5088419d70fd3f0804177b57408ffb0"
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    names = z.namelist()
    prefix = "MWolfR-local_connectivity_model-b9f18bb/"
    sources = [n for n in names if n.endswith(".py")]
    for n in sources:
        ast.parse(z.read(n).decode("utf-8"), filename=n)
    config = json.loads(z.read(prefix + "configs/pnagm_L23E_microns_yscale_experimental_v1p5.json"))
    result = {
        "source": "https://doi.org/10.5281/zenodo.20055048",
        "archive_sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw), "server_md5_match": True, "zip_crc_pass": True,
        "parsed_python_files": sources, "l23_config": config,
        "requirements": z.read(prefix + "src/requirements.txt").decode().splitlines(),
        "member_sha256": {n: hashlib.sha256(z.read(n)).hexdigest() for n in names if not n.endswith("/")},
        "model_executed": False,
        "gate": "SOURCE_INSPECTED_NOT_BIOLOGICAL_VALIDATION",
        "next_gate": "Define adaptation to v1718 population and a calibration/assessment split before model comparison; published v1181 parameters are not independent validation.",
    }
out = HERE / "sgsg_source_inspection.json"
out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"parsed": len(sources), "crc": True, "model_executed": False}))
