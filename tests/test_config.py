import pytest

from cartosynth.config import REPO_ROOT, deep_merge, load_config, run_dirs


def test_default_config_is_valid():
    cfg = load_config()
    assert cfg["num_maps"] > 0 and cfg["fonts"]["styles"]


def test_3la_config_overrides_defaults():
    cfg = load_config(f"{REPO_ROOT}/config/3la.yaml")
    assert cfg["annotation"]["vocabulary"] == "voc148"
    assert cfg["numbers"]["share"] == 0.4
    assert cfg["placement"]["canvas_buffer"] == 10          # inherited from default.yaml
    assert run_dirs(cfg).root.endswith("output/3la")


def test_cli_style_overrides():
    cfg = load_config(overrides={"num_maps": 3, "run_name": "x"})
    assert cfg["num_maps"] == 3 and cfg["run_name"] == "x"


def test_deep_merge_keeps_siblings():
    assert deep_merge({"a": {"b": 1, "c": 2}}, {"a": {"b": 3}}) == {"a": {"b": 3, "c": 2}}


def test_invalid_config_is_rejected():
    with pytest.raises(ValueError, match="digits"):
        load_config(overrides={"numbers": {"share": 0.5},
                               "fonts": {"styles": [{"family": "X", "size": [10, 20], "letters": True,
                                                     "digits": False, "fallback": True}]}})
