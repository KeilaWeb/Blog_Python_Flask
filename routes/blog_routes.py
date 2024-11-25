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

    # Buscar a postagem no banco de dados
    postagem = db.execute(
        'SELECT id, titulo, conteudo, usuario_id FROM postagens WHERE id = ?',
        (postagem_id,)
    ).fetchone()

    if not postagem:
        return "Postagem não encontrada", 404

    # Buscar os comentários da postagem
    comentarios = db.execute(
        'SELECT id, conteudo, usuario_id FROM comentarios WHERE postagem_id = ?',
        (postagem_id,)
    ).fetchall()

    # Caso seja uma requisição POST (novo comentário)
    if request.method == 'POST':
        conteudo = request.form['conteudo']
        usuario_id = session.get('usuario_id')

        if usuario_id:
            db.execute(
                'INSERT INTO comentarios (conteudo, usuario_id, postagem_id) VALUES (?, ?, ?)',
                (conteudo, usuario_id, postagem_id)
            )
            db.commit()
            return redirect(url_for('blog.detalhe_postagem', postagem_id=postagem_id))
        else:
            return "Usuário não autenticado", 403

    # Renderizar o template passando os dados
    return render_template('detalhe_postagem.html', postagem=postagem, comentarios=comentarios)

@blog_bp.route('/editar_postagem/<int:postagem_id>', methods=['GET', 'POST'])
def editar_postagem(postagem_id):
    db = get_db()

    # Buscar a postagem no banco de dados
    postagem = db.execute(
        'SELECT id, titulo, conteudo, usuario_id FROM postagens WHERE id = ?',
        (postagem_id,)
    ).fetchone()

    if not postagem:
        return "Postagem não encontrada", 404

    # Verifica se o usuário tem permissão para editar
    if postagem['usuario_id'] != session.get('usuario_id') and not session.get('eh_administrador'):
        return "Acesso negado", 403

    if request.method == 'POST':
        titulo = request.form['titulo']
        conteudo = request.form['conteudo']

        # Atualizar a postagem no banco de dados
        db.execute(
            'UPDATE postagens SET titulo = ?, conteudo = ? WHERE id = ?',
            (titulo, conteudo, postagem_id)
        )
        db.commit()

        return redirect(url_for('blog.detalhe_postagem', postagem_id=postagem_id))

    return render_template('editar_postagem.html', postagem=postagem)

@blog_bp.route('/excluir_postagem/<int:postagem_id>')
def excluir_postagem(postagem_id):
    return f"Postagem {postagem_id} excluída"

@blog_bp.route('/comentar/<int:postagem_id>', methods=['POST'])
def comentar_postagem(postagem_id):
    conteudo = request.form['conteudo']
    usuario_id = session.get('usuario_id')  # Identifica o usuário logado

    if not usuario_id:
        return redirect(url_for('auth.login'))  # Redireciona para o login se o usuário não estiver autenticado

    db = get_db()
    db.execute(
        'INSERT INTO comentarios (conteudo, usuario_id, postagem_id) VALUES (?, ?, ?)',
        (conteudo, usuario_id, postagem_id)
    )
    db.commit()

    # Redireciona de volta para a página do post após adicionar o comentário
    return redirect(url_for('blog.detalhe_postagem', postagem_id=postagem_id))

@blog_bp.route('/editar_comentario/<int:comentario_id>', methods=['GET', 'POST'])
def editar_comentario(comentario_id):
    usuario_id = session.get('usuario_id')
    db = get_db()

    # Busca o comentário no banco de dados
    comentario = db.execute(
        'SELECT id, conteudo, usuario_id, postagem_id FROM comentarios WHERE id = ?',
        (comentario_id,)
    ).fetchone()

    if not comentario:
        return "Comentário não encontrado", 404

    # Verifica se o usuário tem permissão para editar
    if comentario['usuario_id'] != usuario_id and not session.get('eh_administrador'):
        return "Acesso negado", 403

    if request.method == 'POST':
        novo_conteudo = request.form['conteudo']
        db.execute(
            'UPDATE comentarios SET conteudo = ? WHERE id = ?',
            (novo_conteudo, comentario_id)
        )
        db.commit()
        return redirect(url_for('blog.detalhe_postagem', postagem_id=comentario['postagem_id']))

    return render_template('editar_comentario.html', comentario=comentario)


@blog_bp.route('/excluir_comentario/<int:comentario_id>', methods=['POST'])
def excluir_comentario(comentario_id):
    usuario_id = session.get('usuario_id')  # Verifica o usuário logado
    eh_administrador = session.get('eh_administrador', False)

    db = get_db()
    comentario = db.execute(
        'SELECT usuario_id, postagem_id FROM comentarios WHERE id = ?',
        (comentario_id,)
    ).fetchone()

    if not comentario:
        return "Comentário não encontrado", 404

    # Permitir exclusão apenas pelo autor do comentário ou um administrador
    if comentario['usuario_id'] != usuario_id and not eh_administrador:
        return "Acesso negado", 403

    # Excluir o comentário
    db.execute('DELETE FROM comentarios WHERE id = ?', (comentario_id,))
    db.commit()

    # Redirecionar para a página de detalhes do post
    return redirect(url_for('blog.detalhe_postagem', postagem_id=comentario['postagem_id']))
