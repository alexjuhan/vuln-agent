class BaseTool:
    name: str
    description: str
    parameters: dict
    
    async def execute(self, **kwargs) -> ToolResponse:
        raise NotImplementedError 