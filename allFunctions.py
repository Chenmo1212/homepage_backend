# -*- coding: utf-8 -*-
from models import Message, db
import requests
import json
from flask import jsonify
from flask_sqlalchemy import Model
from datetime import datetime as cdatetime  # 有时候会返回datatime类型
from datetime import date, time
from sqlalchemy import DateTime, Numeric, Date, Time  # 有时又是DateTime

# ===========================
# 路由对应函数
# ===========================
# 插入数据
def post_message(req):
    try:
        obj = req.get_json(force=True)

        try:
            is_insert = check_repeat(obj)  # True 为无重复，False为有重复
            if is_insert:
                return {'msg': '留言重复，请重新更改内容。'}
            obj['is_show'] = 0
            # 保存到数据库
            message = Message(**obj)
            message.save()
        except Exception as e:
            return {'msg': '数据库操作失败。', 'error': str(e)}

        # 发送微信通知
        msg = post_wx(obj)
        return {'msg': msg}
    except Exception as e:
        return {'msg': '发送留言失败。', 'error': str(e), 'origin': str(obj)}


# 获取所有数据
def get_message(req):
    try:
        items = Message.query.all()
        items = query_to_dict(items)  # 转换成字典
        items = filter_not_del_data(items)  # 去除已删除的数据
        items = filter_not_show_data(items)  # 去除不显示的数据
        for i in items:  # 删除掉前端不需要的键值对
            del i['is_delete']
            del i['email']
            del i['update_time']
            del i['delete_time']
            del i['agent']
        response_body = get_return_msg("数据获取成功", items)  # 将响应信息转换为 JSON 格式
        return response_body
    except Exception as e:
        return {'msg': '获取留言失败。', 'e': e}


# ===========================
# 管理员权限
# ===========================
# 管理员获取全部数据
def get_admin_data(req):
    try:
        items = Message.query.all()
        items = query_to_dict(items)  # 转换成字典
        for i in items:  # 删除掉前端不需要的键值对
            del i['delete_time']
            del i['agent']
        response_body = get_return_msg("数据获取成功", items)  # 将响应信息转换为 JSON 格式
        return response_body
    except Exception as e:
        return {'msg': '管理员获取留言失败。', 'e': e}


def delete_admin_data(req):
    try:
        obj = req.json
        Message.query.filter(Message.id == obj["id"]).update({
            "is_delete": 1,
            "delete_time": cdatetime.now()
        })
        db.session.commit()
        response_body = get_return_msg("删除留言成功")  # 将响应信息转换为 JSON 格式
        return response_body
    except Exception as e:
        return {'msg': '删除留言失败。'}


def agree_admin_data(req):
    try:
        obj = req.json
        Message.query.filter(Message.id == obj["id"]).update({
            "is_show": not obj['is_show'],
            "is_delete": 0,
            "admin_time": cdatetime.now()
        })
        db.session.commit()
        if not obj['is_show']:
            response_body = get_return_msg("批准留言成功")  # 将响应信息转换为 JSON 格式
        else:
            response_body = get_return_msg("撤回批准留言成功")  # 将响应信息转换为 JSON 格式
        return response_body
    except Exception as e:
        return {'msg': '批准留言失败。'}


def disagree_admin_data(req):
    try:
        obj = req.json
        Message.query.filter(Message.id == obj["id"]).update({
            "is_delete": not obj['is_delete'],
            "is_show": 0,
            "delete_time": cdatetime.now()
        })
        db.session.commit()
        if not obj['is_delete']:
            response_body = get_return_msg("撤回驳回留言成功")  # 将响应信息转换为 JSON 格式
        else:
            response_body = get_return_msg("驳回留言成功")  # 将响应信息转换为 JSON 格式
        return response_body
    except Exception as e:
        return {'msg': '驳回留言失败。'}


# ===========================
# 通用函数
# ===========================
# 检查数据库是否有重复
def check_repeat(item):
    lists = Message.query.filter_by(**item).all()
    if len(lists):  # 如果返回的长度不为0，则数据库有重复
        return True
    else:
        return False


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
            return res.status_code
        else:
            return False
    except Exception as e:
        return {'msg': '发送微信通知失败。', 'error': str(e), 'origin': str(obj)}


# ===========================
# 返回前端信息
# ===========================
def get_return_msg(msg="OK", items=None):
    response_info = {
        "msg": msg,
        "timestamp": convert_datetime(cdatetime.now()),  # 转换一下时间，不然不能jsonify
        "status": 200
    }  # 生成响应信息
    if items or items == []:
        response_info["data"] = items
    return response_info  # 将响应信息转换为 JSON 格式


# ===========================
# 根据软删除，获取未被删除的数据
# ===========================
def filter_not_del_data(lists):
    temp = []
    for i in lists:
        if not i['is_delete']:
            temp.append(i)
    return temp


def filter_not_show_data(lists):
    temp = []
    for i in lists:
        if i['is_show']:
            temp.append(i)
    return temp


# ===========================
# 格式转换函数： query to dict
# ===========================
def query_to_dict(models):
    if isinstance(models, list):
        if isinstance(models[0], Model):
            lst = []
            for model in models:
                gen = model_to_dict(model)
                dit = dict((g[0], g[1]) for g in gen)
                lst.append(dit)
            return lst
        else:
            res = result_to_dict(models)
            return res
    else:
        if isinstance(models, Model):
            gen = model_to_dict(models)
            dit = dict((g[0], g[1]) for g in gen)
            return dit
        else:
            res = dict(zip(models.keys(), models))
            find_datetime(res)
            return res


# 当结果为result对象列表时，result有key()方法
def result_to_dict(results):
    res = [dict(zip(r.keys(), r)) for r in results]
    # 这里r为一个字典，对象传递直接改变字典属性
    for r in res:
        find_datetime(r)
    return res


def model_to_dict(model):  # 这段来自于参考资源
    for col in model.__table__.columns:
        if isinstance(col.type, cdatetime):
            value = convert_datetime(getattr(model, col.name))
        elif isinstance(col.type, Numeric):
            value = float(getattr(model, col.name))
        else:
            value = getattr(model, col.name)
        yield col.name, value


def find_datetime(value):
    for v in value:
        if isinstance(value[v], cdatetime):
            value[v] = convert_datetime(value[v])  # 这里原理类似，修改的字典对象，不用返回即可修改


def convert_datetime(value):
    if value:
        if isinstance(value, (cdatetime, DateTime)):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(value, (date, Date)):
            return value.strftime("%Y-%m-%d")
        elif isinstance(value, (Time, time)):
            return value.strftime("%H:%M:%S")
    else:
        return ""

