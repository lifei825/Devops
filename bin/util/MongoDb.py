import pymongo
from conf.settings import MONGO_OPS


class Mongodb(object):
    def __init__(self, conf):
        self.conf = conf['master']
        self.db = pymongo.MongoClient(self.conf).devops

    def create_id(self, collection):
        self.db.ids.ensure_index('name', unique=True)
        self.db.ids.save({'name': collection, 'id': 0})


if __name__ == '__main__':
    conn = Mongodb(MONGO_OPS)
    # print(conn.db.test.remove())
    # import random
    # l = "FE:IN:TN:AR".split(':')
    # for i in range(100):
    #     conn.db.test.insert({'id': i, 'sdate': '2016-03-01', 'name': 'aa',
    #                          'stock': 'Yes' if i%2 == 0 else 'No',
    #                          'ship': random.choice(l),
    #                          'note': "haha"})
    #
    # print(conn.db.test.find_one({}, {'_id': 0}))
    conn.create_id('server')
    conn.create_id('operator')
    print(conn.db.ids.find_one({}, {'_id': 0}))
