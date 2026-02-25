from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    from app.main.routes import main as main_bp
    app.register_blueprint(main_bp)

    @app.before_request
    def log_activity():
        from app.models import ActivityLog
        # Log all activity globally
        log = ActivityLog(
            action=f"{request.method} {request.path}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()

    from app.accounts.routes import accounts as accounts_bp
    app.register_blueprint(accounts_bp, url_prefix='/accounts')

    @app.context_processor
    def inject_global_data():
        from app.models import Account, Category
        return {
            'global_accounts': Account.query.all(),
            'global_categories': Category.query.all()
        }

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

    from app.profiles.routes import profiles as profiles_bp
    app.register_blueprint(profiles_bp, url_prefix='/profiles')

    @app.context_processor
    def inject_global_data():
        from app.models import Account, Category, Profile
        current_profile = Profile.query.filter_by(is_active=True).first()
        if not current_profile and Profile.query.count() > 0:
            current_profile = Profile.query.first()
            current_profile.is_active = True
            db.session.commit()
        
        return {
            'global_accounts': Account.query.filter_by(profile_id=current_profile.id).all() if current_profile else [],
            'global_categories': Category.query.all(),
            'current_profile': current_profile,
            'all_profiles': Profile.query.all()
        }

    # Database Change Notifications
    from sqlalchemy import event
    from app.services.telegram_service import TelegramService
    import os

    def get_db_path():
        uri = app.config['SQLALCHEMY_DATABASE_URI']
        if uri.startswith('sqlite:///'):
            db_path = uri.replace('sqlite:///', '')
            # Handle absolute paths or relative to instance
            if not os.path.isabs(db_path):
                # Check current directory first (for launcher)
                if os.path.exists(db_path):
                    return os.path.abspath(db_path)
                db_path = os.path.join(app.instance_path, db_path)
            return db_path
        return None

    @event.listens_for(db.session, 'after_flush')
    def receive_after_flush(session, flush_context):
        # Prevent recursion if we're logging activity
        if getattr(session, '_in_notification', False):
            return

        changes = []
        for obj in session.new:
            changes.append(f"Created: {type(obj).__name__}")
        for obj in session.dirty:
            changes.append(f"Updated: {type(obj).__name__}")
        for obj in session.deleted:
            changes.append(f"Deleted: {type(obj).__name__}")
            
        if changes:
            if not hasattr(session, '_pending_changes'):
                session._pending_changes = []
            session._pending_changes.extend(changes)

    @event.listens_for(db.session, 'after_commit')
    def receive_after_commit(session):
        if getattr(session, '_skip_notification', False):
            session._skip_notification = False # Reset for next use
            return

        if hasattr(session, '_pending_changes') and session._pending_changes:
            changes_text = "\n".join(set(session._pending_changes))
            session._pending_changes = []
            
            # Use current_profile name in caption if available
            # We use a new session here to avoid "session in committed state" errors
            from app.models import Profile
            try:
                # We can't easily start a new transaction here on the same session 
                # without risking issues, so we'll just try to get it carefully 
                # or use a default if it fails during commit hooks
                current_profile = Profile.query.filter_by(is_active=True).first()
                profile_name = current_profile.name if current_profile else "Unknown"
            except:
                profile_name = "System"

            db_path = get_db_path()
            if db_path and os.path.exists(db_path):
                caption = f"<b>Database Updated!</b>\nProfile: <b>{profile_name}</b>\n\nChanges:\n{changes_text}"
                token = app.config.get('TELEGRAM_BOT_TOKEN')
                chat_id = app.config.get('TELEGRAM_CHAT_ID')
                
                if token and chat_id:
                    # Non-blocking background sync
                    TelegramService.send_document_with_token(token, chat_id, db_path, caption=caption)

    # Ensure default profile exists and tables are created/updated
    with app.app_context():
        # First, ensure all tables are created (especially the new 'profile' table)
        db.create_all()
        
        # Check for missing columns in existing tables (SQLite specific auto-migration)
        engine = db.engine
        from sqlalchemy import inspect
        inspector = inspect(engine)
        
        db.session._skip_notification = True
        
        tables_to_patch = ['account', 'category', 'budget', 'loan', 'investment']
        for table_name in tables_to_patch:
            if table_name in inspector.get_table_names():
                columns = [c['name'] for c in inspector.get_columns(table_name)]
                if 'profile_id' not in columns:
                    try:
                        with engine.connect() as conn:
                            conn.execute(db.text(f"ALTER TABLE {table_name} ADD COLUMN profile_id INTEGER REFERENCES profile(id)"))
                            conn.commit()
                        app.logger.info(f"Added profile_id column to {table_name} table.")
                    except Exception as e:
                        app.logger.error(f"Error patching table {table_name}: {e}")

        from app.models import Profile, Account, Category, Budget, Loan, Investment
        if Profile.query.count() == 0:
            default_profile = Profile(name="Ariful Islam", is_active=True)
            db.session.add(default_profile)
            db.session.commit()
            
            # Map existing records to the default profile
            db.session._skip_notification = True
            Account.query.update({Account.profile_id: default_profile.id})
            Category.query.filter(Category.profile_id == None).update({Category.profile_id: default_profile.id})
            Budget.query.update({Budget.profile_id: default_profile.id})
            Loan.query.update({Loan.profile_id: default_profile.id})
            Investment.query.update({Investment.profile_id: default_profile.id})
            db.session.commit()
        
        db.session._skip_notification = False

    return app
