DEBUG = True
# dialect+driver://root:1q2w3e4r5t@127.0.0.1:3306/
# DIALECT = 'mysql'
# DRIVER = 'pymysql'
# USERNAME = 'root'
# PASSWORD = 'nrahbsqt321321.'
# HOST = '127.0.0.1'
# PORT = 3306
# DATABASE = 'test123'

DIALECT = 'mysql'
DRIVER = 'pymysql'
USERNAME = 'root'
PASSWORD = 'nrahbsqt321321.'
HOST = '182.92.67.61'
PORT = 3306
DATABASE = 'test123'

SQLALCHEMY_DATABASE_URI = "{}+{}://{}:{}@{}:{}/{}?charset=utf8".format(DIALECT, DRIVER, USERNAME, PASSWORD, HOST, PORT,
                                                                       DATABASE)
SQLALCHEMY_TRACK_MODIFICATIONS = True
