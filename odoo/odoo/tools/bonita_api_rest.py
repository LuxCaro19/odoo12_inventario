# BY fmorales
#import httplib2 as http
import json
from _symtable import USE

import requests
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

USER = 'odoouser'
PASS = 'odoopass'
SERVICE_URL = 'https://procesos.galilea.cl:8443/bonita'
#SERVICE_URL = 'http://localhost:8080/bonita'
DEFAULT_COL_KEY = 'alias'


class User(object):
    def __init__(self, nombre, rut, cargo, email, login, ubicacion, activo, depende_de):
        self.nombre = nombre
        self.rut = rut
        self.cargo = cargo
        self.email = email
        self.login = login
        self.ubicacion = ubicacion
        self.activo = activo
        self.depende_de = depende_de


class Cargo(object):
    def __init__(self, desc, cod):
        self.descripcion = desc
        self.codigo_cargo = cod


class Ubicacion(object):
    def __init__(self, desc, cod):
        self.descripcion = desc
        self.codigo_ubicacion = cod


# class Request(object):
#     def __init__(self, headers=None):
#         self.serv = http.Http()
#         self.headers = headers  # {'Authorization': 'Basic YWVsbGl1czpMeW5YNEdhbGVsaWE='}
#         if headers:
#             for h in headers.iteritems():
#                 self.headers[h[0]] = h[1]
#         self.method = None
#         self.body = ''
#
#     def parse_url(self, path=None):
#         if path:
#             url = urlparse(SERVICE_URL + path)
#         return url.geturl()
#
#     def do_get(self, path, body=None, params={}):
#         self.method = 'GET'
#         url = self.parse_url(path)
#         if body:
#             self.body = json.dumps(body)
#         return self.call(url=url)
#
#     def do_post(self, path, body=None, has_auth=False, params={}):
#         self.method = 'POST'
#
#         if body:
#             self.body = json.dumps(body)
#
#         url = self.parse_url(path)
#         return self.call(url=url)
#
#     def do_put(self, path, body=None):
#         self.method = 'PUT'
#
#         if body:
#             self.body = json.dumps(body)
#
#         url = self.parse_url(path)
#         return self.call(url=url)
#
#     def do_delete(self, path, body=None):
#         self.method = 'DELETE'
#
#         self.body = body
#
#         url = self.parse_url(path)
#         return self.call(url=url)
#
#     def call(self, url, has_auth=False, params={}):
#         # if has_auth:
#         #    self.serv.add_credentials(USER, PASS)
#         # url = urlparse(SERVICE_URL+path)
#         # if body!='':
#         # self.body = json.dumps(self.body)
#         print 'URL' + url
#         response, content = self.serv.request(url,
#                                               self.method,
#                                               self.body,
#                                               self.headers)
#         #print response  # , content
#         if response['status'] == '200':
#             try:
#                 content = json.loads(content)
#             except:
#                 pass
#             return response, content
#         else:
#             return response, content


