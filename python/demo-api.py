import flask
import logging
import psycopg2
import datetime
import jwt

SECRET_KEY = "1234"

app = flask.Flask(__name__)

StatusCodes = {
    'success': 200,
    'api_error': 400,
    'internal_error': 500
}

##########################################################
## DATABASE ACCESS
##########################################################

def db_connection():
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
    return """

    Base de Dados - Metro Mondego<br/>
    <br/>
    API v1.0<br/>
    <br/>
    Tiago Silva<br/>
    <br/>
    """



@app.route('/metromondego/user', methods=['PUT'])
def login():
    logger.info('PUT /metromondego/user')
    payload = flask.request.get_json()

    if not payload or 'username' not in payload or 'password' not in payload:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'Credenciais em falta!'})
    
    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute('SELECT utilizadorId FROM Utilizador'
                    'WHERE email = %s AND palavraPasse = %s',
                    (payload['username'], payload['password']))
        user = cur.fetchone()

        if user: 
            token = jwt.encode({
                'user_id': user[0],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)},
                SECRET_KEY, algorithm='HS256')
            
            response = {'status': StatusCodes['success'], 'results': token}
        else:
            response = {'status': StatusCodes['api_error'], 'errors': 'Credenciais inválidas!'}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'Erro no login: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}
    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)



@app.route('/metromondego/linhas', methods=['GET'])
def linhas():
    logger.info('GET /metromondego/linhas')
    token = flask.request.headers.get('Authorization')

    if not token:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'Token de autenticação em falta!'})
    
    try:
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

if __name__ == '__main__':

    # set up logging
    logging.basicConfig(filename='log_file.log')
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s', '%H:%M:%S')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    host = 'localhost'
    port = 8080
    app.run(host=host, debug=True, threaded=True, port=port)
    logger.info(f'API v1.0 online: http://{host}:{port}')
