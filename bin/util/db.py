import redis
import base64
import uuid


class Session(object):
    def __init__(self, session_server, session_timeout, session_secret, request, secure):
        self.redis = redis.StrictRedis(connection_pool=redis.ConnectionPool(**session_server))
        self.session_secret = session_secret
        self.session_timeout = session_timeout
        self.request = request
        self.secure = secure

    def set(self):
        sid = base64.b64encode(uuid.uuid5(uuid.NAMESPACE_OID, self.session_secret).bytes+uuid.uuid4().bytes)
        self.redis.setex(sid, self.session_timeout, self.request.uid)
        if self.secure:
            self.request.set_secure_cookie('sid', sid, httponly=True, secure=True)
        else:
            self.request.set_secure_cookie('sid', sid, httponly=True)

    def get(self, argv):
        if argv == 'uid':
            uid = self.request.get_secure_cookie('uid')

            return uid
