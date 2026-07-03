import os
import sys
import json
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse

# Add parent directory to sys.path to import agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.strategist import StrategistAgent

app = FastAPI()

@app.get("/.well-known/agent-card.json")
async def get_agent_card():
    card_path = os.path.join(os.path.dirname(__file__), "agent_card.json")
    return FileResponse(card_path, media_type="application/json")

@app.post("/tasks/send")
async def tasks_send(request: Request):
    payload = await request.json()
    
    # Extract params based on JSON-RPC 2.0 A2A format
    params = payload.get("params", {})
    task_id = params.get("id", "unknown-task")
    message = params.get("message", {})
    parts = message.get("parts", [])
    
    text_content = "[]"
    if parts and len(parts) > 0:
        text_content = parts[0].get("text", "[]")
        
    try:
        requirements = json.loads(text_content)
    except Exception:
        requirements = []

    # Run the StrategistAgent
    strategist = StrategistAgent()
    decision_dict = await strategist.run(requirements)
    
    decision_json = json.dumps(decision_dict)
    
    # Construct standard A2A JSON-RPC 2.0 response
    response = {
        "jsonrpc": "2.0",
        "result": {
            "id": task_id,
            "status": {"state": "completed"},
            "artifacts": [
                {
                    "parts": [{"text": decision_json}]
                }
            ]
        },
        "id": payload.get("id", 1)
    }
    
    return JSONResponse(content=response)
