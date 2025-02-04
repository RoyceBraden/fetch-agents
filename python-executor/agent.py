from uagents import Agent, Context, Model
from utils import execute_code
from typing import Optional
agent = Agent()

class Request(Model):
    message: str
    address: Optional[str]

@agent.on_message(model=Request)
async def handle_message(ctx: Context, sender: str, msg: Request):
    result = execute_code(msg.message)
    await ctx.send(msg.address, Request(message=result))

  
if __name__ == "__main__":
    agent.run()
    