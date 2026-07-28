from flask import Flask, render_template, request, jsonify, redirect, session, url_for
import mysql.connector
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "chave_secreta_123" #Protege a sessão do usuário, evitando que dados sejam modificados

# GERAR SENHA BCRYPT
def gerar_hash(senha_texto): #cria a função 'gerar_hash' que pega a 'senha_texto', a senha 123456
    senha_bytes = senha_texto.encode('utf-8') #bcrypt nao trabalha com string, e sim com bytes | aqui ele transforma a senha comum em bytes usando a codificação UTF-8 que transforma caracteres em numeros que o computador entende
    salt = bcrypt.gensalt() #gensalt() = generate salt | salt faz com que mesmo que dois users usem senhas iguais, tipo 123456, os hashes serão diferentes e não identicos. Assim, não é possível que alguém descubra o padrão entre as duas senhas iguais.
    senha_hash = bcrypt.hashpw(senha_bytes, salt) #pega os bytes gerado + o salt gerado e transforma na senha em hash | hashpw = hash password
    return senha_hash.decode('utf-8') #retorna o valor em bytes(linguegem que o pc entende) em uma string (texto comum que nós entendemos) | processo inverso do encode
    #pq precisa do decode? | Pq o banco espera receber um 'VARCHAR', uma string de texto, não um objeto bytes do Python, então nós precisamos converter os bytes para uma string para que o banco de dados consiga receber esse dado

def verificar_senha(senha_digitada, hash_armazenado): #serve pra verificar a senha que foi digitada na hora do login, pra ver se a senha digitada bate com a senha hash
    if not hash_armazenado: #se não for a senha hash 
        return False #vai dar erro, login negado
    senha_bytes = senha_digitada.encode('utf-8') #converte a senha digitada na hora do login para bytes
    hash_bytes = hash_armazenado.encode('utf-8') #converte a senha que está armazenada para bytes (pq ela veio do banco de dados como texto na hora de verificar)
    return bcrypt.checkpw(senha_bytes, hash_bytes) #o checkpw (check password) pega a senha digitada, extrai o salt do hash_armazenado e cria um novo hash para a senha digitada usando esse mesmo salt, e comparar os dois hashs
        #se os hashs baterem, vai retornar true (senha correta), se não retorna false (senha incorreta)
        
# CONEXÃO
def get_db():
    return mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        password='Mica@2009',
        database='almoxarifado',
    )

# AUTORIZAÇÃO
def login_required():
    return 'usuario' in session #Verifica se existe um usuário

def admin_required():
    return session.get('tipo') == 'admin' #Verifica se é um admin

# HOME
@app.route('/') # Define a página inicial de login
def home():
    return render_template('index.html') # Exibe o arquivo

# LOGIN
@app.route('/login', methods=['POST']) # Rota do login, que envia os dados para o banco 
def login():
    email = request.form.get('email') 
    senha = request.form.get('senha')

    conexao = get_db() # Cria a conexão com o banco
    cursor = conexao.cursor() # Cria o cursor para executar as consultas

    cursor.execute("""
        SELECT * FROM usuarios
        WHERE email = %s AND senha = %s
    """, (email, senha)) # O objetivo é encontrar um usuário com aquele e-mail e senha

    user = cursor.fetchone() # Busca o primeiro resultado da consulta

    cursor.close() # Fecha o cursor
    conexao.close() # Fecha a conexão com o banco

    if user: # Se o usuário for encontrado
        session['usuario'] = user[1] 
        session['tipo'] = user[4]
        session['email'] = user[2] # Salva as informações da sessão
        return redirect('/tabela') # Redireciona para a página de tabela

    return "Email ou senha inválidos" # Se não, retorna uma mensagem de erro

# LOGOUT
@app.route('/logout') # Inicia a rota de logout, que limpa a sessão do usuário
def logout():
    session.clear() # Limpa a sessão do usuário
    return redirect(url_for('home')) # Redireciona para a página inicial, automaticamente com url_for

# TABELA
@app.route('/tabela') # Rota da tabela, que exibe os dados do banco
def tabela():
    if not login_required(): # Se o usuário não estiver logado
        return redirect('/') # Redireciona para a página inicial

    conexao = get_db() # Inicia conexão com o banco
    cursor = conexao.cursor() # Inicia o cursor para executar as consultas

    cursor.execute("SELECT * FROM estoque") # Mostra todos os dados da tabela estoque
    resultado = cursor.fetchall() # Armazena na variável resultado

    cursor.close() # Fecha o cursor
    conexao.close() # Fecha a conexão com o banco

    return render_template('tabela.html', resultado=resultado) # Manda o resultado para a página tabela.html, usando Jinja2

# ENTRADA / SAÍDA ESTOQUE

