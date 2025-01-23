from sammo import Component, Data, Operator, Set, Text, Type, Runner
from sammo.base import Template
import json

class ProofAssistant:
    def __init__(self, llm_runner: Runner):
        self.analyze_failure = _build_analysis_pipeline(llm_runner)

    class Outputs(Type):
        action: str
        premise_index: int | None
        fixed_pln: str | None
        statement1: str | None
        statement2: str | None
        combination_rule: str | None

def _build_analysis_pipeline(runner: Runner) -> Operator:
    return (
        Component(
            "AnalyzeProofFailure",
            Template("""
            Given this failed proof attempt:
            Premises (English): {{premises_english}}
            Premises (PLN): {{premises_pln}}
            Conclusion (English): {{conclusion_english}} 
            Conclusion (PLN): {{conclusion_pln}}
            Existing Proof Steps: {{existing_proof_steps}}
            
            Suggest exactly ONE of these fixes:
            1. "fix_premise" with index and corrected PLN
            2. "combine_statements" with two statements and combination rule
            3. "human_intervention" if no clear fix
            
            Output as JSON with ONLY these keys: 
            action, premise_index, fixed_pln, statement1, statement2, combination_rule
            """)
        )
        .as_function()
        .with_expected_output(Set(ProofAssistant.Outputs))
        .build(runner)
    )

def _parse_suggestion(raw_output: str) -> dict:
    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        # Fallback to text parsing
        return {
            key: None for key in [
                "action", "premise_index", "fixed_pln",
                "statement1", "statement2", "combination_rule"
            ]
        }
