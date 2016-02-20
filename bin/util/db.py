import redis
import base64
import uuid
import json
from conf.settings import log


class Session(object):
    def __init__(self, session_server, session_timeout, session_secret, request, secure):
        self.redis = redis.StrictRedis(connection_pool=redis.ConnectionPool(**session_server))
        self.session_secret = session_secret
        self.session_timeout = session_timeout
        self.request = request
        self.secure = secure

    def set(self, key, val=None):
        if key == "sid":
            sid = base64.b64encode(uuid.uuid5(uuid.NAMESPACE_OID, self.session_secret).bytes+uuid.uuid4().bytes)
            self.redis.setex(sid, self.session_timeout, json.dumps(val))
            if self.secure:
                self.request.set_cookie('sid', sid, httponly=True)
                self.request.set_cookie('uid', str(val['id']), httponly=True)
            else:
                self.request.set_secure_cookie('sid', sid, httponly=True)
                self.request.set_secure_cookie('uid', str(val['id']), httponly=True)
        else:
            user_into = self.get('info')
            user_into[key] = val
            if self.secure:
                sid = self.request.get_cookie('sid')
            else:
                sid = self.request.get_secure_cookie('sid')
            self.redis.setex(sid, self.session_timeout, json.dumps(user_into))

    def get(self, key):
        val = None
        try:
            if self.secure:
                sid = self.request.get_cookie('sid')
            else:
                sid = self.request.get_secure_cookie('sid')
            data = self.redis.get(sid)
            user_info = json.loads(data.decode()) if data else {}
            if key == "uid" and user_info:
                val = user_info.get('id')
                self.redis.setex(sid, self.session_timeout, json.dumps(user_info))

            elif key == 'info':
                val = user_info

            # val = val.decode()
        except Exception as e:
            val = False
            log.info(e)

        return val

    def remove(self):
        if self.secure:
            sid = self.request.get_cookie('sid')
        else:
            sid = self.request.get_secure_cookie('sid')
        self.redis.delete(sid)
        self.request.clear_all_cookies()
