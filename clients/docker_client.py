import docker
from docker.errors import NotFound, APIError
class DockerClient:
    def __init__(self):
        self.client=docker.from_env()
    def list_containers(self,all:bool=True)-> list[dict]:
        container=self.client.containers.list(all=all)
        return [self._summarize(c) for c in container]
    def get_container(self,name_or_id:str)->dict:
        try:
            container=self.client.containers.get(name_or_id)
        except NotFound:
            raise ValueError(f"container '{name_or_id}' not found")
        return self._summarize(container,detailed=True)
    def get_logs(self,name_or_id:str,tail:int=100)-> str:
        try:
            container=self.client.containers.get(name_or_id)
        except NotFound:
            raise ValueError(f"container '{name_or_id}' not found")
        try:
            log=container.logs(tail=tail)
        except ApiError as e:
            raise RuntimeError(f"Failed to retrieve logs for container '{name_or_id}': {str(e)}")
        return log.decode('utf-8',errors='replace')
    def restart_container(self,name_or_id:str,timeout:int=100)->dict:
        try:
            container = self.client.containers.get(name_or_id)
        except NotFound:
            raise ValueError(f"container '{name_or_id}' not found")
        container.restart(timeout=timeout)
        container.reload()
        return self._summarize(container)
    
    @staticmethod
    def _summarize(container, detailed: bool = False) -> dict:
        attrs = container.attrs
        state = attrs.get("State", {})
        summary = {
            "id": container.short_id,
            "name": container.name,
            "image": (
                container.image.tags[0]
                if container.image and container.image.tags
                else "unknown"
            ),
            "status": container.status,          # running, exited, restarting...
            "exit_code": state.get("ExitCode"),
            "started_at": state.get("StartedAt"),
            "finished_at": state.get("FinishedAt"),
        }
        if detailed:
            summary["restart_count"] = attrs.get("RestartCount")
            summary["oom_killed"] = state.get("OOMKilled", False)
            summary["health"] = (
                state.get("Health", {}).get("Status") if state.get("Health") else None
            )
        return summary