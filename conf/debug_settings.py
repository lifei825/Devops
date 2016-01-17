# -*- coding: utf-8 -*-
import os
import logging
import time

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SESSION_SERVER = {'host': '127.0.0.1', 'port': 6379, 'db': 2, 'password': ''}
MONGO_OPS = {'master': 'mongodb://user:passwd@127.0.0.1:27017/devops'}

SESSION_SECRET = 'aaaaaaa'
SESSION_TIMEOUT = 7200


def logs():
    logger = logging.getLogger()
    log_path = os.path.join(ROOT_PATH, 'log/%s-devops.log' % time.strftime("%Y%m%d"))
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.WARN)
    # ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
    fh.setFormatter(formatter)
    # ch.setFormatter(formatter)
    logger.addHandler(fh)
    # logger.addHandler(ch)
    return logger

log = logs()
