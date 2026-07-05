import fitz
from pydantic import BaseModel
from typing import List, Optional, Literal
from google import genai
from google.genai import types
import os
import time
from dotenv import load_dotenv

load_dotenv()

class ValidatedRequirement(BaseModel):
    id: int
    category: str
    description: str
    source_page: int
    is_mandatory: bool

class FlaggedRequirement(BaseModel):
    id: int
    description: str
    source_page: int
    reason: str

class CriticResult(BaseModel):
    validated: List[ValidatedRequirement] = []
    flagged: List[FlaggedRequirement] = []

class CriticAgent:
    def __init__(self):
        self.client = genai.Client()

    async def run(self, extraction_result: dict, pdf_path: str) -> dict:
        page_dict = {}
        try:
            with fitz.open(pdf_path) as doc:
                for i, page in enumerate(doc):
                    page_dict[i + 1] = page.get_text() or ""
        except Exception:
            pass # handle or let fail gracefully
            
        validated = []
        flagged = []
        
        for req in extraction_result.get("requirements", []):
            page_num = req.get("source_page")
            page_text = page_dict.get(page_num, "")
            
            prompt = f"""You are a strict Hallucination Guardrail. You do one thing: verify that extracted requirements actually exist in the source document as described.

You will receive:
1. The text of a specific page from the RFP
2. A requirement that was supposedly extracted from that page

Your job: Does this requirement exist on this page, stated in a way that matches the description?

Rules:
- VALIDATED: The requirement is clearly present on the page, substantially as described
- FLAGGED: The requirement is absent, exaggerated, misattributed to the wrong page, or the page number is wrong
- Do NOT flag requirements just because you would describe them differently
- Do NOT validate requirements you cannot confirm from the provided page text
- Be specific in your flagging reason  "Not found on page 12" is not enough; explain what IS on page 12 instead

Output EXACTLY this JSON and nothing else:
{{
  "result": "validated" | "flagged",
  "reason": "Only required if flagged  specific explanation of what was wrong"
}}

Requirement: {req}
Page Text: {page_text}
"""
            
            class VerifyResponse(BaseModel):
                result: Literal["validated", "flagged"]
                reason: Optional[str] = None
                
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-pro",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=VerifyResponse
                    )
                )
                verify_res = VerifyResponse.model_validate_json(response.text)
                
                if verify_res.result == "validated":
                    validated.append(req)
                else:
                    flagged.append({
                        "id": req.get("id"),
                        "description": req.get("description"),
                        "source_page": page_num,
                        "reason": verify_res.reason or "Failed verification"
                    })
                    
                time.sleep(2) # Prevent Gemini API rate limit exceptions from auto-flagging
            except Exception as e:
                flagged.append({
                    "id": req.get("id", 0),
                    "description": req.get("description", ""),
                    "source_page": page_num or 0,
                    "reason": f"Verification error: {str(e)}"
                })
                
        return {"validated": validated, "flagged": flagged}
