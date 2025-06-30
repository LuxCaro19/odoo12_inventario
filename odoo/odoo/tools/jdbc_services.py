#by fmorales

import psycopg2, psycopg2.extras
import psycopg2_pool
import cx_Oracle
import sys
import mysql.connector
#from comun.models.servicios import OracleQuery
import time

HOSTS = {
    'PY':
        {
            'bonita': 'dbname=business_data user=bonita password=bpm host=192.168.0.173',
            'pyjde': 'dbname=gsa_jde user=odoo_user password=odoo_pass host=192.168.0.173',
#TODO: MODIFICAR JDE EN APPSDEV DESPUES DEL PROCESO DE PRUEBAS -> ESTO ES JDE PD
             #'jde': {'schema': 'proddta', 'host': 'LEGACY/legacy1020@//e1dbs01.galilea.cl:1521/E1PD.GALILEA.CL',
             #        'schema_ctl': 'prodctl',
             #        'user': 'LEGACY',
             #        'pass': 'legacy1020',
             #        'db': 'e1dbs01.galilea.cl:1521/E1PD.GALILEA.CL'},

            'jde': {'schema': 'crpdta', 'host': 'LEGACY/legacy1020@//e1dbs01py.galilea.cl:1521/E1PY.GALILEA.CL',
                    'schema_ctl': 'crpctl',
                    'user': 'LEGACY',
                    'pass': 'legacy1020',
                    'db': 'e1dbs01py.galilea.cl:1521/E1PY.GALILEA.CL'},
            'wordpress': {'user': 'etl', 'password': 'etl1020', 'host': '192.168.0.34',
                          'database': 'wordpress', 'port': '3306',
                          'raise_on_warnings': True}
        },
    'PD':
        {
            'bonita': 'dbname=business_data user=bonita password=bpm host=192.168.0.11',
            'pyjde': 'dbname=gsa_jde user=odoo_user password=odoo_pass host=192.168.0.11',
            'jde': {'schema': 'proddta', 'host': 'LEGACY/legacy1020@//e1dbs01.galilea.cl:1521/E1PD.GALILEA.CL',
                    'schema_ctl': 'prodctl',
                    'user': 'LEGACY',
                    'pass': 'legacy1020',
                    'db': 'e1dbs01.galilea.cl:1521/E1PD.GALILEA.CL'},
            'jde_sys': {'schema': 'proddta', 'host': 'LEGACY/legacy1020@//e1dbs01.galilea.cl:1521/E1PD.GALILEA.CL',
                    'schema_ctl': 'prodctl',
                    'user': 'LEGACY',
                    'pass': 'legacy1020',
                    'db': 'e1dbs01.galilea.cl:1521/E1PD.GALILEA.CL'},
            'wordpress': {'user': 'etl', 'password': 'etl1020', 'host': '192.168.0.34',
                          'database': 'wordpress', 'port': '3306',
                          'raise_on_warnings': True}
        }
}
DEFAULT = 'PY'

HOST = HOSTS[DEFAULT]

class PgConn:
    def __init__(self, db='bonita'):
        self.db = db
        conn_data = HOST.get(self.db, None)
        if not conn_data:
            raise NotImplementedError('La conexion a %s no esta definida'%db)

        self.pool = psycopg2_pool.ThreadSafeConnectionPool(minconn=1, maxconn=30, dsn=conn_data)
        if self.pool:
            print ("Connection to %s pool created successfully" % db)

    def __build_dict(self, cursor, row):
        res = {}
        for i in range(len(cursor.description)):
            res[cursor.description[i][0].lower()] = row[i]
        return res

    def dictfetchall(self, cursor):
        res = []
        rows = cursor.fetchall()
        for row in rows:
            res.append(self.__build_dict(cursor, row))
        return res

    def get_connection(self):
        return self.pool.getconn()

    def do_release(self, connection):
        self.pool.putconn(connection)  # self.do_release(connection)

    def do_query(self, query, as_dict=True, get_one=False, no_fetch=False, connection=None):
        do_release = True
        # calculo de tiempo interno
        if not connection:
            # ini = time.time()
            connection = self.get_connection()
            if not connection:
                raise Exception('No se logro obtener una conexion a la bd: %s' % self.db)
        # print "Tiempo de GET CONNECTION %10.6f" % (time.time() - ini)
        else:
            do_release = False
        try:
            # ini = time.time()
            cursor = connection.cursor()
            # print "Tiempo de GET CURSOR (try) %10.6f" % (time.time() - ini)
            # ini = time.time()
            cursor.execute(query)
            # print "Tiempo de EXECUTE (try) %10.6f" % (time.time() - ini)
        except:
            # try to get a new connection
            # ini = time.time()
            connection = self.get_connection()
            # print "Tiempo de GET CONNECTION (except) %10.6f" % (time.time() - ini)
            # ini = time.time()
            cursor = connection.cursor()
            # print "Tiempo de GET CURSOR (except) %10.6f" % (time.time() - ini)
            ## ini = time.time()
            cursor.execute(query)
            # print "Tiempo de EXECUTE (except) %10.6f" % (time.time() - ini)
        result = None
        # ini = time.time()
        if not no_fetch:
            if as_dict:
                result = self.dictfetchall(cursor)
            else:
                result = cursor.fetchall()
        # print "Tiempo de DICTFETCHALL %10.6f" % (time.time() - ini)
        # ini = time.time()
        cursor.close()
        if result:
            if get_one:
                return result[0]
        if do_release:
            self.do_release(connection)
        # print "Tiempo de EN SOLTAR LA CONECCION %10.6f" % (time.time() - ini)
        return result

    def execute(self, query):
        self.do_query(query, no_fetch=True)


