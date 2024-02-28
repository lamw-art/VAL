import hashlib
import random
import string

from utils import conn_db

salt = "1@#$%^asnd"


def random_choices(k=6):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=k))


def gen_md5(s):
    return hashlib.md5(s.encode()).hexdigest()


def user_login(username=None, password=None):
    if not username or not password:
        return

    query = {"username": username, "password": gen_md5(salt + password)}

    if conn_db('user').find_one(query):
        item = {
            "username": username,
            "token": gen_md5(random_choices(50)),
            "type": "login"
        }
        conn_db('user').update_one(query, {"$set": {"token": item["token"]}})

        return item


def user_logout(token):
    conn_db('user').update_one({"token": token}, {"$set": {"token": None}})


def change_pass(token, old_password, new_password):
    query = {"token": token, "password": gen_md5(salt + old_password)}
    data = conn_db('user').find_one(query)
    if data:
        conn_db('user').update_one({"token": token}, {"$set": {"password": gen_md5(salt + new_password)}})
        return True
    else:
        return False
