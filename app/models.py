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
        result = mongo.db.messages.insert_one({
            'name': self.name,
            'email': self.email,
            'website': self.website,
            'content': self.content,
            'agent': self.agent,
            'create_time': datetime.now(),
            'update_time': datetime.now(),
            'admin_time': datetime.now(),
            'delete_time': datetime.now(),
            'is_delete': False,
            'is_show': False
        })
        inserted_id = str(result.inserted_id)

        return inserted_id

    def delete(self):
        mongo.db.messages.delete_one({'_id': self['id']})

    @staticmethod
    def get_all():
        return mongo.db.messages.find()

    @staticmethod
    def get_visible_list():
        return mongo.db.messages.find({'is_show': True})

