# -*- coding: utf-8 -*-
import datetime
import time
import os
import uuid
from conf.settings import log, IMAGE_DOMAIN, UPLOAD_PATH, UPLOAD_DOC_PATH
from base import AuthHandler, unblock
from util.helper import error, ErrorCode, streamtype, mongo_uid, gen_orderno
from util.mongotool import MongoProxy
import pymongo
from conf.settings import MONGO_HAMLET
import xlrd
import re


class UploadHandler(AuthHandler):
    @unblock
    def post(self):
        if self.userid == 0:
            return error(ErrorCode.LOGINERR)

        if self.request.files:
            try:
                fs = self.request.files['file'][0]['body']
                dbname = self.get_argument('dbname', '')
                zid = int(self.get_argument('zid', 0))
                fid = int(self.get_argument('fid', 0))
                paytype = int(self.get_argument('paytype', 0))
                ImportType = int(self.get_argument('ImportType', 0))
            except Exception as e:
                log.error(e)
                return error(ErrorCode.PARAMERR)

            file_ext = streamtype(fs)
            if file_ext not in ('.jpg', '.png', '.zip', '.xlsdoc'):
                return error(ErrorCode.DATAERR, '无效格式')
        else:
            return error(ErrorCode.REQERR)

        now = datetime.datetime.now()
        subdir = os.path.join(now.strftime('%y%m'), now.strftime('%d%H') + str(now.minute // 30))
        if dbname in ('owner', 'paylog'):
            path = UPLOAD_DOC_PATH
        else:
            path = os.path.join(UPLOAD_PATH, subdir)
        if not os.path.isdir(path):
            try:
                os.makedirs(path)
            except OSError as e:
                if e.errno == 17:
                    log.error('目录已存在：' % path)
                else:
                    log.error('%s - %s' % (e, path))
                    return error(ErrorCode.IOERR, '图片上传失败')
            except Exception as e:
                log.error('%s - %s' % (e, path))
                return error(ErrorCode.IOERR, '图片上传失败')

        if dbname in ('owner', 'paylog'):
            filename = self.request.files['file'][0]['filename']
            url = '%s/import/%s' % (IMAGE_DOMAIN, filename)
        else:
            filename = uuid.uuid4().hex + file_ext
            url = '%s/%s/%s' % (IMAGE_DOMAIN, subdir, filename)

        filepath = os.path.join(path, filename)
        try:
            fout = open(filepath, 'wb')
            fout.write(fs)
            fout.close()

            result = {'url': url}
        except Exception as e:
            log.error('%s - %s' % (e, path))
            return error(ErrorCode.IOERR, '图片上传失败')

        # 批量导入业主信息
        try:
            if dbname == 'owner':
                if ImportType == 1:
                    insertDB = Importcsv1(filepath, dbname, zid, path)
                    result.update(insertDB.run())
                elif ImportType == 2:
                    insertDB = Importcsv2(filepath, dbname, zid, path)
                    result.update(insertDB.run())
                elif ImportType == 3:
                    insertDB = Importcsv3(filepath, dbname, zid, path)
                    result.update(insertDB.run())
            elif dbname == 'paylog':
                insertDB = Importpay(filepath, dbname, zid, path, filename, paytype, fid)
                result.update(insertDB.run())
            else:
                pass
            return result
        except Exception as e:
            log.error('%s - %s' % (e, path))
            return error(ErrorCode.IOERR, '数据导入失败请检查文件格式是否正确（去掉合并单元格等无必要的行，只保留固定列名及数据格式正确）')


class Importcsv3(object):        # 导入方式三
    def __init__(self, filepath, dbname, zid, path):
        self.filepath = filepath
        self.dbname = dbname
        self.zid = zid
        self.path = path

    # 数据初始化
    def startinit(self):
        data = xlrd.open_workbook(self.filepath)
        datalist = []
        field = ['building', 'room', 'name', 'mobile', 'phone', 'sndname', 'sndphone', 'builarea', 'propfee']
        for num in range(len(data.sheets())):
            table = data.sheets()[num]
            for i in range(table.nrows):
                rowdata = table.row_values(i)
                checkdata = [str(i).strip() for i in rowdata]
                checktitle = ['业主', '业主姓名', '联系电话', '姓名']
                if (checkdata != ["" for i in range(len(rowdata))]) and len(set(checktitle) & set(checkdata)) == 0:
                    rowdict = dict(zip(field, rowdata))
                    # 物业费初始化
                    if str(rowdict['propfee']).strip():
                        rowdict['propfee'] = round(float(rowdict['propfee']) * 100)
                    # 面积初始化
                    if str(rowdict['builarea']).strip() != '':
                        rowdict['builarea'] = round(float(re.findall('\d+.\d+', str(rowdict['builarea']))[0]) * 100)
                    # 手机初始化
                    for ip in field:
                        if str(rowdict[ip]).strip() != "":
                            rowdict[ip] = str(rowdict[ip]).replace('.0', '')
                    # 住址初始化
                    if str(rowdict['building']).find('-') >= 0:
                        rowdict['building'], rowdict['unit'] = rowdict['building'].split('-')
                    else:
                        rowdict['unit'] = '1'
                    if rowdict['building'] == '' or rowdict['room'] == '':
                        continue
                    # 备注
                    rowdict['memo'] = '%s %s' % (rowdict['sndname'], rowdict['sndphone'])
                    datalist.append(rowdict)
        return datalist

    # 数据检测有无冲突,否 加入DB
    def run(self):
        conn = pymongo.MongoClient(MONGO_HAMLET['master'])
        db = MongoProxy(conn).hamlet
        zname = db.zone.find_one({'id': self.zid})
        data = self.startinit()
        mobile_err = []
        for i in data:
            result = db[self.dbname].find_one({'zid': self.zid, 'building': i['building'],
                                               'unit': i['unit'], 'room': i['room']}, {'_id': 0})
            if result:
                mobile_err.append(i)
            else:
                oid = mongo_uid('hamlet', self.dbname)
                now = round(time.time() * 1000)
                i['modified'] = now
                if not i['propfee']:
                    i['propfee'] = zname['propfee']
                i.update({
                    'id': oid,
                    'created': now,
                    'zid': self.zid,
                    'zname': zname['name'],
                    'status': 0,
                    'sex': '',
                    'idcard': '',
                    'propcert': '',
                    'checked': 0,
                    'opid': 0,
                    })
                db[self.dbname].insert(i)
        result_dict = {'冲突': len(mobile_err), '已导入': len(data)-len(mobile_err)}
        if len(mobile_err) > 0:
            result_dict["冲突信息"] = ['%s-%s-%s,' % (i['building'], i['unit'], i['room'])+i['name'] for i in mobile_err]
        return result_dict


class Importcsv1(object):        # 天畅园格式
    def __init__(self, filepath, dbname, zid, path):
        self.filepath = filepath
        self.dbname = dbname
        self.zid = zid
        self.path = path

    # 数据初始化
    def startinit(self):
        data = xlrd.open_workbook(self.filepath)
        datalist = []
        field = ['address', 'name', 'phone', 'mobile', 'builarea', 'propfee', 'sndname', 'sndphone']
        for num in range(len(data.sheets())):
            table = data.sheets()[num]
            for i in range(table.nrows):
                rowdata = table.row_values(i)
                checkdata = [str(i).strip() for i in rowdata]
                checktitle = ['业主', '业主姓名', '联系电话', '姓名']
                if (checkdata != ["" for i in range(len(rowdata))]) and len(set(checktitle) & set(checkdata)) == 0:
                    rowdict = dict(zip(field, rowdata))
                    print(rowdict)
                    # 物业费初始化
                    if str(rowdict['propfee']).strip():
                        rowdict['propfee'] = round(float(rowdict['propfee']) * 100),
                    # 面积初始化
                    if str(rowdict['builarea']).strip() != '':
                        rowdict['builarea'] = round(float(re.findall('\d+.\d+', str(rowdict['builarea']))[0]) * 100)
                    # 手机初始化
                    for ip in ['mobile', 'phone', 'sndphone']:
                        if str(rowdict[ip]).strip() != "":
                            rowdict[ip] = str(rowdict[ip]).replace('.0', '')
                    # 住址初始化
                    rowdict['building'], rowdict['unit'], rowdict['room'] = re.split('\D+', rowdict['address'])
                    if rowdict['building'] == '' or rowdict['room'] == '':
                        continue
                    # 备注
                    rowdict['memo'] = '%s %s' % (rowdict['sndname'], rowdict['sndphone'])
                    del rowdict['address']
                    datalist.append(rowdict)
        return datalist

    # 数据检测有无冲突,否 加入DB
    def run(self):
        conn = pymongo.MongoClient(MONGO_HAMLET['master'])
        db = MongoProxy(conn).hamlet
        zname = db.zone.find_one({'id': self.zid})
        data = self.startinit()
        mobile_err = []
        for i in data:
            result = db[self.dbname].find_one({'zid': self.zid, 'building': i['building'],
                                               'unit': i['unit'], 'room': i['room']}, {'_id': 0})
            if result:
                mobile_err.append(i)
            else:
                oid = mongo_uid('hamlet', self.dbname)
                now = round(time.time() * 1000)
                i['modified'] = now
                if not i['propfee']:
                    i['propfee'] = zname['propfee']
                i.update({
                    'id': oid,
                    'created': now,
                    'zid': self.zid,
                    'zname': zname['name'],
                    'status': 0,
                    'sex': '',
                    'idcard': '',
                    'propcert': '',
                    'checked': 0,
                    'opid': 0,
                    })
                db[self.dbname].insert(i)
        result_dict = {'冲突': len(mobile_err), '已导入': len(data)-len(mobile_err)}
        if len(mobile_err) > 0:
            result_dict["冲突信息"] = ['%s-%s-%s,' % (i['building'], i['unit'], i['room'])+i['name'] for i in mobile_err]
        return result_dict


class Importcsv2(object):        # 宏泽园格式
    def __init__(self, filepath, dbname, zid, path):
        self.filepath = filepath
        self.dbname = dbname
        self.zid = zid
        self.path = path

    # 数据初始化
    def startinit(self):
        data = xlrd.open_workbook(self.filepath)
        datalist = []
        field = ['name', 'sex', 'mobile', 'phone', 'idcard', 'building', 'unit', 'room', 'address', 'propcert', 'builarea', 'checked', 'memo']
        for num in range(len(data.sheets())):
            table = data.sheets()[num]
            for i in range(table.nrows):
                rowdata = table.row_values(i)
                checkdata = [str(i).strip() for i in rowdata]
                checktitle = ['业主', '业主姓名', '联系电话', '姓名']
                if (checkdata != ["" for i in range(len(rowdata))]) and len(set(checktitle) & set(checkdata)) == 0:
                    rowdict = dict(zip(field, rowdata))
                    # 面积初始化
                    if str(rowdict['builarea']).strip() != '':
                        rowdict['builarea'] = round(float(re.findall('\d+.\d+', str(rowdict['builarea']))[0]) * 100)
                    # 手机初始化
                    if rowdict['mobile'] != "":
                        rowdict['mobile'] = str(int(rowdict['mobile']))
                    # 住址初始化
                    rowdict['building'], rowdict['unit'], rowdict['room'] = rowdict['address'].split('-')
                    if rowdict['building'] == '' or rowdict['room'] == '':
                        continue
                    del rowdict['address']
                    # 日期初始化
                    if str(rowdict['checked']).find('.') == 2:
                        rowdict['checked'] = round(time.mktime(time.strptime('20'+str(rowdict['checked']), '%Y.%m.%d')) * 1000)
                    elif str(rowdict['checked']).find('.') == 4:
                        rowdict['checked'] = round(time.mktime(time.strptime(str(rowdict['checked']), '%Y.%m.%d')) * 1000)
                    datalist.append(rowdict)
        return datalist

    # 数据检测有无冲突,否 加入DB
    def run(self):
        conn = pymongo.MongoClient(MONGO_HAMLET['master'])
        db = MongoProxy(conn).hamlet
        zname = db.zone.find_one({'id': self.zid})
        data = self.startinit()
        mobile_err = []
        for i in data:
            result = db[self.dbname].find_one({'zid': self.zid, 'building': i['building'],
                                               'unit': i['unit'], 'room': i['room']}, {'_id': 0})
            if result:
                mobile_err.append(i)
            else:
                propfee = db.zone.find_one({'id': self.zid}, {'_id': 0})
                oid = mongo_uid('hamlet', self.dbname)
                now = round(time.time() * 1000)
                i['modified'] = now
                i.update({
                    'id': oid,
                    'created': now,
                    'zid': self.zid,
                    'zname': zname['name'],
                    'status': 0,
                    'propfee': propfee['propfee'],
                    })
                db[self.dbname].insert(i)
        result_dict = {'冲突': len(mobile_err), '已导入': len(data)-len(mobile_err)}
        if len(mobile_err) > 0:
            result_dict["冲突信息"] = ['%s-%s-%s,' % (i['building'], i['unit'], i['room'])+i['name'] for i in mobile_err]
        return result_dict


class Importpay(object):  # 导入paylog
    def __init__(self, filepath, dbname, zid, path, filename, paytype, fid):
        self.filepath = filepath
        self.dbname = dbname
        self.zid = zid
        self.fid = fid
        self.path = path
        self.paytype = paytype
        self.onlyfilename = 'error'+os.path.splitext(filename)[0]+'.txt'
        self.filename = os.path.join(path, self.onlyfilename)
        # info
        log.info(self.filename)
        if os.path.isfile(self.filename):
            date = datetime.datetime.now().strftime("%Y%m%d%H%M")
            newfilename = os.path.join(path, date+self.onlyfilename)
            os.rename(self.filename, newfilename)

    def errlog(self, errdata, errtype):
        with open(self.filename, 'a') as f:
            strs = errtype+errdata
            f.write(strs+'\n')

    # 数据初始化
    def startinit(self):
        # info
        log.info("start open xlrd")
        data = xlrd.open_workbook(self.filepath)
        payloglist = []
        paymentlist = []
        field = ['uname', 'sex', 'mobile', 'phone', 'idcard', 'building', 'unit', 'room', 'address', 'propcert', 'builarea', 'checked', 'fee', 'light']
        propfee_stat = 0
        # 判断是否有物业费表
        feename = '物业费'
        if feename in [i.name for i in data.sheets()]:
            propfee_dict = {}
            # info
            log.info("start read 物业费")
            propfee_table = data.sheet_by_name(feename)
            propfee_dict.update([propfee_table.row_values(i) for i in range(propfee_table.nrows)])
            propfee_stat = 1
        # 初始化收费年数
        vaildData = [i for i in data.sheets() if i.name != feename]
        colnum = vaildData[0].ncols
        year = datetime.datetime.now().year
        yearlist = []
        yearnum = colnum - len(field)
        for y in range(yearnum):
            yearlist += [year]
            year -= 1
        field[-1:-1] = sorted(yearlist)
        # 数据转换为字典存入列表
        for num in range(len(data.sheets())):
            table = data.sheets()[num]
            # info
            log.info("sheets name:"+table.name)
            if table.name == '物业费':
                continue
            if propfee_stat == 1:
                builnum = int(re.findall('\d+', table.name)[0])
                propfee = round(float(propfee_dict.get(builnum, 0)) * 100)

            for i in range(table.nrows):
                rowdata = table.row_values(i)
                # 一行非空小于4的移到err日志
                fkong = len(rowdata)-rowdata.count('')
                if fkong < 4 or str(rowdata[11]).strip() == '':
                    self.errlog(','.join(map(str, rowdata)), "数据缺失:")
                elif (rowdata != ["" for i in range(len(rowdata))]) and ('姓名' not in rowdata):
                    rowdict = dict(zip(field, rowdata))
                # 日期初始化
                    checked0 = str(rowdict['checked']).strip()
                    try:
                        if checked0.find('.') == 2 and checked0.count('.') == 2:
                            checked = round(time.mktime(time.strptime('20'+checked0, '%Y.%m.%d')) * 1000)
                        elif checked0.find('.') == 4 and checked0.count('.') == 2:
                            checked = round(time.mktime(time.strptime(checked0, '%Y.%m.%d')) * 1000)
                    except Exception as e:
                            self.errlog(','.join(map(str, rowdata)), "数据缺失:")
                            continue
                # 手机初始化
                    if rowdict['mobile'] == "" and rowdict['phone'] != "":
                        del rowdict['mobile']
                        rowdict['mobile'] = rowdict['phone']
                    if rowdict['mobile'] != "":
                        rowdict['mobile'] = str(int(rowdict['mobile']))
                    # 住址初始化
                    rowdict['building'], rowdict['unit'], rowdict['room'] = rowdict['address'].split('-')
                    # 面积初始化
                    if str(rowdict['builarea']).strip() != '':
                        rowdict['builarea'] = round(float(re.findall('\d+.\d+', str(rowdict['builarea']))[0]) * 100)
                    # 每行 年循环
                    for y in yearlist:
                        appdict = {
                            'zid': self.zid,
                            'fid': self.fid,
                            'sex': rowdict['sex'],
                            'idcard': rowdict['idcard'],
                            'propcert': rowdict['propcert'],
                            'checked': checked,
                            'phone': rowdict['phone'],
                            'uname': rowdict['uname'],
                            'mobile': rowdict['mobile'],
                            'building': rowdict['building'],
                            'room': rowdict['room'],
                            'unit': rowdict['unit'],
                            'fee': round(float(rowdict['fee']) * 100),
                            'stime': round(time.mktime(time.strptime(str(y)+'0101', '%Y%m%d')) * 1000),
                            'etime': round(time.mktime(time.strptime(str(y)+'1231', '%Y%m%d')) * 1000),
                            'type': self.paytype,
                            'builarea': rowdict['builarea'],
                            'propfee': locals().get('propfee', 0)
                        }
                        if str(rowdict[y]).strip() != '' and str(rowdict[y]).find('未') < 0:
                            appdict['paytype'] = 0
                            appdict['qtorder'] = ''
                            payloglist.append(appdict)
                        else:
                            paymentlist.append(appdict)
                        del appdict
                    del rowdict

        return payloglist, paymentlist

    # 数据检测有无冲突,否 加入DB
    def run(self):
        conn = pymongo.MongoClient(MONGO_HAMLET['master'])
        db = MongoProxy(conn).hamlet
        zoneone = db.zone.find_one({'id': self.zid}, {'_id': 0})
        dataname = {1: 'paylog', 2: 'payment'}
        payloglist, paymentlist = self.startinit()
        result_dict = {}
        n = 1
        for data in (payloglist, paymentlist):
            data_err = []
            owner_new = []
            for i in data:
                sex, idcard, propcert, checked, phone = i.pop('sex'), i.pop('idcard'), i.pop('propcert'), i.pop('checked'), i.pop('phone')
                query = db[dataname[n]].find_one(i)
                if query:
                    data_err.append(i)
                else:
                    # 是否有物业费表
                    if i.get('propfee', 0) == 0:
                        i['propfee'] = zoneone['propfee']

                    owners = db.owner.find_one({'building': i['building'], 'unit': i['unit'], 'room': i['room'],
                                                'zid': self.zid}, {'_id': 0})
                    uid = 0
                    if owners:
                        i['oid'] = owners['id']
                        user_dict = db.user.find_one({'oid': owners['id']}, {'_id': 0})
                        uid = 0 if not user_dict else user_dict['id']

                    else:  # owner无此业主，则创建
                        oid = mongo_uid('hamlet', 'owner')
                        now = round(time.time() * 1000)
                        owneradd = {'modified': now}
                        owneradd.update({
                            'id': oid,
                            'created': now,
                            'zid': self.zid,
                            'zname': zoneone['name'],
                            'name': i['uname'],
                            'sex': sex,
                            'mobile': i['mobile'],
                            'phone': phone,
                            'idcard': idcard,
                            'building': i['building'],
                            'unit': i['unit'],
                            'room': i['room'],
                            'propcert': propcert,
                            'builarea': i['builarea'],
                            'status': 0,
                            'propfee': i['propfee'],
                            'checked': checked,
                            'opid': 0
                            })
                        db.owner.insert(owneradd)
                        owner_new.append(owneradd)
                        i['oid'] = oid

                    payid = mongo_uid('hamlet', dataname[n])
                    i['orderno'] = gen_orderno(payid)
                    i['modified'] = i['etime']
                    i.update({
                        'id': payid,
                        'created': i['etime'],
                        'uid': uid,
                    })
                    db[dataname[n]].insert(i)
            result_dict[dataname[n]] = {'冲突': len(data_err), '添加业主': len(owner_new), '已导入': len(data)-len(data_err)}
            del data
            n += 1
        result_dict["错误信息"] = "%s/import/%s" % (IMAGE_DOMAIN, self.onlyfilename)
        return result_dict