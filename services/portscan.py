import json
import subprocess

from services.service import Service
from config import settings, logger


class PortScanner(Service):
    def __init__(self, site, scan_type="top100"):
        super().__init__()
        self.task = "端口扫描任务"
        self.naabu_path = settings.Tools_dir.joinpath("naabu")
        self.site = site
        self.scan_type = scan_type

    def run(self):
        target = self.site.replace('http://', '').replace('https://', '').replace('/', '')
        if self.scan_type == "top100":
            top100 = settings.port_TOP_100
            naabu_cmd = f"{self.naabu_path} -json -exclude-cdn -host {target} -port {top100}"
        elif self.scan_type == "top1000":
            top1000 = settings.port_TOP_1000
            naabu_cmd = f"{self.naabu_path} -json -exclude-cdn -host {target} -port {top1000}"
        elif self.scan_type == "all":
            naabu_cmd = f"{self.naabu_path} -json -exclude-cdn -host {target} -p -"
        else:
            naabu_cmd = f"{self.naabu_path} -json -exclude-cdn -host {target} -port {self.scan_type}"
        try:
            print(naabu_cmd)
            result = subprocess.run(args=naabu_cmd, shell=True, capture_output=True, check=True, text=True).stdout
            try:
                result_list = [json.loads(line) for line in result.strip().split('\n')]
                return result_list
            except json.JSONDecodeError:
                return []
        except subprocess.CalledProcessError as e:
            logger.log("ERROR", "naabu run  error {}".format(e))
            return []


if __name__ == "__main__":
    res = PortScanner("47.97.210.37", "80,443,8000,3600,8888,5003").run()
    print(res)
