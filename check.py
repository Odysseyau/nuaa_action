# encoding=utf-8
import traceback
import re
import json
import sys
import time
import traceback
import requests
from send_mail import send_mail
# from requests_toolbelt.utils import dump

try_times = 1   # 失败这么多次后就直接不管了
delay = 2   # 访问页面前的延迟，为了防止过快访问网站被封IP


# 登陆并且返回json形式的cookie，如果登陆失败返回空串
# 先访问/uc/wap/login，获得eai-sess，然后带着她访问/uc/wap/login/check，获得UUkey
def login(stu_number, password):
    cookies = ''
    for _ in range(try_times):
        try:
            time.sleep(delay)
            response = requests.get(
                'https://m.nuaa.edu.cn/uc/wap/login', cookies=cookies)
            print('get login page:', response.status_code)

            # cookies = response.headers['Set-Cookie']
            # cookies = re.search(r'eai-sess=([a-zA-Z0-9]+)', cookies).group(0)
            cookies = dict(response.cookies)

            time.sleep(delay)
            response = requests.get('https://m.nuaa.edu.cn/uc/wap/login/check', cookies=cookies,
                                    data='username={}&password={}'.format(stu_number, password))
            print('login...:', response.status_code)

            # cookies2 = response.headers['Set-Cookie']
            # cookies = cookies + '; ' + \
            #     re.search(r'UUkey=([a-zA-Z0-9]+)', cookies2).group(0)
            cookies.update(dict(response.cookies))
            
            # print(cookies)
            print(response.text)
            return cookies, '登陆结果：' + response.text + '\n'
        except:
            print('login failed.')
            traceback.print_exc()
            pass
    # raise Exception('lOGIN FAIL')
    return {}, '登陆结果：login faild,请检查账号密码\n'

# longitude: 经度； latitude: 纬度
# 根据经纬度访问高德API，并且返回打卡时候“geo_api_info”字段的值
def get_address_info(longitude, latitude):
    for _ in range(try_times):
        try:
            time.sleep(delay)
            response = requests.get(
                'https://restapi.amap.com/v3/geocode/regeo', params={
                    'key': '729923f88542d91590470f613adb27b5',
                    's': 'rsv3',
                    'location': str(longitude) + ',' + str(latitude)
                })
            geo_data = json.loads(response.text)
            geo_data = geo_data['regeocode']
            geo_api_info = {
                "type": "complete",
                "position": {
                    "Q": latitude,
                    "R": longitude,
                    "lng": longitude,
                    "lat": latitude
                },
                "location_type": "html5",
                "message": "Get ipLocation failed.Get geolocation success.Convert Success.Get address success.",
                "accuracy": 102,    # ???
                "isConverted": True,    # ?
                "status": 1,
                "addressComponent": {
                    "citycode": geo_data['addressComponent']['citycode'],
                    "adcode": geo_data['addressComponent']['adcode'],
                    "businessAreas": [],
                    "neighborhoodType": "",
                    "neighborhood": "",
                    "building": "",
                    "buildingType": "",
                    "street": geo_data['addressComponent']['streetNumber']['street'],
                    "streetNumber": geo_data['addressComponent']["streetNumber"]['number'],
                    "country": geo_data['addressComponent']['country'],
                    "province": geo_data['addressComponent']['province'],
                    "city": geo_data['addressComponent']['city'],
                    "district": geo_data['addressComponent']['district'],
                    "township": geo_data['addressComponent']['township']
                },
                "formattedAddress": geo_data['formatted_address'],
                "roads": [],
                "crosses": [],
                "pois": [],
                "info": "SUCCESS"
            }
            return geo_api_info
        except:
            traceback.print_exc()
    return geo_api_info
    # print(dump.dump_all(response).decode('utf-8'))

# 获取uid，id，打卡时候会用到，获取失败异常最可能的原因是账号密码错误
def get_uid_id(cookies):
    for _ in range(try_times):
        try:
            time.sleep(delay)
            response = requests.get(
                'https://m.nuaa.edu.cn/ncov/wap/default', cookies=cookies)
            response.encoding = 'utf-8'
            uid = re.search(r'"uid":"([0-9]*)"', response.text).group(1)
            id = re.search(r'"id":([0-9]*)', response.text).group(1)
            return uid,id, 'UID获取成功\n'
        except:
            traceback.print_exc()
    # 就这样吧，让他崩溃，万一假打卡了就不好了
    print('获取id、uid失败')
    return False, '获取id、uid失败\n'

