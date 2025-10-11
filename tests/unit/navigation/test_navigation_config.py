from __future__ import annotations

from domains.product.navigation import config


def test_mode_config_defaults():
    cfg = config.ModeConfig(
        name="custom",
        providers=("a", "b"),
        k_base=10,
        temperature=0.2,
        epsilon=0.1,
        author_threshold=1,
        tag_threshold=2,
        allow_random=True,
        curated_boost=0.9,
    )

    assert cfg.name == "custom"
    assert cfg.providers == ("a", "b")
    assert cfg.allow_random is True
    assert cfg.curated_boost == 0.9


def test_default_configs_expose_expected_modes():
    normal_cfg = config.DEFAULT_MODE_CONFIGS["normal"]
    assert normal_cfg.name == "normal"
    assert "curated" in normal_cfg.providers
    assert normal_cfg.allow_random is True

    lite_cfg = config.DEFAULT_MODE_CONFIGS["lite"]
    assert lite_cfg.allow_random is False
    assert lite_cfg.k_base < normal_cfg.k_base


def test_all_exports_match():
    exported = set(config.__all__)
    assert {
        "ModeConfig",
        "DEFAULT_BASE_WEIGHTS",
        "DEFAULT_BADGES_BY_PROVIDER",
        "DEFAULT_MODE_CONFIGS",
    } <= exported
