import psutil
class HealthClient:
    def get_system_health(self) -> dict:
        mem=psutil.virtual_memory()
        disk=psutil.disk_usage('/')
        return{
            "cpu_percent":psutil.cpu_percent(interval=0.5),
            "memory":{
                "total_gb":round(mem.total/(1024**3),2),
                "used_gb":round(mem.used/(1024**3),2),
                "percentage":mem.percent
                }, 
            "disk":{
                "total_gb":round(disk.total/(1024**3),2),
                "used_gb":round(disk.used/(1024**3),2),
                "percentage":disk.percent
                },
            "load_avg": (
                [round(x, 2) for x in psutil.getloadavg()]
                if hasattr(psutil, "getloadavg")
                else None
            ),
         }
                 
    
            