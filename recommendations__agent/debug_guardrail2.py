import asyncio
from unittest.mock import patch, MagicMock
from agents import InputGuardrailTripwireTriggered as GT1
from agents.exceptions import InputGuardrailTripwireTriggered as GT2
from agent import agent as agent_mod
from agent.agent import run_turn

print("GT1 id:", id(GT1))
print("GT2 id:", id(GT2))

try:
    raise GT1("test")
except GT2:
    print("GT2 catches GT1")
except Exception:
    print("Exception catches GT1")
except:
    print("bare except catches GT1")

class _GuardrailTrip:
    def __init__(self, *a, **kw):
        self.final_output = ""
        self.agent = MagicMock()
    async def stream_events(self):
        print("  in stream_events, about to raise")
        from agents import InputGuardrailTripwireTriggered
        from agents.exceptions import InputGuardrailTripwireTriggered as GT3
        print(f"  GT(id={id(GT3)})")
        raise InputGuardrailTripwireTriggered("guardrail triggered")
        yield

async def test():
    from agents import InputGuardrailTripwireTriggered
    print(f"test GT id: {id(InputGuardrailTripwireTriggered)}")
    print(f"agent_mod GT id: {id(agent_mod.InputGuardrailTripwireTriggered)}")
    
    with patch.object(agent_mod.Runner, "run_streamed", _GuardrailTrip):
        try:
            result = await run_turn("test", "guard-test", "tester")
            print(f"Result: {result['response']}")
        except InputGuardrailTripwireTriggered as e:
            print(f"CAUGHT InputGuardrailTripwireTriggered: {e}")
        except Exception as e:
            print(f"CAUGHT {type(e).__name__}: {e}")

asyncio.run(test())
