from flask import jsonify, request
from app import app, mongo
from app.models import Message
from datetime import datetime
import requests, json
from bson import ObjectId
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@app.route('/', methods=['GET'])
def index():
    return "hello world"


# ============ User Api ============

@app.route('/messages', methods=['GET'])
def get_visible_list_api():
    res = get_visible_list()
    return jsonify(res)


@app.route('/messages', methods=['POST'])
def add_new_message_api():
    res = add_new_message()
    return jsonify(res)


# ============ Admin Api ============

@app.route('/admin/messages', methods=['GET'])
def get_all_message_list_api():
    res = get_all_message_list()
    return jsonify(res)


@app.route('/admin/messages/<string:message_id>/status', methods=['PUT'])
def update_message_status_api(message_id):
    res = update_message_status(message_id)
    return jsonify(res)


@app.route('/admin/messages/<string:message_id>', methods=['DELETE'])
def update_message_api(message_id):
    res = delete_message(message_id)
    return jsonify(res)


@app.route('/admin/messages/delete', methods=['POST'])
def update_many_messages_api():
    res = delete_many_message()
    return jsonify(res)


# ==================================== Functions ====================================

def get_visible_list():
    try:
        messages = Message.get_visible_list()

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
        return {'error': str(e), 'status': 500}


def add_new_message():
    try:
        data = request.json

        required_fields = ['name', 'email', 'content']
        extracted_fields = {field: data.get(field, '') for field in required_fields}

        additional_fields = {
            'website': data.get('website', ''),
            'agent': data.get('agent', ''),
            'admin_time': data.get('admin_time'),
            'create_time': data.get('create_time'),
            'delete_time': data.get('delete_time'),
            'update_time': data.get('update_time'),
            'is_delete': data.get('is_delete', False),
            'is_show': data.get('is_show', False)
        }

        message_data = {**extracted_fields, **additional_fields}

        if all(extracted_fields.values()):
            # Create a new Message instance with the merged data
            message = Message(**message_data)
            id_ = message.save()

            try:
                # Send WeChat notification
                res_obj = post_wx({'content': message_data['content']})
                if res_obj['status'] != 200:
                    return {'error': res_obj['msg'], 'status': 500}

                return {'msg': 'Message created successfully', 'status': 200, 'data': {'id': id_}}
            except Exception as e:
                return {'error': 'Failed to post wechat message.' + str(e), 'status': 500}
        else:
            return {'error': 'Missing required fields', 'status': 400}
    except Exception as e:
        return {'error': str(e), 'status': 500}


def get_all_message_list():
    try:
        messages = Message.get_all()

        message_list = []
        for message in messages:
            message_dict = {key: message.get(key) for key in message}
            message_dict["id"] = str(message_dict.pop("_id"))
            message_list.append(message_dict)

        return {'data': message_list, 'status': 200}
    except Exception as e:
        return {'error': str(e), 'status': 500}


def update_message_status(message_id):
    try:
        obj = request.json
        is_show = obj.get("is_show")
        is_delete = obj.get("is_delete")

        update_fields = {}
        update_msg = ""

        if is_show is not None:
            update_fields["is_show"] = bool(is_show)
            update_msg += f"is_show changed to {is_show}, "

        if is_delete is not None:
            update_fields["is_delete"] = bool(is_delete)
            update_msg += f"is_delete changed to {is_delete}, "

        if not update_fields:
            return {'error': 'No valid fields provided for update', 'status': 400}

        update_fields["admin_time"] = datetime.now()

        result = mongo.db.messages.update_one(
            {'_id': ObjectId(message_id)},
            {'$set': update_fields}
        )

        if result.matched_count > 0:
            response_msg = 'Message updated successfully'
            if update_msg:
                response_msg += ' (' + update_msg.rstrip(', ') + ')'
            return {'msg': response_msg, 'status': 200}
        else:
            return {'error': 'No document found to update', 'status': 404}

    except Exception as e:
        return {'error': 'Failed to update message. ' + str(e), 'status': 500}


def delete_many_message():
    try:
        id_list = request.json['id_list']
        if id_list:
            object_ids = [ObjectId(item_id) for item_id in id_list]
            result = mongo.db.messages.delete_many({'_id': {'$in': object_ids}})
            return {'msg': f'Deleted {result.deleted_count} messages', 'status': 200}
        else:
            return {'error': 'Missing id_list field', 'status': 400}
    except Exception as e:
        return {'error': str(e), 'status': 500}


def delete_message(message_id):
    try:
        result = mongo.db.messages.delete_one({'_id': ObjectId(message_id)})
        if result.deleted_count == 1:
            return {'msg': 'Item deleted successfully', 'status': 200}
        else:
            return {'msg': 'No item found to delete', 'status': 404}
    except Exception as e:
        return {'error': str(e), 'status': 500}


def post_wx(obj):
    try:
        CORPID = os.getenv('CORPID')  # enterprise id
        AGENTID = os.getenv('AGENTID')  # application id
        CORPSECRET = os.getenv('CORPSECRET')  # application secret

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
                    "title": "Home message",
                    "description": obj['content'],
                    "url": os.getenv('ADMINURL'),
                    "btntxt": "More"
                },
                "enable_id_trans": 0,
                "enable_duplicate_check": 0,
                "duplicate_check_interval": 1800
            }
            res = requests.post(send_msg_url, data=json.dumps(data))
            return {'msg': 'Failed to post wechat notification.', 'status': res.status_code}
        else:
            return {'error': 'Failed to post wechat notification. access_token is invalid.', 'status': 500}
    except Exception as e:
        return {'error': 'Failed to post wechat notification.' + str(e), 'status': 500}
