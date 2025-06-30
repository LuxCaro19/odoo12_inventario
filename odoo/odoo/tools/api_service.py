import requests
import datetime
import json

__author__ = 'fmorales'

from .jdbc_services import DEFAULT
import redis
#import sqlite3

def default_enc(o):
	if isinstance(o, (datetime.date, datetime.datetime)):
		return o.isoformat()
TTL = 28800 #12 horas de cache de la sesion
redis_cnx = redis.Redis(host='192.168.0.22', port=6379, db=0)

# def create_connection(host='localhost', port=6379, db=0)):
#     """ create a database connection to a database that resides
#         in the memory
#     """
#     try:
#         conn = sqlite3.connect(':memory:')
#         sql = "create table if not exists odoo_session (session_id varchar(50), createtime timestamp default current_timestamp )"
#
#         cursor = conn.cursor()
#         cursor.execute(sql)
#         conn.commit()
#         return conn
#     except Exception as e:
#         print(e)
#     return None
#
#
# sqlite_conn = create_connection()
#
# def get_session():
#     sql = "select session_id from odoo_session;"
#     cursor = sqlite_conn.cursor()
#     cursor.execute(sql)
#     result = cursor.fetchone()
#     if result:
#         print "get session from memory %s" % result[0]
#         return result[0]
#     return None
#
# def create_session(session_id):
#     sql = "insert into odoo_session (session_id) values ('%s')"%session_id
#     cursor = sqlite_conn.cursor()
#     cursor.execute(sql)
#     sqlite_conn.commit()
#     print "create session in memory %s" % session_id


SERVICES = {
    'PY': {
        'odoo': {
            'host': 'appsdev12.galilea.cl',
            'protocol': 'https',
            'port': '443',
            'ssl_check': True,
            'auth': {
                'api': '/web/session/authenticate',
                'method': requests.Session,
                'session_id': None,
                'credentials': json.dumps({
                        "params": {
                            "db": "appsdev12.galilea.cl",
                            "login": "restuser@galilea.cl",
                            "password": "4sme3#PbM3bPmx4#S7Cy"
                            }
                    })
                 },
            'header': {'content-type': 'application/json'},
            'default_data': json.dumps({}),
            'parser': None,

        },
        'graphql':{
            #TODO: Define this
        },
        'odoo12': {
            'host': 'odoo12dev.galilea.cl',
            'protocol': 'http',
            'port': '80'
        }
    },
    'PD': {
        'odoo': {
            'host': 'apps.galilea.cl',
            'protocol': 'http',
            'port': '8069',
            'ssl_check': False,
            'auth': {
                'api': '/web/session/authenticate',
                'method': requests.Session,
                'session_id': None,
                'credentials': json.dumps({
                        "params": {
                            "db": "odoopd",
                            "login": "restuser@galilea.cl",
                            "password": "4sme3#PbM3bPmx4#S7Cy"
                            }
                    })
                 },
            'header': {'content-type': 'application/json'},
            'default_data': json.dumps({}),
            'parser': None
        },
        'graphql':{
            #TODO: Define this
        },
        'odoo12' : {
            #TODO: changethis to PD
            'host': 'odoo12dev.galilea.cl',
            'protocol': 'http',
            'port': '80'
        }
    },
}

SERVICE = SERVICES[DEFAULT]

class ApiRequest:

    def __init__(self):
        pass
    def login(self, url, data, headers, service):
        '''
        :return: session id si corresponde
        '''
        call_auth = service.post(url=url, data=data, headers=headers)
        result = call_auth.json().get('result', None)
        if call_auth.ok and result:
            return result.get('session_id')

    def post(self, api=None, data={}, motor='odoo'):
        '''
        :param api:
        :param data: objeto con la data que se desea enviar a la api
        :param motor: por defecto odoo
        :return:
        '''

        if motor != 'odoo':
            raise NotImplementedError
        conf = SERVICE.get(motor, None)
        if not data:
            raise Exception('Data es un argumento obligatorio para POST')
        if not api:
            raise Exception('Api es un argumento obligatorio')
        if not api.startswith('/'):
            api = '/%s' % api
        if not conf:
            raise Exception('Motor %s no esta configurado para este ambiente'%motor)

        url = '%(protocol)s://%(host)s:%(port)s' % conf
        header = conf.get('header', None)
        #data = conf.get('default_data', None)
        try:
            data = json.dumps(data, default=default_enc)
        except:
            pass

        if conf['auth']:
            auth_service = conf['auth']
            #si la api requiere que este autenticado
            method = auth_service['method']()

            session_id = redis_cnx.get('session_id')

            if not session_id:
                session_id = self.login(url=url + auth_service['api'], data=auth_service['credentials'], headers=header,
                                        service=method)
                result = redis_cnx.setex('session_id',TTL , session_id)
                if not result:
                    pass
                    #result

            cookie = requests.cookies.create_cookie(name='session_id', value=str(session_id))
            # method.cookies['session_id'] = session_id
            method.cookies.set_cookie(cookie)

            response = method.post(url+api, data=data, verify=conf['ssl_check'], headers=header)
        else:
            response = requests.post(url+api, data=data, auth=conf['auth'], verify=conf['ssl_check'], headers=header)

        if response.status_code is not 201:
            return response.text
        return response.json()

    def get(self, api=None, motor='odoo'):
        '''
        :param api: en formato /api/../../..
        :param motor:
            'odoo' -> para api escritas en odoo
            'graphql' -> para api disponible en graphql
        :return: requests.get()
        '''
        conf = SERVICE.get(motor, None)
        #conf = {
        #    'host': 'apps.galilea.cl',
        #    'protocol': 'http',
        #    'port': '8069'
        #},
        if motor != 'odoo':
            raise NotImplementedError
        if not api:
            raise Exception('Api es un argumento obligatorio')
        if not api.startswith('/'):
            api = '/%s' % api
        if not conf:
            raise Exception('Motor %s no esta configurado para este ambiente'%motor)

        header = conf.get('header', None)
        url = '%(protocol)s://%(host)s:%(port)s' % conf

        data = conf.get('default_data', None)

        if conf['auth']:
            auth_service = conf['auth']
            #si la api requiere que este autenticado
            method = auth_service['method']()

            session_id = redis_cnx.get('session_id')

            if not session_id:
                session_id = self.login(url=url + auth_service['api'], data=auth_service['credentials'], headers=header, service=method)
                result = redis_cnx.setex('session_id', TTL, session_id)
                if not result:
                    pass
                    #result

            cookie = requests.cookies.create_cookie(name='session_id', value=str(session_id))
            #method.cookies['session_id'] = session_id
            method.cookies.set_cookie(cookie)

            response = method.get(url+api, data=data, verify=conf['ssl_check'], headers=header)
        else:
            response = requests.get(url+api, data=data, verify=conf['ssl_check'], headers=header)
        if response.status_code is not 200:
            return response.text
        #TODO: hacer parser de la respuesta por motor, para obtener siempre un response limpio
        return response.json()


if __name__ == '__main__':
    api = ApiRequest()
    result = api.get('/api/get_correos_niveles/victor.palma@galilea.cl/2')
    print (result)
    result = api.get('/api/get_correos_niveles/felipe.morales@galilea.cl/3')

    print (result)

