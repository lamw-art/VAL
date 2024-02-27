import binascii
import re
from urllib.parse import urljoin
from config import logger

from utils.req import Http_Request
import mmh3
from pyquery import PyQuery


def get_title(body):
    """
    根据页面源码返回标题
    :param body: <title>sss</title>
    :return: sss
    """
    result = ''
    title_patten = re.compile(rb'<title>([^<]{1,200})</title>', re.I)
    title = title_patten.findall(body)
    if len(title) > 0:
        try:
            result = title[0].decode("utf-8")
        except Exception as e:
            result = title[0].decode("gbk", errors="replace")
    return result.strip()


def fetch_favicon(url):
    f = FetchFavicon(url)
    return f.run()


http_req = Http_Request()


class FetchFavicon(object):
    def __init__(self, url):
        self.url = url
        self.favicon_url = None

    def build_result(self, data):
        result = {
            "data": data,
            "url": self.favicon_url,
            "hash": mmh3.hash(data)
        }
        return result

    def run(self):
        result = {}
        try:
            favicon_url = urljoin(self.url, "/favicon.ico")
            data = self.get_favicon_data(favicon_url)
            if data:
                self.favicon_url = favicon_url
                return self.build_result(data)

            favicon_url = self.find_icon_url_from_html()
            if not favicon_url:
                return result
            data = self.get_favicon_data(favicon_url)
            if data:
                self.favicon_url = favicon_url
                return self.build_result(data)

        except Exception as e:
            logger.warning("error on {} {}".format(self.url, e))

        return result

    def get_favicon_data(self, favicon_url):
        conn = http_req.get(favicon_url)
        if conn is not None:
            if conn.status_code != 200:
                return

            if len(conn.content) <= 80:
                logger.debug("favicon content len lt 100")
                return

        if "image" in conn.headers.get("Content-Type", ""):
            data = self.encode_bas64_lines(conn.content)
            return data

    @staticmethod
    def encode_bas64_lines(s):
        """Encode a string into multiple lines of base-64 data."""
        MAXLINESIZE = 76  # Excluding the CRLF
        MAXBINSIZE = (MAXLINESIZE // 4) * 3
        pieces = []
        for i in range(0, len(s), MAXBINSIZE):
            chunk = s[i: i + MAXBINSIZE]
            pieces.append(bytes.decode(binascii.b2a_base64(chunk)))
        return "".join(pieces)

    def find_icon_url_from_html(self):
        conn = http_req.get(self.url)
        if b"<link" not in conn.content:
            return
        d = PyQuery(conn.content)
        links = d('link').items()
        icon_link_list = []
        for link in links:
            if link.attr("href") and 'icon' in link.attr("rel"):
                icon_link_list.append(link)

        for link in icon_link_list:
            if "shortcut" in link:
                return urljoin(self.url, link.attr('href'))

        if icon_link_list:
            return urljoin(self.url, icon_link_list[0].attr('href'))


def get_headers(response, body):
    # version 字段目前只能是10或者11
    version = "1.1"
    if response.version == 10:
        version = "1.0"

    first_line = "HTTP/{} {} {}\n".format(version, response.status, response.reason)

    headers = str(response.headers)

    headers = headers.strip()
    if not response.headers.get("Content-Length"):
        headers = "{}\nContent-Length: {}".format(headers, len(body))

    return first_line + headers
