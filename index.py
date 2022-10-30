'''
api调用格式: HOST:PORT/API?msg=YOURMESSAGE
举个栗子: localhost:9999/testApi?msg=helloworld
'''

import json, requests
import time

from flask import Flask, request


CORPID = 'ww09de43a6da48f6a4'  # 企业id
AGENTID = '1000006'  # 应用id
CORPSECRET = 'A_Wtv3PFqgUHDnqV93HcCzsLQuLGUjRjkQMDaAUcb8w'  # 应用secret

HOST = 'localhost'  # 如需部署外网访问，请设置0.0.0.0
PORT = 9999  # 端口号
API = 'testApi'  # API接口名，如localhost:9999/test?msg=


def send_to_wecom(text, wecom_cid, wecom_aid, wecom_secret, wecom_touid='@all'):
    get_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={wecom_cid}&corpsecret={wecom_secret}"
    response = requests.get(get_token_url).content
    access_token = json.loads(response).get('access_token')
    if access_token and len(access_token) > 0:
        send_msg_url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
        data = {
            "touser": wecom_touid,
            "agentid": wecom_aid,
            "msgtype": "template_card",
            "template_card": {
                "card_type": "vote_interaction",
                "source": {
                    "icon_url": "图片的url",
                    "desc": "企业微信"
                },
                "main_title": {
                    "title": "欢迎使用企业微信",
                    "desc": "您的好友正在邀请您加入企业微信"
                },
                "task_id": "task_id",
                "checkbox": {
                    "question_key": "question_key1",
                    "option_list": [
                        {
                            "id": "option_id1",
                            "text": "选择题选项1",
                            "is_checked": True
                        },
                        {
                            "id": "option_id2",
                            "text": "选择题选项2",
                            "is_checked": False
                        }
                    ],
                    "mode": 1
                },
                "submit_button": {
                    "text": "提交",
                    "key": "key"
                }
            },
            "enable_id_trans": 0,
            "enable_duplicate_check": 0,
            "duplicate_check_interval": 1800
        }
        response = requests.post(send_msg_url, data=json.dumps(data)).content
        return response
    else:
        return False


app = Flask(__name__)


@app.route('/' + API)
def myApi():
    # msg = request.args.get('msg')

    time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    # msg = f"<h1 class=\"gray\">{time_now}</h1> <div class=\"normal\">注意！</div><div class=\"highlight\">今日有新债，坚持打新！</div><a href='https://www.baidu.com'>test</a>"
    msg = """您的会议室已经预定，稍后会同步到`邮箱` 
                                >**事项详情** 
                                >事　项：<font color=\"info\">开会</font> 
                                >组织者：@miglioguan 
                                >参与者：@miglioguan、@kunliu、@jamdeezhou、@kanexiong、@kisonwang 
                                > 
                                >会议室：<font color=\"info\">广州TIT 1楼 301</font> 
                                >日　期：<font color=\"warning\">2018年5月18日</font> 
                                >时　间：<font color=\"comment\">上午9:00-11:00</font> 
                                > 
                                >请准时参加会议。 
                                > 
                                >如需修改会议信息，请点击：[修改会议信息](https://work.weixin.qq.com)"""

    ret = send_to_wecom(msg, CORPID, AGENTID, CORPSECRET)
    return ret


if __name__ == "__main__":
    app.run(HOST, PORT)