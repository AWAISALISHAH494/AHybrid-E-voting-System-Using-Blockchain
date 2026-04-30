# ==========================================
# Author: Awais Ali Shah
# License: All Rights Reserved
# Unauthorized use or submission is prohibited
# ==========================================
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, current_user
from config import Config
from models import db
from models.user import User

login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from routes.auth import auth_bp
    from routes.voter import voter_bp
    from routes.admin import admin_bp
    from routes.blockchain import blockchain_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(voter_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(blockchain_bp)

    @app.route('/')
    def landing():
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('voter.dashboard'))
        return render_template('landing.html')

    with app.app_context():
        db.create_all()
        _seed_admin()

    return app


def _seed_admin():
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = User(
            full_name='System Admin',
            cnic='00000-0000000-0',
            email='admin@evoting.com',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
# ==========================================
# Author: Awais Ali Shah
# License: All Rights Reserved
# Unauthorized use or submission is prohibited
# ==========================================