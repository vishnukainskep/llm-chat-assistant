from llm_guard.input_scanners import Toxicity as InputToxicity 
from llm_guard.input_scanners.toxicity import MatchType as InputMatchType 
from llm_guard.output_scanners import Toxicity as OutputToxicity 
from llm_guard.output_scanners.toxicity import MatchType as OutputMatchType 

# Initialize Scanners
input_toxicity_scanner = InputToxicity(threshold=0.5, match_type=InputMatchType.SENTENCE) 
output_toxicity_scanner = OutputToxicity(threshold=0.5, match_type=OutputMatchType.SENTENCE) 

def input_guardrail_check(text: str): 
    return input_toxicity_scanner.scan(text) 

def output_guardrail_check(prompt: str, output: str): 
    return output_toxicity_scanner.scan(prompt, output)
