# -*- coding: utf-8 -*-
import uuid
import base64
import json


def cookie_secret():
    return base64.b64encode(uuid.uuid4().bytes+uuid.uuid4().bytes)


class Dict(dict):
    def transform(self, dtype, key, d):
        val = self.get(key, None)
        val = val.replace("'", '"').strip() if val else None
        if val is None:
            return d
        if dtype in ('dict', 'tuple', 'list'):
            return json.loads(val)
        if dtype == 'str':
            return val
        if dtype == 'int':
            return int(val)
        if dtype == 'float':
            return float(val)

    def get_dict(self, key, d=None):
        return self.transform('dict', key, d)

    def get_list(self, key, d=None):
        return self.transform('list', key, d)

    def get_tuple(self, key, d=None):
        return self.transform('tuple', key, d)

    def get_str(self, key, d=None):
        return self.transform('str', key, d)

    def get_int(self, key, d=None):
        return self.transform('int', key, d)

    def get_float(self, key, d=None):
        return self.transform('float', key, d)


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

    a = Dict()
    a.update({1: json.dumps(['1', '2', '3']), 'aa': '     aaaa', 'bb': '111', 'cc': '2.12'})
    print(a.get_dict(1))
    print(a.get_str('aa'))
    print(a.get_int('bb'))
    print(type(a.get_float('cc')))
    print(a.get_float('ccc'))
