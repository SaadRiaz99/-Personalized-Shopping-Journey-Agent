import asyncio
from unittest.mock import patch, MagicMock
from agents import InputGuardrailTripwireTriggered
from agent import agent as agent_mod
from agent.agent import run_turn

class _GuardrailTrip:
    def __init__(self, *a, **kw):
        print(f"_GuardrailTrip.__init__(*{a}, **{kw})")
        self.final_output = ""
        self.agent = MagicMock()
    async def stream_events(self):
        print("_GuardrailTrip.stream_events() called")
        raise InputGuardrailTripwireTriggered("guardrail triggered")
        yield

async def test():
    with patch.object(agent_mod.Runner, "run_streamed", _GuardrailTrip):
        try:
            result = await run_turn("test", "guard-test", "tester")
            print(f"Result: {result}")
        except InputGuardrailTripwireTriggered as e:
            print(f"CAUGHT InputGuardrailTripwireTriggered: {e}")
        except Exception as e:
            print(f"CAUGHT {type(e).__name__}: {e}")

asyncio.run(test())
