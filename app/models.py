from app import mongo
from datetime import datetime


class Message:
    def __init__(self, name, email, website, content, agent, id=None):
        self.id = str(id)
        self.name = name
        self.email = email
        self.website = website
        self.content = content
        self.agent = agent

    def save(self):
        mongo.db.messages.insert_one({
            'name': self.name,
            'email': self.email,
            'website': self.website,
            'content': self.content,
            'agent': self.agent,
            'create_time': datetime.now(),
            'update_time': datetime.now(),
            'admin_time': datetime.now(),
            'delete_time': datetime.now(),
            'is_delete': 0,
            'is_show': 1
        })

    def delete(self):
        print(self['id'])
        mongo.db.messages.delete_one({'_id': self['id']})

    @staticmethod
    def get_all():
        return mongo.db.messages.find()

    @staticmethod
    def get_all_show():
        return mongo.db.messages.find({'is_show': 1})

