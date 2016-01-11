# -*- coding: utf-8 -*-
import os

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SESSION_SERVER = {'host': '127.0.0.1', 'port': 6379, 'db': 2, 'password': ''}
MONGO_OPS = {'master': 'mongodb://user:passwd@127.0.0.1:27017/devops'}

SESSION_SECRET = 'aaaaaaa'
SESSION_TIMEOUT = 7200


