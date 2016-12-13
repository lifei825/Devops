import pymongo
from conf.settings import MONGO_OPS


class Mongodb(object):
    def __init__(self, conf):
        self.conf = conf['master']
        self.db = pymongo.MongoClient(self.conf)

    def create_id(self, collection):
        if not self.db['devops'].ids.index_information().get('name_1', ''):
            self.db['devops'].ids.ensure_index('name', unique=True)
        try:
            self.db['devops'].ids.save({'name': collection, 'id': 0})
        except Exception as e:
            print(e)

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
    print(conn.db['devops'].ids.index_information())
    conn.create_id('server')
    conn.create_id('operator')
    print(list(conn.db['devops'].ids.find({}, {'_id': 0})))
