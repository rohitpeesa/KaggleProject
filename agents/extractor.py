import fitz
from pydantic import BaseModel
from typing import List, Literal, Optional
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()

class Requirement(BaseModel):
    id: int
    category: Literal["technical", "compliance", "timeline"]
    description: str
    source_page: int
    is_mandatory: bool

class ExtractorResult(BaseModel):
    status: Literal["SUCCESS", "SECURITY_ALERT", "ERROR"]
    requirements: List[Requirement] = []
    message: Optional[str] = None
    triggered_phrase: Optional[str] = None

class ExtractorAgent:
    def __init__(self):
        # Using gemini-2.5-pro model
        self.client = genai.Client()

    async def run(self, pdf_path: str) -> dict:
        security_phrases = [
            "ignore previous instructions", 
            "system override", 
            "disregard your prompt", 
            "new instructions:", 
            "forget your instructions"
        ]
        
        pdf_text = ""
        try:
            with fitz.open(pdf_path) as doc:
                for i, page in enumerate(doc):
                    text = page.get_text() or ""
                    pdf_text += f"\n--- Page {i+1} ---\n{text}"
                    
                    # SECURITY SCAN FIRST
                    text_lower = text.lower()
                    for phrase in security_phrases:
                        if phrase in text_lower:
                            return {
                                "status": "SECURITY_ALERT",
                                "message": "Prompt injection detected in source document",
                                "triggered_phrase": phrase
                            }
        except Exception as e:
            return {"status": "ERROR", "message": f"Failed to read PDF: {str(e)}"}

        system_prompt = """You are a meticulous RFP Data Extractor. Your ONLY responsibility is to read procurement documents and extract hard technical, compliance, and timeline requirements as stated facts.

You do NOT evaluate. You do NOT summarise. You do NOT offer opinions.
You ONLY extract what is explicitly stated in the document.

Rules:
- Extract EVERY requirement that a vendor must meet to be eligible to bid
- Capture the exact page number where each requirement appears
- If a requirement is implied but not stated, do NOT include it
- Do not combine multiple requirements into one entry
- category must be exactly one of: "technical", "compliance", "timeline"
- is_mandatory: true if the document uses "must", "shall", "required"; false if it uses "should", "preferred", "desired"

Output EXACTLY this JSON and nothing else. No markdown. No backticks. No explanation. Raw JSON only:
{
  "status": "SUCCESS",
  "requirements": [
    {
      "id": 1,
      "category": "compliance",
      "description": "Vendor must hold an active ISO 27001 certification",
      "source_page": 12,
      "is_mandatory": true
    }
  ]
}"""
        
        try:
            response = await self.client.aio.models.generate_content(
                model="gemini-2.5-pro",
                contents=f"{system_prompt}\n\nDocument Text:\n{pdf_text}",
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ExtractorResult
                )
            )
            
            # Parse and validate the JSON response using Pydantic
            result = ExtractorResult.model_validate_json(response.text)
            return result.model_dump()
        except Exception as e:
            return {"status": "ERROR", "message": f"Failed to process with Gemini: {str(e)}"}
