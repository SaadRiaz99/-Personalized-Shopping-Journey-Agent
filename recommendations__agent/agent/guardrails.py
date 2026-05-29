"""
guardrails.py
-------------
Input and output guardrails for the recommendation agent.

Input guardrails  -> run BEFORE the agent processes the message.
Output guardrails -> run AFTER the agent produces its response.

Uses @input_guardrail / @output_guardrail decorators from `agents`.
"""

from __future__ import annotations
import re                                        # Regex pattern matching
from agents import (
    Agent,
    RunContextWrapper,
    GuardrailFunctionOutput,                     # Return type for guardrail hooks
    input_guardrail,
    output_guardrail,
)
from .context import AgentContext

# ── Blocked terms (injection / abuse) ─────────────────────────────────────────
_BLOCKED_INPUT_PATTERNS = [
    r"\b(hack|exploit|steal|fraud|scam|bypass|jailbreak)\b",
    r"\bignore\b.*\binstructions?\b",
    r"you are now",
    r"pretend (you are|to be)",
    r"act as (a |an )?(different|unrestricted|evil)",
]
_BLOCKED_INPUT_RE = re.compile(
    "|".join(_BLOCKED_INPUT_PATTERNS), re.IGNORECASE
)

# ── Off-topic patterns matched against every user message ──────────────────────
# Only product-related queries should pass; everything else is redirected.
_OFF_TOPIC_PATTERNS = [
    # Coding / programming / algorithms
    r"\b(algorithm|recursion|iteration|complexity|optimization|data structure)\b",
    r"\b(debug|debugging|bug|error|exception|stack trace|traceback)\b",
    r"\b(function|variable|class|object|method|inheritance|polymorphism)\b",
    r"\b(compile|compiler|interpreter|runtime|syntax|semantic)\b",
    r"\b(programming|software development|software engineer|developer)\b",
    r"\b(write code|code snippet|code review|refactor|merge|pull request)\b",
    r"\b(api|rest api|graphql|endpoint|http|request|response)\b",
    r"\b(database|sql|nosql|query|table|schema|index|migration)\b",
    r"\b(git|github|repository|branch|commit|push|clone|fork)\b",
    r"\b(linux|unix|bash|shell|terminal|command line|cli)\b",
    r"\b(docker|container|kubernetes|k8s|deploy|deployment|pipeline|ci/cd)\b",
    r"\b(html|css|javascript|typescript|python|java|rust|golang|c\+\+|react|angular|vue|node|deno)\b",
    r"\b(web (app|site|development|framework|server)|frontend|backend|full.?stack)\b",
    r"\b(develop|build|create|implement|design) (a|an|the) (app|software|system|tool|platform)\b",
    # Math / physics / science
    r"\b(calculation|compute|solve|equation|formula|theorem|proof)\b",
    r"\b(physics|chemistry|biology|science (experiment|lab|project))\b",
    r"\b(statistics|probability|regression|distribution|correlation)\b",
    r"\b(convert|conversion|unit|measurement|dimension)\b",
    # Writing / editing / homework
    r"\b(essay|assignment|homework|project|report|paper|thesis|dissertation)\b",
    r"\b(write|edit|proofread|rewrite|draft|compose|summarize) (a|an|the|my|this)\b",
    r"\b(grammar|spelling|vocabulary|paragraph|citation|bibliography|reference)\b",
    # Medical / health
    r"\b(medical|doctor|hospital|clinic|surgery|diagnosis|diagnose|symptom)\b",
    r"\b(disease|illness|infection|treatment|therapy|medication|prescription)\b",
    r"\b(diet|nutrition|calorie|workout|exercise|fitness|weight loss)\b",
    r"\b(mental health|anxiety|depression|therapy|counseling|therapist)\b",
    # Finance / investing
    r"\b(stock|share|market|trading|invest|investing|investment|portfolio)\b",
    r"\b(crypto|cryptocurrency|bitcoin|ethereum|blockchain|nft|token)\b",
    r"\b(tax|loan|mortgage|interest|credit|debt|banking|insurance)\b",
    r"\b(budget|financial|finance|retirement|savings|401k|ira)\b",
    # Weather
    r"\b(weather|forecast|temperature|rain|snow|sunny|cloudy|wind|humidity)\b",
    r"\b(climate|climate change|global warming|season|storm|hurricane)\b",
    # News / politics / current events
    r"\b(news|headline|breaking|current (event|affair)|politics|political)\b",
    r"\b(election|campaign|candidate|president|senator|congress|parliament)\b",
    r"\b(war|military|army|weapon|conflict|invasion|sanction|treaty)\b",
    r"\b(law|legal|court|judge|attorney|lawsuit|legislation|regulation)\b",
    # Sports
    r"\b(sport|game|match|tournament|championship|league|team|player|coach)\b",
    r"\b(football|soccer|basketball|tennis|cricket|baseball|golf|hockey)\b",
    r"\b(olympic|world cup|super bowl|final|score|standings|playoff)\b",
    # Travel / transportation
    r"\b(flight|airline|airport|hotel|motel|resort|booking|reservation)\b",
    r"\b(vacation|trip|travel|tour|destination|sightseeing|itinerary)\b",
    r"\b(direction|map|navigate|navigation|route|traffic|commute)\b",
    r"\b(car|truck|vehicle|driving|parking|fuel|gas|mechanic|repair)\b",
    # Time / date / calendar
    r"\b(current time|what time|what day|what date|today|tomorrow|yesterday)\b",
    r"\b(calendar|schedule|appointment|reminder|timezone|dst|daylight saving)\b",
    # Food / cooking (not product queries like "kitchen appliances")
    r"\b(recipe|how to cook|cook(ing|book)?|baking|ingredient|meal prep)\b",
    r"\b(restaurant|cafe|menu|dinner|lunch|breakfast|snack|cuisine)\b",
    # Entertainment (movies / music / TV / gaming)
    r"\b(actor|actress|director|cinema|theater|tv show|episode)\b",
    r"\b(music|song|album|artist|band|concert|playlist|spotify|itunes)\b",
    r"\b(gaming|video game|console|xbox|playstation|nintendo|steam|rpg)\b",
    r"\b(novel|author|reading|library|publisher|chapter|genre)\b",
    # Relationships / personal advice
    r"\b(relationship|dating|marriage|boyfriend|girlfriend|advice (on|about))\b",
    r"\b(friend|family|parent|child|partner|colleague|boss|manager) (issue|problem|advice)\b",
    # General knowledge / definitions
    r"\b(who is|what is|define|meaning of|explain|tell me about|how (does|do|can|to))\b",
    r"\b(history|origin|biography|background|overview|introduction to)\b",
    # Homework / study help
    r"\b(study|learn|teach|tutor|lesson|course|class|education|training)\b",
    r"\b(question|answer|solve|help (me|with) (my|this|a))\b",
    # Miscellaneous off-topic
    r"\b(philosophy|religion|god|atheist|bible|quran|spiritual|meditation)\b",
    r"\b(astrology|horoscope|psychic|supernatural|ghost|paranormal|ufo)\b",
    r"\b(dream|interpretation|meaning (of life|behind)|purpose)\b",
    r"\b(funeral|death|dying|afterlife|suicide|self.?harm)\b",
    r"\b(joke|riddle|puzzle|brain teaser|trivia|fun fact)\b",
    r"\b(pet|dog|cat|animal|veterinary|breed|grooming|training (a|my) (dog|cat|pet))\b",
]
_OFF_TOPIC_RE = re.compile(
    "|".join(_OFF_TOPIC_PATTERNS), re.IGNORECASE
)

