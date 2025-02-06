from flask import Flask, request, jsonify
from flask_cors import CORS
from fetchai.crypto import Identity
from fetchai.registration import register_with_agentverse
from fetchai.communication import parse_message_from_agent, send_message_to_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent
import logging
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
app = Flask(__name__)
client_identity = None

CORS(app)

def init_client():
    global client_identity
    try:
        client_identity = Identity.from_seed(os.getenv("BROWSER_AGENT_KEY"), 0)
        logger.info(f"Browser agent started with address: {client_identity.address}")

        readme = """
        <description>Runs a task in a web browser</description>
        <use_cases>
            <use_case>Backup for tasks which cannot be completed by agents</use_case>
            <use_case>Scrape the web using AI</use_case>
        </use_cases>
        """

        register_with_agentverse(
            identity=client_identity,
            url="http://localhost:4444/api/webhook",
            agentverse_token=os.getenv("AGENTVERSE_API_KEY"),
            agent_title="Test Agent",
            readme=readme
        )

        logger.info("Browser agent registration complete!")

    except Exception as e:
        logger.error(f"Initialization error: {e}")
        raise
    
@app.route('/api/webhook', methods=['POST'])
async def webhook():
    try:
        data = request.get_data().decode("utf-8")
        message = parse_message_from_agent(data)
        sender = message.sender
        task = message.payload["task"]
        output = await run_browser_agent(task)
        payload = {"output": output}

        send_message_to_agent(
            client_identity,
            sender,
            payload
        )
        

        return jsonify({"status": "success"})

    except Exception as e:
        logger.error(f"Error in webhook: {e}")
        return jsonify({"error": str(e)}), 500


    
def start_server():
    try:
        load_dotenv()
        init_client()
        app.run(host="0.0.0.0", port=4444)
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


async def run_browser_agent(task):
    agent = Agent(
        task=task,
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", google_api_key=os.getenv("GOOGLE_API_KEY"))
    )
    result = await agent.run()
    result = "Finished task"
    return result

if __name__ == "__main__":
    start_server()