@app.route('/entrada', methods=['POST']) # Rota para entrada e saída, manda os dados 
def entrada():

    nome = request.form.get('nome')
    categoria = request.form.get('categoria')
    qtde = request.form.get('qtde')
    responsavel = request.form.get('responsavel')
    estoque_min = request.form.get('estoque_min')
    preco = request.form.get('preco')
    descricao = request.form.get('descricao')
    tipo = request.form.get('tipo')
    imagem = request.files.get("imagem") # Captura os dados enviados pelo editar.html

    caminho_imagem = "" # Variável vazia para receber imagem

    if imagem: # Se o usuário mandou uma imagem
        nome_arquivo = secure_filename(imagem.filename) # Garante que o nome do arquivo seja seguro

        pasta = os.path.join("static", "uploads") # Cria a pasta uploads dentro da pasta static
        os.makedirs(pasta, exist_ok=True) # Verifica se existe

        caminho_salvar = os.path.join(pasta, nome_arquivo) # Caminho da imagem para salvar
        imagem.save(caminho_salvar) # Salva a imagem na pasta uploads

        caminho_imagem = url_for('static', filename=f'uploads/{nome_arquivo}') # Monta a url para exibir na tabela

    if not nome or not qtde or not responsavel or not tipo: # Se algum campo obrigatório não for preenchido
        return jsonify({"success": False, "erro": "Campos obrigatórios"}), 400 # Bad request
    qtde = int(qtde) # Converte a quantidade para inteiro para cálculos

    conexao = get_db() # Inicia a conexão com o banco
    cursor = conexao.cursor() # Inicia o cursor para executar as consultas

    cursor.execute("SELECT qtde, preco FROM estoque WHERE nome = %s", (nome,)) # Procura o produto
    item = cursor.fetchone() # Vai receber os dados do produto

    if item: # Se o item existir, vai buscar os dados atuais do produto para atualizar

        cursor.execute(""" 
            SELECT categoria, estoque_min, descricao, preco
            FROM estoque
            WHERE nome = %s
        """, (nome,)) # Busca os dados atuais do produto no banco

        dados = cursor.fetchone() # Vai receber os dados atuais do produto

        categoria_atual, estoque_min_atual, descricao_atual, preco_atual = dados # Separa as informações

        categoria = categoria if categoria else categoria_atual # Se o usuário não preencher a categoria, vai manter a atual

        estoque_min = ( 
            int(estoque_min) # Se o usuário preencher o estoque mínimo, vai converter para inteiro
            if estoque_min 
            else estoque_min_atual # Se não, vai manter o atual 
        )

        descricao = descricao if descricao else descricao_atual # Se o usuário não preencher a descrição, vai manter a atual

        if preco:
            preco = float(preco) # Se o usuário preencher o preço, vai converter para float
        else:
            preco = 0 # Se não, vai considerar o preço como 0 para não alterar o preço atual