_MIN_OUTPUT_WORDS = 10                            # Minimum acceptable response length
_HALLUCINATED_ID_RE = re.compile(r"\bid\s*[:#]?\s*(\d+)\b", re.IGNORECASE)


# ─────────────────────────────────────────────────────────────────────────────
# INPUT GUARDRAIL 1 - Prompt injection / abuse check
# ─────────────────────────────────────────────────────────────────────────────
@input_guardrail(name="injection_abuse_check")
async def injection_abuse_guardrail(
    ctx:   RunContextWrapper[AgentContext],
    agent: Agent,
    input: str,
) -> GuardrailFunctionOutput:
    """Block prompt injection, jailbreak attempts, and abuse."""
    # Extract the user message text (handles both str and list-of-dicts input)
    if isinstance(input, str):
        text = input
    elif isinstance(input, list) and len(input) > 0:
        last = input[-1]
        if isinstance(last, dict):
            text = last.get("content", str(last))
        else:
            text = str(last)
    else:
        text = str(input)

    if _BLOCKED_INPUT_RE.search(text):
        ctx.context.log_tool("GUARDRAIL:input", f"BLOCKED injection/abuse: '{text[:60]}'")
        return GuardrailFunctionOutput(
            output_info={"reason": "Blocked: potential prompt injection or abusive input detected."},
            tripwire_triggered=True,
        )

    return GuardrailFunctionOutput(output_info={"passed": True}, tripwire_triggered=False)