class BonitaApiRest:
    APIS = {
            'LOGIN' : '/loginservice',
            'CHECK_USER': '/API/identity/user?p=0&c=1&f=userName=%s&d=manager_id',
            'UPDATE_USER': '/API/identity/user/%s',
            'REMOVE_USER': '/API/identity/user/%s',
            'GET_GROUP': '/API/identity/group?p=0&c=1&f=name=%s',
            'GET_ROLE': '/API/identity/role?p=0&c=1&f=name=%s',
            'CREATE_USER': '/API/identity/user',
            'CREATE_MEMBERSHIP': '/API/identity/membership',
            'DELETE_MEMBERSHIP': '/API/identity/membership/%s/%s/%s', #/:userId/:groupId/:roleId
            'CREATE_PROFILEMEMBER': '/API/portal/profileMember',
            'DELETE_PROFILEMEMBER': '/API/portal/profileMember/%s',
            'GET_LAST_PROCESS': '/API/bpm/process?p=0&c=1&f=name=%s&f=activationState=ENABLED&o=version DESC',
            'INSTANTIATION': '/API/bpm/process/%s/instantiation'
        }

    def __init__(self, service_name=SERVICE_URL, ssl_check=True):
        self.ssl_check = ssl_check
        self.cookie = None
        self.request = None
        self.rollback_operations = []
        self.service_name = service_name

    def login(self, username, password):
        url = self.service_name + self.APIS['LOGIN']

        values = {"username": username,
                  "password": password,
                  "redirect": "false"}

        pst = requests.post(url, values, verify=self.ssl_check)
        if pst.status_code == 200:
            self.username = username
            self.cookie = pst.cookies
            apiUser = self.APIS['CHECK_USER'] % (username)
            self.user_id = self.call_api('GET', apiUser)[0]['id']

    def __do_post__(self, api=None, body=None, status_ok=200):
        if api is None:
            return
        data = json.dumps(body)
        url = self.service_name + api

        r = requests.post(url, data, verify=self.ssl_check, cookies=self.cookie)
        return r.status_code, r.json()

    def __do_put__(self, api=None, body = None, status_ok = 200):
        if api is None:
            return
        url = self.service_name + api

        r = requests.put(url, json.dumps(body), verify=self.ssl_check,cookies = self.cookie)
        return r.status_code, r.json()

    def __do_get__(self, api=None):
        if api is None:
            return
        url = self.service_name + api

        r = requests.get(url, cookies = self.cookie, verify=self.ssl_check)
        return r.json()

    def call_api(self, method= 'GET', api=None, body=None):
        if api is None:
            return
        if method == 'GET':
            return self.__do_get__(api)
        elif method == 'POST':
            return self.__do_post__(api, body)
        elif method == 'PUT':
            return self.__do_put__(api, body)
        #print self.request.do_get(api)

    def do_rollback(self):
        #print 'DO ROLLBACK!!'
        for operation in self.rollback_operations:

            func = operation.get('function', None)
            api = operation.get('path',None)
            data = operation.get('data', None)
            #print 'TRY ROLLBACK IN %s' % api
            if not (func or api):
                raise Exception('No se puede realizar rollback sin funcion ni api')
            resp, content = func(api, data)
            if resp['status'] == '200':
                continue
            else:
                data_str = data.__str__() if data else 'SIN DATA'
                raise Exception('Imposible realizar rollback de la operacion %s, con la data %s'%(api, data_str))

    def delete_user(self, user):
        resp, bonita_user = self.call_api('GET', self.APIS['CHECK_USER'] % user.login)
        if isinstance(bonita_user, list) and len(bonita_user) != 0:
            #Si el usuario existe en bonita por Login
            bonita_user = bonita_user[0]
            try:
                resp, user_delete = self.call_api('GET', self.APIS['REMOVE_USER'] % bonita_user["id"])
            except Exception as e:
                pass
            finally:
                if resp['status'] != '200':
                    raise Exception('Imposible borrar el usuario %s'%user.login)
        else:
            return

    def create_user(self, user):
        '''
        recibe un objeto model inventory_usuario
        1. check si usuario existe /API/identity/user?p=0&c=1&f=userName=%s
            si existe no hacer nada
        2. si espefica "DEPENDE DE" buscar el manager por userName y traer el ID
        3. crear usuario
            API = /API/identity/user
            DATA = {
              "userName":"New.User",
              "password":"bpm",
              "password_confirm":"bpm",
              "icon":"",
              "firstname":"New",
              "lastname":"User",
              "title":"Mr",
              "job_title":"Human resources benefits",
              "manager_id":"3"
            }
            la API retorna el id del usuario en el json
        4. buscar grupo por name API/identity/group?p=0&c=1&f=name=NAME
        5. Buscar rol por description /API/identity/role?f=description=NAME
        5. Crear membership /API/identity/membership
            {
              "user_id":"4",
              "group_id":"5",
              "role_id":"1"
            }
        '''

        # Check si usuario existe
        if user.login == '' or user.login is None or user.login == '-':
            return None

        resp, bonita_user = self.call_api('GET', self.APIS['CHECK_USER'] % user.login)

        if isinstance(bonita_user, list) and len(bonita_user) != 0:
            #Si el usuario existe en bonita por Login
            bonita_user = bonita_user[0]
            bonita_state = True if bonita_user['enabled'] == "true" else False

            if bonita_state != user.activo:
                # actualizar el estado del usuario segun estado en user
                new_bonita_state = 'true' if user.activo else 'false'
                post_data = {'enabled': new_bonita_state}
                resp, update_resp = self.call_api('PUT', self.APIS['UPDATE_USER'] % bonita_user['id'], post_data)
                if(resp['status']!='200'):
                    raise Exception('No se logro actualizar el usuario %s, ID (bonita) %s'%(user.login, bonita_user['id']))
                self.rollback_operations.append(dict(function=self.__do_put__
                                                     , path=self.APIS['UPDATE_USER'] % bonita_user['id']
                                                     , data={'enabled': bonita_user["enabled"]}
                                                     )
                                                )
                bonita_user['enabled'] = new_bonita_state

            if bonita_user['manager_id'] != '0' and user.depende_de:
                #si el usuario de bonita tiene manager id comparamos login
                if bonita_user['manager_id']['userName'] != user.depende_de.login:

                    pass
        else:
            # Si el usuario no existe hay que crearlo
            #obtener grupo en bonita a partir de la ubicacion del usuario
            resp, bonita_group = self.call_api('GET', self.APIS['GET_GROUP'] % user.ubicacion.codigo_ubicacion)
            if isinstance(bonita_group, list) and len(bonita_group) != 0:
                bonita_group = bonita_group[0]
            else:
                bonita_group = None
            #obtener role en bonita a partir del cargo del usuario
            resp, bonita_role = self.call_api('GET', self.APIS['GET_ROLE'] % user.cargo.codigo_cargo)
            if isinstance(bonita_role, list) and len(bonita_role) != 0:
                bonita_role = bonita_role[0]
            else:
                bonita_role = None
            bonita_manager = {"id": ""}
            if user.depende_de is not None: #TODO: Verificar si depende_de es None cuando no esta especificado
                #si esta especificado, se debe ir a buscar al usuario jefe para obtener el ID
                resp, bonita_manager = self.call_api('GET', self.APIS['CHECK_USER'] % user.depende_de.login)
                if isinstance(bonita_manager, list) and len(bonita_manager) != 0:
                    #Si usuario existe
                    bonita_manager = bonita_manager[0]
                else:
                    #si no existe crear manager
                    bonita_manager = self.create_user(user.depende_de)
                    if not bonita_manager:
                        raise Exception('No se logro crear el manager con login %s' % user.depende_de.login)
            try:
                #CREANDO EL USUARIO Y SUS RELACIONES
                user_data = {
                    "userName": user.login,
                    "password": "1020", #TODO: Obtener la password del usuario desde el formulario
                    "password_confirm": "1020",
                    "firstname": user.nombre,
                    "lastname": "",
                    "title": "",
                    "job_title": bonita_role["displayName"] if bonita_role is not None else "",
                    "manager_id": bonita_manager["id"],
                    "enabled": "true"
                }


                resp, bonita_user = self.call_api('POST', self.APIS['CREATE_USER'], user_data)
                if resp['status'] != '200':
                    #self.do_rollback()
                    raise Exception('No se logro crear el usuario %s'%bonita_user)

                self.rollback_operations.append(dict(function=self.__do_get__
                                                    , path=self.APIS['REMOVE_USER'] % bonita_user['id']
                                                     )
                                                )
                #crear membership con usuario, grupo y rol
                if bonita_group and bonita_role:
                    membership_data = {
                          "user_id": bonita_user["id"],
                          "group_id": bonita_group["id"],
                          "role_id": bonita_role["id"]
                        }
                    resp, bonita_membership = self.call_api('POST', self.APIS['CREATE_MEMBERSHIP'], membership_data)
                    if resp['status'] != '200':
                        #self.do_rollback()
                        raise Exception('No fue posible crear relacion "membership" para el usuario %s, groupid %s, roleid %s' %
                                        (bonita_user["id"], bonita_group["id"], bonita_role["id"]))

                    #self.rollback_operations.append(dict(function=self.request.do_delete
                    #                                , path=self.APIS['DELETE_MEMBERSHIP'] % (bonita_user['id'], bonita_group["id"], bonita_role["id"])
                    #                                 )
                    #                            )
                profile_data = {
                      "profile_id": "1", #USER
                      "member_type": "USER",
                      "user_id": bonita_user["id"]
                    }
                resp, bonita_profilemember = self.call_api('POST', self.APIS['CREATE_PROFILEMEMBER'], profile_data)
                if resp['status'] != '200':
                    #self.do_rollback()
                    raise Exception('No fue posible generar el profilemember para el usuario %s', user.login)

                #self.rollback_operations.append(dict(function=self.request.do_delete
                #                                    , path=self.APIS['DELETE_PROFILEMEMBER'] % (bonita_profilemember["id"])
                #                                     )
                #                                )
            except Exception as e:
                #print e
                self.do_rollback()
        return bonita_user

    def instantiation(self, process_name=None, data=None):
        if not process_name:
            return
        if not data:
            return
        #get last process
        proceso = self.call_api('GET', self.APIS['GET_LAST_PROCESS'] % process_name)
        pid = 0

        try:
            if proceso:
                pid = proceso[0]['id']
        except Exception as e:
            pass

        status_code, response = self.call_api('POST', self.APIS['INSTANTIATION'] % pid, data)
        if status_code == 200:
            return response
        else:
            raise response

