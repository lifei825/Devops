# -*- coding: utf-8 -*-
import time
from tornado.options import options
from tornado.web import RequestHandler
from conf.settings import SESSION_SECRET, SESSION_SERVER, SESSION_TIMEOUT
from bin.util.db import Session


class BaseHandler(RequestHandler):
    def __init__(self, application, request, **kwargs):
        self.start = time.time()
        self.uid = 0

        super(BaseHandler, self).__init__(application, request, **kwargs)
        self.db = self.settings['db']


class AuthHandler(BaseHandler):
    def __init__(self, application, request, **kwargs):
        super(AuthHandler, self).__init__(application, request, **kwargs)
        self.session = Session(SESSION_SERVER, SESSION_TIMEOUT, SESSION_SECRET, self, options.debug)
        self.save_uid()

    def get_current_user(self):
        return self.session.get('uid')

    def save_uid(self, uid=None):
        if uid:
            self.uid = uid
            self.session.set('sid')
        else:
            self.uid = self.session.get('uid')

        if options.debug:
            self.set_cookie("uid", str(self.uid), expires_days=30, httponly=True)
        else:
            self.set_cookie("uid", str(self.uid), expires_days=30, httponly=True, secure=True)