get_bpms_cursor = PgConn('bonita')
get_pyjde_cursor = PgConn('pyjde')

#oracle pool
oracle_db_pool = cx_Oracle.SessionPool(HOST['jde']['user'], HOST['jde']['pass'], HOST['jde']['db'], 4, 50, 1
                                       , threaded=True, encoding='UTF-8')

def tiempo(f):
    def inner(*args, **kwargs):
        ini = time.time()
        ret = f(*args, **kwargs)
        print ("Tiempo de %s %s args=%s" % (f.__name__,time.time()-ini, args.__str__()))
        return ret
    return inner

def get_cx_cursor():
    try:
        sys.oracle_cursor.execute("select 1 from dual")
        return sys.oracle_cursor
    except:
        sys.oracle_cursor = cx_Oracle.connect(HOST['jde']['host']).cursor()
        return sys.oracle_cursor


def get_mysql_cursor():
    try:
        sys.mysql_cursor.execute("select 1")
        return sys.mysql_cursor
    except:
        sys.mysql_cursor = mysql.connector.connect(**HOST['wordpress'])
        sys.mysql_cursor.connect()
        print ("Conectando a : %s (%s)" % (DEFAULT, HOST['wordpress']))
        return sys.mysql_cursor.cursor()


def __build_dict(cursor, row):
    res = {}
    for i in range(len(cursor.description)):
        res[cursor.description[i][0].lower()] = row[i]
    return res


def dictfetchall(cursor):
    res = []
    rows = cursor.fetchall()
    for row in rows:
        res.append(__build_dict(cursor, row))
    return res


class OracleQuery:

    def __init__(self):
        self.pool = oracle_db_pool
        #self.connection = self.pool.acquire()

    def __build_dict(self, cursor, row):
        res = {}
        for i in range(len(cursor.description)):
            res[cursor.description[i][0].lower()] = row[i]
        return res

    def dictfetchall(self, cursor):
        res = []
        rows = cursor.fetchall()
        for row in rows:
            res.append(self.__build_dict(cursor, row))
        return res
    #@tiempo
    def do_query(self, query, as_dict=True, get_one=False, no_fetch=False, connection=None):
        do_release = True
        #calculo de tiempo interno
        if not connection:
            #ini = time.time()
            connection = self.get_connection()
           # print "Tiempo de GET CONNECTION %10.6f" % (time.time() - ini)
        else:
            do_release = False
        try:
            #ini = time.time()
            ora_cursor = connection.cursor()
            #print "Tiempo de GET CURSOR (try) %10.6f" % (time.time() - ini)
            #ini = time.time()
            ora_cursor.execute(query)
            #print "Tiempo de EXECUTE (try) %10.6f" % (time.time() - ini)
        except:
            #try to get a new connection
            #ini = time.time()
            connection = self.get_connection()
            #print "Tiempo de GET CONNECTION (except) %10.6f" % (time.time() - ini)
            #ini = time.time()
            ora_cursor = connection.cursor()
            #print "Tiempo de GET CURSOR (except) %10.6f" % (time.time() - ini)
           ## ini = time.time()
            ora_cursor.execute(query)
            #print "Tiempo de EXECUTE (except) %10.6f" % (time.time() - ini)
        result = None
        #ini = time.time()
        if not no_fetch:
            if as_dict:
                result = self.dictfetchall(ora_cursor)
            else:
                result = ora_cursor.fetchall()
        #print "Tiempo de DICTFETCHALL %10.6f" % (time.time() - ini)
        #ini = time.time()
        ora_cursor.close()
        if result:
            if get_one:
                return result[0]
        if do_release:
            self.do_release(connection)
        #print "Tiempo de EN SOLTAR LA CONECCION %10.6f" % (time.time() - ini)
        return result

    def get_connection(self):
        return self.pool.acquire()

    def do_release(self, conn):
        self.pool.release(conn)


'''
query = OracleQuery()
query.do_query(sql)

'''

if __name__ == '__main__':

    cur = get_bpms_cursor
    for i in range(10):
        #cur = get_bpms_cursor()
        result = cur.do_query('''SELECT saldo
                FROM vwinventario
                WHERE cod_area = '115'
                AND cod_producto = 1205411;''')
        #print result

    cnx = get_bpms_cursor.get_connection()
    cur = get_bpms_cursor
    for i in range(10):
        #cur = get_bpms_cursor()
        result = cur.do_query('''SELECT saldo
                FROM vwinventario
                WHERE cod_area = '115'
                AND cod_producto = 1205411;''', connection=cnx)
        #print result
        #cur.close()

