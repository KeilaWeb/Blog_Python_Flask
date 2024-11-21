from flask import Flask, redirect, url_for
from config import Config
from models.db import init_db
from routes.auth_routes import auth_bp
from routes.blog_routes import blog_bp

app = Flask(__name__)
app.config.from_object(Config)

@app.route('/')
def home():
    return redirect(url_for('blog.index'))

# Registra os blueprints para organizar as rotas
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(blog_bp, url_prefix='/blog')

if __name__ == '__main__':
    app.run(debug=True)