# ─────────────────────────────────────────────────────────────────────────────
# INPUT GUARDRAIL 2 - Off-topic topic check
# ─────────────────────────────────────────────────────────────────────────────
@input_guardrail(name="off_topic_check")
async def off_topic_guardrail(
    ctx:   RunContextWrapper[AgentContext],
    agent: Agent,
    input: str,
) -> GuardrailFunctionOutput:
    """Redirect clearly off-topic queries (coding help, medical advice, etc.)."""
    if isinstance(input, str):
        text = input
    elif isinstance(input, list) and len(input) > 0:
        last = input[-1]
        if isinstance(last, dict):
            text = last.get("content", str(last))
        else:
            text = str(last)
    else:
        text = str(input)

    if _OFF_TOPIC_RE.search(text):
        ctx.context.log_tool("GUARDRAIL:input", f"BLOCKED off-topic: '{text[:60]}'")
        return GuardrailFunctionOutput(
            output_info={
                "reason": (
                    "I'm a product recommendation assistant. "
                    "I can't help with that topic, but I'd be happy to help you "
                    "find a great product!"
                )
            },
            tripwire_triggered=True,
        )

    return GuardrailFunctionOutput(output_info={"passed": True}, tripwire_triggered=False)


# ─────────────────────────────────────────────────────────────────────────────
# OUTPUT GUARDRAIL 1 - Response quality check
# ─────────────────────────────────────────────────────────────────────────────
@output_guardrail(name="response_quality_check")
async def response_quality_guardrail(
    ctx:    RunContextWrapper[AgentContext],
    agent:  Agent,
    output: str,
) -> GuardrailFunctionOutput:
    """
    Ensure the agent's response meets a minimum quality bar:
    - Not too short (likely an empty or broken response)
    - Does not contain raw error tracebacks
    """
    text = output if isinstance(output, str) else str(output)
    word_count = len(text.split())

    if word_count < _MIN_OUTPUT_WORDS:
        ctx.context.log_tool("GUARDRAIL:output", f"BLOCKED too short ({word_count} words)")
        return GuardrailFunctionOutput(
            output_info={"reason": f"Response too short ({word_count} words). Minimum is {_MIN_OUTPUT_WORDS}."},
            tripwire_triggered=True,
        )

    if "Traceback (most recent call last)" in text:
        ctx.context.log_tool("GUARDRAIL:output", "BLOCKED traceback in output")
        return GuardrailFunctionOutput(
            output_info={"reason": "Response contained an internal error traceback."},
            tripwire_triggered=True,
        )

    ctx.context.log_tool("GUARDRAIL:output", f"passed quality check ({word_count} words)")
    return GuardrailFunctionOutput(output_info={"passed": True, "word_count": word_count}, tripwire_triggered=False)
