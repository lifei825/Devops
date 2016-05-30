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
from bin.api.server import ServerList, ServerSave
from bin.api.operator import OperatorSave
from bin.base import AuthHandler, BaseHandler
from conf.settings import ROOT_PATH, MONGO_OPS, COOKIE_SECRET, log


tornado.options.define('port', default=8888, help='http port', type=int)
tornado.options.define('debug', default=False, help='debug mode', type=bool)
tornado.options.parse_command_line()


class IndexHandler(BaseHandler):
    def get(self):
        log.warning("index,%s" % self._headers)
        # self.write("hahah")
        # self.redirect('/overview')
        self.render('blank.html')


class OverviewHandler(AuthHandler):
    @authenticated
    @coroutine
    def get(self):
        print(self.user_info)
        test = yield self.db['ops'].server.find({}, {'_id': 0}).to_list(100)
        self.render('overview.html', test=test, title="overview")


class ServerListHandler(AuthHandler):
    @authenticated
    @coroutine
    def get(self):
        doc = yield self.db['ops'].server.find({}, {'_id': 0}).to_list(100)
        self.render('server.html', doc=doc, title="资产管理")


class LoginHandler(AuthHandler):
    def get(self):
        if self.session.get('uid'):
            self.redirect('/overview')
        else:
            self.render('login.html')

    @coroutine
    def post(self):
        user = self.get_argument('user')
        passwd = self.get_argument('passwd')
        print(self.user_info)
        try:
            user_info = yield self.db['ops'].operator.find_one({'user': user, 'pwd': passwd},
                                                               {'_id': 0, 'passwd': 0})
            if user_info:
                self.save_user_info(user_info)
                self.redirect(self.get_argument("next", "/overview"))
            else:
                raise self.ecode.LOGIN_ERR

        except Exception as e:
            state = isinstance(e, Exception) and e or self.ecode.UNKNOW
            log.error(e)
            self.render('login.html', status=state.eid)


class LogoutHandler(AuthHandler):
    @authenticated
    def get(self):
        self.session.remove()
        self.redirect("/login")


class WebPortal(Application):
    def __init__(self):
        handlers = [
            # test
            (r'/', IndexHandler),
            (r'/api/test/test', Test),
            # manager
            (r'/login', LoginHandler),
            (r'/logout', LogoutHandler),
            # overview
            (r'/overview', OverviewHandler),
            # server
            (r'/server', ServerListHandler),
            (r'/server/list', ServerList),
            (r'/server/save', ServerSave),
            (r'/operator/save', OperatorSave),
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
