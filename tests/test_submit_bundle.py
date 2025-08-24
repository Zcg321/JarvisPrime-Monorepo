import tarfile
import hashlib
import json
from scripts import submit_bundle


def test_submit_bundle(tmp_path, monkeypatch):
    export = tmp_path / "exp.csv"
    export.write_text("PG,SG,SF,PF,C,G,F,UTIL\n")
    sim = tmp_path / "sim.json"
    sim.write_text("{}")
    monkeypatch.chdir(tmp_path)
    bundle = submit_bundle.submit(str(export), str(sim))
    assert bundle.exists()
    with tarfile.open(bundle, "r:gz") as tar:
        names = tar.getnames()
        assert "exp.csv" in names and "sim.json" in names and "MANIFEST.json" in names
        man = json.loads(tar.extractfile("MANIFEST.json").read().decode())
        assert set(man["export"].keys()) == {"generated_by", "slate_id", "sha256", "count"}
    sha = hashlib.sha256(bundle.read_bytes()).hexdigest()
    sums = (bundle.parent / "SHA256SUMS").read_text()
    assert sha in sums