#TESTING USEs
# if __name__ == "__main__":
#
#     api = BonitaApiRest(SERVICE_URL, False)
#
#     api.login(USER, PASS)
#
#     data = {
#             "cod_area":115,
#             "desc_area":"OBRA TALCA",
#             "detalle_ajuste":[
#                 {
#                     "cantidad_actual":3,
#                     "cod_producto":1249334,
#                     "desc_producto":"UNION AMERICANA 75 MM SO-SO  1",
#                     "unidad":"UN",
#                     "merma":2
#                 },
#                 {
#                     "cantidad_actual":1,
#                     "cod_producto":1180390,
#                     "desc_producto":"CARRETILLA DOSIFICADORA  1 UN",
#                     "unidad":"UN",
#                     "merma":1
#                 }
#
#             ],
#             "fecha_ajuste":"2018-04-19",
#             "id_ajuste":1,
#             "login_usuario":"fmorales"
#             }
#
#     response = api.instantiation('CargaAjuste', data)
#
#     #api = '/API/bpm/process?p=0&c=10'
#     #b.call_api(api)
#
#     # init test
#     #cargo_usuario = Cargo('Administrativo de Obra', 'ADOB')
#     #cargo_jefe = Cargo('CONSTRUCTOR RESIDENTE', 'CRE')
#     #ubicacion = Ubicacion('OBRA SMB- CURICO', "OBRASMBCURICO")
#
#     #jefe = User('Usuario Jefe Test 2', '1212121212', cargo_jefe, 'email@email.com', 'usuariojefe2', ubicacion, True, None)
#     #usuario = User('Usuario Test 2', '1212121212', cargo_usuario, 'email@email.com', 'usuariotest', ubicacion, True, jefe)
#
#     #b.create_user(usuario)
#     #b.delete_user(usuario)
#     #b.delete_user(jefe)
