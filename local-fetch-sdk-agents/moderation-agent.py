from flask import Flask, request, jsonify
from flask_cors import CORS
from fetchai.crypto import Identity
from fetchai import fetch
from fetchai.registration import register_with_agentverse
from fetchai.communication import parse_message_from_agent, send_message_to_agent
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import logging
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
app = Flask(__name__)
client_identity = None

model = AutoModelForSequenceClassification.from_pretrained("KoalaAI/Text-Moderation")
tokenizer = AutoTokenizer.from_pretrained("KoalaAI/Text-Moderation", use_fast=False, verbose=True)

CORS(app)

def init_client():
    global client_identity
    try:
        client_identity = Identity.from_seed(os.getenv("MODERATION_AGENT_KEY"), 0)
        logger.info(f"Test agent started with address: {client_identity.address}")

        readme = """
        <description>Agent which decides which category a prompt falls under in regards to text moderation</description>
        <use_cases>
            <use_case>Quickly decides which category a prompt belongs to</use_case>
        </use_cases>
        <table>
        # Content Categories
        | Category | Label | Definition |
        |----------|--------|------------|
        | Sexual | S | Content meant to arouse sexual excitement, such as the description of sexual activity, or that promotes sexual services (excluding sex education and wellness). |
        | Hate | H | Content that expresses, incites, or promotes hate based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste. |
        | Violence | V | Content that promotes or glorifies violence or celebrates the suffering or humiliation of others. |
        | Harassment | HR | Content that may be used to torment or annoy individuals in real life, or make harassment more likely to occur. |
        | Self-harm | SH | Content that promotes, encourages, or depicts acts of self-harm, such as suicide, cutting, and eating disorders. |
        | Sexual/Minors | S3 | Sexual content that includes an individual who is under 18 years old. |
        | Hate/Threatening | H2 | Hateful content that also includes violence or serious harm towards the targeted group. |
        | Violence/Graphic | V2 | Violent content that depicts death, violence, or serious physical injury in extreme graphic detail. |
        | Not Offensive | OK | Not offensive |
        </table>
        """

        register_with_agentverse(
            identity=client_identity,
            url="http://localhost:2222/api/webhook",
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
        sender = message.sender
        prompt = message.payload["prompt"]
        output = run_text_moderation(prompt)
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


@app.route('/api/search-agents', methods=['GET'])
def search_agents():
    try:
        available_ais = fetch.ai('I need help deciding what to do')
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
        app.run(host="0.0.0.0", port=2222)
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


def run_text_moderation(prompt):
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model(**inputs)
    logits = outputs.logits
    probabilities = logits.softmax(dim=-1).squeeze()
    id2label = model.config.id2label
    labels = [id2label[idx] for idx in range(len(probabilities))]
    label_prob_pairs = list(zip(labels, probabilities.detach().numpy().tolist()))  # Convert to Python floats
    label_prob_pairs.sort(key=lambda item: item[1], reverse=True)
    return label_prob_pairs

if __name__ == "__main__":
    start_server()