from app import mongo
from datetime import datetime
from bson import ObjectId


class Message:
    def __init__(self, name, email, website, content, agent, create_time=None, update_time=None,
                 admin_time=None, delete_time=None, is_delete=False, is_show=False, id=None):
        self.id = ObjectId(id)
        self.name = name
        self.email = email
        self.website = website
        self.content = content
        self.agent = agent
        self.create_time = create_time
        self.update_time = update_time
        self.admin_time = admin_time
        self.delete_time = delete_time
        self.is_delete = is_delete
        self.is_show = is_show

    def save(self):
        current_time = datetime.now()
        result = mongo.db.messages.insert_one({
            'name': self.name,
            'email': self.email,
            'website': self.website,
            'content': self.content,
            'agent': self.agent,
            'create_time': self.create_time or current_time,
            'update_time': self.update_time or current_time,
            'admin_time': self.admin_time or current_time,
            'delete_time': self.delete_time or current_time,
            'is_delete': self.is_delete,
            'is_show': self.is_show
        })
        inserted_id = str(result.inserted_id)
        return inserted_id

    def delete(self):
        mongo.db.messages.delete_one({'_id': ObjectId(self.id)})

    @staticmethod
    def get_all():
        return mongo.db.messages.find()

    @staticmethod
    def get_visible_list():
        return mongo.db.messages.find({'is_show': True})
