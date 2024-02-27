import json

from config import settings, logger
from services import Service
from utils import Http_Request, match_subdomains, call_massdns


class SubFind(Service):
    def __init__(self, domain):
        super().__init__()
        self.service_name = "子域名发现"
        self.task_describe = "收集子域名任务"
        self.domain = domain
        self.subdomains = set()  # 存放发现的子域名
        self.request = Http_Request()  # 初始化封装的request请求
        self.sub_dict = set()  # 子域名字典

    def match_subdomains(self, resp, fuzzy=True):
        if not resp:
            return set()
        elif isinstance(resp, str):
            return match_subdomains(self.domain, resp, fuzzy)
        elif hasattr(resp, 'text'):
            return match_subdomains(self.domain, resp.text, fuzzy)
        else:
            return set()

    def crtsh(self):
        addr = 'https://crt.sh/'
        params = {'q': f'%.{self.domain}'}
        resp = self.request.get(addr, params=params, )
        self.subdomains.update(self.match_subdomains(resp, True))

    def chinaz(self):
        addr = "https://alexa.chinaz.com/" + self.domain
        resp = self.request.get(addr)
        self.subdomains.update(self.match_subdomains(resp, True))

    def securitytrails_api(self):
        addr = 'https://api.securitytrails.com/v1/domain/'
        url = f'{addr}{self.domain}/subdomains'
        api_key = getattr(settings, 'securitytrailsAPI', None)
        if api_key:
            params = {'apikey': api_key}
            resp = self.request.get(url, params=params)
            if not resp:
                return
            prefixs = resp.json()['subdomains']
            subdomains = [f'{prefix}.{self.domain}' for prefix in prefixs]
            if subdomains:
                self.subdomains.update(subdomains)
        else:
            logger.log('ERROR', "未发现securitytrails的API设置")

    def burp(self):
        dict_path = settings.data_storage_dir.joinpath('subdomain_dict.txt')
        # 读入字典
        with open(dict_path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                subdomain = line.strip() + '.' + self.domain
                self.sub_dict.add(subdomain)
        temp_dict_path = settings.temp_dir.joinpath(f"{self.domain}.txt")
        # 生成临时子域名字典文件
        with open(temp_dict_path, 'w') as f:
            for subdomain in self.sub_dict:
                f.write(subdomain + "\n")
        massdns_path = settings.Tools_dir.joinpath("massdns")
        ns_path = settings.data_storage_dir.joinpath("ns.txt")
        output_path = settings.temp_dir.joinpath(f"{self.domain}.json")
        log_path = settings.logs_dir.joinpath("massdns_log.txt")
        call_massdns(massdns_path, temp_dict_path,
                     ns_path, output_path,
                     log_path,
                     query_type='A', process_num=1,
                     quiet_mode=True)
        try:
            with open(output_path, "r") as f:
                for line in f.readlines():
                    data = json.loads(line.strip())
                    subdomain = data.get('name')
                    self.subdomains.add(subdomain.strip('.'))
            temp_dict_path.unlink()
            output_path.unlink()
        except Exception as e:
            logger.log("ERROR", str(e))

    def run(self):
        self.begin()
        self.crtsh()
        self.chinaz()
        self.securitytrails_api()
        self.burp()
        self.result_describe = f"共收集{len(self.subdomains)}个子域名"
        self.finsh()
        return self.subdomains


if __name__ == '__main__':
    subfind = SubFind('qq.com')
    res = subfind.run()
    print(res)
