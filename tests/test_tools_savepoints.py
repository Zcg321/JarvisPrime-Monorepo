from src.tools import savepoints
import src.tools.savepoint as sp

def test_save_and_list(tmp_path, monkeypatch):
    monkeypatch.setattr(sp, 'SAVE_DIR', tmp_path)
    path = savepoints.save('moment')
    assert path
    lst = savepoints.list_last(1)
    assert lst and lst[0]['moment'] == 'moment'
