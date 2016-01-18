# coding:utf-8


class ErrorCode(Exception):
    def __init__(self, eid, message):
        self.eid = eid
        self.message = message

OK = ErrorCode(0, '正确')
UNKNOW = ErrorCode(1, '未知错误')
LOGINERR = ErrorCode(2, '登陆验证错误')
