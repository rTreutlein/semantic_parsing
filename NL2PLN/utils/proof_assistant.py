from frozendict import frozendict
from sammo.base import Component, Result, Runner, Template
from sammo.components import GenerateText, Output
from sammo.runners import OpenAIChat
from pydantic import BaseModel
import os

class ProofAnalysisResult(BaseModel):
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


class ParseSuggestion(Component):
    """Component to parse and validate proof analysis suggestions."""
    
    async def _call(self, runner: Runner, context: dict, dynamic_context: frozendict | None) -> Result:
        raw_output = await self._child(runner, context, dynamic_context)
        print(raw_output.value)
        parsed = ProofAnalysisResult.model_validate_json(raw_output.value[0])
        return Result([parsed.model_dump()], parent=raw_output, op=self)


def analyze_failure(runner: Runner, sample) -> Result:
    """Build SAMMO pipeline for proof failure analysis.
    
    Returns:
        Operator: Configured SAMMO pipeline for proof analysis
    """
    analysis_prompt = Template("""
        Analyze this failed proof attempt and suggest the most appropriate fix:
        
        ### Premises (English)
        {{input.premises_english}}
        
        ### Premises (PLN)
        {{input.premises_pln}}
        
        ### Conclusion (English)
        {{input.conclusion_english}}
        
        ### Conclusion (PLN)
        {{input.conclusion_pln}}
        
        ### Existing Proof Steps
        {{input.existing_proof_steps}}
        
        ### Instructions
        1. Identify the root cause of the failure
        2. Suggest exactly ONE of these fixes:
           - "fix_premise": Provide index and corrected PLN
           - "combine_statements": Identify two statements to combine
        3. Output as JSON with ONLY these keys: 
           action, premise_index, fixed_pln, statement1, statement2, combination_rule
    """)

    return Output(
                GenerateText(
                    analysis_prompt,
                    json_mode=ProofAnalysisResult.get_json_schema()
                )
            ).run(runner, [sample])

def main():
    """Simple test of ProofAssistant functionality"""
    
    # Initialize with Claude model using SAMMO
    runner = OpenAIChat(model_id="gpt-4o-mini",api_config={"api_key": os.environ['OPENAI_API_KEY']})
    
    # Create simple test case
    test_data = {
        "premises_english": ["All birds can fly", "Penguins are birds"],
        "premises_pln": ["(ForAll $x (Implication (Bird $x) (CanFly $x)))", 
                        "(ForAll $x (Implication (Penguin $x) (Bird $x)))"],
        "conclusion_english": "Penguins can fly",
        "conclusion_pln": ["(ForAll $x (Implication (Penguin $x) (CanFly $x)))"],
        "existing_proof_steps": []
    }
    
    # Run analysis
    print("Running Proof Assistant test...")
    result = analyze_failure(runner, test_data)
    print("\nProof Assistant Analysis Result:")
    print(result)

if __name__ == "__main__":
    main()
