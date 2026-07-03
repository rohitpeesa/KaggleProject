import os
import json
import urllib.request
import urllib.error

from .extractor import ExtractorAgent
from .critic import CriticAgent
async def run_pipeline(pdf_path: str) -> dict:
    # 1. Extractor
    extractor = ExtractorAgent()
    extraction_result = await extractor.run(pdf_path)
    
    # 2. Security Check (Abort if alert)
    if extraction_result.get("status") == "SECURITY_ALERT":
        return extraction_result
        
    # 3. Critic
    critic = CriticAgent()
    critic_result = await critic.run(extraction_result, pdf_path)
    
    # Return intermediate results for optional HITL pause
    return {
        "extraction": extraction_result,
        "critic": critic_result,
        "ready_for_strategist": True
    }

async def run_strategist(validated_items: list, hitl_resolved_items: list) -> dict:
    all_items = validated_items + hitl_resolved_items
    
    service_url = os.environ.get("STRATEGIST_SERVICE_URL", "http://localhost:8080").rstrip("/")
    
    # 1. Read the Strategist's AgentCard
    agent_card_url = f"{service_url}/.well-known/agent-card.json"
    try:
        req_card = urllib.request.Request(agent_card_url)
        with urllib.request.urlopen(req_card) as response:
            card_data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"error": f"Failed to reach Strategist Service AgentCard at {agent_card_url}: {str(e)}"}
        
    # 2. POST a JSON-RPC 2.0 task
    tasks_url = f"{service_url}/tasks/send"
    payload = {
        "jsonrpc": "2.0",
        "method": "tasks/send",
        "params": {
            "id": "task-123",
            "message": {
                "role": "user",
                "parts": [
                    {"text": json.dumps(all_items)}
                ]
            }
        },
        "id": 1
    }
    
    try:
        req = urllib.request.Request(
            tasks_url, 
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req) as response:
            rpc_resp = json.loads(response.read().decode('utf-8'))
            
            # 3 & 4. Parse response and extract decision artifact
            try:
                artifacts = rpc_resp.get("result", {}).get("artifacts", [])
                if artifacts and len(artifacts) > 0:
                    parts = artifacts[0].get("parts", [])
                    if parts and len(parts) > 0:
                        decision_text = parts[0].get("text", "{}")
                        return json.loads(decision_text)
            except Exception as e:
                return {"error": f"Failed to parse artifact decision: {str(e)}"}
                
            return {"error": "No valid decision artifact found in the response."}
            
    except Exception as e:
        return {"error": f"Failed to execute task on Strategist Service: {str(e)}"}
