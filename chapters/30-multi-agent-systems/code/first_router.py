"""One model call picks a worker, then that worker does the whole job."""
from team_setups import Setups
from whitebox import load_model

QUESTIONS = ["How much is the till float?", "How much did the film crew pay to use Old Mill?",
             "Who was the guest at the Riverside cupping club in June 2025?", "How much extra do oat, soya and coconut milk cost?"]

router = Setups(load_model()).router()
for question in QUESTIONS:
    result = router.run(question)
    print(f"{router.chosen[-1]:<9} {question}")
    print(f"          {' '.join(result.answer.split())[:96]}")
