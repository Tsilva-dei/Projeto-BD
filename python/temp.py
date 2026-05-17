##
## =============================================
## ============== Bases de Dados ===============
## ============== LEI  2025/2026 ===============
## =============================================
## =================== Demo ====================
## =============================================
## =============================================
## === Department of Informatics Engineering ===
## =========== University of Coimbra ===========
## =============================================
##
## Authors:
##   João R. Campos <jrcampos@dei.uc.pt>
##   BD 2025/2026 Team
##   University of Coimbra


import flask
import logging
import psycopg2
import time
import jwt
from datetime import datetime, timezone, timedelta 

SECRET_KEY = "projetomondego"

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
        host='127.0.0.1',
        port='5432',
        database='metromondego'
    )

    return db




##########################################################
## ENDPOINTS
##########################################################

###alteracao projeto#########################################################
@app.route('/dbproj/user', methods=['PUT'])
def login():
    logger.info('Acedeu ao endpoint: PUT /dbproj/user')    
    payload = flask.request.get_json()
    
    response = {}
    status_code = StatusCodes['success']
    conn = None

    if not payload or 'email' not in payload or 'password' not in payload:
        logger.warning('Tentativa de login com dados incompletos')
        response = {"status": StatusCodes['api_error'], "errors": "missing data", "results": None}
        status_code = StatusCodes['api_error']
    else:
        try:
            conn = db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT utilizadorid, nome
                FROM utilizador
                WHERE email = %s AND palavrapasse = %s
            """, (payload['email'], payload['password']))

            user = cur.fetchone()

            if user:
                logger.info(f'Login efetuado com sucesso para o utilizador: {payload["email"]}')
                token = jwt.encode({
                    'user_id': user[0],
                    'exp': datetime.now(timezone.utc) + timedelta(hours=4) 
                }, SECRET_KEY, algorithm="HS256")

                response = {"status": StatusCodes['success'], "errors": None, "results": token}
            else:
                logger.warning(f'Falha no login: Dados inválidos para {payload["email"]}')
                response = {"status": StatusCodes['api_error'], "errors": "invalid login", "results": None}
                status_code = StatusCodes['api_error']

        except (Exception, psycopg2.DatabaseError) as error:
            logger.error(f'Erro no login: {error}')
            response = {"status": StatusCodes['internal_error'], "errors": str(error), "results": None}
            status_code = StatusCodes['internal_error']
        finally:
            if conn is not None:
                cur.close()
                conn.close()

    return flask.jsonify(response), status_code

@app.route('/dbproj/authorization', methods=['GET'])
def authorization():
    logger.info('A verificar autorização do token - GET /dbproj/authorization')
    token_header = flask.request.headers.get('Authorization')
    
    response = {}
    status_code = StatusCodes['success']

    if not token_header:
        logger.warning('Tentativa de autorização falhou: token_header em falta')
        response = {"status": StatusCodes['api_error'], "errors": "Token missing", "results": None}
        status_code = StatusCodes['api_error']
    else:
        if token_header.startswith("Bearer "):
            token = token_header.split(" ")[1]
        else:
            token = token_header

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            logger.info(f"Token validado com sucesso. Utilizador ID: {data['user_id']}")
            response = {
                "status": StatusCodes['success'], 
                "errors": None, 
                "results": f"Acesso Autorizado! És o utilizador com ID: {data['user_id']}"
            }
        except jwt.ExpiredSignatureError:
            logger.warning('O token apresentado já expirou.')
            response = {"status": StatusCodes['api_error'], "errors": "Token expired", "results": None}
            status_code = StatusCodes['api_error']
        except jwt.InvalidTokenError:
            logger.error('Foi apresentado um token inválido!')
            response = {"status": StatusCodes['api_error'], "errors": "Invalid token", "results": None}
            status_code = StatusCodes['api_error']

    return flask.jsonify(response), status_code
################################################


##
## Demo GET
##
## Obtain all utilizadores in JSON format
##
## To use it, access:
##
## http://localhost:8080/utilizador/
##

#alteracao projeto#########################################################
@app.route('/utilizador/', methods=['GET'])
def get_users():
    logger.info('Solicitada listagem de utilizadores - GET /utilizador/')
    
    response = {}
    status_code = StatusCodes['success']
    conn = None

    try:
        conn = db_connection()
        cur = conn.cursor()
       
        cur.execute("SELECT utilizadorid, nome, email FROM utilizador")
        rows = cur.fetchall()

        logger.info(f'Query executada. Encontrados {len(rows)} utilizadores.')

        resultado = []
        for row in rows:
            resultado.append({
                "id": row[0],
                "nome": row[1],
                "email": row[2]
            })

        response = {
            "status": StatusCodes['success'],
            "errors": None,
            "results": resultado
        }

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'Erro ao listar utilizadores: {error}')
        
        response = {
            "status": StatusCodes['internal_error'], 
            "errors": str(error),
            "results": None
        }
        status_code = StatusCodes['internal_error']

    finally:
        if conn is not None:
            cur.close()
            conn.close()

    return flask.jsonify(response), status_code

##########################################################

##
## Demo GET
##
## Obtain department with ndep <ndep>
##
## To use it, access:
##
## http://localhost:8080/departments/10
##

@app.route('/departments/<ndep>/', methods=['GET'])
def get_department(ndep):
    logger.info('GET /departments/<ndep>')

    logger.debug(f'ndep: {ndep}')

    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute('SELECT ndep, nome, local FROM dep where ndep = %s', (ndep,))
        rows = cur.fetchall()

        row = rows[0]

        logger.debug('GET /departments/<ndep> - parse')
        logger.debug(row)
        content = {'ndep': int(row[0]), 'nome': row[1], 'localidade': row[2]}

        response = {'status': StatusCodes['success'], 'results': content}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'GET /departments/<ndep> - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


##
## Demo POST
##
## Add a new department in a JSON payload
##
## To use it, you need to use postman or curl:
##
## curl -X POST http://localhost:8080/departments/ -H 'Content-Type: application/json' -d '{'localidade': 'Polo II', 'ndep': 100, 'nome': 'Seguranca'}'
##

@app.route('/departments/', methods=['POST'])
def add_departments():
    logger.info('POST /departments')
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f'POST /departments - payload: {payload}')

    # do not forget to validate every argument, e.g.,:
    if 'ndep' not in payload:
        response = {'status': StatusCodes['api_error'], 'results': 'ndep value not in payload'}
        return flask.jsonify(response)

    # parameterized queries, good for security and performance
    statement = 'INSERT INTO dep (ndep, nome, local) VALUES (%s, %s, %s)'
    values = (payload['ndep'], payload['localidade'], payload['nome'])

    try:
        cur.execute(statement, values)

        # commit the transaction
        conn.commit()
        response = {'status': StatusCodes['success'], 'results': f'Inserted dep {payload["ndep"]}'}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /departments - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


##
## Demo PUT
##
## Update a department based on a JSON payload
##
## To use it, you need to use postman or curl:
##
## curl -X PUT http://localhost:8080/departments/ -H 'Content-Type: application/json' -d '{'ndep': 100, 'localidade': 'Porto'}'
##

@app.route('/departments/<ndep>', methods=['PUT'])
def update_departments(ndep):
    logger.info('PUT /departments/<ndep>')
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f'PUT /departments/<ndep> - payload: {payload}')

    # do not forget to validate every argument, e.g.,:
    if 'localidade' not in payload:
        response = {'status': StatusCodes['api_error'], 'results': 'localidade is required to update'}
        return flask.jsonify(response)

    # parameterized queries, good for security and performance
    statement = 'UPDATE dep SET local = %s WHERE ndep = %s'
    values = (payload['localidade'], ndep)

    try:
        res = cur.execute(statement, values)
        response = {'status': StatusCodes['success'], 'results': f'Updated: {cur.rowcount}'}

        # commit the transaction
        conn.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

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

    host = '127.0.0.1'
    port = 8080
    app.run(host=host, debug=True, threaded=True, port=port)
    logger.info(f'API v1.0 online: http://{host}:{port}')