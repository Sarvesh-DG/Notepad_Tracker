from flask import Flask
from app.routes.editor import editor_bp
from app.routes.git_routes import git_bp
def create_app():
    app=Flask(__name__)
    app.register_blueprint(editor_bp)
    app.register_blueprint(git_bp)
    return app


