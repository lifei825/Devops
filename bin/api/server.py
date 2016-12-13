# coding:utf8
from bin.base import AuthHandler
from tornado.gen import coroutine
from tornado.web import authenticated
from conf.settings import log
import time


class ServerList(AuthHandler):
    @authenticated
    @coroutine
    def get(self):
        doc = []
        page = records = total = ""
        try:
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
            inside_ip = request_param.get_str('inside_ip')
            outside_ip = request_param.get_str('outside_ip')
            server_type = request_param.get_int('server_type')
            server_id = request_param.get_str('id', None)
            modified = time.strftime("%F %T")
            project = request_param.get_str("project_name")
            status = request_param.get_str("status")
            location = request_param.get_str("location_name")
            note = request_param.get_str("note")
            if oper == 'add':
                uid = yield self.get_id('server')
                yield self.db['ops'].test.insert({'id': uid['id'], 'modified': modified, 'project_name': project,
                                                  'inside_ip': inside_ip,
                                                  'outside_ip': outside_ip,
                                                  'server_type': server_type,
                                                  'status': status,
                                                  'location_name': location,
                                                  'note': note})
            elif oper == 'edit':
                yield self.db['ops'].test.update({'id': server_id}, {"$set": {'modified': modified,
                                                                              'inside_ip': inside_ip,
                                                                              'outside_ip': outside_ip,
                                                                              'server_type': server_type,
                                                                              'project_name': project,
                                                                              'status': status,
                                                                              'location_name': location,
                                                                              'note': note}})

            state = self.ecode.OK
        except Exception as e:
            state = isinstance(e, Exception) and e or self.ecode.UNKNOWN
            log.error(e)

        self.write(dict(state=state.eid))
