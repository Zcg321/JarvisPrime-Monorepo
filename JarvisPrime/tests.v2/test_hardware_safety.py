from src.tools.hardware_safety import recommend_config


def test_recommend_config():
    cfg = recommend_config(min_gb=0.0)
    assert "micro_bsz" in cfg and "grad_accum" in cfg
