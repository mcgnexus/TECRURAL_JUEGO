from pathlib import Path


def test_pilot_entry_uses_municipality_and_comparison_api():
    base = Path(__file__).resolve().parents[1] / 'apps/web/src'
    entry = (base / 'main.tsx').read_text(encoding='utf-8')
    view = (base / 'PilotApp.tsx').read_text(encoding='utf-8')
    assert 'PilotApp' in entry
    assert '/pilot/municipios' in view and '/pilot/comparar' in view
    assert 'ni una recomendación profesional' in view.lower()
