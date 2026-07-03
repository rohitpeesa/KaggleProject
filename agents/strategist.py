import sys
import os
from pydantic import BaseModel
from typing import List
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
from google_adk.mcp import MCPClient
from google_adk.session import InMemorySessionService

class StrategistDecision(BaseModel):
    decision: str
    confidence_score: int
    dealbreakers_found: List[str]
    strong_matches: List[str]
    risks: List[str]
    reasoning: str

class StrategistAgent:
    def __init__(self):
        server_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mcp_server', 'capabilities_server.py')
        
        self.mcp_client = MCPClient(
            command=sys.executable,
            args=[server_path]
        )
        self.session_service = InMemorySessionService()
        self.client = genai.Client()

    async def run(self, validated_requirements: list) -> dict:
        capabilities_context = {}
        
        async with self.mcp_client as client:
            for req in validated_requirements:
                # Provide domain context
                domain_res = await client.call_tool("query_company_capabilities", {"domain": req.get("description", "")})
                capabilities_context[f"req_{req.get('id')}_domain"] = domain_res
                
                # Verify compliance certs explicitly
                if req.get("category") == "compliance":
                    cert_res = await client.call_tool("check_certification", {"cert_name": req.get("description", "")})
                    capabilities_context[f"req_{req.get('id')}_cert"] = cert_res
                    
        prompt = f"""You are a Senior Solutions Architect making a Bid/No-Bid decision for a contract pursuit. You have two tools available to query our company's capabilities. You MUST use both tools before making your decision.

Process:
1. For each requirement, call query_company_capabilities with the relevant domain keyword
2. For any requirement mentioning a certification, standard, or compliance framework, call check_certification
3. After gathering all tool results, cross-reference our capabilities against ALL requirements
4. Make your final decision

Decision rules:
- A "dealbreaker" is any is_mandatory=true requirement we CANNOT meet (NOT CERTIFIED, or no relevant capability)
- ONE OR MORE dealbreakers = automatic NO-BID regardless of other matches
- "IN PROGRESS" certifications are RISKS, not capabilities  note them but do not count as meeting the requirement
- Confidence score: 100 = we meet every requirement perfectly; 0 = we meet nothing; scale linearly

Be honest. Do not inflate the confidence score. Judges may cross-check your reasoning.

Output EXACTLY this JSON and nothing else. No markdown. No backticks. Raw JSON only:
{{
  "decision": "BID",
  "confidence_score": 82,
  "dealbreakers_found": [],
  "strong_matches": ["ISO 27001  CERTIFIED Active", "GCP primary cloud  exact match"],
  "risks": ["HIPAA certification IN PROGRESS  not yet active, flag to legal team"],
  "reasoning": "NexusTech meets 8 of 10 mandatory requirements fully. The two compliance gaps (HIPAA active certification, FedRAMP) are in progress but not yet active, presenting contract risk if timeline is under 6 months. No hard dealbreakers found. Recommend BID with legal review of compliance timeline."
}}

Requirements:
{validated_requirements}

Company Capabilities Context:
{capabilities_context}
"""
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=StrategistDecision
                )
            )
            decision = StrategistDecision.model_validate_json(response.text)
            return decision.model_dump()
        except Exception as e:
            # Fallback if generation fails
            return {
                "decision": "ERROR",
                "confidence_score": 0,
                "dealbreakers_found": [],
                "strong_matches": [],
                "risks": [str(e)],
                "reasoning": "Failed to generate decision"
            }

    async def update_with_hitl_resolution(self, resolved_items: list) -> dict:
        self.session_service.set("hitl_resolved_items", resolved_items)
        
        # We re-run the decision with the updated items. 
        # In a real app, we might retrieve previously validated items from session too.
        return await self.run(resolved_items)
