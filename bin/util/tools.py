# -*- coding: utf-8 -*-
import uuid
import base64


def cookie_secret():
    return base64.b64encode(uuid.uuid4().bytes+uuid.uuid4().bytes)

if __name__ == '__main__':
    from conf.settings import SESSION_SECRET as secret
    print(cookie_secret())
    print(uuid.uuid5(uuid.NAMESPACE_X500, "a"))
    print(uuid.uuid5(uuid.NAMESPACE_OID, "a"))
    print(uuid.uuid5(uuid.NAMESPACE_URL, "a"))
    print(uuid.uuid5(uuid.NAMESPACE_X500, "2"))
    print(uuid.uuid5(uuid.NAMESPACE_DNS, "2"))
    print(base64.b64encode(uuid.uuid5(uuid.NAMESPACE_OID, secret).bytes+uuid.uuid4().bytes))
    print(base64.b64encode(uuid.uuid5(uuid.NAMESPACE_OID, secret).bytes+uuid.uuid4().bytes))
    print(base64.b64encode(uuid.uuid5(uuid.NAMESPACE_OID, secret).bytes+uuid.uuid4().bytes))
    print(base64.b64encode(uuid.uuid5(uuid.NAMESPACE_OID, secret).bytes+uuid.uuid4().bytes))
    print(base64.b64encode(uuid.uuid5(uuid.NAMESPACE_OID, secret).bytes+uuid.uuid4().bytes))
