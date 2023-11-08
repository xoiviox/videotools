from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
#from flask_sessionstore import Session

from videotools.config import AppConfig

#db = SQLAlchemy()

app = Flask(__name__)
app.jinja_env.auto_reload = True
app.config.from_object(AppConfig)

socketio = SocketIO(app, async_mode='threading')

#db.init_app(app)
db = SQLAlchemy(app)
#db.init_app(app)
#session = Session(app)
#session.app.session_interface.db.create_all()
#print(f'app ==== {app}')
#print(f'app.config ==== {app.config}')
#print(f'db.app.config ==== {db.app.config}')

from videotools.routes import main
app.register_blueprint(main)


