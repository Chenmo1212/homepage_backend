from flask import jsonify, request
from app import app, mongo
from app.models import Message
from datetime import datetime
import requests, json
from bson import ObjectId


@app.route('/', methods=['GET'])
def index():
    return "hello world"


@app.route('/message/post', methods=['POST'])
def post():
    res = add_new_message(request)
    return jsonify(res)


@app.route('/message/get', methods=['GET'])
def get():
    res = get_visible_list()
    return jsonify(res)


@app.route('/message/admin/get', methods=['GET'])
def admin_get():
    res = get_all_messages()
    return jsonify(res)


@app.route('/message/admin/show', methods=['POST'])
def admin_agree():
    res = update_is_show(request)
    return jsonify(res)


@app.route('/message/admin/delete', methods=['POST'])
def admin_disagree():
    res = update_is_delete(request)
    return jsonify(res)


@app.route('/message/delete', methods=['POST'])
def delete():
    try:
        data = request.json
        count = mongo.db.messages.delete_one({'content': "3333333"})
        if count.deleted_count == 1:
            return {'msg': 'Message deleted successfully', 'status': 200}
        else:
            return {'msg': 'Cannot find this id: ' + data['id'], 'status': 200}
    except Exception as e:
        return {'msg': 'Failed to delete message. ' + str(e), 'status': 500}


def add_new_message(req):
    try:
        data = req.json
        name = data.get('name')
        email = data.get('email')
        content = data.get('content')
        website = data.get('website') or ""
        agent = data.get('agent') or ""

        if name and email and content:
            message = Message(name=name, email=email, website=website, content=content, agent=agent)
            message.save()

            try:
                # Send WeChat notification
                res_obj = post_wx({'content': content})
                if res_obj['status'] != 200:
                    return {'msg': res_obj['msg'], 'status': 400}
                return {'msg': 'Message created successfully', 'status': 200}
            except Exception as e:
                return {'msg': 'Failed to post wechat message.' + str(e), 'status': 400}
        else:
            return {'msg': 'Missing required fields', 'status': 400}
    except Exception as e:
        return {'msg': str(e), 'status': 400}


def get_visible_list():
    try:
        messages = Message.get_all_show()
        message_list = []
        for message in messages:
            message_dict = {
                'name': message['name'],
                'email': message['email'],
                'content': message['content'],
                'create_time': message['create_time'],
            }
            message_list.append(message_dict)
        return {'data': message_list, 'status': 200}
    except Exception as e:
        return {'msg': str(e), 'status': 400}


def get_all_messages():
    try:
        messages = Message.get_all()
        message_list = []
        for message in messages:
            message_dict = {
                'id': str(message['_id']),
                'name': message['name'],
                'email': message['email'],
                'content': message['content'],
                'website': message['website'],
                'agent': message['agent'],
                'is_show': message['is_show'],
                'is_delete': message['is_delete'],
                'create_time': message['create_time'],
                'update_time': message['update_time'],
                'admin_time': message['admin_time'],
                'delete_time': message['delete_time'],
            }
            message_list.append(message_dict)
        return {'data': message_list, 'status': 200}
    except Exception as e:
        return {'msg': str(e), 'status': 500}


def update_is_show(req):
    try:
        obj = req.json
        result = mongo.db.messages.update_one(
            {'_id': ObjectId(obj["id"])},
            {
                '$set': {
                    "is_show": obj["is_show"],
                    "is_delete": 0,
                    "admin_time": datetime.now()
                }
            }
        )

        if result.matched_count > 0:
            # Document matched and updated successfully
            if obj["is_show"]:
                return {'msg': 'Approve the message successfully', 'status': 200}
            else:
                return {'msg': 'Withdraw approval message successfully', 'status': 200}
        else:
            # No document matched the given criteria
            return {'msg': 'No document found to update', 'status': 401}

    except Exception as e:
        return {'msg': 'Failed to approve message. ' + str(e), 'status': 500}


def update_is_delete(req):
    try:
        obj = req.json
        result = mongo.db.messages.update_one(
            {'_id': ObjectId(obj["id"])},
            {
                '$set': {
                    "is_delete": obj["is_delete"],
                    "is_show": 0,
                    "delete_time": datetime.now()
                }
            }
        )

        if result.matched_count > 0:
            # Document matched and updated successfully
            if obj["is_delete"]:
                return {'msg': 'Delete the message successfully', 'status': 200}
            else:
                return {'msg': 'Withdraw delete message successfully', 'status': 200}
        else:
            # No document matched the given criteria
            return {'msg': 'No document found to update', 'status': 401}
    except Exception as e:
        return {'msg': 'Failed to dismiss message. ' + str(e), 'status': 500}


def post_wx(obj):
    try:
        CORPID = 'ww09de43a6da48f6a4'  # 企业id
        AGENTID = '1000006'  # 应用id
        CORPSECRET = 'A_Wtv3PFqgUHDnqV93HcCzsLQuLGUjRjkQMDaAUcb8w'  # 应用secret

        get_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={CORPID}&corpsecret={CORPSECRET}"
        response = requests.get(get_token_url).content
        access_token = json.loads(response).get('access_token')

        if access_token and len(access_token) > 0:
            send_msg_url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
            data = {
                "touser": '@all',
                "agentid": AGENTID,
                "msgtype": "textcard",
                "textcard": {
                    "title": "主页留言",
                    "description": obj['content'],
                    "url": "https://chenmo1212.cn/admin",
                    "btntxt": "查看更多"
                },
                "enable_id_trans": 0,
                "enable_duplicate_check": 0,
                "duplicate_check_interval": 1800
            }
            res = requests.post(send_msg_url, data=json.dumps(data))
            return {'msg': 'Failed to post wechat notification.', 'status': res.status_code}
        else:
            return {'msg': 'Failed to post wechat notification. access_token is invalid.', 'status': 500}
    except Exception as e:
        return {'msg': 'Failed to post wechat notification.' + str(e), 'status': 500}
