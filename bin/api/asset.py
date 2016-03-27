# coding:utf8
from bin.base import AuthHandler
from tornado.gen import coroutine
from tornado.web import authenticated
from conf.settings import log


class ServerList(AuthHandler):
    @authenticated
    @coroutine
    def get(self):
        doc = []
        page = records = total = ""
        try:
            # a = yield self.get_id('server')
            request_param = self.request_arguments(['page'])
            page = request_param.get_int('page', 1)
            length = request_param.get_int('rows', 10)
            sord = request_param.get_str('sord', 1)
            sidx = request_param.get_str('sidx', 'id')
            start = (page-1) * length
            sord = 1 if sord == 'desc' else -1
            doc = yield self.db['ops'].test.find({}, {'_id': 0}
                                                 ).sort([(sidx, sord)]).skip(start).limit(length).to_list(length)
            records = yield self.db['ops'].test.count()
            total, reste = divmod(records, length)
            total = total+1 if reste > 0 else total

            state = self.ecode.OK
        except Exception as e:
            state = isinstance(e, Exception) and e or self.ecode.UNKNOWN
            log.error(e)

        self.write(dict(rows=doc, page=page, records=records, total=total, state=state.eid))


class ServerSave(AuthHandler):
    @authenticated
    @coroutine
    def post(self):
        try:
            request_param = self.request_arguments(['oper'])
            oper = request_param.get_str('oper')
            print(request_param)
            if oper == 'add':
                uid = yield self.get_id('server')
                yield self.db['ops'].test.insert({'id': uid['id'], 'sdate': '2016-03-01', 'name': 'aa',
                                                  'stock': 'Yes',
                                                  'ship': "aa",
                                                  'note': "haha"})

            state = self.ecode.OK
        except Exception as e:
            state = isinstance(e, Exception) and e or self.ecode.UNKNOWN
            log.error(e)

        self.write(dict(state=state.eid))
