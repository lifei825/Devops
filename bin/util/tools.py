# -*- coding: utf-8 -*-
import uuid
import base64


def cookie_secret():
    return base64.b64encode(uuid.uuid4().bytes+uuid.uuid4().bytes)

if __name__ == '__main__':
    print(cookie_secret())