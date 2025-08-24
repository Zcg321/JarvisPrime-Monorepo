import importlib

gr = importlib.import_module("src.tools.ghost_roi")


def test_half_life_math():
    assert round(gr.half_life_to_alpha(45), 6) == round(1 - 0.5 ** (1 / 45), 6)


def test_decay_alpha_from_config():
    alpha = gr.decay_alpha("nba", "classic")
    assert round(alpha, 6) == round(gr.half_life_to_alpha(45), 6)
