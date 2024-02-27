from pymongo import MongoClient
from config import settings


class ConnMongo(object):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(ConnMongo, cls).__new__(cls)
            cls.instance.conn = MongoClient(settings.MONGO_URL)
        return cls.instance


def conn_db(collection, db_name=None):
    conn = ConnMongo().conn
    if db_name:
        return conn[db_name][collection]
    else:
        return conn[settings.MONGO_DB][collection]
