import json
import sys
import os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from mcp.server.fastmcp import FastMCP
from clients.docker_client import DockerClient
from clients.health_client import HealthClient
from safety import gate,scope
from db import audit
mcp=FastMCP("homelab-ops-agent")
_docker=DockerClient()
_health=HealthClient()
@mcp.tool()
def list_containers()->str:
    result = _docker.list_containers()
    return json.dumps(result,indent=2)
@mcp.tool()
def get_container_status(name:str)->str:
    try:
        result=_docker.get_container(name)
    except ValueError as e:
        return str(e)
    return json.dumps(result,indent=2)
@mcp.tool()
def get_container_logs(name:str,tail:int=100)->str:
    try:
        result=_docker.get_logs(name,tail=tail)
    except ValueError as e:
        return str(e)
    return result
@mcp.tool()
def get_system_health()->str:
    result=_health.get_system_health()
    return json.dumps(result,indent=2)
@mcp.tool()
def restart_container(name: str, confirmation_token: str = "") -> str:
    args = {"name": name, "confirmation_token": confirmation_token}
    try:
        scope.check_scope(name, scope.ALLOWED_RESTART_TARGETS)
    except gate.ScopeError as e:
        audit.log_tool_call("restart_container", args, result, success=False, is_destructive=True)
        return f"Blocked: {e}"
    parms = {}
    if not confirmation_token:
        plan = f"Restart container '{name}'. This will briefly interrupt anything using it."
        result = gate.request_confirmation("restart_container", name, parms, plan)
        result_str = json.dumps(result, indent=2)
        audit.log_tool_call("restart_container", args, result_str, success=True, is_destructive=True)
        return result_str
    try:
        gate.validate_confirmation("restart_container", name, parms, confirmation_token)
    except ValueError as e:
        result = str(e)
        audit.log_tool_call("restart_container", args, result, success=False, is_destructive=True)
        return result
    try:
        result = _docker.restart_container(name)
    except ValueError as e:
        result_str = str(e)
        audit.log_tool_call("restart_container", args, result_str, success=False, is_destructive=True)
        return result_str
    result_str = f"Restarted successfully.\n{json.dumps(result, indent=2)}"
    audit.log_tool_call("restart_container", args, result_str, success=True, is_destructive=True)
    return result_str
if __name__=="__main__":
    mcp.run(transport="stdio")