import pytest
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
from bridge.policy import validate_plan
from duet.duet_foreman import FileSpec


def test_policy_denied_path():
    fs = [FileSpec(path='scripts/backup.sh', op='write', encoding='utf-8')]
    with pytest.raises(ValueError):
        validate_plan(fs, 'YOURORG/alchohalt')


def test_policy_max_files():
    fs = [FileSpec(path=f'apps/alchohalt/{i}.txt', op='write', encoding='utf-8') for i in range(21)]
    with pytest.raises(ValueError):
        validate_plan(fs, 'YOURORG/alchohalt')


def test_policy_allow_pass():
    fs = [FileSpec(path='apps/alchohalt/x.txt', op='write', encoding='utf-8')]
    validate_plan(fs, 'YOURORG/alchohalt')
