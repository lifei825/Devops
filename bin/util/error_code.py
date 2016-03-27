# coding:utf-8


class ErrorCode(Exception):
    def __init__(self, eid, message):
        self.eid = eid
        self.message = message

OK = ErrorCode(0, '正确')
UNKNOWN = ErrorCode(1, '未知错误')
LOGIN_ERR = ErrorCode(2, '登陆验证错误')
PARAM_ERR = ErrorCode(3, '参数错误')
