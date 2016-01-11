# -*- coding: utf-8 -*-
import os
import tornado.escape
import tornado.ioloop
import tornado.options
from tornado.gen import coroutine
from tornado.options import options
from tornado.web import authenticated, Application, RequestHandler
from bin.api.test import Test
from bin.base import AuthHandler, BaseHandler
from conf.settings import ROOT_PATH, MONGO_OPS, COOKIE_SECRET
import motor

tornado.options.define('port', default=8000, help='http port', type=int)
tornado.options.define('debug', default=False, help='debug mode', type=bool)
tornado.options.parse_command_line()


def auth_api(run):
    def wrapper(self, *args, **kwargs):
        if self._headers['Server'] == 'TornadoServer/4.2':
            print('success', self._headers)
            run(self, *args, **kwargs)
    return wrapper


class IndexHandler(RequestHandler):
    #@auth_api
    def get(self):
        self.redirect('/overview')


class OverviewHandler(RequestHandler):
    def __init__(self, application, request, **kwargs):
        super(OverviewHandler, self).__init__(application, request, **kwargs)
        self.db = self.settings['db']

    @coroutine
    def get(self):
        test = yield self.db['ops'].server.find({}, {'_id': 0}).to_list(100)
        self.render('index.html', test=test)
        # self.write('start1111')


class LogoutHandler(AuthHandler):
    def get(self):
        # self.session.remove()
        self.redirect("/login")


class WebPortal(Application):
    def __init__(self):
        handlers = [
            (r'/', IndexHandler),
            (r'/overview', OverviewHandler),
            (r'/api/test/test', Test),
            # (r'/login', LoginHandler),
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
            # session=Session(SESSION_SECRET, SESSION_SERVER, SESSION_TIMEOUT)
        )
        print(settings["static_path"])
        super(WebPortal, self).__init__(handlers, **settings)

    def start(self):
        self.listen(options.port, xheaders=True)
        tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    WebPortal().start()
