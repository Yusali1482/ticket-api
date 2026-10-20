from flask import Flask

from . import db
from .tickets import bp


def create_app(database="tickets.db"):
    app = Flask(__name__)
    app.config["DATABASE"] = database
    app.teardown_appcontext(db.close_db)
    with app.app_context():
        db.init_db()
    app.register_blueprint(bp)
    return app
