from flask import Blueprint, render_template, request, redirect, url_for, session
from models.db import get_db

blog_bp = Blueprint('blog', __name__)

@blog_bp.route('/')
def index():
    db = get_db()
    postagens = db.execute( '''
        SELECT id, titulo,
               CASE
                   WHEN LENGTH(conteudo) > 180 THEN SUBSTR(conteudo, 1, 180) || '...'
                   ELSE conteudo
               END AS resumo,
               usuario_id
        FROM postagens
        '''
    ).fetchall()
    return render_template('index.html', postagens=postagens)

@blog_bp.route('/criar_postagem', methods=['GET', 'POST'])
def criar_postagem():
    if request.method == 'POST':
        titulo = request.form['titulo']
        conteudo = request.form['conteudo']
        usuario_id = session.get('usuario_id')  # A lógica de sessão pode variar, ajuste conforme necessário

        # Inserir a postagem no banco de dados
        db = get_db()
        db.execute('INSERT INTO postagens (titulo, conteudo, usuario_id) VALUES (?, ?, ?)',
                   [titulo, conteudo, usuario_id])
        db.commit()

        return redirect(url_for('blog.index'))  # Redireciona para a página inicial ou lista de postagens

    return render_template('criar_postagem.html')

@blog_bp.route('/postagem/<int:postagem_id>', methods=['GET', 'POST'])
def detalhe_postagem(postagem_id):
    db = get_db()
    # Busca os detalhes da postagem pelo ID
    postagem = db.execute(
        'SELECT id, titulo, conteudo, usuario_id FROM postagens WHERE id = ?',
        (postagem_id,)
    ).fetchone()

    # Verifica se a postagem existe
    if not postagem:
        return "Postagem não encontrada", 404

    # Busca os comentários associados ao post (opcional)
    comentarios = db.execute(
        'SELECT id, conteudo, usuario_id FROM comentarios WHERE postagem_id = ?',
        (postagem_id,)
    ).fetchall()

    return render_template('detalhe_postagem.html', postagem=postagem, comentarios=comentarios)

@blog_bp.route('/comentar/<int:postagem_id>', methods=['POST'])
def comentar_postagem(postagem_id):
    conteudo = request.form['conteudo']
    usuario_id = session.get('usuario_id')

    if not usuario_id:
        return redirect(url_for('auth.login'))

    db = get_db()
    db.execute(
        'INSERT INTO comentarios (conteudo, usuario_id, postagem_id) VALUES (?, ?, ?)',
        (conteudo, usuario_id, postagem_id)
    )
    db.commit()

    return redirect(url_for('blog.detalhe_postagem', postagem_id=postagem_id))


@blog_bp.route('/excluir_postagem/<int:postagem_id>')
def excluir_postagem(postagem_id):
    return f"Postagem {postagem_id} excluída"
