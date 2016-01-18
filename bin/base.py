# -*- coding: utf-8 -*-
import time
from tornado.options import options
from tornado.web import RequestHandler
from conf.settings import SESSION_SECRET, SESSION_SERVER, SESSION_TIMEOUT
from bin.util.db import Session
from bin.util import error_code


class BaseHandler(RequestHandler):
    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(application, request, **kwargs)
        self.start = time.time()
        self.uid = 0
        self.db = self.settings['db']
        self.ecode = error_code


class AuthHandler(BaseHandler):
    def __init__(self, application, request, **kwargs):
        super(AuthHandler, self).__init__(application, request, **kwargs)
        self.session = Session(SESSION_SERVER, SESSION_TIMEOUT, SESSION_SECRET, self, options.debug)

    def get_current_user(self):
        return self.session.get('uid')

