# -*- coding: utf-8 -*-
import os
import motor
import tornado.escape
import tornado.ioloop
import tornado.options
from tornado.gen import coroutine
from tornado.options import options
from tornado.web import authenticated, Application
from bin.api.test import Test
from bin.base import AuthHandler, BaseHandler
from conf.settings import ROOT_PATH, MONGO_OPS, COOKIE_SECRET, log


tornado.options.define('port', default=8888, help='http port', type=int)
tornado.options.define('debug', default=False, help='debug mode', type=bool)
tornado.options.parse_command_line()


class IndexHandler(BaseHandler):
    def get(self):
        log.warning("index,%s" % self._headers)
        self.write("hahah")
        # self.redirect('/overview')


class OverviewHandler(AuthHandler):
    @authenticated
    @coroutine
    def get(self):
        test = yield self.db['ops'].server.find({}, {'_id': 0}).to_list(100)
        self.render('index.html', test=test)


class LoginHandler(BaseHandler):
    def get(self):
        pass

    def post(self):
        pass


class LogoutHandler(AuthHandler):
    @authenticated
    def get(self):
        self.session.remove()
        self.redirect("/login")


class WebPortal(Application):
    def __init__(self):
        handlers = [
            (r'/', IndexHandler),
            (r'/overview', OverviewHandler),
            (r'/api/test/test', Test),
            (r'/login', LoginHandler),
            (r'/logout', LogoutHandler),
        ]
        settings = dict(
            debug=options.debug,
            xsrf_cookies=True,
            login_url='/login',
            cookie_secret=COOKIE_SECRET,
            static_path=os.path.join(ROOT_PATH, 'static'),
            template_path=os.path.join(ROOT_PATH, 'templates'),
            db={'ops': motor.MotorClient(MONGO_OPS['master']).devops},
        )
        super(WebPortal, self).__init__(handlers, **settings)

    def start(self):
        self.listen(options.port, xheaders=True)
        tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    WebPortal().start()
