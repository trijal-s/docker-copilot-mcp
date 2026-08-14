from mcp.types import Tool,TextContent
import json
from clients.docker_client import DockerClient
_docker=DockerClient()
def get_tool_definations()->list[Tool]:
    return[
        Tool(
            name="list_containers",
            description="List all Docker containers on this host, including stopped ones. "
                        "Use this to get an overview of what's running or crashed.",
            inputSchema={
                "type":"object",
                "properties":{}
            }
        ),
        Tool(
            name="get_container_status",
            description="Get detailed status for one specific container by name or ID, "
                        "including restart count and whether it was OOM-killed.",
            inputSchema={
                "type":"object",
                "properties":{
                    "name":{"type":string,"description":"Name or ID of the container to inspect."}
                },
                "required":["name"]
            }
        ),
        Tool(
            name="get_container_logs",
            description="Fetch recent logs from a container. Use this to diagnose why "
                        "a container crashed or is behaving unexpectedly.",
            inputSchema={
                "type":"object",
                "properties":{
                    "name":{"type":string,"description":"Name or ID of the container to fetch logs from."},
                    "tail":{"type":integer,"description":"Number of log lines to retrieve (default 100)."}
                },
                "required":["name"]
            }
        ),
    ] 
async def handle_tool_call(name:str,argument:dict)->list[TextContent]:
    if name=="list_containers":
        result=_docker.list_containers()
        return [TextContent(type="text",text=json.dumps(result,indent=2))]
    if name=="get_container_status":
        try:
            result=_docker.get_container(arguments["name"])
        except NotFound:
            return [TextContent(type="text",text=f"Container '{arguments['name']}' not found.")]
        return [TextContent(type="text",text=json.dumps(result,indent=2))]
    if name=="get_container_logs":
        try:
            result=_docker.get_logs(arguments["name"],tail=arguments.get("tail",100))
        except ValueError as e:
            return [TextContent(type="text",text=str(e))]
        return [TextContent(type="text",text=result)]
    raise ValueError(f"Unknown tool name: {name}")