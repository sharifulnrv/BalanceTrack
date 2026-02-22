from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    from app.auth.routes import auth as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main.routes import main as main_bp
    app.register_blueprint(main_bp)

    @app.before_request
    def log_activity():
        from app.models import ActivityLog
        if current_user.is_authenticated:
            log = ActivityLog(
                user_id=current_user.id,
                action=f"{request.method} {request.path}",
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()

    from app.accounts.routes import accounts as accounts_bp
    app.register_blueprint(accounts_bp, url_prefix='/accounts')

    from app.transactions.routes import transactions as transactions_bp
    app.register_blueprint(transactions_bp, url_prefix='/transactions')

    from app.loans.routes import loans as loans_bp
    app.register_blueprint(loans_bp, url_prefix='/loans')

    from app.investments.routes import investments as investments_bp
    app.register_blueprint(investments_bp, url_prefix='/investments')

    from app.budgets.routes import budgets as budgets_bp
    app.register_blueprint(budgets_bp, url_prefix='/budgets')

    from app.categories.routes import categories as categories_bp
    app.register_blueprint(categories_bp, url_prefix='/categories')

    return app
