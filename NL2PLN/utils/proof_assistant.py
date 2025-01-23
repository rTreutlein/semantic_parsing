from sammo import Component, Data, Operator, Set, Text, Type, Runner, Result
from frozendict import frozendict
from sammo.base import Template
from sammo.components import Output, GenerateText, ForEach, Union
from sammo.extractors import ExtractRegex
from pydantic import BaseModel
import json

class ProofAssistant:
    """Assists in analyzing and fixing failed logical proofs using SAMMO components."""
    
    def __init__(self, llm_runner: Runner):
        """
        Args:
            llm_runner: SAMMO runner instance for executing language model operations
        """
        self.analyze_failure = self._build_analysis_pipeline(llm_runner)

    class Outputs(BaseModel):
        """Structured output type for proof analysis results using Pydantic."""
        action: str
        premise_index: int | None = None
        fixed_pln: str | None = None
        statement1: str | None = None
        statement2: str | None = None
        combination_rule: str | None = None

        @classmethod
        def get_json_schema(cls):
            """Get JSON schema for the output structure."""
            return cls.model_json_schema()

    @staticmethod
    def _build_analysis_pipeline(runner: Runner) -> Operator:
        """Build SAMMO pipeline for proof failure analysis.
        
        Returns:
            Operator: Configured SAMMO pipeline for proof analysis
        """
        analysis_prompt = Template("""
            Analyze this failed proof attempt and suggest the most appropriate fix:
            
            ### Premises (English)
            {{premises_english | join('\n')}}
            
            ### Premises (PLN)
            {{premises_pln | join('\n')}}
            
            ### Conclusion (English)
            {{conclusion_english}}
            
            ### Conclusion (PLN)
            {{conclusion_pln}}
            
            ### Existing Proof Steps
            {{existing_proof_steps | join('\n')}}
            
            ### Instructions
            1. Identify the root cause of the failure
            2. Suggest exactly ONE of these fixes:
               - "fix_premise": Provide index and corrected PLN
               - "combine_statements": Identify two statements to combine
            3. Output as JSON with ONLY these keys: 
               action, premise_index, fixed_pln, statement1, statement2, combination_rule
        """)
        
        return (
            Output(
                ParseSuggestion(
                    GenerateText(
                        analysis_prompt,
                        json_mode=ProofAssistant.Outputs.get_json_schema()
                    )
                )
            )
            .with_expected_output(Set(ProofAssistant.Outputs))
            .build(runner)
        )

class ParseSuggestion(Component):
    """Component to parse and validate proof analysis suggestions."""
    
    async def _call(self, runner: Runner, context: dict, dynamic_context: frozendict | None) -> Result:
        raw_output = await self._child(runner, context, dynamic_context)
        
        try:
            parsed = ProofAssistant.Outputs.model_validate_json(raw_output.value[0])
            return Result([parsed.model_dump()], parent=raw_output, op=self)
        except Exception as e:
            # Fallback to empty result
            empty_result = {
                key: None for key in [
                    "action", "premise_index", "fixed_pln",
                    "statement1", "statement2", "combination_rule"
                ]
            }
            return Result([empty_result], parent=raw_output, op=self)

def main():
    """Simple test of ProofAssistant functionality"""
    from sammo import Runner, Data
    
    # Initialize with Claude model using SAMMO
    lm = Runner('anthropic/claude-3-5-sonnet-20241022')
    assistant = ProofAssistant(lm)
    
    # Create simple test case
    test_data = Data.from_dict({
        "premises_english": ["All birds can fly", "Penguins are birds"],
        "premises_pln": ["(ForAll $x (Implication (Bird $x) (CanFly $x)))", 
                        "(ForAll $x (Implication (Penguin $x) (Bird $x)))"],
        "conclusion_english": "Penguins can fly",
        "conclusion_pln": ["(ForAll $x (Implication (Penguin $x) (CanFly $x)))"],
        "existing_proof_steps": []
    })
    
    # Run analysis
    print("Running Proof Assistant test...")
    result = assistant.analyze_failure(test_data)
    print("\nProof Assistant Analysis Result:")
    print(result)

if __name__ == "__main__":
    main()
