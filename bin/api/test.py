# -*- coding: utf-8 -*-
from tornado.web import authenticated, Application, RequestHandler
import time
import os


class Test(RequestHandler):
    def get(self):
        time.sleep(5)
        self.write({'status': 1})

import random
a = random.sample(range(10000),15)
print(a)
i = 0
j = len(a)-1


def kp(L, low, hight):
    i = low
    j = hight
    if i >= j:
        return L
    K = L[i]
    while i<j:
        while K <= L[j] and i < j:
                j -= 1
        L[i] = L[j]
        while K >= L[i] and i < j:
                i += 1
        L[j] = L[i]
    L[i] = K
    print(L, i, j, K)
    kp(L, low, i-1)
    kp(L, j+1, hight)
    return (L)


if __name__ == '__main__':
    print(kp(a, i, j))

