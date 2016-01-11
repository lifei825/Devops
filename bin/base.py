# -*- coding: utf-8 -*-
import time
from tornado.options import options
from tornado.web import RequestHandler


class BaseHandler(RequestHandler):
    def __init__(self, application, request, **kwargs):
        self.start = time.time()
        self.userid = 0
        self.errcode = 0
        self.response = None

        super(BaseHandler, self).__init__(application, request, **kwargs)
        self.db = self.settings['db']


class AuthHandler(BaseHandler):
    def __init__(self, application, request, **kwargs):
        super(AuthHandler, self).__init__(application, request, **kwargs)

    def get_current_user(self):
        return self.session.get('userid')

        # if options.debug:
        #     self.set_cookie("uid", str(self.userid), expires_days=30, httponly=True)
        # else:
        #     self.set_cookie("uid", str(self.userid), expires_days=30, httponly=True, secure=True)