# 签到，返回True成功，否则失败
def check(cookies, geo_api_info, id, uid):
    # Post的data，如果你是勇士可以尝试给这个打上注释，老谜语人了，看不懂ヾ(•ω•`)o
    data = {
        'sfzx': '1',  #是否在校1是 0否。
        'gzczxq':'2', #工作常驻校区：1明故宫 2将军路 3天目湖
        'sfzhux': '1', #是否住校 1是 0否
        'sfzgn': '1',
        #'zhuxdz': '',
        'njrddz': "南区35栋",
        'szgj': '',
        'szcs': '',
        'szgjcs': '',
        'sfjwfh': '0', #今日是否在中高风险地区 1是 0否
        'sfyjsjwfh': '0',
        'sfjcjwfh': '0',
        'sflznjcjwfh': '0',
        'sflqjkm': '4', #是否拥有苏康码 4是 0否
        'jkmys': '1',  #健康码颜色 1绿色 2黄色 3红色
        'sfjtgfxdq': '0',
       #'tw': '1',  #体温值，这里我设成1
        
        'zrwjtw': '1', #体温值，这里我设成1
        'jrzjtw': '1',
        'sfcxtz': '0',
        'sfjcbh': '0',
        'sfcxzysx': '0',
        'qksm': '',
        'sfyyjc': '0',
        'jcjgqr': '0',
        'remark': '',
        'address': geo_api_info['formattedAddress'],
        'geo_api_info': json.dumps(geo_api_info, separators=(',', ':')),
        'area': geo_api_info['addressComponent']['province'] + ' ' + geo_api_info['addressComponent']['city']
                 + ' ' + geo_api_info['addressComponent']['district'],
        'province': geo_api_info['addressComponent']['province'],
        'city': geo_api_info['addressComponent']['city'],
        'sfjcwhry': '0',
        'sfjchbry': '0',
        'sfcyglq': '0',
        'gllx': '',
        'glksrq': '',
        'jcbhlx': '',
        'jcbhrq': '',
        'bztcyy': '',
        'sftjhb': '0',
        'sftjwh': '0',
        'sftjwz': '0',
        'sfjcwzry': '0',
        'jcjg': '',
        'date': time.strftime("%Y%m%d", time.localtime()),  # 打卡年月日一共8位
        'uid': uid,  # UID
        'created': round(time.time()), # 时间戳
        'jcqzrq': '',
        'sfjcqz': '',
        'szsqsfybl': '0',
        'sfsqhzjkk': '0',
        'sqhzjkkys': '',
        'sfygtjzzfj': '0',
        'gtjzzfjsj': '',
        'created_uid': '0',
        'id': id,# 打卡的ID，其实这个没影响的
        'gwszdd': '',
        'sfyqjzgc': '',
        'jrsfqzys': '',
        'jrsfqzfy': '',
        'ismoved': '0'
    }
    for _ in range(try_times):
        try:
            time.sleep(delay)
            response = requests.post('https://m.nuaa.edu.cn/ncov/wap/default/save', data=data, cookies=cookies)
            print('sign statue code:', response.status_code)
            #print('sign return:', response.text) 
            response.encoding = 'utf-8'

            if response.text.find('成功') >= 0:
                print('打卡成功')
                return True, '打卡成功' + '\n'
            else:
                print('打卡失败')
        except:
            traceback.print_exc()
    return False, '打卡失败' + '\n'


def send_result(config, recever, result, messgae):
    mail_sender = config['mail_sender']
    smtp_password = config['smtp_password']
    smtp_host = config['smtp_host']
    if result == True:
        send_mail(mail_sender, smtp_password, smtp_host,
                  recever, messgae, '打卡成功', '主人', '打卡姬')
    else:
        send_mail(mail_sender, smtp_password, smtp_host,
                  recever, messgae, '打卡失败', '主人', '打卡姬')

def main():
    config = sys.stdin.read()
    config = json.loads(config)

    for student in config['students']:
        result = False  # 打卡结果，False表示没有打上
        stu_number = student['stu_number']
        password = student['password']
        longitude = student['longitude']
        latitude = student['latitude']
        mail = student['mail']
        message = ''
        message2 = ''
        print('--------------------------------------')
        try:
            cookies, message = login(stu_number, password)
            geo_api_info = get_address_info(longitude, latitude)
            uid, id, message1 = get_uid_id(cookies)
            result, message2 = check(cookies, geo_api_info, id, uid)
            message += message1 + message2
        except:
            print('发生错误，可能原因是打卡密码错误或者经纬度错误')
            message += '发生错误，可能原因是打卡密码错误或者经纬度错误'
        if mail != '':
            send_result(config, mail, result, message)


if __name__ == '__main__':
    main()
