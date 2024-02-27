import random
import requests
from config import settings, logger
import urllib3
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)


class Http_Request(object):
    def __init__(self):
        self.header = settings.request_default_headers
        if settings.enable_random_ua:
            self.header['User-Agent'] = random.choice(settings.user_agents)
        self.proxy = None
        if settings.proxy_enable:
            self.proxy = settings.request_proxy_pool
        self.timeout = settings.request_timeout_second
        self.verify = settings.request_ssl_verify
        self.cookie = None

    def get(self, url, params=None, **kwargs):
        """
        Custom get request

        :param str  url: request url
        :param dict params: request parameters
        :param kwargs: other params
        :return: response object
        """
        session = requests.Session()
        session.trust_env = False
        try:
            resp = session.get(url,
                               params=params,
                               cookies=self.cookie,
                               headers=self.header,
                               proxies=self.proxy,
                               timeout=self.timeout,
                               verify=self.verify,
                               **kwargs)
        except Exception as e:
            logger.info(e)
            return None
        return resp

    def post(self, url, data=None, **kwargs):
        """
        Custom post request

        :param str  url: request url
        :param dict data: request data
        :param kwargs: other params
        :return: response object
        """
        session = requests.Session()
        session.trust_env = False
        try:
            resp = session.post(url,
                                data=data,
                                cookies=self.cookie,
                                headers=self.header,
                                proxies=self.proxy,
                                timeout=self.timeout,
                                verify=self.verify,
                                **kwargs)
        except Exception as e:
            logger.log('ERROR', e.args[0])
            return None
        return resp
