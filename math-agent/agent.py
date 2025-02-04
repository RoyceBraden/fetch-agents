from uagents import Agent, Context, Model
from utils import ask_groq, get_code_from_groq
from typing import Optional
agent = Agent()

class Request(Model):
    message: str
    address: Optional[str]

PYTHON_EXECUTOR_AGENT_ADDRESS = 'agent1qfv7ldd6rjccdswg5p7n3vs62yespen20tcffzkutk2w70exrgp7vgxhqh4'

async def process_query(ctx: Context, question: str) -> None:
    ctx.logger.info(f"Question: {question}")
    response, code_blocks = await get_code_from_groq(question)
    await ctx.send(PYTHON_EXECUTOR_AGENT_ADDRESS, Request(message=code_blocks[0], address=agent.address))

@agent.on_message(model=Request)
async def handle_message(ctx: Context, sender: str, msg: Request):
    if sender == PYTHON_EXECUTOR_AGENT_ADDRESS:
        ctx.logger.info(f"Answer: {msg.message}")
    else:
        await process_query(ctx, msg.message)

@agent.on_event("startup")
async def send_message(ctx: Context):
    # Below code is for testing purpose (runs on startup)
    question = "What is the sum of the first 30 even squares"
    await process_query(ctx, question)

if __name__ == "__main__":
    agent.run()
    