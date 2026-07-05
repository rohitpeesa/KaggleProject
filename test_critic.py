import asyncio
import json
from agents.extractor import ExtractorAgent
from agents.critic import CriticAgent

async def test():
    extractor = ExtractorAgent()
    ext_res = await extractor.run("mock_sam_rfp.pdf")
    print("Extractor Res:", ext_res)
    
    critic = CriticAgent()
    crit_res = await critic.run(ext_res, "mock_sam_rfp.pdf")
    print("Critic Res:", crit_res)

if __name__ == "__main__":
    asyncio.run(test())
