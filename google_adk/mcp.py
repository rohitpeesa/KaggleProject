class MCPClient:
    def __init__(self, command, args):
        self.command = command
        self.args = args

    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
        
    async def call_tool(self, tool_name, kwargs):
        return {}
