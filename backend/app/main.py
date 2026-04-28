from flask import Flask
from flask_cors import CORS
import logging

from app.routes.api import api
from app.models.database import create_tables

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s — %(message)s")


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(api)
    return app


app = create_app()

if __name__ == "__main__":
    create_tables()
    app.run(host="0.0.0.0", port=5001, debug=False)