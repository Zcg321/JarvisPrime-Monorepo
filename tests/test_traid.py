import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.tools import traid
import math

def test_zscore():
    data = [10, 10, 10, 20]
    z = traid.zscore(data)
    assert math.isclose(z, 1.7320508075688772, rel_tol=1e-3)
