from __future__ import annotations

from datetime import date

from app.human_learning import mask_sensitive_values, save_learned_recipe, load_learned_recipe, recipe_path


def test_mask_sensitive_values_redacts_password_like_fields() -> None:
    assert mask_sensitive_values("secret-value", "password") == "[REDACTED]"
    assert mask_sensitive_values("normal", "customer") == "normal"


def test_save_and_load_learned_recipe_roundtrip() -> None:
    report = "unit_test_recipe"
    path = recipe_path(report)
    if path.exists():
        path.unlink()
    recipe = {
        "report": report,
        "report_name": "Unit Test",
        "learned_at": "2026-06-17T00:00:00",
        "steps": [
            {
                "action": "fill",
                "selector": "#start_date_dh",
                "value_template": "{date_from_ddmmyyyy}",
                "candidates": {"css": "#start_date_dh", "id": "start_date_dh"},
            }
        ],
    }

    save_learned_recipe(report, recipe)
    loaded = load_learned_recipe(report)

    assert loaded is not None
    assert loaded["report"] == report
    assert loaded["steps"][0]["value_template"] == "{date_from_ddmmyyyy}"
    path.unlink()
