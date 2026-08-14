from mcp.types import Tool,TextContent
import json
from clients.health_client import HealthClient
_health=HealthClient()
def get_tool_definations()->list(Tool):
    return[
        Tool(
            name="get_system_health",
            description="Get current CPU, memory, and disk usage for this host. "
                        "Use this to check if the host is under resource pressure "
                        "(e.g., before diagnosing why a container crashed).",
            inputSchema={
                "type":"object",
                "properties":{}
            }
        ),
    ]
async def handle_tool_call(name:str,arguments:dict)->list[TextContent]:
    if name=="get_system_health":
        result=_health.get_system_health()
        return [TextContent(type="text",text=json.dumps(result,indent=2))]
    raise ValueError(f"Unknown tool name: {name}")