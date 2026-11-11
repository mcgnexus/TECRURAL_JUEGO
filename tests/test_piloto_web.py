from pathlib import Path


def test_pilot_entry_uses_municipality_and_comparison_api():
    base = Path(__file__).resolve().parents[1] / 'apps/web/src'
    entry = (base / 'main.tsx').read_text(encoding='utf-8')
    view = (base / 'PilotApp.tsx').read_text(encoding='utf-8')
    assert 'PilotApp' in entry
    assert '/pilot/municipios' in view and '/pilot/comparar' in view
    assert 'ni una recomendación profesional' in view.lower()


def test_soil_cross_section_is_integrated_and_disclaims_measured_roots():
    base = Path(__file__).resolve().parents[1] / 'apps/web/src'
    view = (base / 'PilotApp.tsx').read_text(encoding='utf-8')
    assert '<SoilCrossSection' in view
    diagram = (base / 'SoilCrossSection.tsx').read_text(encoding='utf-8')
    assert 'distribución del agua por profundidad' in diagram
    assert 'result.escenarios' in diagram
    assert 'result.suelo.capacity_mm' in diagram
