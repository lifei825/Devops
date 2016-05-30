# coding:utf8
from bin.base import AuthHandler
from tornado.gen import coroutine
from tornado.web import authenticated
from conf.settings import log


class OperatorSave(AuthHandler):
    def get(self, *args, **kwargs):
        self.render('test.html')

    # @authenticated
    @coroutine
    def post(self):
        try:
            request_param = self.request_arguments(['oper'])
            oper = request_param.get_str('oper', 'add')
            if oper == 'add':
                uid = yield self.get_id('operator')
                yield self.db['ops'].operator.insert({'id': uid['id'], 'modified': '2016-03-01 01:00', 'role': 0,
                                                      'status': 1,
                                                      'pid': [],
                                                      'pwd': "123",
                                                      'user': 'admin',
                                                      })

            state = self.ecode.OK
        except Exception as e:
            state = isinstance(e, Exception) and e or self.ecode.UNKNOWN
            log.error(e)

        self.write(dict(state=state.eid))


