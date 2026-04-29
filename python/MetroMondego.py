import flask
import logging
import psycopg2
import datetime
import jwt

# Configuração da chave secreta para geração de tokens JWT
SECRET_KEY = "1234"

app = flask.Flask(__name__)

StatusCodes = {
    'success': 200,
    'api_error': 400,
    'internal_error': 500
}

##########################################################
## DATABSE
##########################################################

def db_connection():
    """Estabelece e retorna uma conexão com a base de dados PostgreSQL."""
    db = psycopg2.connect(
        user='aulaspl',
        password='aulaspl',
        host='localhost',
        port='5432',
        database='metromondego'
    )
    return db

##########################################################
## ENDPOINTS
##########################################################

@app.route('/')
def landing_page():
    """Página inicial simples da API."""
    return """
    Base de Dados - Metro Mondego<br/>
    <br/>
    API v1.0<br/>
    <br/>
    Tiago Silva<br/>
    <br/>
    """

@app.route('/dbproj/user', methods=['PUT'])
def login():
    logger.info('PUT /metromondego/user')
    payload = flask.request.get_json()

    # Validação dos dados de entrada
    if not payload or 'username' not in payload or 'password' not in payload:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'Credenciais em falta!'})
    
    conn = db_connection()
    cur = conn.cursor()

    try:
        # Verifica se o utilizador existe na base de dados
        cur.execute('SELECT utilizadorId FROM Utilizador '
                    'WHERE email = %s AND palavraPasse = %s',
                    (payload['username'], payload['password']))
        user = cur.fetchone()

        if user: 
            # Gera o token JWT se as credenciais estievrem corretas
            token = jwt.encode({
                'user_id': user[0],
                'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)}, 
                SECRET_KEY, algorithm='HS256')

            response = {'status': StatusCodes['success'], 'results': token}
        else:
            response = {'status': StatusCodes['api_error'], 'errors': 'Credenciais inválidas!'}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'Erro no login: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}
    finally:
        if conn is not None:
            cur.close()
            conn.close()

    return flask.jsonify(response)

@app.route('/dbproj/authorization', methods=['GET'])
def check_authorization():
    logger.info('GET /dbproj/authorization')
    token = flask.request.headers.get('Authorization')

    # Remove o prefixo "Bearer " do token
    if token.startswith("Bearer "):
        token = token.split(" ")[1]
    
    if not token:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'Token de autenticação em falta!'})
    
    try:
        # Descodifica o token para validar o acesso
        dados_user = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

        response = {
            'status': StatusCodes['success'],
            'results': f"Acesso autorizado! User ID: {dados_user['user_id']}."
        }
    except jwt.ExpiredSignatureError:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'Token expirado! Faça login novamente.'})
    except jwt.InvalidTokenError:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'Token inválido!'})
    
    return flask.jsonify(response)

##########################################################
## INICIALIZAÇÃO DO SERVIDOR
##########################################################

if __name__ == '__main__':
    # Configuração do sistema de logs (ficheiro e consola)
    logging.basicConfig(filename='log_file.log')
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s', '%H:%M:%S')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Definições do servidor
    host = 'localhost'
    port = 8080
    logger.info(f'API v1.0 online: http://{host}:{port}')
    app.run(host=host, debug=True, threaded=True, port=port)
