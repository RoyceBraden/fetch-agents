from flask import Flask, request, jsonify
from flask_cors import CORS
from fetchai.crypto import Identity
from fetchai import fetch
from fetchai.registration import register_with_agentverse
from fetchai.communication import parse_message_from_agent, send_message_to_agent
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
        client_identity = Identity.from_seed(os.getenv("TEST_AGENT_KEY"), 0)
        logger.info(f"Test agent started with address: {client_identity.address}")

        readme = """
        <description>Agent for testing the browser agent</description>
        <use_cases>
            <use_case>Test whether browser agent works</use_case>
        </use_cases>
        """

        register_with_agentverse(
            identity=client_identity,
            url="http://localhost:3333/api/webhook",
            agentverse_token=os.getenv("AGENTVERSE_API_KEY"),
            agent_title="Test Agent",
            readme=readme
        )

        logger.info("Test agent registration complete!")

    except Exception as e:
        logger.error(f"Initialization error: {e}")
        raise
    
@app.route('/api/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_data().decode("utf-8")
        message = parse_message_from_agent(data)
        response = message.payload

        logger.info(f"Processed response: {response}")
        return jsonify({"status": "success"})

    except Exception as e:
        logger.error(f"Error in webhook: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/send-data', methods=['POST'])
def send_data():
    global dashboard_response
    dashboard_response = None

    try:
        data = request.json
        task= data.get('task')
        BROWSER_AGENT_ADDRESS = "agent1qv5j8kw7shanr802r274y46zsgssxasljkjg465fr6yz2kmcf4vpx5ut63r"

        if not task:
            return jsonify({"error": "Missing task"}), 400

        logger.info(f"Sending task {task} to {BROWSER_AGENT_ADDRESS}")

        payload = {"task": task} 
        send_message_to_agent(
            client_identity,
            BROWSER_AGENT_ADDRESS,
            payload
        )

        return jsonify({"status": "request_sent"})

    except Exception as e:
        logger.error(f"Error sending data path: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/search-agents', methods=['GET'])
def search_agents():
    try:
        available_ais = fetch.ai('I need to use a browser to finish this task')
        print(f'---------------------{available_ais}----------------------')
        agents = available_ais.get('ais', [])
        print(f'----------------------------------{agents}------------------------------------')

        extracted_data = []
        for agent in agents:
            name = agent.get('name')
            address = agent.get('address')
            extracted_data.append({
                'name': name,
                'address': address,
            })
        response = jsonify(extracted_data)
        response.headers.add('Content-Type', 'application/json; charset=utf-8')
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response, 200

    except Exception as e:
        logger.error(f"Error finding agents: {e}")
        return jsonify({"error": str(e)}), 500
    
def start_server():
    try:
        load_dotenv()
        init_client()
        app.run(host="0.0.0.0", port=3333)
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == "__main__":
    start_server()