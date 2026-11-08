"""One question, with a Meter on the agent. usage: python3 measure_one.py MODEL"""
import sys

from models_setup import build_agent, build_model, prices_of
from whitebox import Meter

spec = sys.argv[1]
meter = Meter(prices_of(spec))
agent = build_agent(build_model(spec), hooks=[meter])
result = agent.run("How much is the till float?")
print(f"{spec}: {' '.join(result.answer.split())}")
print(meter.report())
