# flask-sqlacodegen https://blog.csdn.net/s1156605343/article/details/104988437
# -*- coding: utf-8 -*-
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
db = SQLAlchemy(app)


# 建立映射模型 类->表  类属性->字段  对象->记录
class Message(db.Model):
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    website = db.Column(db.String(255))
    content = db.Column(db.String(10000), nullable=False)
    create_time = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue())
    update_time = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue())
    is_delete = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue())
    is_show = db.Column(db.Integer, nullable=True, server_default=db.FetchedValue())
    admin_time = db.Column(db.DateTime)
    delete_time = db.Column(db.DateTime)
    agent = db.Column(db.String(255))

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()
