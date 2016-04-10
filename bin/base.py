# -*- coding: utf-8 -*-
import time
from tornado.options import options
from tornado.web import RequestHandler
from conf.settings import SESSION_SECRET, SESSION_SERVER, SESSION_TIMEOUT, log
from bin.util.db import Session
from bin.util import error_code
from bin.util.tools import Dict


class BaseHandler(RequestHandler):
    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(application, request, **kwargs)
        self.start = time.time()
        self.user_info = {}
        self.uid = 0
        self.db = self.settings['db']
        self.ecode = error_code

    def request_arguments(self, params):
        arguments = self.request.arguments
        for param in params:
            if not arguments.get(param, ''):
                log.error("param:%s is need" % param)
                raise self.ecode.PARAM_ERR
        dto = Dict()
        dto.update({key: arguments[key][0].decode('utf-8') for key in arguments})
        log.warning("req params=%s" % dto)
        return dto

    def get_id(self, name):
        db_id = self.db['ops'].ids.find_and_modify(query={'name': name}, update={'$inc': {'id': 1}},
                                                   new=True, fields={'_id': 0, 'id': 1})
        return db_id


class AuthHandler(BaseHandler):
    def __init__(self, application, request, **kwargs):
        super(AuthHandler, self).__init__(application, request, **kwargs)
        self.session = Session(SESSION_SERVER, SESSION_TIMEOUT, SESSION_SECRET, self, options.debug)
        self.save_user_info()

    def get_current_user(self):
        return self.session.get('uid')

    def save_user_info(self, user_info=None):
        if user_info:
            self.user_info = user_info
            self.session.set('sid', user_info)
        else:
            self.user_info = self.session.get('info') or {}

        if self.user_info:
            if options.debug:
                self.set_cookie("uid", str(self.user_info['id']), expires_days=30, httponly=True)
            else:
                self.set_secure_cookie("uid", str(self.user_info['id']), expires_days=30, httponly=True)
