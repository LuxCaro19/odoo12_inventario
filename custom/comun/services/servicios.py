from odoo.tools.jdbc_services import OracleQuery, HOST as DEFAULT_HOST
from odoo.tools.jde_orm_service import JDETable
from odoo.exceptions import UserError
from datetime import datetime, date
import random


class JDEService:

    HOST = DEFAULT_HOST

    def __init__(self):
        print ("Clientes: Conectando Oracle")
        self.ora_cursor = OracleQuery()


    def get_fecha_rm_real_mesa_venta(self, codigo_proyecto, lote, cnx=None):
        parametros = {
            'SCHEMA': self.HOST['jde']['schema'],
            'codigo_proyecto': codigo_proyecto,
            'lote': lote,
        }
        sql = """
        SELECT
          %(SCHEMA)s.TO_DATE_FROM_JDE(SMUSD2) fecha_rm_real
        FROM %(SCHEMA)s.F44h501
        WHERE SMHBMCUS = '    %(codigo_proyecto)s'
              AND SMHBLOT = %(lote)s
              AND SMACTVSEQ='1'
        """ % parametros
        if cnx:
            result = self.ora_cursor.do_query(sql, connection=cnx)
        else:
            result = self.ora_cursor.do_query(sql)
        if result:
            return result[0]
        return None

    def get_fecha_rm_real_maestro_lote(self, codigo_proyecto, lote):
        params = {'schema': self.HOST['jde']['schema'],
                  'lote':lote,
                  'proyecto':codigo_proyecto,}
        sql = """ select %(schema)s.to_date_from_jde(lmusd1) fecha_rm_real from %(schema)s.f44h201 
                    where 
                    lmhbmcus='    %(proyecto)s'
                    and lmhblot='%(lote)s'""" % params

        result = self.ora_cursor.do_query(sql)
        if result:
            return result[0]
        return None

    def get_fecha_rm_real(self, codigo_proyecto, lote, cnx=None):
        fecha_mesa = self.get_fecha_rm_real_mesa_venta(codigo_proyecto=codigo_proyecto, lote=lote, cnx=cnx)
        fecha_jde = self.valida_fecha_jde(fecha_jde=fecha_mesa)

        if not fecha_jde:
            fecha_maestro = self.get_fecha_rm_real_maestro_lote(codigo_proyecto=codigo_proyecto, lote=lote)
            fecha_jde = self.valida_fecha_jde(fecha_jde=fecha_maestro)
        return fecha_jde
        

    def valida_fecha_jde(self, fecha_jde):
        if fecha_jde is not None and fecha_jde['fecha_rm_real'] is not None:
                fecha_jde = fecha_jde['fecha_rm_real']
                if fecha_jde.date() != date(1980, 1, 1):
                    return fecha_jde.date()
        return None
                    






    # def set_fecha_rm(self, codigo_proyecto, lote, campo, fecha, cnx=None, elimina_fecha=False):
    #     if not fecha:
    #         fecha = None
    #
    #     parametros = {
    #         'schema': self.HOST['jde']['schema'],
    #         'codigo_proyecto': codigo_proyecto,
    #         'lote': lote,
    #         'campo': campo,
    #         'fecha': fecha,
    #     }
    #     if not elimina_fecha:
    #         # curso normal de los eventos, por defecto siempre seguira por aca
    #         sql = """
    #             update %(schema)s.f44h501
    #                 set
    #                   %(campo)s = %(schema)s.to_jde_date(to_date('%(fecha)s', 'YYYY-MM-DD'))
    #             where smhbmcus='%(codigo_proyecto)s'
    #               and smhblot='%(lote)s'
    #               and SMACTVSEQ='1'
    #             """ % parametros
    #     else:
    #         sql = """
    #             update %(schema)s.f44h501
    #                 set
    #                   %(campo)s = 0
    #             where smhbmcus='%(codigo_proyecto)s'
    #               and smhblot='%(lote)s'
    #               and SMACTVSEQ='1'
    #             """ % parametros
    #
    #     if not cnx:
    #         try:
    #             connection = self.ora_cursor.get_connection()
    #             self.ora_cursor.do_query(sql, no_fetch=True, connection=connection)
    #             connection.commit()
    #         except Exception as e:
    #             connection.rollback()
    #             return e
    #         finally:
    #             self.ora_cursor.do_release(connection)
    #     else:
    #         connection = cnx
    #         self.ora_cursor.do_query(sql, no_fetch=True, connection=connection)

    def get_nextnumber_an8(self):
        pass

        # cnx = self.ora_cursor.get_connection()
        # sql_get_nxt_nmb = """select nnn001 from %s.f0002 where nnsy ='01'""" % self.HOST['jde']['schema_ctl']
        # cursor = cnx.cursor()
        # try:
        #     cnx.begin()
        #     cursor.execute(sql_get_nxt_nmb)
        #     next_number = cursor.fetchone()
        #     if not next_number:
        #         raise UserError('No fue posible obtener el an8 correspondiente')
        #     next_number = next_number[0]
        #     # incremento
        #     next_an8 = next_number + 1
        #
        #     # update con next_nmb
        #     sql_update_next_nmb = """update %s.f0002 set nnn001 = %s where nnsy ='01' and nnn001 = %s"""
        #
        #     cursor.execute(sql_update_next_nmb % (self.HOST['jde']['schema_ctl']
        #                                           , next_an8
        #                                           , next_number))
        #
        #     cnx.commit()
        #     cursor.close()
        #     self.ora_cursor.do_release(cnx)
        #     return ((next_number - 80000000)*10) + random.randint(1,10)
        # except Exception as e:
        #     cnx.rollback()
        #     cursor.close()
        #     self.ora_cursor.do_release(cnx)
        #     raise UserError("Error, favor contactese con personal de sistemas a sistemas@galilea.cl\n %s" % e)

    def guardar_cliente(self, data):
        pass

        # if not data['estado_civil']:
        #     data['estado_civil'] = ''
        # if not data['numero_hijos']:
        #     data['numero_hijos'] = ''
        # if not data['ocupacion']:
        #     data['ocupacion'] = ''
        #
        # # TABLA DE LIBRO DE DIRECCIONES
        # cliente = JDETable('F0101')
        #
        # cliente.aban8 = data['an8']
        # cliente.abalky = ' '
        # cliente.abac02 = ' '
        # cliente.abac03 = ' '
        # cliente.abac04 = ' '
        # cliente.abtx2 = ' '
        # cliente.abtax = data['vat']
        # cliente.abalph = data['name']
        # cliente.abdc = data['nombre_sin_espacios']
        # cliente.abmcu = 1
        # cliente.absic = '0200'
        # cliente.abat1 = 'C'
        # cliente.abat3 = 'N'
        # cliente.abat4 = 'N'
        # cliente.abat5 = 'N'
        # cliente.abatp = 'N'
        # cliente.abatr = 'N'
        # cliente.abatpr = 'N'
        # cliente.abate = 'N'
        # cliente.aban81 = data['an8']
        # cliente.aban82 = data['an8']
        # cliente.aban83 = data['an8']
        # cliente.aban84 = data['an8']
        # cliente.aban85 = data['an8']
        # cliente.aban86 = data['an8']
        # cliente.abac01 = '004'
        # cliente.abac23 = data['estado_civil']
        # if data['numero_hijos'] != '0':
        #     cliente.abac24 = data['numero_hijos']
        # cliente.abac25 = data['ocupacion']
        # cliente.abuser = 'ODOO'
        #
        # # TABLA WHO'S WHO
        # f0111 = JDETable('F0111')
        #
        # f0111.wwan8 = data['an8']
        # f0111.wwmlnm = data['name']
        # f0111.wwmalph = data['name']
        # f0111.wwdc = data['nombre_sin_espacios']
        # f0111.wwidln = '0'
        # f0111.wwuser = 'ODOO'
        #
        # # TABLA DE TELEFONO
        # telefono = JDETable('F0115')
        #
        # telefono.wpan8 = data['an8']
        # telefono.wpidln = '0'
        # telefono.wpcnln = '0'
        # telefono.wprck7 = 1
        # telefono.wpph1 = data['phone']
        # telefono.WPuser = 'ODOO'
        #
        # # TABLA DE EMAIL
        # email = JDETable('F01151')
        #
        # email.eaan8 = data['an8']
        # email.eaidln = '0'
        # email.earck7 = 1
        # email.eaetp = 'E'
        # email.eaemail = data['email']
        # email.eauser = 'ODOO'
        #
        # # TABLA DE DIRECCIONES
        # direccion = JDETable('F0116')
        #
        # direccion.alan8 = data['an8']
        # direccion.aleftb = '0'
        # direccion.aladd1 = data['street']
        # direccion.alcty1 = data['city']
        # direccion.alcoun = data['city']
        # #region
        # region = {
        #     'I': '1  ',
        #     'II': '2  ',
        #     'III': '3  ',
        #     'IV': '4  ',
        #     'V': '5  ',
        #     'VI': '6  ',
        #     'VII': '7  ',
        #     'VIII': '8  ',
        #     'IX': '9  ',
        #     'X': '10 ',
        #     'XI': '11 ',
        #     'XII': '12 ',
        #     'XIII': '13 ',
        #     'XIV': '14 ',
        #     'XV': '15 ',
        #     'XVI': '16 ',
        # }
        # region_cliente = region[data['region']]
        # direccion.aladds = region_cliente
        # direccion.alctr = 'CL'
        # direccion.aluser = 'ODOO'
        #
        # # CREACION DE SQLS
        # sql_f0101 = cliente.sql_insert()
        # sql_f0111 = f0111.sql_insert()
        # sql_f0115 = telefono.sql_insert()
        # sql_f01151 = email.sql_insert()
        #
        # connection = self.ora_cursor.get_connection()
        #
        # mensaje = ''
        # try:
        #     connection.begin()
        #     mensaje = 'Ocurrió un error ejecutando creación del Cliente:'
        #     self.ora_cursor.do_query(sql_f0101, no_fetch=True, connection=connection)
        #     mensaje = 'Ocurrió un error ejecutando creación de Whos Who:'
        #     self.ora_cursor.do_query(sql_f0111, no_fetch=True, connection=connection)
        #     mensaje = 'Ocurrió un error ejecutando creación de Teléfono:'
        #     self.ora_cursor.do_query(sql_f0115, no_fetch=True, connection=connection)
        #     mensaje = 'Ocurrió un error ejecutando creación de Email:'
        #     self.ora_cursor.do_query(sql_f01151, no_fetch=True, connection=connection)
        #     connection.commit()
        #     self.ora_cursor.do_release(connection)
        #     return [1, '']
        # except Exception as e:
        #     connection.rollback()
        #     self.ora_cursor.do_release(connection)
        #     return [e, mensaje]


jde = JDEService()

