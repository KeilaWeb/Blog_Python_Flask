from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models.db import get_db

auth_bp = Blueprint('auth', __name__)

# Rota de Cadastro
@auth_bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome_usuario = request.form['nome_usuario']
        senha = request.form['senha']
        
        # Conexão com o banco de dados
        db = get_db()
        
        # Verifica se o usuário já existe
        if db.execute('SELECT id FROM usuarios WHERE nome_usuario = ?', (nome_usuario,)).fetchone() is not None:
            flash('Nome de usuário já existe.')
            return redirect(url_for('auth.cadastro'))
        
        # Insere o novo usuário
        db.execute(
            'INSERT INTO usuarios (nome_usuario, senha) VALUES (?, ?)',
            (nome_usuario, generate_password_hash(senha))
        )
        db.commit()
        flash('Cadastro realizado com sucesso! Faça login.')
        return redirect(url_for('auth.login'))

    return render_template('cadastro.html')

# Rota de Login
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nome_usuario = request.form['nome_usuario']
        senha = request.form['senha']
        
        # Conexão com o banco de dados
        db = get_db()
        
        # Busca o usuário pelo nome
        user = db.execute('SELECT * FROM usuarios WHERE nome_usuario = ?', (nome_usuario,)).fetchone()
        
        # Verifica se o usuário existe e se a senha está correta
        if user is None or not check_password_hash(user['senha'], senha):
            flash('Nome de usuário ou senha incorretos.')
            return redirect(url_for('auth.login'))
        
        # Armazena o usuário na sessão
        session['usuario_id'] = user['id']
        session['nome_usuario'] = user['nome_usuario']
        session['eh_administrador'] = user['eh_administrador']
        flash('Login realizado com sucesso!')
        return redirect(url_for('blog.index'))

    return render_template('login.html')

# Rota de Logout
@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta.')
    return redirect(url_for('blog.index'))
