# -*- coding: utf-8 -*-
from tornado.web import authenticated, Application, RequestHandler
import time
import os


class Test(RequestHandler):
    def get(self):
        time.sleep(5)
        self.write({'status': 1})

if __name__ == '__main__':
    pass
