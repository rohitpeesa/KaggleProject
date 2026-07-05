import asyncio
from agents.extractor import ExtractorAgent

async def test():
    extractor = ExtractorAgent()
    res = await extractor.run("mock_sam_rfp.pdf")
    print(res)

if __name__ == "__main__":
    asyncio.run(test())
