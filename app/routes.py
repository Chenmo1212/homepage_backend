from flask import jsonify, request
from app import main, mongo
from app.models import Message
from datetime import datetime


@main.route('/', methods=['GET'])
def index():
    return 'hello world1111'


@main.route('/message/post', methods=['POST'])
def post():
    res = add_new_message(request)
    return res


@main.route('/message/get', methods=['GET'])
def get():
    res = get_visible_list()
    return res


@main.route('/message/admin/get', methods=['GET'])
def admin_get():
    res = get_all_messages()
    return res


@main.route('/message/admin/show', methods=['POST'])
def admin_agree():
    res = update_is_show(request)
    return res


@main.route('/message/admin/delete', methods=['POST'])
def admin_disagree():
    res = update_is_delete(request)
    return res


@main.route('/message/delete', methods=['POST'])
def delete():
    try:
        data = request.json
        count = mongo.db.messages.delete_one({'content': "3333333"})
        if count.deleted_count == 1:
            return jsonify({'msg': 'Message deleted successfully', 'status': 200})
        else:
            return jsonify({'msg': 'Cannot find this id: ' + data['id'], 'status': 200})
    except Exception as e:
        return jsonify({'msg': 'Failed to delete message. ' + str(e), 'status': 500})


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
            return jsonify({'msg': 'Message created successfully', 'status': 200})
        else:
            return jsonify({'msg': 'Missing required fields', 'status': 400})
    except Exception as e:
        return jsonify({'msg': str(e), 'status': 400})


def get_visible_list():
    try:
        messages = Message.get_all_show()
        message_list = []
        for message in messages:
            message_dict = {
                'name': message['name'],
                'email': message['email'],
                'content': message['content']
            }
            message_list.append(message_dict)
        return jsonify({'data': message_list, 'status': 200})
    except Exception as e:
        return jsonify({'msg': str(e), 'status': 400})


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
        return jsonify({'data': message_list, 'status': 200})
    except Exception as e:
        return jsonify({'msg': str(e), 'status': 500})


def update_is_show(req):
    try:
        obj = req.json
        mongo.db.messages.update_one(
            {'id': obj["id"]},
            {
                '$set': {
                    "is_show": obj["is_show"],
                    "is_delete": 0,
                    "admin_time": datetime.now()
                }
            }
        )

        if obj["is_show"]:
            return jsonify({'msg': 'Approve the message successfully', 'status': 200})
        else:
            return jsonify({'msg': 'Withdraw approval message successfully', 'status': 200})
    except Exception as e:
        return jsonify({'msg': 'Failed to approve message. ' + str(e), 'status': 500})


def update_is_delete(req):
    try:
        obj = req.json
        mongo.db.messages.update_one(
            {'id': obj["id"]},
            {
                '$set': {
                    "is_delete": obj["is_delete"],
                    "is_show": 0,
                    "delete_time": datetime.now()
                }
            }
        )
        if obj["is_delete"]:
            return jsonify({'msg': 'Delete the message successfully', 'status': 200})
        else:
            return jsonify({'msg': 'Withdraw delete message successfully', 'status': 200})
    except Exception as e:
        return jsonify({'msg': 'Failed to dismiss message. ' + str(e), 'status': 500})

