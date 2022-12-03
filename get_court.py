#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:Gary
# Time : 2021/11/14 9:50
import time
import requests
import json
import datetime
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr


class SportInfoService:
    """
智慧珞珈小程序  场馆预约信息爬取
    """

    def __init__(self):
        self.uid = ''  # 需要抓包
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36 MicroMessenger/7.0.9.501 NetType/WIFI MiniProgramEnv/Windows WindowsWechat',
            'content-type': 'application/json',
            'token': '',
            'x-outh-sid': '',  # 需要抓包
            'x-outh-token': self.uid,
            'Referer': 'https://servicewechat.com/wx20499591d49cdb5c/53/page-frame.html',
            'Accept-Encoding': 'gzip, deflate, br',
            "Host": "miniapp.whu.edu.cn",
            "Connection": "keep - alive",
            "Content - Length": "138"

        }
        self.session = requests.Session()
        self.session.headers = self.headers
        self.today_str = datetime.datetime.now().strftime('%Y-%m-%d')
        self.tomorrow_str = (datetime.datetime.now() +
                             datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        self.result = []
        self.result_v2 = {}
        self.receiver_list = {'xxx@qq.com': "x", }  # 键是邮箱地址 值是收件人姓名
        self.ignore_list = ['医学部体育馆']
        self.get_page_time = ''

    def get_base_info(self):
        url = 'https://miniapp.whu.edu.cn/wisdomapi/v1.0.0/ballBooking/queryHomeBookingInfo'
        data = {"uid": self.uid, }
        res = requests.post(url, json=data, headers=self.headers)
        # print(res.text)
        data = json.loads(res.text)
        gym_list = []
        if data.get("errcode") == 0:
            data_info = data.get("data").get("gymnasiumList")
            for gym in data_info:
                placeId = gym.get("placeId")
                placeName = gym.get("placeName")

                # print('场馆id：', placeId, '场馆名：', placeName)
                if placeName != '医学部体育馆' and placeName != '宋卿体育馆':  # 去除医学部、宋卿体育馆
                    gym_list.append((placeId, placeName))
                    self.result_v2[placeName] = []
        else:
            print(data.get("errmsg"), data.get("detailErrMsg"))
        return gym_list

    def get_free_seat(self, place_id, place_name, date):
        url = 'https://miniapp.whu.edu.cn/wisdomapi/v1.0.0/ballBooking/queryPlaceListByTypeId'
        data = {
            "typeId": "1372606679c04412b5afbb675fd9f6cb",
            "reserveDate": self.today_str if date == 'today' else self.tomorrow_str,
            "uid": self.uid,
            "placeId": place_id,
            "currentPage": 1,
            "pageSize": 5
        }
        res = requests.post(url, json=data, headers=self.headers)
        # if place_name == '信息学部西区体育馆':
        #     print(res.text)
        data = json.loads(res.text)
        if data.get("errcode") == 0:
            try:
                data_info = data.get("data")
                if data_info:
                    data_info = data_info.get("pageData")[0]
                    placeName = data_info.get("placeName")
                    canReserve = data_info.get("canReserve")
                    placeStatus = data_info.get("placeStatus")
                    if placeStatus == '1':
                        print(place_name, '该馆已闭馆')
                    elif canReserve == '0':
                        morningCanReserve = data_info.get("morningCanReserve")
                        # print(morningCanReserve,type(morningCanReserve),morningCanReserve == 0)
                        if morningCanReserve == '0':
                            self.result.append([placeName, '早上（8-14点）有场子哦'])
                            morningCanReserve = '有'
                        else:
                            morningCanReserve = '无'
                        afternoonCanReserve = data_info.get(
                            "afternoonCanReserve")
                        if afternoonCanReserve == '0':
                            self.result.append([placeName, '下午（14-18点）有场子哦'])
                            afternoonCanReserve = '有'
                        else:
                            afternoonCanReserve = '无'
                        eveningCanReserve = data_info.get("eveningCanReserve")
                        if eveningCanReserve == '0':
                            self.result.append([placeName, '晚上（18-21点）有场子哦'])
                            eveningCanReserve = '有'
                        else:
                            eveningCanReserve = '无'

                        # 精确到场地号
                        placeFieldInfoList = data_info.get(
                            "placeFieldInfoList")
                        detail_all = ''
                        for i in placeFieldInfoList:
                            fieldReserveStatus = i.get("fieldReserveStatus")
                            if fieldReserveStatus == '0':
                                fieldNum = i.get("fieldNum")  # 场地号
                                reserveTimeInfoList = i.get(
                                    "reserveTimeInfoList")
                                detail_info = str(
                                    fieldNum) + '号场' + '  '
                                time_info = ''
                                for reserve_time in reserveTimeInfoList:
                                    canReserve_ = reserve_time.get(
                                        "canReserve")
                                    if canReserve_ == "0":
                                        reserveBeginTime = reserve_time.get(
                                            "reserveBeginTime")
                                        reserveEndTime = reserve_time.get(
                                            "reserveEndTime")
                                        time_info += reserveBeginTime + '到' + reserveEndTime + '、'

                                detail_info = detail_info + time_info + '有场子'
                                print(detail_info)
                                detail_all = detail_all + detail_info + '。'
                        if len(detail_all) > 0:
                            self.result_v2[place_name] = detail_all
                        else:
                            # self.result_v2[place_name] = '无'
                            self.result_v2.pop(place_name)

                        print(place_name, '早上有空场子不?', morningCanReserve, '下午有空场子不?', afternoonCanReserve,
                              '晚上有空场子不?',
                              eveningCanReserve)
                    else:
                        print(place_name, '无可用时间')
                else:
                    print(place_name, '无羽毛球场馆')
            except Exception as e:
                print(res.text, str(e))
        else:
            print(data.get("errmsg"), data.get("detailErrMsg"))
        return None

    def get_free_seat_v2(self, date):
        url = 'https://miniapp.whu.edu.cn/wisdomapi/v1.0.0/ballBooking/queryPlaceListByTypeId'
        data = {
            "typeId": "1372606679c04412b5afbb675fd9f6cb",
            # 1372606679c04412b5afbb675fd9f6cb 羽毛球
            # fecb21a37a4b4845882fa39bf011682b 乒乓球

            "reserveDate": self.today_str if date == 'today' else self.tomorrow_str,
            "uid": self.uid,
            "currentPage": 1,
            "pageSize": 10
        }
        self.get_page_time = str(datetime.datetime.now())
        res = self.session.post(url, json=data, headers=self.headers)
        # if place_name == '信息学部西区体育馆':
        #     print(res.text)
        return res

    def ana_data(self, html):
        data = json.loads(html.text)
        if data.get("errcode") == 0:
            try:
                data_info_all = data.get("data")
                if data_info_all:
                    data_info_list = data_info_all.get("pageData")
                    for data_info in data_info_list:
                        placeName = data_info.get("placeName")
                        canReserve = data_info.get("canReserve")
                        placeStatus = data_info.get("placeStatus")
                        if placeName not in self.ignore_list:
                            if placeStatus == '1':
                                print(placeName, '该馆已闭馆')
                            elif canReserve == '0':
                                morningCanReserve = data_info.get(
                                    "morningCanReserve")
                                if morningCanReserve == '0':
                                    self.result.append(
                                        [placeName, '早上（8-14点）有场子哦'])
                                    morningCanReserve = '有'
                                else:
                                    morningCanReserve = '无'
                                afternoonCanReserve = data_info.get(
                                    "afternoonCanReserve")
                                if afternoonCanReserve == '0':
                                    self.result.append(
                                        [placeName, '下午（14-18点）有场子哦'])
                                    afternoonCanReserve = '有'
                                else:
                                    afternoonCanReserve = '无'
                                eveningCanReserve = data_info.get(
                                    "eveningCanReserve")
                                if eveningCanReserve == '0':
                                    self.result.append(
                                        [placeName, '晚上（18-21点）有场子哦'])
                                    eveningCanReserve = '有'
                                else:
                                    eveningCanReserve = '无'

                                # 精确到场地号
                                placeFieldInfoList = data_info.get(
                                    "placeFieldInfoList")
                                detail_all = ''
                                for i in placeFieldInfoList:
                                    fieldReserveStatus = i.get(
                                        "fieldReserveStatus")
                                    if fieldReserveStatus == '0':
                                        fieldNum = i.get("fieldNum")  # 场地号
                                        reserveTimeInfoList = i.get(
                                            "reserveTimeInfoList")
                                        detail_info = str(
                                            fieldNum) + '号场' + '  '
                                        time_info = ''
                                        for reserve_time in reserveTimeInfoList:
                                            canReserve_ = reserve_time.get(
                                                "canReserve")
                                            if canReserve_ == "0":
                                                reserveBeginTime = reserve_time.get(
                                                    "reserveBeginTime")
                                                reserveEndTime = reserve_time.get(
                                                    "reserveEndTime")
                                                time_info += reserveBeginTime + '到' + reserveEndTime + '、'

                                        detail_info = detail_info + time_info + '有场子'
                                        print(detail_info)
                                        detail_all = detail_all + detail_info + '。'
                                if len(detail_all) > 0:
                                    self.result_v2[placeName] = detail_all
                                # else:
                                # self.result_v2[place_name] = '无'
                                # self.result_v2.pop(placeName)

                                print(placeName, '早上有空场子不?', morningCanReserve, '下午有空场子不?', afternoonCanReserve,
                                      '晚上有空场子不?',
                                      eveningCanReserve)
                            else:
                                print(placeName, '无可用时间')
            except Exception as e:
                print('异常', str(e))
        else:
            print(data.get("errmsg"), data.get("detailErrMsg"))

    # 发邮件
    def send_email(self, receivers, text, title='', date='today'):
        ##### 配置区  #####
        mail_host = 'smtp.qq.com'
        mail_port = '465'  # Linux平台上面发
        # 发件人邮箱账号
        login_sender = 'sender@163.com'
        # 发件人邮箱授权码而不是邮箱密码，授权码由邮箱官网可设置生成
        login_pass = 'password'
        # 邮箱文本内容
        # str = text
        # 发送者
        sendName = "熊"
        # 接收者
        resName = self.receiver_list.get(receivers)
        # 邮箱正文标题
        # title = "座位预约通知"
        ########## end  ##########

        # msg = MIMEText(text + str(datetime.datetime.now()), 'plain', 'utf-8')  # 一般文字
        text += '<p>发件时间:{}</p>'.format(datetime.datetime.now())
        msg = MIMEText(text, 'html', 'utf-8')  # 发html格式的
        msg['From'] = formataddr([sendName, login_sender])
        msg['To'] = formataddr([resName, receivers])
        # 邮件的标题
        if date == 'today':
            msg['Subject'] = "空闲场地监控通知|{}|{}".format(
                '今天' + self.today_str, title)
        else:
            msg['Subject'] = "空闲场地监控通知|{}|{}".format(
                '明天' + self.tomorrow_str, title)
        try:
            # 服务器
            server = smtplib.SMTP_SSL(mail_host, mail_port)
            server.login(login_sender, login_pass)
            server.sendmail(login_sender, [receivers, ], msg.as_string())
            print("已发送到" + receivers + "的邮箱中！")
            server.quit()

        except smtplib.SMTPException:
            print("发送邮箱失败！")

    def main(self, date='today'):
        gym_ = self.get_base_info()
        for i in gym_:
            self.get_free_seat(place_id=i[0], place_name=i[1], date=date)
            time.sleep(1)
        if len(self.result) > 0:
            print(self.result)
            msg = ""
            for i in self.result_v2:
                msg += '<p>{}:{}</p>'.format(i, self.result_v2.get(i))
            msg += '<p>当前时间:{}</p>'.format(datetime.datetime.now())
            print(msg)
            for receiver in self.receiver_list:
                self.send_email(receivers=receiver, text=str(
                    msg), title='有空位，快去抢', date=date)
            # exit()
        # else:
        #     for receiver in self.receiver_list:
        #         self.send_email(receivers=receiver, text='空空如也', title='空空如也')
        #         exit()

    def main_v2(self, date='today'):
        for i in range(10):
            html = self.get_free_seat_v2(date=date)
            self.ana_data(html)
            if len(self.result) > 0:
                print(self.result)
                msg = ""
                msg += '<p>获取时间:{}</p>'.format(self.get_page_time)
                for i in self.result_v2:
                    msg += '<p>{}:{}</p>'.format(i, self.result_v2.get(i))
                print(msg)
                # self.send_email(receivers='1349380978@qq.com', text=str(msg), title='有空位，快去抢', date=date)
                for receiver in self.receiver_list:
                    self.send_email(receivers=receiver, text=str(
                        msg), title='有空位，快去抢', date=date)
                break
            time.sleep(5)


if __name__ == '__main__':
    service = SportInfoService()
    time_1 = datetime.datetime.strptime(
        service.today_str + '0:00', '%Y-%m-%d%H:%M')
    time_2 = datetime.datetime.strptime(
        service.today_str + '8:00', '%Y-%m-%d%H:%M')
    time_3 = datetime.datetime.strptime(
        service.today_str + '18:00', '%Y-%m-%d%H:%M')
    time_4 = datetime.datetime.strptime(
        service.today_str + '20:00', '%Y-%m-%d%H:%M')
    time_5 = datetime.datetime.strptime(
        service.tomorrow_str + '18:00', '%Y-%m-%d%H:%M')
    now_time = datetime.datetime.now()
    if time_1 < now_time < time_2:
        print("0:00-8:00不监控", now_time)
        # service.main()
        # service.main(date='tomorrow')
    elif time_2 < now_time < time_3:
        print("8:00-18:00监控今天", now_time)
        # service.main()
        service.main_v2()
    elif time_3 < now_time < time_4:
        print("18:00-20:00监控今天+明天", now_time)
        # service.main()
        # service.result = []  # 第二次这个得置空
        # service.main(date='tomorrow')
        service.main_v2(date='tomorrow')
        service.result = []  # 第二次这个得置空
        service.result_v2 = {}
        service.get_page_time = ''
        service.main_v2()
    elif time_4 < now_time < time_5:
        print("21:00-0:00监控明天", now_time)
        # service.main(date='tomorrow')
        service.main_v2(date='tomorrow')
    else:
        print("???", now_time)
