from flask import request, jsonify
from flask import Blueprint
from allFunctions import post_message, get_message, delete_admin_data, get_admin_data, agree_admin_data, disagree_admin_data

main = Blueprint('todo', __name__)


@main.route('/', methods=['GET'])
def index():
    return 'hello world222222'


@main.route('/message/post', methods=['POST'])
def post():
    res = post_message(request)
    return jsonify(res)


@main.route('/message/get', methods=['GET'])
def get():
    res = get_message(request)
    return jsonify(res)


@main.route('/message/admin/get', methods=['GET'])
def admin_get():
    res = get_admin_data(request)
    return jsonify(res)


@main.route('/message/admin/delete', methods=['POST'])
def admin_delete():
    res = delete_admin_data(request)
    return jsonify(res)


@main.route('/message/admin/agree', methods=['POST'])
def admin_agree():
    res = agree_admin_data(request)
    return jsonify(res)


@main.route('/message/admin/disagree', methods=['POST'])
def admin_disagree():
    res = disagree_admin_data(request)
    return jsonify(res)