# ENTRADA (SOMA)
    if tipo == "entrada": # Se clicar no botão de entrada, vai somar a quantidade e o preço

        if item:
            qtde_atual, preco_atual = item # Se o item existir, vai buscar os dados atuais do produto para atualizar

            nova_qtde = qtde_atual + qtde # Soma a quantidade atual com a quantidade enviada pelo usuário
            novo_preco = float(preco_atual) + float(preco) # Soma o preço atual com o preço enviado pelo usuário

            cursor.execute(""" 
                UPDATE estoque
                SET qtde = %s,
                    estoque_min = %s,
                    categoria = %s,
                    preco = %s,
                    descricao = %s,
                    imagem = %s
                WHERE nome = %s
            """, (nova_qtde, estoque_min, categoria, novo_preco, descricao, nome, imagem)) # Atualiza os dados do produto

        else: # Se o item não existir, vai inserir um novo produto no banco
            cursor.execute("""
                INSERT INTO estoque
                (responsavel, nome, categoria, qtde, estoque_min, descricao, preco, imagem)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (responsavel, nome, categoria, qtde, estoque_min, descricao, preco, caminho_imagem))

        conexao.commit() # Salva as alterações no banco


# SAÍDA (SUBTRAI)
    elif tipo == "saida": # Se clicar no botão de saída, vai subtrair a quantidade e o preço

        cursor.execute(
            "SELECT qtde, preco FROM estoque WHERE nome = %s",
            (nome,) # Busca o produto no banco para verificar a quantidade atual e o preço atual
        )

        produto = cursor.fetchone() # Vai receber os dados do produto

        if not produto: # Se o produto não existir, vai retornar um erro
            return jsonify({
                "success": False,
                "erro": "Produto não encontrado"
            }), 404 # Not Found

        qtde_atual, preco_atual = produto # Separa a quantidade atual e o preço atual do produto

        if qtde_atual < qtde: # Se a quantidade atual for menor que a quantidade enviada pelo usuário, vai retornar um erro
            return jsonify({
                "success": False,
                "erro": "Estoque insuficiente"
            }), 400 # Bad Request

        nova_qtde = qtde_atual - qtde # Subtrai a quantidade atual com a quantidade enviada pelo usuário
        novo_preco = float(preco_atual) - float(preco) # Subtrai o preço atual com o preço enviado pelo usuário

        if novo_preco < 0: # Se o preço ficar negativo, vai considerar o preço como 0
            novo_preco = 0

        cursor.execute("""
            UPDATE estoque
            SET qtde = %s,
                estoque_min = %s,
                categoria = %s,
                preco = %s,
                descricao = %s,
                imagem = %s
            WHERE nome = %s
        """, (
            nova_qtde,
            estoque_min,
            categoria,
            novo_preco,
            descricao,
            caminho_imagem,
            nome
        )) # Atualiza os dados do produto no banco

        conexao.commit() # Salva as alterações no banco

    else: # Se o tipo enviado pelo usuário não for "entrada" nem "saida", vai retornar um erro
        return jsonify({"success": False, "erro": "Tipo inválido"}), 400 # Bad Request

    cursor.close() # Fecha o cursor
    conexao.close() # Fecha a conexão com o banco

    return jsonify({"success": True}), 200 # OK

# EXCLUIR ITEM
@app.route('/excluir/<int:id>', methods=['DELETE']) # Rota para excluir um item do estoque, recebe o id do item
def excluir(id):

    conexao = get_db() # Inicia a conexão com o banco
    cursor = conexao.cursor() # Inicia o cursor para executar as consultas

    cursor.execute("DELETE FROM estoque WHERE id = %s", (id,)) # Deleta o item do estoque com o id recebido
    conexao.commit() # Salva as alterações no banco

    cursor.close() # Fecha o cursor
    conexao.close() # Fecha a conexão com o banco

    return jsonify({"success": True}) # Retorna um json com sucesso

# EDITAR
@app.route('/editar') # Rota para editar um item do estoque
def editar():
    if not login_required(): # Se o usuário não estiver logado, redireciona para a página inicial
        return redirect('/')

    return render_template('editar.html')

# ACESSO
@app.route('/acesso') # Rota para acessar a página de acesso
def acesso():
    if not login_required(): # Se o usuário não estiver logado, redireciona para a página inicial
        return redirect('/')

    if not admin_required(): # Se o usuário não for admin, retorna uma mensagem de acesso negado
        return "Acesso negado"

    conexao = get_db() # Inicia a conexão com o banco
    cursor = conexao.cursor() # Inicia o cursor para executar as consultas

    cursor.execute("SELECT * FROM usuarios") # Busca todos os usuários no banco
    resultado = cursor.fetchall() # Armazena o resultado da consulta na variável resultado

    cursor.close() # Fecha o cursor
    conexao.close() # Fecha a conexão com o banco

    return render_template('acesso.html', resultado=resultado) # Manda o resultado para a página acesso.html, usando Jinja2

# EXCLUIR USUÁRIO
@app.route('/excluirUsuario/<int:id>', methods=['DELETE']) # Rota para excluir um usuário, recebe o id do usuário
def excluir_usuario(id):

    conexao = get_db() # Inicia a conexão com o banco
    cursor = conexao.cursor() # Inicia o cursor para executar as consultas

    cursor.execute("DELETE FROM usuarios WHERE id = %s", (id,)) # Deleta o usuário com o id recebido 

    conexao.commit() # Salva as alterações no banco

    cursor.close() # Fecha o cursor
    conexao.close() # Fecha a conexão com o banco

    return jsonify({"success": True}) # Retorna um json com sucesso

# CADASTRO
@app.route('/cadastro', methods=['GET', 'POST']) # Rota para cadastrar um novo usuário, ele recebe e envia informações
def cadastro():

    if not login_required(): # Se o usuário não estiver logado, redireciona para a página inicial
        return redirect('/')

    if not admin_required(): # Se o usuário não for admin, retorna uma mensagem de acesso negado
        return "Acesso negado"

    if request.method == 'GET': # Se o método da requisição for GET, retorna a página de cadastro
        return render_template('cadastro.html')

    usuario = request.form.get('user')
    email = request.form.get('email')
    senha = request.form.get('senha')
    perfil = request.form.get('perfil') # Pega os dados enviados pelo formulário de cadastro GET

    conexao = get_db() # Inicia a conexão com o banco
    cursor = conexao.cursor() # Inicia o cursor para executar as consultas

    cursor.execute("""
        INSERT INTO usuarios (user, email, senha, tipo)
        VALUES (%s, %s, %s, %s)
    """, (usuario, email, senha, perfil)) # Insere os dados do novo usuário no banco POST

    conexao.commit() # Salva as alterações no banco
    cursor.close() # Fecha o cursor
    conexao.close() # Fecha a conexão com o banco

    return redirect('/acesso') # Redireciona para a página de acesso após o cadastro

# RODAR
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000) 