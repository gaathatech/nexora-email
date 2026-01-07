from flask import Flask
from config import get_config
from extensions import db
from routes import main_routes

def create_app():
    app = Flask(__name__)
    app.config.from_object(get_config())

    db.init_app(app)
    app.register_blueprint(main_routes)

    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
