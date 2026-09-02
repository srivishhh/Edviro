from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

with (ROOT / 'scenarios.json').open('r', encoding='utf-8') as fh:
    SCENARIOS = json.load(fh)

with (ROOT / 'expected_outputs.json').open('r', encoding='utf-8') as fh:
    EXPECTED = json.load(fh)


def evaluate_response(scenario: str, response: dict) -> dict:
    scenario_data = SCENARIOS[scenario]
    expected = EXPECTED[scenario]
    root_cause = (response.get('root_cause') or '').lower()
    evidence = response.get('evidence') or []
    evidence_text = ' '.join(str(item).lower() for item in evidence)
    recommendation = (response.get('recommended_action') or response.get('recommendation') or '').lower()

    score = {
        'root_cause_accuracy': 1 if expected['root_cause'] in root_cause else 0,
        'evidence_grounding': 1 if all(item in evidence_text for item in expected['evidence']) else 0,
        'recommendation_quality': 1 if expected['recommendation'].lower() in recommendation or recommendation else 0,
        'hallucination_rate': 0,
    }
    score['total'] = sum(score.values()) - score['hallucination_rate']
    return score


def list_scenarios() -> list[str]:
    return sorted(SCENARIOS)
