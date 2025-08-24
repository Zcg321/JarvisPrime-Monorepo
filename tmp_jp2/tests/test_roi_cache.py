from pathlib import Path
import time
from src.tools import roi_cache, dfs


def test_roi_cache_invalidation(tmp_path, monkeypatch):
    log = tmp_path / "roi.jsonl"
    log.write_text('{"player_id":"P1","roi":0.1}\n')
    monkeypatch.setattr(dfs, "ROI_LOG", log)
    data1 = roi_cache.load_ema(30, 0.5)
    data2 = roi_cache.load_ema(30, 0.5)
    assert data1 is data2
    time.sleep(0.01)
    log.write_text('{"player_id":"P1","roi":0.2}\n')
    data3 = roi_cache.load_ema(30, 0.5)
    assert data3 != data2
    roi_cache._invalidate()
    assert roi_cache._CACHE is None
