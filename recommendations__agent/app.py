import chainlit as cl
import uuid

from agent.agent import run_turn
from agent.session_memory import get_or_create_session
from agents import InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered


@cl.on_chat_start
async def on_chat_start():
    session_id = str(uuid.uuid4())
    cl.user_session.set("session_id", session_id)

    get_or_create_session(session_id)

    msg = cl.Message(
        content="🛍️ Welcome to ShopBot! I can help you find great products. What are you looking for today?"
    )
    await msg.send()


@cl.on_message
async def on_message(message: cl.Message):
    session_id = cl.user_session.get("session_id")

    thinking = cl.Message(content="🔎 **Searching products...**")
    await thinking.send()

    try:
        result = await run_turn(
            user_message=message.content,
            session_id=session_id,
            user_id="chainlit-user",
        )

        await thinking.remove()

        msg = cl.Message(
            content=result.get("response", ""),
        )
        await msg.send()

        session = get_or_create_session(session_id)
        cl.user_session.set("turn_count", session.turn_count)
        cl.user_session.set("products_seen", len(session.seen_ids))
        cl.user_session.set("preferences", dict(session.preferences))

    except InputGuardrailTripwireTriggered:
        await thinking.remove()
        warning = cl.Message(
            content="🛑 **I'm here to help with product recommendations only.**\n\nPlease ask me about products, comparisons, or what to buy!",
        )
        await warning.send()

    except OutputGuardrailTripwireTriggered:
        await thinking.remove()
        retry_msg = cl.Message(
            content="🔄 **I couldn't generate a complete response. Please try again.**\n\nRephrase your question about products.",
        )
        await retry_msg.send()

    except Exception:
        await thinking.remove()
        error_msg = cl.Message(
            content="❌ **Something went wrong. Please try again.**",
        )
        await error_msg.send()
