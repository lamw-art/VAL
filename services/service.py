import time
from config import logger


# 服务的基类
class Service(object):
    def __init__(self):
        self.service_name = ""
        self.start_time = time.time()
        self.end_time = None
        self.elapse = None
        self.task_describe = ""
        self.result_describe = ""

    def begin(self):
        logger.log('INFOR', f'开始{self.service_name}服务去完成{self.task_describe} ')

    def finsh(self):
        self.end_time = time.time()
        self.elapse = round(self.end_time - self.start_time, 1)
        logger.log('INFOR', f' {self.service_name}服务耗时{self.elapse}秒完成了{self.task_describe} '
                            f'执行结果为:{self.result_describe}')
