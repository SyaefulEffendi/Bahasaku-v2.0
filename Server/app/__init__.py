from flask import Flask
from app.config import Config
from flask_jwt_extended import JWTManager
import datetime

from flask_cors import CORS

import sys
if sys.version_info >= (3, 13):
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)

from app.extensions import db, migrate

jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.config["JWT_SECRET_KEY"] = app.config["SECRET_KEY"]
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=8)
    
    jwt.init_app(app)

    db.init_app(app)
    migrate.init_app(app, db)

    CORS(app,
        resources={r"/api/*": {"origins": ["*","http://localhost:3000"]}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])

    from app.routes.user_routes import user_bp
    app.register_blueprint(user_bp, url_prefix='/api/users')
    
    from app.routes.feedback_routes import feedback_bp
    app.register_blueprint(feedback_bp, url_prefix='/api/feedback')

    from app.routes.kosa_kata_routes import kosa_kata_bp
    app.register_blueprint(kosa_kata_bp, url_prefix='/api/kosa-kata')

    from app.routes.ai_routes import ai_bp
    app.register_blueprint(ai_bp, url_prefix='/api/ai')

    from app.routes.information_routes import information_bp
    app.register_blueprint(information_bp, url_prefix='/api/information')

    @app.cli.command("create-db")
    def create_db_command():
        """Membuat tabel database."""
        with app.app_context():
            from app.models.user_model import User
            from app.models.kosa_kata_model import KosaKata
            from app.models.information_model import Information
            
            db.create_all()
        print("Database tables created!")

    return app