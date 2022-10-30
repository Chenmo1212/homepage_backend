from flask import Flask
from routes import main as todo_routes
from flask_sqlalchemy import SQLAlchemy
import config

app = Flask(__name__)
app.config.from_object(config)
app.register_blueprint(todo_routes)
db = SQLAlchemy(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, threaded=True, debug=True)

    # https://zhuanlan.zhihu.com/p/460215635
