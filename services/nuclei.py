import json
import subprocess
import yaml
from config import settings, logger
from services.service import Service

from utils import conn_db


class Nuclei(Service):
    def __init__(self, site, level="info", poc_id="", tags=""):
        Service.__init__(self)
        self.service_name = "Nuclei"
        self.site = site
        self.task_describe = "进行漏洞检测任务"
        self.nuclei_path = settings.Tools_dir.joinpath("nuclei")
        self.tags = tags
        self.level = level
        self.poc_id = poc_id
        self.vul_result = []

    def extract_info(self, output):
        # 将输出拆分成行
        lines = output.split('\n')

        for line in lines:
            if not line.strip():
                continue
            # 尝试解析行中的 JSON 数据
            try:
                data = json.loads(line)
                template_id = data.get('template-id')
                name = data.get('info').get('name')
                severity = data.get('info').get('severity')
                match_url = data.get('matched-at')
                item = {
                    "templateId": template_id,
                    "name": name,
                    "severity": severity,
                    "matchedAt": match_url
                }
                self.vul_result.append(item)
            except json.JSONDecodeError:
                logger.log("ERROR", f"解码行中的 JSON 数据时出错:{line}")

    @staticmethod
    def get_poc_info():
        poc_dir = settings.data_storage_dir.joinpath("POC")
        file_list = [item for item in poc_dir.iterdir()]
        for item in file_list:
            with open(item, "r") as f:
                data = yaml.safe_load(f)
                existing_poc = conn_db("POC").find_one({'id': data['id']})
                if not existing_poc:
                    conn_db("POC").insert_one({
                        "poc_id": data["id"],
                        "name": data["info"].get("name"),
                        "severity": data["info"].get("severity"),
                        "tags": data["info"].get("tags"),
                        "description": data["info"].get("description"),
                        "remediation": data["info"].get("remediation")
                    })

    def run(self):
        poc_path = settings.data_storage_dir.joinpath("POC")
        # 同步数据库中的poc信息和本地poc库
        self.get_poc_info()
        command = (f"{self.nuclei_path} -u {self.site}  -duc -silent -nc -jsonl "
                   f"-tags '{self.tags}' -id '{self.poc_id}' -t {poc_path} -es {self.level} ")

        try:
            result = subprocess.run(args=command, shell=True, capture_output=True, check=True)
            output = result.stdout.decode('utf-8')
            self.extract_info(output)
            return self.vul_result
        except subprocess.CalledProcessError as e:
            logger.log("ERROR", f"运行 nuclei 命令时发生错误，站点：{self.site} 错误信息：{e}")


if __name__ == "__main__":
    res = Nuclei("action.weixin.qq.com").run()
    print(res)
