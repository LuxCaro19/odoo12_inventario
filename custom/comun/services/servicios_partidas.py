# -*- coding: utf-8 -*-
from itertools import groupby

# import time
import datetime
from odoo.exceptions import UserError
from odoo.tools.api_service import redis_cnx, json

from odoo.tools.jdbc_services import get_bpms_cursor, get_pyjde_cursor \
    , dictfetchall, OracleQuery, HOST as DEFAULT_HOST


class BonitaModelService:
    HOST = DEFAULT_HOST  # HOSTS[DEFAULT]

    def __init__(self):
        # print "Generar EEPP: Conectando BPMS"
        self.cursor = get_bpms_cursor
        # print "Generar EEPP: pyJDE"
        self.pyjde_cursor = get_pyjde_cursor
        # print "Generar EEPP: Conectando Oracle"
        self.ora_cursor = OracleQuery()  # get_cx_cursor()
        # self.ora_cursor = cx_Oracle.connect(self.HOST['jde']['host']).cursor()

        # self.ora_cursor = cx_Oracle.connect('LEGACY/legacy1020@//e1dbs01py.galilea.cl:1521/E1PY')

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

    def get_estado_asignacion(self, asignacion):
        pass
        # sql = """
        #     select
        #       asignacion.pendienteentrega pendiente_entrega,
        #       r.persistenceid id_recepcion,
        #       r.estado estado_recepcion
        #     from asignacion
        #       left join recepcionasignacion r on asignacion.persistenceid = r.asignacion_pid
        #     where asignacion.persistenceid = %s
        # """ % asignacion
        #
        # self.cursor.execute(sql)
        # return self.cursor.fetchone()

    def cambia_estado_partidas(self, codigo_area, codigo_proveedor, estado='EP'):
        pass

        # if estado == "EP":
        #     estado_inicial = 'A'
        # else:
        #     estado_inicial = 'EP'
        #
        # sql = """
        #     update recepcionasignacion set estado = '%s'
        #     where persistenceid in (
        #         select
        #             r.persistenceid
        #         from recepcionasignacion r
        #         join asignacion a on a.persistenceid = r.asignacion_pid
        #         where a.cod_area='%s'  and a.cod_proveedor = %s and r.estado = '%s'
        #     )
        #     """ % (estado, codigo_area, codigo_proveedor, estado_inicial)
        #
        # self.cursor.execute("begin")
        # try:
        #     self.cursor.execute(sql)
        #     self.cursor.execute("commit")
        #     return 1
        # except Exception as e:
        #     self.cursor.execute('rollback')
        #     return 0

    def get_partidas_recibidas(self, codigo_area, codigo_proveedor):
        sql = """select
            a.desc_proveedor,
            cod_presupuesto,
            a.fecha_recepcion,
            a.cod_partida,
            desc_presupuesto,
            desc_partida
            , case when r.estado is null then 'ASIGNADO'
            when r.estado = 'A' then 'RECIBIDO'
            when r.estado = 'P' then 'PAGADO'
            end estado
            ,ppto.cantidad_presupuestado,
            case when ppto.precio_presupuestado = 0 then 1 else ppto.precio_presupuestado end precio_presupuestado
            , sum(a.cantidad_asignada) cantidad_asignada
            , sum(r.cantidad) cantidad_recibida
            , sum(r.cantidad_pagada) cantidad_pagada
            ,0 seq
            , cod_proveedor
            , cod_proyecto
            ,
            '' pdp2, '' sub, desc_actividad, a.cod_actividad,
            string_agg(coalesce(r.observacion, ''), ' ') observacion,
			 ppto.cod_tipo_actividad, ppto.num_actividad
        from asignacion a
        join recepcionasignacion r on a.persistenceid=r.asignacion_pid
        join (select * from dblink('%s', '
             select distinct cod_plantilla_centro_costo              cod_presupuesto,
                              cod_actividad,
                              cod_tipo_actividad,
                              cod_insumo                              cod_partida,
                              case
                                when cod_etapa < cast(900 as text)
                                        then 1
                                else a.cubicacion * da.cubicacion end cantidad_presupuestado,
                              case
                                when cod_etapa < cast(900 as text)
                                        then a.cubicacion * da.cubicacion * da.valor_insumo
                                else da.valor_insumo end              precio_presupuestado,
                              num_actividad
              from actividad a
                     join detalle_actividad da using (cod_actividad)
                     join presupuestos_abiertos
                       on genjob = cod_plantilla_centro_costo
                     join plantilla_centro_costo using (cod_plantilla_centro_costo)
              where activa
                and en_uso')
            vw(cod_presupuesto integer, cod_actividad integer, cod_tipo_actividad integer, cod_partida integer, cantidad_presupuestado numeric, precio_presupuestado numeric, num_actividad integer)
            ) ppto
            using (cod_presupuesto, cod_actividad, cod_partida)
        where a.cod_area='%s' and a.cod_proveedor = %s and r.estado = 'A' and a.estado='Aprobado'
        group by desc_partida, a.cod_actividad, a.cod_partida, a.cod_presupuesto, a.fecha_recepcion
        , cod_proveedor, etapa, cod_proyecto,r.estado, a.cod_proveedor, a.desc_proveedor, desc_partida, desc_actividad
        , a.cantidad_presupuestado, a.precio_presupuestado
        , desc_presupuesto, r.observacion, ppto.cod_tipo_actividad, ppto.cantidad_presupuestado
				, ppto.precio_presupuestado, num_actividad
        order by a.cod_presupuesto asc, a.cod_partida;
        """ % (self.HOST['pyjde'], codigo_area, codigo_proveedor)

        self.cursor.execute(sql)

        return self.cursor.fetchall()

    def get_total_partidas_recibidas(self):
        sql = """select
            a.desc_proveedor,
            cod_presupuesto,
            a.cod_partida,
            a.fecha_recepcion,
            desc_presupuesto,
            desc_partida
            , case when r.estado is null then 'ASIGNADO'
            when r.estado = 'A' then 'RECIBIDO'
            when r.estado = 'P' then 'PAGADO'
            end estado
            ,ppto.cantidad_presupuestado,
            case when ppto.precio_presupuestado = 0 then 1 else ppto.precio_presupuestado end precio_presupuestado
            , sum(a.cantidad_asignada) cantidad_asignada
            , sum(r.cantidad) cantidad_recibida
            , sum(r.cantidad_pagada) cantidad_pagada
            ,0 seq
            , cod_proveedor
            , cod_proyecto
            ,
            '' pdp2, '' sub, desc_actividad, a.cod_actividad,
            string_agg(coalesce(r.observacion, ''), ' ') observacion,
             ppto.cod_tipo_actividad, ppto.num_actividad
        from asignacion a
        join recepcionasignacion r on a.persistenceid=r.asignacion_pid
        join (select * from dblink('%s', '
             select distinct cod_plantilla_centro_costo              cod_presupuesto,
                              cod_actividad,
                              cod_tipo_actividad,
                              cod_insumo                              cod_partida,
                              case
                                when cod_etapa < cast(900 as text)
                                        then 1
                                else a.cubicacion * da.cubicacion end cantidad_presupuestado,
                              case
                                when cod_etapa < cast(900 as text)
                                        then a.cubicacion * da.cubicacion * da.valor_insumo
                                else da.valor_insumo end              precio_presupuestado,
                              num_actividad
              from actividad a
                     join detalle_actividad da using (cod_actividad)
                     join presupuestos_abiertos
                       on genjob = cod_plantilla_centro_costo
                     join plantilla_centro_costo using (cod_plantilla_centro_costo)
              where activa
                and en_uso')
            vw(cod_presupuesto integer, cod_actividad integer, cod_tipo_actividad integer, cod_partida integer, cantidad_presupuestado numeric, precio_presupuestado numeric, num_actividad integer)
            ) ppto
            using (cod_presupuesto, cod_actividad, cod_partida)
        where  r.estado = 'A' and a.estado='Aprobado'
        group by desc_partida, a.cod_actividad, a.cod_partida, a.cod_presupuesto,  a.fecha_recepcion
        , cod_proveedor, etapa, cod_proyecto,r.estado, a.cod_proveedor, a.desc_proveedor, desc_partida, desc_actividad
        , a.cantidad_presupuestado, a.precio_presupuestado
        , desc_presupuesto, r.observacion, ppto.cod_tipo_actividad, ppto.cantidad_presupuestado
                , ppto.precio_presupuestado, num_actividad
        order by a.cod_presupuesto asc, a.cod_partida;
        """ % (self.HOST['pyjde'])

        self.cursor.execute(sql)

        return self.cursor.fetchall()

    def get_lotes_by_contratista_partida(self, codigo_area, codigo_proveedor, codigo_presupuesto, codigo_partida,
                                         codigo_actividad):
        sql = """select
                cod_presupuesto,
                a.cod_partida,
                desc_presupuesto,
                desc_partida
                ,substr(a.cod_lote, length(a.cod_lote)-3,4) as cod_lote
                , case when r.estado is null then 'ASIGNADO'
                when r.estado = 'A' then 'RECIBIDO'
                when r.estado = 'P' then 'PAGADO'
                when r.estado = 'EP' then 'EN PROCESO'
                end estado
                ,ppto.cantidad_presupuestado,
                case when ppto.precio_presupuestado = 0 then 1 else ppto.precio_presupuestado end precio_presupuestado
                , sum(a.cantidad_asignada) cantidad_asignada
                , sum(r.cantidad) cantidad_recibida
                , sum(r.cantidad_pagada) cantidad_pagada,
                0 seq
                , cod_proveedor
                , cod_proyecto
                , a.desc_proveedor,
                '' pdp2, '' sub, desc_partida, desc_actividad, a.cod_actividad,
                a.etapa, a.desc_proyecto,
                r.persistenceid recepcion_id,
                r.insertby recibido_por,
                r.inserttime::date fecha_recepcion,
                a.motivoreasignacion motivo_reasignacion,
                r.proyeccion lote_proyectado
            from asignacion a
            join recepcionasignacion r on a.persistenceid=r.asignacion_pid
            left join (select * from dblink('%s', '
             select distinct cod_plantilla_centro_costo              cod_presupuesto,
                              cod_actividad,
                              cod_tipo_actividad,
                              cod_insumo                              cod_partida,
                              case
                                when cod_etapa < cast(900 as text)
                                        then 1
                                else a.cubicacion * da.cubicacion end cantidad_presupuestado,
                              case
                                when cod_etapa < cast(900 as text)
                                        then a.cubicacion * da.cubicacion * da.valor_insumo
                                else da.valor_insumo end              precio_presupuestado,
                              num_actividad
              from actividad a
                     join detalle_actividad da using (cod_actividad)
                     join presupuestos_abiertos
                       on genjob = cod_plantilla_centro_costo
                     join plantilla_centro_costo using (cod_plantilla_centro_costo)
              where activa
                and en_uso')
            vw(cod_presupuesto integer, cod_actividad integer, cod_tipo_actividad integer, cod_partida integer, cantidad_presupuestado numeric, precio_presupuestado numeric, num_actividad integer)
            ) ppto
            using (cod_presupuesto, cod_actividad, cod_partida)
            where
                a.cod_area='%s'  and a.cod_proveedor = %s
                and cod_presupuesto=%s
                and cod_partida = %s and r.estado = 'A' and a.cod_actividad = %s 
            group by
                desc_partida, a.cod_actividad, substr(a.cod_lote,
                length(a.cod_lote)-3,4), a.cod_partida, cod_presupuesto
                , cod_proveedor, etapa, cod_proyecto,r.estado, a.cod_proveedor,
                a.desc_proveedor, desc_partida, desc_actividad, ppto.cantidad_presupuestado,
                ppto.precio_presupuestado , desc_presupuesto, desc_proyecto, r.persistenceid, r.insertby, r.inserttime, a.motivoreasignacion
            order by desc_presupuesto, desc_partida, substr(a.cod_lote,
            length(a.cod_lote)-3,4);
            """ % (
        self.HOST['pyjde'], codigo_area, codigo_proveedor, codigo_presupuesto, codigo_partida, codigo_actividad)
        self.cursor.execute(sql)
        # print sql
        return self.cursor.fetchall()

    def get_subsidiaria_tipo_actividades(self, codigo_presupuesto):
        sql_actividad = """select
                                distinct cod_plantilla_centro_costo cod_presupuesto, cod_actividad, num_actividad
                                , cod_tipo_actividad, cod_insumo, desc_actividad
                        from actividad
                        join detalle_actividad using (cod_actividad)
                        where cod_plantilla_centro_costo = %s
                        order by cod_actividad
                """ % codigo_presupuesto
        # print sql_actividad
        self.pyjde_cursor.execute(sql_actividad)
        return self.pyjde_cursor.fetchall()

    def get_sobrecargas_by_lote(self, codigo_presupuesto, codigo_proveedor, lote, subsidiaria, tipo_actividad,
                                codigo_partida):

        params = {'genjob': codigo_presupuesto,
                  'an8': codigo_proveedor,
                  'SCHEMA': self.HOST['jde']['schema'],
                  'lote': lote,
                  'subsidiaria': subsidiaria,
                  'tipo_actividad': tipo_actividad,
                  'codigo_partida': codigo_partida}
        # print params

        sql = """
        select swlitm, imdsc1, swmcu,max(
                      case
                      when SWLSWPOSTC = 'C' -- or SWLSWPOSTC = 'A' --and swoorn = ' ' and epan8 is null)
                        then 0
                      when SWLSWPOSTC ='A'
                        then 1
                      when SWLSWPOSTC ='P'
                        then 2 end
                      --  *
                      -- case when DWAN8CR = vaan8 or epan8 = vaan8
                      --   then 1 else -1
                      -- end
                      ) estado,
                      swcrr,
                      swprrc / 10000,
                      swsub,
                      swdsc1,
                      swobj,
                      swhblot,
                      swhbarea,
                      swhbmcus,
                      max(case when swlswpostc ='A' and swoorn = ' ' then swseq  else 0 end) seq,
                      trim(swdesc)||trim(swvr02) ,
                      swgenjob,
                      swpdp2,
                      SWITM,
                      0 comprado,
                      0 facturado
        from
          %(SCHEMA)s.f44h711
          left join %(SCHEMA)s.f56h0711 on dwmcu = swmcu and dwobj = swobj and dwsub = swsub and dwitm = switm and dwseq = swseq
          -- left join %(SCHEMA)s.f560711z on epmcu = swmcu and epobj = swobj and epsub = swsub and epitm = switm and ephblot = swhblot
          join %(SCHEMA)s.f4101 on swlitm = imlitm
          -- join %(SCHEMA)s.f44h604 on vahbarea = swhbarea and vahblot = swurrf and vahbmcus = swhbmcus -- and vaan8 = %(an8)s
        where swgenjob = %(genjob)s
              and swobj = '111903'
              and swsub = '%(subsidiaria)s'
              and swpdp2 = '%(tipo_actividad)s'
              and swhblot = '%(lote)s'
              and switm = '%(codigo_partida)s'  -- numero de item
             /* and (exists
                              (select dwoorn from %(SCHEMA)s.f56h0711 dw
                              where dw.dwlitm = swlitm and dw.DWAN8CR = %(an8)s
                              and dwupmj >= %(SCHEMA)s.TO_JDE_DATE(current_date -600) )
                              or exists (
                                select epoorn from %(SCHEMA)s.f560711z dw
                                where dw.eplitm = swlitm and dw.epAN8 = %(an8)s )) */
        group by swlitm, imdsc1, swmcu,swcrr, swprrc, swsub, swdsc1, swobj, swhblot, swhbarea, swhbmcus,
                trim(swdesc)||trim(swvr02) ,swgenjob, swpdp2, SWITM
        order by swsub, swlitm, swmcu""" % params
        # print sql
        return self.ora_cursor.do_query(sql, get_one=True)

        # self.ora_cursor.execute(sql)
        # result = self.dictfetchall(self.ora_cursor)
        # if result:
        #    return result[0]
        # return []

    def get_obras_contratistas(self):
        sql = """
            select
                distinct (asig.cod_area) codigo,
                asig.desc_area nombre,
                asig.cod_proveedor an8
            from recepcionasignacion recep
                join asignacion asig on recep.asignacion_pid = asig.persistenceid
            where
                recep.inserttime < now()
                and recep.inserttime > now() - interval '1 year'"""

        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def get_datos_contatista(self, contratista_an8):

        params = {
            'SCHEMA': self.HOST['jde']['schema'],
            'an8': contratista_an8
        }
        sql = """
            select
                abalph nombre,
                abtax rut,
                aban8 an8
            from
                %(SCHEMA)s.f0101
            where aban8=%(an8)s
        """ % (params)

        return self.ora_cursor.do_query(sql, get_one=True)
        # self.ora_cursor.execute(sql)
        # result = self.dictfetchall(self.ora_cursor)
        # if result:
        #    return result[0]
        # return []

    def get_oorn_z(self, id_eepp):
        params = {
            'SCHEMA': self.HOST['jde']['schema'],
            'id': id_eepp}
        # print params

        sql = """
            select unique (EPOORN) oorn
            from %(SCHEMA)s.F560711Z
            where EPHBOPID = %(id)s
        """ % params

        # return self.do_oracle_query(sql, get_one=True)
        return self.ora_cursor.do_query(sql, get_one=True)

        # self.ora_cursor.execute(sql)
        # result = self.dictfetchall(self.ora_cursor)
        # if result:
        #    return result[0]
        # return []

    def get_estado_f4311(self, oorn):
        params = {
            'SCHEMA': self.HOST['jde']['schema'],
            'oorn': oorn}
        # print params

        sql = """
            select oorn, estado_1, estado_2, porcentaje from (
                select pdoorn oorn,
                    pdlttr estado_1,
                    pdnxtr estado_2,
                    count(*) peso,
                    round((count(*)* 100 / (
                        select case when count(*)= 0 then 0.1 else count(*) end
                        from %(SCHEMA)s.f4311
                        where pdoorn='%(oorn)s'
                            and 100 not in pdlitm
                            and 16509 not in pdlitm  )), 2 ) as porcentaje
                from %(SCHEMA)s.f4311
                where pdoorn='%(oorn)s'
                    and 100 not in pdlitm
                    and 16509 not in pdlitm
                group by pdoorn, pdnxtr, pdlttr)
            group by oorn, estado_1, estado_2, porcentaje
            having porcentaje > 50 and porcentaje < 101
        """ % params

        return self.ora_cursor.do_query(sql, get_one=True)

        # self.ora_cursor.execute(sql)
        # result = self.dictfetchall(self.ora_cursor)
        # if result:
        #    return result[0]
        # return []

    def get_estado_facturado_pagado(self, params):

        params['SCHEMA'] = self.HOST['jde']['schema']

        sql = """
            select
              round(sum(prpq))                            monto_facturado
            from %(SCHEMA)s.f4311
              join (select
                      sum(pruptd)                            pruptd,
                      sum(prprrc / 10000 * pruptd / 1000000) prpq,
                      prdoco,
                      prdcto,
                      prlnid,
                      prlitm,
                      prmatc
                    from %(SCHEMA)s.f43121
                    where prmatc != '3' and pruptd > 0 and prprrc > 0
                    group by prdoco, prdcto, prlnid, prlitm, prmatc)
                on pddoco = prdoco and pddcto = prdcto and pdlnid = prlnid and pdlitm = prlitm
            where PDOORN = '%(oorn)s'
        """ % params

        return self.ora_cursor.do_query(sql, get_one=True)

    def get_historial_asignaciones(self, codigo_proveedor):
        sql = """
            select
                    a.persistenceid,
                    a.cod_proveedor an8,
                    a.num_lote lote,
                    a.desc_actividad actividad,
                    a.desc_area area,
                    a.desc_partida partida,
                    a.desc_presupuesto presupuesto,
                    a.desc_proyecto proyecto,
                    a.estado estado_asignacion,
                    ra.estado estado_recepcion,
                   case when ra.estado is null then a.estado
                when ra.estado = 'A' then 'Recepcionado'
                when ra.estado = 'EP' then 'Estado de Pago'
                else null end as estado,
                    a.etapa,
                    a.startedby usuario,
                    a.inserttime fecha,
                    a.precio_presupuestado,
                    a.cantidad_presupuestado
                from asignacion a
                left join recepcionasignacion ra on ra.asignacion_pid = a.persistenceid
                where cod_proveedor = %s
                order by persistenceid desc
        """ % (codigo_proveedor)

        self.cursor.execute(sql)

        return self.cursor.fetchall()

    def get_datos_lote(self, params):
        # cx = get_cx_cursor()

        params['SCHEMA'] = self.HOST['jde']['schema']

        sql = """select
                     case when ocsp is not null and omp is not null then round((coalesce(ocsp,0)+ coalesce((ompq/omq),0))/2,2) else round(coalesce(ocsp,0)+ coalesce(omp,0),2) end precio_compra,
                     round(coalesce(ocsq,0)+ coalesce(omq,0),2) cant_compra,
                     round(coalesce(fcsq,0)+ coalesce(omqf,0)  ,2) cant_facturada,
                     round(coalesce(fcsp,0)+ coalesce(ompf,0) ,2) precio_facturado,
                     swseqmax
                from (
                    select
                        swhbmcus ppomcu,
                        swurrf ppurrf,
                        swobj ppobj,
                        swlitm pplitm,
                        max(swseq) swseqmax,
                        case when swobj ='111903' then 'MO' else 'MT' end ppswdsc1,
                        wb.swgenjob ppgenjob,
                        sum(pduorg) / 1000000 ocsq,
                        sum(pduorg / 1000000 * pdprrc / 10000) / (case when sum(pduorg) / 1000000 = 0 then 1 else sum(pduorg) / 1000000 end) ocsp,
                        sum(pruptd/1000000) fcsq,
                        sum(prpq)  / case when sum(pruptd/1000000)=0 then 1 else sum(pruptd/1000000) end  fcsp
                    from %(SCHEMA)s.f44h711 wb
                        left join %(SCHEMA)s.f4311 on pdkcoo = swkcoo and pddcto = swdcto and pddoco = swdoco and pdlnid = swlnid and swlitm=pdlitm and  not (pdlttr = 980 and pdnxtr = 999)
                        left join (
                            select
                                sum(pruptd) pruptd,
                                sum(prprrc/10000*pruptd/1000000) prpq,
                                prdoco,
                                prdcto,
                                prlnid,
                                prlitm,
                                prmatc
                            from %(SCHEMA)s.f43121
                            where prmatc != '3'
                            group by prdoco,
                                prdcto,
                                prlnid,
                                prlitm,
                                prmatc
                            ) on pddoco = prdoco and pddcto = prdcto and pdlnid = prlnid and pdlitm = prlitm

                    where swgenjob = '%(codigo_presupuesto)s'            -- codigo de presupuesto
                        and switm = '%(numero_item)s'             -- numero de item
                        and swpdp2 = '%(tipo_actividad)s'            -- tipo de actividad 1 abierto, 2 cerrado
                        and swobj = '111903'         -- Por defecto
                        and swsub = '%(subsidiaria)s'             -- Por defecto
                        and swhblot = '%(codigo_lote)s'           -- Lote

                    group by swhbarea ,
                        swhbmcus,
                        swpdp2,
                        swurrf,
                        swhbplan,
                        swobj,
                        swlitm,
                        wb.swgenjob,
                        swprrc
                   ) ppto
                left join %(SCHEMA)s.f4311_mig on ppomcu = omhbmcus and ppobj = omobj
                and pplitm = omlitm and omurrf = ppurrf and omgenjob = ppgenjob
                """ % params
        return self.ora_cursor.do_query(sql, get_one=True)
        # self.ora_cursor.execute(sql)
        # return dictfetchall(self.ora_cursor)

    def get_montos_globales(self, params):
        params['SCHEMA'] = self.HOST['jde']['schema']

        sql = """
            select
              swlswpostc swlswpostc,
              case
                when swuorg is NULL 
                    then 0
                else
                    swuorg/1000000
              end as swuorg,
              case
                when dwuorg is NULL 
                    then 0
                else
                    dwuorg/100000
              end as dwuorg,
              case
                when dwprrc is NULL 
                    then 0
                else
                    dwprrc/100000
              end as dwprrc
            from %(SCHEMA)s.f44h711
              left join %(SCHEMA)s.f56h0711
                on dwmcu = swmcu
                   and dwobj = swobj
                   and dwsub = swsub
                   and dwitm = switm
                   and dwseq = swseq
            where SWMCU = '%(mcu)s'
                  and SWOBJ = '%(obj)s'
                  and SWSUB = '%(sub)s'
                  and SWLITM = '%(litm)s'
        """ % params

        response = self.ora_cursor.do_query(sql)
        result = {}
        if response:
            uorg = 0  # f56h0711
            lswogba = 0
            uord = 0  # f44h711
            aexp = 0
            for r in response:
                if r['swlswpostc'] == 'C':
                    uorg += r['dwuorg']
                    if r['dwuorg'] and r['dwprrc']:
                        lswogba += r['dwuorg'] * r['dwprrc']
                if r['swlswpostc'] in ('A', 'P'):
                    uord += r['swuorg']
                    if r['swuorg'] and r['dwprrc']:
                        aexp += r['swuorg'] * r['dwprrc']
            result = {
                'uorg': uorg,
                'lswogba': lswogba,
                'uord': uord,
                'aexp': aexp
            }
        return result

    def get_historia_lote(self, params):
        params['SCHEMA'] = self.HOST['jde']['schema']

        sql_historia = """select
              pdoorn as numero_ep,
              case
                when coalesce(hwtrdj,0) = 0
                    then Null
                else
                    to_date(to_char(hwtrdj+1900000),'YYYYDDD')
                end as fecha_ep,
              swhblot lote,
              imdsc1||imdsc2 insumo,
              abalph proveedor,
              swlitm item,
              1 tipo_id,
              sum(pduorg/1000000) cantidad_comprado,
              coalesce(sum(prurec/1000000),0)  cantidad_facturado,
              coalesce(avg(pdprrc/10000),0)  precio_promedio_comprado,
              coalesce(avg(prprrc/10000),0)  precio_promedio_facturado,
              sum((pduorg/1000000)*(pdprrc/10000))  monto_comprado,
              sum((prurec/1000000)*(prprrc/10000))  monto_facturado,
              max(swprrc/10000.0) precio_presupuesto
            from
              %(SCHEMA)s.f44h711 wf
              join %(SCHEMA)s.f4311
                on pdkcoo = swkcoo
                and pddcto = swdcto
                and pddoco = swdoco
                and pdlnid = swlnid
                and swlitm=pdlitm
                and SWLSWPOSTC!='C'
                and pdlttr!='980'
              join %(SCHEMA)s.f56h0701 on pdoorn = hwoorn
              join %(SCHEMA)s.f4101 on imlitm = swlitm
              left join (
                select
                    sum(pruptd) prurec,
                    avg(prprrc) prprrc,
                    prdoco,
                    prdcto,
                    prlnid,
                    prlitm
                from
                    %(SCHEMA)s.F43121
                group by prdoco,prdcto,prlnid,prlitm)
                on prdoco = pddoco
                and  prdcto = pddcto
                and prlnid = pdlnid
                and prlitm=pdlitm
              left join %(SCHEMA)s.f0101 on pdan8=aban8
              where wf.swgenjob = %(genjob)s
                  and wf.swobj = '111903'
                  and wf.swsub = '%(subsidiaria)s'
                  and wf.swpdp2 = '%(tipo_actividad)s'
                  and switm= '%(codigo_partida)s'
                  and wf.swhblot = '%(lote)s'
              group by swhblot, pdoorn, hwtrdj,
              imdsc1||imdsc2,
              abalph,
              swlitm""" % params
        # print sql_historia
        return self.ora_cursor.do_query(sql_historia)

        # try:
        #    self.ora_cursor.execute(sql_historia)
        #    return dictfetchall(self.ora_cursor)
        # except:
        #    return {}

    def get_historial_productos(self, params):
        params['SCHEMA'] = self.HOST['jde']['schema']

        sql = """select
              pdoorn as numero_ep,
              case
                when coalesce(hwtrdj,0) = 0
                    then Null
                else
                    to_date(to_char(hwtrdj+1900000),'YYYYDDD')
                end as fecha_ep,
              swhblot lote,
              imdsc1||imdsc2 insumo,
              abalph proveedor,
              swlitm item,
              2 tipo_id,
              sum(pduorg/1000000) cantidad_comprado,
              coalesce(sum(prurec/1000000),0)  cantidad_facturado,
              coalesce(avg(pdprrc/10000),0)  precio_promedio_comprado,
              coalesce(avg(prprrc/10000),0)  precio_promedio_facturado,
              sum((pduorg/1000000)*(pdprrc/10000))  monto_comprado,
              sum((prurec/1000000)*(prprrc/10000))  monto_facturado,
              max(swprrc/10000.0) precio_presupuesto
            from
              %(SCHEMA)s.f44h711 wf
              join %(SCHEMA)s.f4311
                on pdkcoo = swkcoo
                and pddcto = swdcto
                and pddoco = swdoco
                and pdlnid = swlnid
                and swlitm=pdlitm
                and SWLSWPOSTC!='C'
                and pdlttr!='980'
              join %(SCHEMA)s.f56h0701 on pdoorn = hwoorn
              join %(SCHEMA)s.f4101 on imlitm = swlitm
              join %(SCHEMA)s.f56h0711 on SWMCU=DWMCU AND SWOBJ=DWOBJ AND SWSUB=DWSUB AND SWOPTION=DWOPTION AND SWAN8 = DWAN8  AND SWITM=DWITM AND SWSEQ = DWSEQ
              JOIN (select imlitm cod_producto from %(SCHEMA)s.f4101 where IMSRP1='PRO') on cod_producto = dwlitm
              left join (
                select
                    sum(pruptd) prurec,
                    avg(prprrc) prprrc,
                    prdoco,
                    prdcto,
                    prlnid,
                    prlitm
                from
                    %(SCHEMA)s.F43121
                group by prdoco,prdcto,prlnid,prlitm)
                on prdoco = pddoco
                and  prdcto = pddcto
                and prlnid = pdlnid
                and prlitm=pdlitm
              left join %(SCHEMA)s.f0101 on pdan8=aban8
              where wf.swgenjob = %(genjob)s
                  and wf.swobj = '111903'
                  and wf.swsub = '%(subsidiaria)s'
                  and wf.swpdp2 = '%(tipo_actividad)s'
                  and switm= '%(codigo_partida)s'
                  and wf.swhblot = '%(lote)s'
              group by swhblot, pdoorn, hwtrdj,
              imdsc1||imdsc2,
              abalph,
              swlitm""" % params
        # print sql
        return self.ora_cursor.do_query(sql)
        # try:
        #    self.ora_cursor.execute(sql)
        #    return dictfetchall(self.ora_cursor)
        # except:
        #    return

    def get_max_seq(self, lote):

        params = {
            'SCHEMA': self.HOST['jde']['schema'],
            'genjob': lote.codigo_presupuesto,
            'lote': lote.codigo_lote,
            'subsidiaria': lote.subsidiaria,
            'tipo_actividad': lote.tipo_actividad,
            'codigo_partida': lote.numero_item,
            'mcu': lote.mcu}

        sql = """select coalesce(max(swseq),0) max_seq from %(SCHEMA)s.f44H711 wf
                  WHERE SWMCU=%(mcu)s
                  and wf.swobj = '111903'
                  and wf.swsub = '%(subsidiaria)s'
                  and switm= '%(codigo_partida)s'
                  AND SWOPTION='        '
                  AND SWAN8=9999
                  and wf.swpdp2 = '%(tipo_actividad)s'
                  and wf.swhblot = '%(lote)s'
                  and SWLSWPOSTC='A'
                  and SWOORN = '        '
                  and SWOCTO = '  '
                  and SWDOCO = 0
                  and SWDCTO = '  '
        """ % params

        return self.ora_cursor.do_query(sql, as_dict=False, get_one=True)
        # cx = get_cx_cursor()
        # cx.execute(sql)
        # return cx.fetchone()
        # return dictfetchall(cx)

    def exporta_estado_de_pago(self, eepp):
        pass
        # print
        # "Exporta EEPP", self.HOST['jde']['host']
        # # db = cx_Oracle.connect(HOST['jde']['host'])
        # # cursor = db.cursor()
        # # cursor.execute("select %s.to_jde_date(sysdate) from dual"%self.HOST['jde']['schema'])
        # connection = self.ora_cursor.get_connection()
        # jde_date = self.ora_cursor.do_query("select %s.to_jde_date(sysdate) from dual" % self.HOST['jde']['schema']
        #                                     , as_dict=False
        #                                     , get_one=True
        #                                     , connection=connection)[0]
        # # self.ora_cursor.do_query("begin end;", no_fetch=True)
        # try:
        #     print
        #     "Begin"
        #     connection.begin()
        #     self.cursor.execute('begin')
        #     an8_contratista = eepp.contratista_id.an8
        #     to_insert = []
        #     for linea in eepp.detalle_estado_pago_ids:
        #         precio = linea.precio * 10000
        #         codigo_presupuesto = linea.codigo_presupuesto
        #         codigo_tipo_actividad = linea.codigo_tipo_actividad
        #         observacion = linea.observacion
        #         if not observacion:
        #             observacion = 'Generado desde ODOO'
        #         for lote in linea.lotes_ids:
        #             if lote.lote_proyectado:
        #                 print
        #                 "Lote proyectado o no habilitado", lote.lote
        #                 lote.lote_habilitado = False
        #                 self.cursor.execute("""update recepcionasignacion
        #                                         set estado='A'
        #                                         where persistenceid = %s""" % lote.recepcion_id)
        #             else:
        #                 print
        #                 "Lote", lote.lote
        #                 user = lote.env.user.usuario_jde
        #                 if not user:
        #                     usuario = "odoo"
        #                 else:
        #                     usuario = user[:10]
        #                 observacion_aprobador = ' '
        #                 if lote.observacion:
        #                     observacion_aprobador = lote.observacion[:80]
        #                 comentario_constructor = ' '
        #                 if lote.comentario_constructor:
        #                     comentario_constructor = comentario_constructor[:30]
        #
        #                 parametros = {
        #                     'SCHEMA': self.HOST['jde']['schema'],
        #                     'epmcu': lote.mcu,
        #                     'epobj': lote.objeto,
        #                     'epsub': lote.subsidiaria,
        #                     'epseq': lote.seq,
        #                     'epitm': lote.numero_item,
        #                     'eplitm': lote.numero_item_largo,
        #                     'ephbarea': lote.codigo_area,
        #                     'ephbmcus': lote.codigo_comunidad,
        #                     'ephblot': lote.codigo_lote,
        #                     # 'epan8': lote.detalle_estado_pago_id.estado_pago_id.contratista_id.an8,
        #                     'epan8': an8_contratista,
        #                     # 'epuorg': lote.cantidad * 1000000,
        #                     'epuorg': int(lote.cantidad * 1000000),
        #                     # 'epprrc': lote.detalle_estado_pago_id.precio * 10000,
        #                     'epprrc': int(precio),
        #                     'epcrtu': usuario,
        #                     'epwrkstnid': 'odoo',
        #                     'comentario_constructor': comentario_constructor,
        #                     # 'epgenjob': lote.detalle_estado_pago_id.codigo_presupuesto,
        #                     # 'eppdp2': lote.detalle_estado_pago_id.codigo_tipo_actividad,
        #                     'epgenjob': codigo_presupuesto,
        #                     'eppdp2': codigo_tipo_actividad,
        #                     'id': eepp.id,
        #                     'epoorn': eepp.numero,
        #                     'jde_date': jde_date,
        #                     'lote_id': lote.id,
        #                     'observacion_aprobacion': observacion_aprobador,
        #                 }
        #                 to_insert.append(parametros)
        #     sqls = []
        #     for key, value in groupby(to_insert, \
        #                               key=lambda x: (x['epmcu'], x['epobj'], x['epsub'], x['epseq'], x['epitm'] \
        #                                                      , x['ephblot'])):
        #         cantidad = 0
        #         for params in value:
        #             cantidad += params['epuorg']
        #
        #         params['epuorg'] = cantidad
        #
        #         sqlz = """
        #                 into %(SCHEMA)s.F560711Z
        #                 (epmcu,
        #                 epobj,
        #                 epsub,
        #                 epseq,
        #                 epitm,
        #                 eplitm,
        #                 ephbarea,
        #                 ephbmcus,
        #                 ephblot,
        #                 epan8,
        #                 epuorg,
        #                 epprrc,
        #                 epcrtu,
        #                 epwrkstnid,
        #                 epgenjob,
        #                 eppdp2,
        #                 epcrtt,
        #                 EPHBOPID,
        #                 epoorn,
        #                 EPUKID,
        #                 EPON1,
        #                 EPEDSP,
        #                 epadesc
        #                 )
        #                 values (
        #                 '%(epmcu)s',
        #                 '%(epobj)s',
        #                 '%(epsub)s',
        #                 %(epseq)s,
        #                 %(epitm)s,
        #                 '%(eplitm)s',
        #                 '%(ephbarea)s',
        #                 '%(ephbmcus)s',
        #                 '%(ephblot)s',
        #                 %(epan8)s,
        #                 %(epuorg)s,
        #                 %(epprrc)s,
        #                 '%(epcrtu)s',
        #                 '%(epwrkstnid)s',
        #                 %(epgenjob)s,
        #                 %(eppdp2)s,
        #                 %(jde_date)s,
        #                 %(id)s,
        #                 %(epoorn)s,
        #                 %(lote_id)s,
        #                 '%(comentario_constructor)s',
        #                 0,
        #                 '%(observacion_aprobacion)s'
        #                 )
        #             """ % params
        #         # print sqlz
        #         sqls.append(sqlz)
        #
        #     self.ora_cursor.do_query('INSERT ALL %s select * from dual' % (' '.join(sqls)), no_fetch=True,
        #                              connection=connection)
        #     # cursor.execute(sqlz)
        #     # print "Insertado"
        #     # self.ora_cursor.do_query(sqlz, no_fetch=True, connection=connection)
        #     # cursor.execute(sqlz)
        #     # print "Insertado"
        #     connection.commit()
        #     self.cursor.execute('commit')
        #
        # except Exception as e:
        #     connection.rollback()
        #     self.cursor.execute('rollback')
        #     return e
        # finally:
        #     self.ora_cursor.do_release(connection)
        # return None
        # # cursor.close()
        # # db.close()
        # # cursor = db = None

    def get_valor_uf(self, fecha):

        params = {'fecha': fecha,
                  'SCHEMA': self.HOST['jde']['schema']}

        sql = """select CXCRR 
            from %(SCHEMA)s.f0015 
            where CXCRCD = 'UF' 
                and CXEFT = %(SCHEMA)s.to_jde_date(TO_DATE('%(fecha)s','DD-MM-YYYY'))""" % params

        # print sql
        return self.ora_cursor.do_query(sql, get_one=True)

        # self.ora_cursor.execute(sql)
        # result = self.dictfetchall(self.ora_cursor)
        # if result:
        #    return result[0]
        # return []

    def get_f560711z(self):

        params = {'SCHEMA': self.HOST['jde']['schema']}

        sql = """
        select *
        from %(SCHEMA)s.f560711z
        where EPOORN is not null and EPOORN != '-1      '
        """ % params

        return self.ora_cursor.do_query(sql)

    def delete_f560711z(self, params, connection):
        pass
        # params['SCHEMA'] = self.HOST['jde']['schema']
        #
        # sql = """
        # delete
        # from %(SCHEMA)s.f560711z
        # where EPMCU = '%(epmcu)s' AND EPOBJ = '%(epobj)s' AND EPSUB = '%(epsub)s' AND EPSEQ = %(epseq)s AND
        #   EPITM = %(epitm)s AND EPHBLOT = '%(ephblot)s'
        #   AND EPOORN = '%(epoorn)s' AND EPHBOPID='%(ephbopid)s'
        # """ % params
        #
        # self.ora_cursor.do_query(sql, no_fetch=True, connection=connection)

    def get_detalle_liberacion(self, params):
        params['SCHEMA'] = self.HOST['jde']['schema']

        sql = """
            select
              NOMBRE_PPTO,
              DESC_TIPO_ACTIVIDAD,
              --   INSUMO,
              INSDSC,
              PRODDSC,
              CANT_PPTO,
              CANT_OC,
              coalesce(CANT_OCP, 0)                                                                   CANT_OCP,
              CANT_OC + coalesce(CANT_OCP, 0)   AS                                                    CANT_OCL,
              coalesce(CANT_FACT, 0)                                                                  CANT_FACT,
              PRECIO_PPTO,
              PRECIO_OC,
              PRECIO_FIJADO,
              coalesce(PRECIO_OCP, 0)                                                                 PRECIO_OCP,
              coalesce(PRECIO_FACT, 0)                                                                PRECIO_FACT,
              MONTO_PPTO,
              MONTO_OC,
              coalesce(MONTO_OCP, 0)                                                                  MONTO_OCP,
              MONTO_OC + coalesce(MONTO_OCP, 0) AS                                                    MONTO_OLC,
              coalesce(MONTO_FACT, 0)                                                                 MONTO_FACT,
              TOTAL_OC,

              --round((MONTO_OC + coalesce(MONTO_OCP,0)) / (CANT_OC + coalesce(CANT_OCP,0)) / PRECIO_PPTO * 100) PRECIO_PORC, -- MOD. FMORALES, CAUSA: PRECIO PPTO EN 0 PROVOCA DIVISION POR 0.
              round(
                  (MONTO_OC + coalesce(MONTO_OCP, 0)) / (CANT_OC + coalesce(CANT_OCP, 0)) / DECODE(PRECIO_PPTO, 0, 1, PRECIO_PPTO) *
                  100)                                                                                PRECIO_PORC,
              -- MOD FMORALES DIV x 0
              ROUND((CANT_OC + coalesce(CANT_OCP, 0)) / DECODE(CANT_PPTO, 0, 1, CANT_PPTO) * 100)     CANT_PORC,
              --round((MONTO_OC + coalesce(MONTO_OCP,0)) / MONTO_PPTO *100) MONTO_PORC, -- MOD. FMORALES, CAUSA: MONTO DE PPTO EN 0 PROVOCA DIVISION POR 0.
              round((MONTO_OC + coalesce(MONTO_OCP, 0)) / DECODE(MONTO_PPTO, 0, 1, MONTO_PPTO) * 100) MONTO_PORC,
              --   COMENTARIO,
              SWGENJOB,
              SWPDP2,
              SWLITM
            from
              --OC_ACTUAL
              (
                select
                  100                            TOTAL_OC,
                  '%(descripcion_actividad)s'    insdsc,
                  prod.imdsc1                    proddsc,
                  round(swprrc / 10000, 1)       precio_ppto,
                  %(cantidad_oc)s                cant_oc,
                  %(precio_oc)s                  precio_oc,
                  %(monto_oc)s                   monto_oc,
                  coalesce(MPUPRC / 10000, 0) as precio_fijado,
                  swgenjob,
                  swpdp2,
                  SWLITM
                from %(SCHEMA)s.f44h711
                  join %(SCHEMA)s.f4101 prod on SWITM = prod.imitm
                  left join %(SCHEMA)s.f44h603 on mphbarea = swhbarea
                                              and mpitm = SWITM
                where swlswpostc != 'C'
                      and SWGENJOB = %(codigo_presupuesto)s
                      and SWPDP2 = %(codigo_tipo_actividad)s
                      and SWITM = %(codigo_partida)s
                      and SWSUB = '%(subsidiaria)s'
                group by case when substr(swsub, 1, 1) = '8'
                  then trim(SWDESC) || trim(SWVR02)
                         else trim(SWDESC) || trim(SWVR02) end,
                  prod.imdsc1,
                  swprrc / 10000,
                  MPUPRC,
                  swgenjob,
                  swpdp2,
                  SWLITM
              ) oc
              left join
              ( select
                 case when substr(swsub, 1, 1) = '8'
                   then trim(SWDESC) || trim(SWVR02)
                 else trim(SWDESC) || trim(SWVR02) end            NOMBRE_PPTO,
                 ta.drdl01                                        DESC_TIPO_ACTIVIDAD,
                 swgenjob,
                 swpdp2,
                 swlitm,
                 round(sum(swuorg / 1000000), 2)                  cant_ppto,
                 round(swprrc / 10000, 1)                         precio_ppto,
                 round(sum(swprrc / 10000 * swuorg / 1000000), 1) monto_ppto
               from %(SCHEMA)s.f44h711
                 join %(SCHEMA)s.f0005 ta on ta.drsy = '41' and ta.drrt = 'P2' and trim(ta.drky) = trim(swpdp2)
               where swlswpostc != 'C'
               --and SWGENJOB=5448 and SWPDP2='12 ' and SWLITM='14512                    '
               group by case when substr(swsub, 1, 1) = '8'
                 then trim(SWDESC) || trim(SWVR02)
                        else trim(SWDESC) || trim(SWVR02) end,
                 ta.drdl01, swgenjob, swpdp2, swlitm,
                 round(swprrc / 10000, 1))
              ppto using (SWGENJOB, SWPDP2, SWLITM, precio_ppto)
              left join
              --OC_PROCESADA
              ( select
                 sum(pduorg / 1000000)                         cant_ocp,
                 round(avg(pdprrc / 10000), 2)                 precio_ocp,
                 round(sum(pduorg / 1000000 * pdprrc / 10000)) monto_ocp,
                 sum(pdaexp)                                   monto_axp_ocp,
                 swgenjob,
                 swpdp2,
                 swlitm
               from %(SCHEMA)s.f44h711
                 join %(SCHEMA)s.f4311
                   on swlitm = pdlitm and pddcto = swdcto and pddoco = swdoco and pdkcoo = swkcoo and pdsfxo = swsfxo and
                      pdlnid = swlnid
               where swlswpostc != 'C' and SWSUB = '%(subsidiaria)s' and not (pdlttr = 980 and pdnxtr = 999)
               group by swgenjob, swpdp2, swlitm
              ) oc_procesada
              using (swgenjob, swpdp2, swlitm)
              left join
              --FACTURA
              ( select
                 round(sum(pruptd / 1000000), 2)             cant_fact,
                 round(sum(prpq) / sum(pruptd / 1000000), 2) precio_fact,
                 round(sum(prpq))                            monto_fact,
                 swgenjob,
                 swpdp2,
                 swlitm
               from %(SCHEMA)s.f44h711 sw
                 join %(SCHEMA)s.f4311 on pdkcoo = swkcoo and pddcto = swdcto and pddoco = swdoco and pdlnid = swlnid and
                                      not (pdlttr = 980 and pdnxtr = 999)
                 --swlitm=pdlitm and pddcto = swdcto and  pddoco = swdoco and pdkcoo = swkcoo and pdsfxo = swsfxo and pdlnid = swlnid
                 join (select
                         sum(pruptd)                            pruptd,
                         sum(prprrc / 10000 * pruptd / 1000000) prpq,
                         prdoco,
                         prdcto,
                         prlnid,
                         prlitm,
                         prmatc
                       from %(SCHEMA)s.f43121
                       where prmatc != '3'
                       group by prdoco, prdcto, prlnid, prlitm, prmatc)
                   on pddoco = prdoco and pddcto = prdcto and pdlnid = prlnid and pdlitm = prlitm
               where
                 swlswpostc != 'C' and not (pdlttr = 980 and pdnxtr = 999)
               group by swgenjob, swpdp2, swlitm) fact using (swgenjob, swpdp2, swlitm)

        """ % params
        # print sql
        return self.ora_cursor.do_query(sql)

    def get_presupuestado_partida(self, params):
        params['SCHEMA'] = self.HOST['jde']['schema']

        sql = """
            select
                 round(sum(swuorg) / 1000000 ,2) cant_ppto,
                 round(swprrc / 10000 ,2) precio_ppto,
                  SWUOM unidad
            from %(SCHEMA)s.f44h711
            where SWGENJOB = %(genjob)s and SWITM = '%(imitm)s'
            group by swprrc, SWUOM
        """ % params

        return self.ora_cursor.do_query(sql)

    def get_proyeccion_lote(self, recepcion_id):
        sql = """
            select proyeccion 
              from recepcionasignacion 
            where persistenceid = %s 
        """ % recepcion_id

        self.cursor.execute(sql)
        if self.cursor.rowcount != 0:
            return self.cursor.fetchone()
        else:
            return []

    def get_num_oc_jde(self):
        pass
        # cnx = self.ora_cursor.get_connection()
        # sql_get_nxt_nmb = """select nnn002 from %s.f0002 where nnsy ='44H'""" % self.HOST['jde']['schema_ctl']
        # cursor = cnx.cursor()
        # try:
        #     cnx.begin()
        #     # cursor.execute('commit')
        #     # cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE NAME 'GETNXTOC'")
        #     # obtengo el nextnumber
        #     cursor.execute(sql_get_nxt_nmb)
        #     oorn = cursor.fetchone()
        #     # self.ora_cursor.do_query("SET TRANSACTION READ WRITE NAME 'GETNXTOC'", no_fetch=True, connection=cnx)
        #     # oorn = self.ora_cursor.do_query(sql, as_dict=False, get_one=True, connection=cnx)
        #     if not oorn:
        #         raise Exception('No fue posible obtener el número de orden del EP correspondiente')
        #     oorn = oorn[0]
        #     # incremento
        #     next_oorn = oorn + 1
        #
        #     # update con next_nmb
        #     sql_update_next_nmb = """update %s.f0002 set nnn002=%s where nnsy ='44H' and nnn002!=%s"""
        #
        #     cursor.execute(sql_update_next_nmb % (self.HOST['jde']['schema_ctl']
        #                                           , next_oorn
        #                                           , next_oorn))
        #
        #     if cursor.rowcount == 0:
        #         # si no actualizo ninguna linea quiere decir que otra transaccion aumento la secuencia.
        #         # en este caso obtenemos nuevamente la secuencia y la aumentamos
        #         # RE LEER EL NXT NMB ANTES DE HACER COMMIT 494438
        #         cursor.execute(sql_get_nxt_nmb)
        #         oorn = cursor.fetchone()
        #         # if not new_oorn:
        #         #    pass
        #         oorn = oorn[0]
        #         # new_oorn = new_oorn[0]
        #         next_oorn = oorn + 1
        #         cursor.execute(sql_update_next_nmb % (self.HOST['jde']['schema_ctl']
        #                                               , next_oorn
        #                                               , next_oorn))
        #
        #     cnx.commit()
        #     # cursor.execute('commit')
        #     cursor.close()
        #     # cnx.commit()
        #     self.ora_cursor.do_release(cnx)
        #     return oorn
        # except Exception as e:
        #     cnx.rollback()
        #     # cursor.execute('rollback')
        #     cursor.close()
        #     self.ora_cursor.do_release(cnx)
        #     raise UserError(e)

    def get_presupuesto_miscelaneo(self, codigo_area):
        params = {
            'codigo_area': codigo_area,
            'SCHEMA': self.HOST['jde']['schema']
        }

        sql = """ select distinct SWMCU, SWOBJ, SWSUB, SWOPTION, SWAN8, SWITM, SWSEQ, SWLITM, swhbarea, SWLSWPOSTC, swdesc, swvr01, swgenjob, swpdp2, swhblot
                 from %(SCHEMA)s.f0006
                 join %(SCHEMA)s.f44h711 on swmcu = mcmcu and switm = 1244921 --and SWLSWPOSTC='A'
                 join sy910.f00950 on FSOBNM='F44H711' and FSDTAI='GENJOB' and FSFRDV = cast(SWGENJOB as NCHAR(30))
                 where mcrp16='999' and mcstyl='MS' and mcco='00004' and swhbarea=%(codigo_area)s
                 order by swlswpostc asc, swseq desc""" % params

        return self.ora_cursor.do_query(sql, get_one=True)


class PyJDEModelService:

    def __init__(self):

        self.cursor = get_pyjde_cursor

    def get_presupuestos_abiertos(self):

        sql = """select distinct
                    pa.genjob codigo, 
                    pa.cod_proyecto codigo_proyecto,
                    pa.desc_proyecto descripcion_proyecto,
                    pa.cod_area codigo_area,
                    pa.desc_area descripcion_area,
                    pc.nom_plantilla_centro_costo nombre,
                    pc.cod_plantilla_padre,
                    pc.num_viviendas, 
                    pc.usuario,
                    case 	
                        when da.cod_insumo_mo is null then 1
                        else 0 end as get_optimizado
                from presupuestos_abiertos pa
                join plantilla_centro_costo pc on pa.genjob = pc.cod_plantilla_centro_costo
                join actividad ac on pc.cod_plantilla_centro_costo = ac.cod_plantilla_centro_costo
                join detalle_actividad da on ac.cod_actividad = da.cod_actividad
        """

        return self.cursor.do_query(sql)
        #return dictfetchall(self.cursor)

    def get_optimizado_by_codigo(self, codigo):

        sql = """
            select distinct
                pa.genjob cod_presupuesto, 
                pa.cod_proyecto,
                pa.desc_proyecto,
                pc.cod_plantilla_centro_costo,
                pc.cod_plantilla_padre,
                pa.cod_area,
                pa.desc_area,
                pc.nom_plantilla_centro_costo,
                pc.fecha_creacion,
                pc.num_viviendas,
                pc.cod_etapa,
                pc.tipo_mcu
            from presupuestos_abiertos pa
            join plantilla_centro_costo pc on pa.genjob = pc.cod_plantilla_centro_costo
            join actividad ac on pc.cod_plantilla_centro_costo = ac.cod_plantilla_centro_costo
            join detalle_actividad da on ac.cod_actividad = da.cod_actividad
            where da.cod_insumo_mo is not null  and pa.genjob = %s
        """ % codigo

        return self.cursor.do_query(sql)
        # return dictfetchall(self.cursor)

    def get_actividad_by_plantilla(self, codigo):

        sql = """
            select distinct
                ac.desc_actividad nombre,
                ac.desc_proyecto proyecto,
                ac.unidad,
                ac.num_actividad numero,
                ac.cubicacion,
                ac.actividad_ref actividad_referencia,
                ac.cod_actividad codigo
            from actividad ac 
            where ac.cod_plantilla_centro_costo = %s
            order by ac.desc_proyecto asc
        """ % codigo

        return self.cursor.do_query(sql)
        # return dictfetchall(self.cursor)

    def get_partida_by_actividad(self, codigo):

        sql = """
            select 
                da.cod_actividad,
                da.cod_tipo_actividad,
                ta.desc_tipo_actividad tipo_actividad,
                da.cod_insumo_mo codigo_mano_obra,
                da.cubicacion,
                da.valor_insumo,
                da.cod_detalle_actividad_rel actividad_relacionada,
                da.cod_detalle_actividad cod_detalle_actividad,
                ins.imdsc1 nombre,
                ins.imuom1 unidad,
                ins.imsrp1,
                ins.imaitm,
                ins.imlitm,
                ins.imitm
            from 
            detalle_actividad da
            join F4101 ins on da.cod_insumo = ins.imitm 
            join tipo_actividad ta on da.cod_tipo_actividad = ta.cod_tipo_actividad
            where da.cod_insumo_mo is null and da.cod_actividad = %s and da.activa and (ta.cuenta_objeto='111903' or ta.cuenta_objeto='9999')
            order by ins.imdsc1 asc
        """ % codigo

        return self.cursor.do_query(sql)
        # return dictfetchall(self.cursor)

    def get_material_by_actividad(self, actividad, partida):

        sql = """
            select 
                da.cod_actividad,
                da.cod_tipo_actividad,
                ta.desc_tipo_actividad tipo_actividad,
                da.cod_insumo_mo cod_insumo_mo,
                da.cubicacion,
                da.valor_insumo,
                da.cod_detalle_actividad_rel actividad_relacionada,
                ins.imdsc1 nombre,
                ins.imuom1 unidad,
                ins.imsrp1,
                ins.imaitm,
                ins.imlitm,
                ins.imitm cod_insumo
            from 
            detalle_actividad da
            join F4101 ins on da.cod_insumo = ins.imitm 
            join tipo_actividad ta on da.cod_tipo_actividad = ta.cod_tipo_actividad
            where da.cod_actividad = %s and cod_insumo_mo = %s and da.cod_insumo_mo is not null and da.activa and ta.cuenta_objeto='111904'
            order by ins.imdsc1 asc;
        """ % (actividad, partida)
        # print sql
        return self.cursor.do_query(sql)
        # return dictfetchall(self.cursor)

    def get_materiales_partidas_by_actividad(self, codigo):

        sql = """select 
                da.cod_actividad,
                da.cod_tipo_actividad,
                ta.desc_tipo_actividad tipo_actividad,
                da.cod_insumo_mo cod_insumo_mo,
                da.cubicacion,
                da.valor_insumo,
                da.cod_detalle_actividad_rel actividad_relacionada,
                ins.imdsc1 nombre,
                ins.imuom1 unidad,
                ins.imsrp1,
                ins.imaitm,
                ins.imlitm,
                ins.imitm cod_insumo
            from 
            detalle_actividad da
            join F4101 ins on da.cod_insumo = ins.imitm 
            join tipo_actividad ta on da.cod_tipo_actividad = ta.cod_tipo_actividad
            join actividad a on a.cod_actividad = da.cod_actividad
            where da.cod_insumo_mo is null and da.activa and ta.cuenta_objeto='111904' and a.cod_actividad = %s
            order by ta.desc_tipo_actividad asc;
        """ % codigo

        return self.cursor.do_query(sql)
        # return dictfetchall(self.cursor)

    def get_presupuesto_no_optimizado_by_codigo(self, codigo):
        sql = """
                select  pcc.cod_plantilla_centro_costo,
                    pcc.nom_plantilla_centro_costo,
                    pcc.cod_plantilla_padre,
                    pcc.num_viviendas,
                    pcc.cod_etapa,
                    pcc.tipo_mcu,
                    pa.inserttime,
                    pa.desc_proyecto,
                    a.unidad unidad_actividad,
                    a.cubicacion cubicacion_actividad,
                    a.actividad_ref actividad_ref,
                    a.num_actividad,
                    a.desc_actividad,

                    det.imdsc1 desc_mo,
                    da.cod_tipo_actividad,
                    a.cod_actividad,
                    ta.desc_tipo_actividad,
                    da.cubicacion cubicacion,
                    da.valor_insumo valor,
                    da.cod_insumo_mo codigo_mano_obra,
                    det.imuom1 unidad,
                    det.imdsc1 desc_mt,
                    det.imlitm,
                    det.imaitm,
                    det.imsrp1,
                    det.imitm,
                    da.cod_detalle_actividad_rel,
                    da.cod_detalle_actividad,
                    da.cod_insumo cod_mo,                  
                    case when ta.cuenta_objeto='111903' then 'MO' else 'MT' end tipo
                from presupuestos_abiertos pa
                join plantilla_centro_costo pcc on pcc.cod_plantilla_centro_costo = pa.genjob
                join actividad a on a.cod_plantilla_centro_costo = pcc.cod_plantilla_centro_costo
                join detalle_actividad da on da.cod_actividad = a.cod_actividad
                join tipo_actividad ta on ta.cod_tipo_actividad = da.cod_tipo_actividad
                join f4101 det on det.imitm = da.cod_insumo
                --join actividad aref on aref.cod_actividad = a.actividad_ref

                where genjob = %s and da.activa
                order by a.desc_actividad, da.cod_insumo
                """ % codigo

        return self.cursor.do_query(sql)
        # return dictfetchall(self.cursor)

    def get_plantilla_by_genjob(self, codigo):
        sql = """
                select
                    nom_plantilla_centro_costo nombre,
                    genjob cod_plantilla,
                    num_viviendas viviendas,
                    inserttime fecha_creacion,
                    cod_etapa,
                    tipo_mcu,
                    desc_proyecto desc_proyecto

                from presupuestos_abiertos pa
                join plantilla_centro_costo pcc on pcc.cod_plantilla_centro_costo = pa.genjob
                where genjob = %s
                """ % codigo

        return self.cursor.do_query(sql)
        # return dictfetchall(self.cursor)

    def get_actividad_by_genjob(self, codigo):
        sql = """--ACTIVIDADES
            select
                a.desc_actividad nombre,
                pa.desc_proyecto proyecto,
                a.unidad,
                a.cubicacion,
                a.num_actividad numero,
                a.actividad_ref actividad_referencia,
                a.cod_actividad codigo

            from presupuestos_abiertos pa
            join plantilla_centro_costo pcc on pcc.cod_plantilla_centro_costo = pa.genjob
            join actividad a on a.cod_plantilla_centro_costo = pcc.cod_plantilla_centro_costo
            where genjob = %s

                """ % codigo

        return self.cursor.do_query(sql)
        # return dictfetchall(self.cursor)

    def get_descripcion_actividad_relacionada(self, actividad_relacionada):
        sql = """
            select DISTINCT a.desc_actividad, mo.imdsc1 partida_relacionada, da.cod_detalle_actividad codigo_partida, a.cod_actividad codigo_actividad
            from detalle_actividad da
              join actividad a on a.cod_actividad = da.cod_actividad
              join f4101 mo on mo.imitm = da.cod_insumo
            where da.cod_detalle_actividad = %s
            """ % actividad_relacionada
        # print sql
        return self.cursor.do_query(sql)
        # return dictfetchall(self.cursor)

    def get_nexval_centro_de_costo(self):
        sql = """select nextval('plantilla_centro_costo_cod_plantilla_centro_costo_seq'::regclass) 
                            from plantilla_centro_costo limit 1 """

        return self.cursor.do_query(sql)
        # return dictfetchall(self.cursor)

    def get_nexval_actividad(self):
        sql = """select nextval('actividad_cod_actividad_seq'::regclass) 
                                    from actividad limit 1 """

        return self.cursor.do_query(sql)
        # return dictfetchall(self.cursor)

    def get_nexval_detalle_actividad(self):
        sql = """select nextval('detalle_actividad_cod_detalle_actividad_seq'::regclass) 
                                    from detalle_actividad limit 1 """

        return self.cursor.do_query(sql)
        # return dictfetchall(self.cursor)

    def insert_plantilla_respaldo(self, plantilla, nextval):
        pass
        # codigo_proyecto = str(plantilla.presupuesto_id.codigo_proyecto).zfill(8).rjust(12, ' ')
        # params = {
        #     'cod_plantilla_centro_costo': nextval,
        #     'nom_plantilla_centro_costo': plantilla.presupuesto_id.nombre,
        #     'num_viviendas': plantilla.viviendas,
        #     'usuario': plantilla.presupuesto_id.usuario,
        #     'fecha_creacion': datetime.datetime.strptime(plantilla.fecha_creacion, "%Y-%m-%d"),
        #     'cod_plantilla_padre': plantilla.cod_plantilla_padre,
        #     'cod_tipo_plantilla_centro_costo': "",
        #     'firma_1': True,
        #     'firma_2': True,
        #     'cod_proyecto': codigo_proyecto,
        #     'cod_etapa': plantilla.cod_etapa,
        #     'tipo_mcu': plantilla.tipo_mcu,
        #     'en_jde': False,
        #     'firma_ppto': True,
        # }
        #
        # sql_crear_plantilla_original = """
        #           insert into plantilla_centro_costo
        #           (cod_plantilla_centro_costo,
        #             nom_plantilla_centro_costo,
        #             num_viviendas,
        #             usuario,
        #             fecha_creacion,
        #             cod_plantilla_padre,
        #             firma_1,
        #             firma_2,
        #             cod_proyecto,
        #             cod_etapa,
        #             tipo_mcu,
        #             en_jde,
        #             firma_ppto)
        #         values (
        #             %(cod_plantilla_centro_costo)s,
        #             concat('%(nom_plantilla_centro_costo)s',' RESPALDO'),
        #             %(num_viviendas)s,
        #             '%(usuario)s',
        #             '%(fecha_creacion)s',
        #             %(cod_plantilla_padre)s,
        #             %(firma_1)s,
        #             %(firma_2)s,
        #             '%(cod_proyecto)s',
        #             '%(cod_etapa)s',
        #             '%(tipo_mcu)s',
        #             %(en_jde)s,
        #             %(firma_ppto)s)""" % params
        # # print sql_crear_plantilla_original
        # sql_actualizar_activiades = """
        #         update  actividad
        #         set     cod_plantilla_centro_costo = %s
        #         where   cod_plantilla_centro_costo = %s
        #     """ % (nextval, plantilla.cod_plantilla)
        #
        # sql_actualizar_donde_es_padre = """
        #         update  plantilla_centro_costo
        #         set     cod_plantilla_padre = %s
        #         where   cod_plantilla_padre = %s
        #     """ % (nextval, plantilla.cod_plantilla)
        #
        # sql_actualizar_lotes = """
        #         update plantilla_cc_lote
        #         set cod_plantilla_centro_costo = %s
        #         where cod_plantilla_centro_costo = %s;
        #     """ % (nextval, plantilla.cod_plantilla)
        #
        # sql_eliminar_plantilla = """
        #                           delete from plantilla_centro_costo
        #                           where cod_plantilla_centro_costo = %s
        #                           """ % (plantilla.cod_plantilla)
        #
        # self.cursor.execute(sql_crear_plantilla_original)
        # self.cursor.execute(sql_actualizar_activiades)
        # self.cursor.execute(sql_actualizar_donde_es_padre)
        # self.cursor.execute(sql_actualizar_lotes)
        # self.cursor.execute(sql_eliminar_plantilla)
        # return 1

    def insertar_plantilla_homologada(self, plantilla, next_val):
        pass
        # codigo_proyecto = str(plantilla.presupuesto_id.codigo_proyecto).zfill(8).rjust(12, ' ')
        # params = {
        #     'cod_plantilla_centro_costo': plantilla.cod_plantilla,
        #     'nom_plantilla_centro_costo': plantilla.presupuesto_id.nombre,
        #     'num_viviendas': plantilla.viviendas,
        #     'usuario': plantilla.presupuesto_id.usuario,
        #     'fecha_creacion': datetime.datetime.strptime(plantilla.fecha_creacion, "%Y-%m-%d"),
        #     'cod_plantilla_padre': plantilla.cod_plantilla_padre,
        #     'cod_tipo_plantilla_centro_costo': "",
        #     'firma_1': True,
        #     'firma_2': True,
        #     'cod_proyecto': codigo_proyecto,
        #     'cod_etapa': plantilla.cod_etapa,
        #     'tipo_mcu': plantilla.tipo_mcu,
        #     'en_jde': False,
        #     'firma_ppto': True,
        #     'cod_plantilla_optimizada': plantilla.presupuesto_id.optimizado_id.cod_plantilla,
        #     'next_val': next_val
        # }
        #
        # sql = """
        #   insert into plantilla_centro_costo
        #   (cod_plantilla_centro_costo,
        #     nom_plantilla_centro_costo,
        #     num_viviendas,
        #     usuario,
        #     fecha_creacion,
        #     cod_plantilla_padre,
        #     firma_1,
        #     firma_2,
        #     cod_proyecto,
        #     cod_etapa,
        #     tipo_mcu,
        #     en_jde,
        #     firma_ppto,
        #     cod_plantilla_optimizada
        #     )
        # values (
        #     %(cod_plantilla_centro_costo)s,
        #     concat('%(nom_plantilla_centro_costo)s',' OPTIMIZADA'),
        #     %(num_viviendas)s,
        #     '%(usuario)s',
        #     '%(fecha_creacion)s',
        #     %(cod_plantilla_padre)s,
        #     %(firma_1)s,
        #     %(firma_2)s,
        #     '%(cod_proyecto)s',
        #     '%(cod_etapa)s',
        #     '%(tipo_mcu)s',
        #     %(en_jde)s,
        #     %(firma_ppto)s,
        #     %(cod_plantilla_optimizada)s
        #     )""" % params
        #
        # sql_insert = """
        # insert into plantilla_cc_lote
        #   select  %(cod_plantilla_centro_costo)s cod_plantilla_centro_costo,
        #           nextval('plantilla_cc_lote_cod_plantilla_cc_lote_seq'::regclass),
        #           cod_lote,
        #           num_lote
        #   from plantilla_cc_lote where cod_plantilla_centro_costo = %(next_val)s""" % params
        #
        # # self.cursor.execute("begin")
        # self.cursor.execute(sql)
        # self.cursor.execute(sql_insert)
        # # self.cursor.execute("commit")

    def insertar_actividades_plantilla_homologada(self, args):
        pass
        # sql_nextval = """select nextval('actividad_cod_actividad_seq'::regclass)
        #                             from actividad limit 1 """
        #
        # self.cursor.execute(sql_nextval)
        # nextval = dictfetchall(self.cursor)[0]['nextval']
        #
        # params = {
        #     'cod_actividad': nextval,
        #     'desc_actividad': args['desc_actividad'],
        #     'desc_proyecto': args['desc_proyecto'],
        #     'actividad_ref': args['actividad_ref'],
        #     'usuario': args['usuario'],
        #     'fecha_creacion': args['fecha_creacion'],
        #     'unidad': args['unidad'],
        #     'num_actividad': args['num_actividad'],
        #     'cod_plantilla_centro_costo': args['cod_plantilla_centro_costo'],
        #     'cubicacion': args['cubicacion'],
        #     'es_padre': 'N',
        #     'en_uso': True,
        #     'modificada': True,
        # }
        #
        # sql = """
        # insert into actividad
        #     (cod_actividad,
        #     desc_actividad,
        #     desc_proyecto,
        #     actividad_ref,
        #     usuario,
        #     fecha_creacion,
        #     unidad,
        #     num_actividad,
        #     cod_plantilla_centro_costo,
        #     cubicacion,
        #     es_padre,
        #     en_uso,
        #     modificada)
        # values (
        #   %(cod_actividad)s,
        #   '%(desc_actividad)s',
        #   '%(desc_proyecto)s',
        #   %(actividad_ref)s,
        #   '%(usuario)s',
        #   '%(fecha_creacion)s',
        #   '%(unidad)s',
        #   %(num_actividad)s,
        #   %(cod_plantilla_centro_costo)s,
        #   %(cubicacion)s,
        #   '%(es_padre)s',
        #   %(en_uso)s,
        #   %(modificada)s
        # ) """ % params
        # # print sql
        # self.cursor.execute(sql)
        # return nextval

    def buscar_actividad_en_pyjde(self, cod_actividad, cod_plantilla):
        sql = """
            select a.cod_actividad
            from actividad a
            where cod_plantilla_centro_costo = %s and cod_actividad = %s
        """ % (cod_plantilla, cod_actividad)
        # print sql
        return self.cursor.do_query(sql)
        # return dictfetchall(self.cursor)

    def insertar_partidas_plantilla_homologada(self, args, cod_actividad):
        pass
        # sql_nextval = """select nextval('detalle_actividad_cod_detalle_actividad_seq'::regclass)
        #                             from detalle_actividad limit 1 """
        #
        # self.cursor.execute(sql_nextval)
        # nextval = dictfetchall(self.cursor)[0]['nextval']
        #
        # params = {
        #     'cod_actividad': cod_actividad,
        #     'cod_tipo_actividad': args['cod_tipo_actividad'],
        #     'semana_inicio': 0,
        #     'modificado': 'N',
        #     'comentario': "",
        #     'cod_detalle_actividad': nextval,
        #     'cubicacion': args['cubicacion'],
        #     'valor_insumo': args['valor_insumo'],
        #     'transitorio': False,
        #     'activa': True,
        #     'precio_fijado': 0,
        #     'cod_insumo': args['cod_insumo'],
        # }
        # sql = """
        # insert into detalle_actividad(
        #   cod_actividad,
        #   cod_tipo_actividad,
        #   semana_inicio,
        #   modificado,
        #   comentario,
        #   cod_detalle_actividad,
        #   cubicacion,
        #   valor_insumo,
        #   transitorio,
        #   activa,
        #   precio_fijado,
        #   cod_insumo)
        # values
        # (
        #   %(cod_actividad)s,
        #   %(cod_tipo_actividad)s,
        #   %(semana_inicio)s,
        #   '%(modificado)s',
        #   '%(comentario)s',
        #   %(cod_detalle_actividad)s,
        #   %(cubicacion)s,
        #   %(valor_insumo)s,
        #   %(transitorio)s,
        #   %(activa)s,
        #   %(precio_fijado)s,
        #   %(cod_insumo)s)""" % params
        # # print sql
        # # self.cursor.execute("begin")
        # self.cursor.execute(sql)
        # # self.cursor.execute("commit")
        # # print sql
        # return nextval

    def insertar_materiales_plantilla_homologada(self, material, cod_partida, cod_actividad):
        pass
        # params = {
        #     'cod_actividad': cod_actividad,
        #     'cod_tipo_actividad': material.cod_tipo_actividad,
        #     'semana_inicio': 0,
        #     'modificado': 'N',
        #     'comentario': "",
        #     'cod_detalle_actividad': "NEXTVAL",
        #     'cubicacion': material.cubicacion,
        #     'valor_insumo': material.valor_insumo,
        #     'transitorio': False,
        #     'activa': True,
        #     'precio_fijado': 0,
        #     'cod_insumo': material.cod_insumo,
        #     'cod_insumo_mo': cod_partida,
        # }
        # sql = """
        # insert into detalle_actividad(
        #   cod_actividad,
        #   cod_tipo_actividad,
        #   semana_inicio,
        #   modificado,
        #   comentario,
        #   cod_detalle_actividad,
        #   cubicacion,
        #   valor_insumo,
        #   transitorio,
        #   activa,
        #   precio_fijado,
        #   cod_insumo,
        #   cod_insumo_mo)
        # values
        # (
        #   %(cod_actividad)s,
        #   %(cod_tipo_actividad)s,
        #   %(semana_inicio)s,
        #   '%(modificado)s',
        #   '%(comentario)s',
        #   nextval('detalle_actividad_cod_detalle_actividad_seq'::regclass),
        #   %(cubicacion)s,
        #   %(valor_insumo)s,
        #   %(transitorio)s,
        #   %(activa)s,
        #   %(precio_fijado)s,
        #   %(cod_insumo)s,
        #   %(cod_insumo_mo)s)
        #   """ % params
        #
        # # print sql
        #
        # # nextval('detalle_actividad_cod_detalle_actividad_seq'::regclass)
        # # self.cursor.execute("begin")
        # self.cursor.execute(sql)
        # # self.cursor.execute("commit")

    def insertar_materiales_punto_de_entrega(self, material, cod_partida, cod_actividad):
        pass
        # params = {
        #     'cod_actividad': cod_actividad,
        #     'cod_tipo_actividad': material.cod_tipo_actividad,
        #     'semana_inicio': 0,
        #     'modificado': 'N',
        #     'comentario': "",
        #     'cod_detalle_actividad': "NEXTVAL",
        #     'cubicacion': material.cubicacion,
        #     'valor_insumo': material.valor_insumo,
        #     'transitorio': False,
        #     'activa': True,
        #     'precio_fijado': 0,
        #     'cod_insumo': material.cod_insumo,
        # }
        # sql = """
        # insert into detalle_actividad(
        #   cod_actividad,
        #   cod_tipo_actividad,
        #   semana_inicio,
        #   modificado,
        #   comentario,
        #   cod_detalle_actividad,
        #   cubicacion,
        #   valor_insumo,
        #   transitorio,
        #   activa,
        #   precio_fijado,
        #   cod_insumo)
        # values
        # (
        #   %(cod_actividad)s,
        #   %(cod_tipo_actividad)s,
        #   %(semana_inicio)s,
        #   '%(modificado)s',
        #   '%(comentario)s',
        #   nextval('detalle_actividad_cod_detalle_actividad_seq'::regclass),
        #   %(cubicacion)s,
        #   %(valor_insumo)s,
        #   %(transitorio)s,
        #   %(activa)s,
        #   %(precio_fijado)s,
        #   %(cod_insumo)s
        #   )
        #   """ % params
        #
        # # print sql
        #
        # # nextval('detalle_actividad_cod_detalle_actividad_seq'::regclass)
        # # self.cursor.execute("begin")
        # self.cursor.execute(sql)
        # # self.cursor.execute("commit")

    def insertar_materiales_entrega_otra_partida(self, material, cod_partida_rel, cod_actividad):
        pass
        # params = {
        #     'cod_actividad': cod_actividad,
        #     'cod_tipo_actividad': material.cod_tipo_actividad,
        #     'semana_inicio': 0,
        #     'modificado': 'N',
        #     'comentario': "",
        #     'cod_detalle_actividad': "NEXTVAL",
        #     'cubicacion': material.cubicacion,
        #     'valor_insumo': material.valor_insumo,
        #     'transitorio': False,
        #     'activa': True,
        #     'precio_fijado': 0,
        #     'cod_insumo': material.cod_insumo,
        #     'cod_detalle_actividad_rel': cod_partida_rel,
        # }
        # sql = """
        # insert into detalle_actividad(
        #   cod_actividad,
        #   cod_tipo_actividad,
        #   semana_inicio,
        #   modificado,
        #   comentario,
        #   cod_detalle_actividad,
        #   cubicacion,
        #   valor_insumo,
        #   transitorio,
        #   activa,
        #   precio_fijado,
        #   cod_insumo,
        #   cod_detalle_actividad_rel)
        # values
        # (
        #   %(cod_actividad)s,
        #   %(cod_tipo_actividad)s,
        #   %(semana_inicio)s,
        #   '%(modificado)s',
        #   '%(comentario)s',
        #   nextval('detalle_actividad_cod_detalle_actividad_seq'::regclass),
        #   %(cubicacion)s,
        #   %(valor_insumo)s,
        #   %(transitorio)s,
        #   %(activa)s,
        #   %(precio_fijado)s,
        #   %(cod_insumo)s,
        #   %(cod_detalle_actividad_rel)s
        #   )
        #   """ % params
        #
        # # print sql
        # self.cursor.execute(sql)

    def set_detalle_actividad_relacionados(self, cod_plantilla_padre, cod_plantilla_hijo):
        pass
        # """esta funcion actualiza todas las lineas de detalle de actividad en la plantilla 'cod_plantilla_hijo'
        # que estan configuradas para ser entregadas en una mano de obra de otra actividad
        # en el padre 'cod_plantilla_padre'.
        # """
        # sql = """
        #   select da_orig.cod_insumo, a_orig.num_actividad, da_orig.cod_insumo_mo
        #         , da_rel.cod_insumo cod_insumo_relacionado
        #         , da_rel.cod_insumo_mo cod_insumo_mo_rel
        #         , a_ref.num_actividad num_actividad_rel
        #     --,a_ref.cod_plantilla_centro_costo
        #     from detalle_actividad  da_orig
        #     join actividad a_orig on da_orig.cod_actividad = a_orig.cod_actividad
        #     join detalle_actividad da_rel on da_orig.cod_detalle_actividad_rel = da_rel.cod_detalle_actividad
        #     join actividad a_ref on da_rel.cod_actividad = a_ref.cod_actividad
        #     where da_orig.cod_detalle_actividad_rel is not null
        #     and a_orig.cod_plantilla_centro_costo = %s
        # """ % cod_plantilla_padre
        #
        # actividades_rel_padre = self.cursor.dictfetchall(sql)
        # self.cursor.execute("begin")
        # for actrel in actividades_rel_padre:
        #     # buscar por insumo y num_actividad el cod_detalle_actividad de la plantilla_recientemente guardada
        #     cod_insumo_mo = 'is null' if actrel['cod_insumo_mo_rel'] is None else '= %s' % actrel['cod_insumo_mo_rel']
        #     sql = """select cod_detalle_actividad from detalle_actividad
        #                 join actividad using (cod_actividad)
        #                 where cod_plantilla_centro_costo =%s and cod_insumo = %s and cod_insumo_mo %s
        #                 and num_actividad =%s
        #                 """ % (cod_plantilla_hijo, actrel['cod_insumo_relacionado']
        #                                          , cod_insumo_mo, actrel['num_actividad_rel'])
        #     self.cursor.execute(sql)
        #     da_to_set = self.cursor.fetchone()
        #     if not da_to_set:
        #         continue
        #     cod_insumo_mo = 'is null' if actrel['cod_insumo_mo'] is None else '= %s' % actrel['cod_insumo_mo']
        #     sql = """select cod_detalle_actividad from detalle_actividad
        #               join actividad using (cod_actividad)
        #                where cod_plantilla_centro_costo =%s and cod_insumo = %s and cod_insumo_mo %s and num_actividad =%s
        #     """ % (cod_plantilla_hijo, actrel['cod_insumo'], cod_insumo_mo, actrel['num_actividad'])
        #     self.cursor.execute(sql)
        #     da_set_to = self.cursor.fetchall()
        #     for da in da_set_to:
        #         da[0]  # cod_detalle_actividad
        #         sql_update = "update detalle_actividad set cod_detalle_actividad_rel = %s where cod_detalle_actividad = %s" \
        #                      % (da_to_set[0], da[0])
        #         self.cursor.execute(sql_update)
        # self.cursor.execute("commit")

    def get_plantillas_punto_entrega(self):
        sql = """
        select distinct
          nom_plantilla_centro_costo,
          cod_plantilla_centro_costo
        from plantilla_centro_costo
        where nom_plantilla_centro_costo like '%OPTIMIZADA%'
              and cod_plantilla_centro_costo not in (select pcc.cod_plantilla_centro_costo
                                                     from plantilla_centro_costo pcc
                                                       join actividad a
                                                         on pcc.cod_plantilla_centro_costo = a.cod_plantilla_centro_costo and
                                                            a.num_actividad = 1000001)"""

        return self.cursor.do_query(sql)
        # return dictfetchall(self.cursor)

    def set_da_punto_de_entrega(self, cod_plantilla, cod_partida):
        pass
        # sql = """
        #     update detalle_actividad
        #       set cod_detalle_actividad_rel = %s
        #     where cod_detalle_actividad in (select cod_detalle_Actividad from detalle_actividad da
        #       join tipo_actividad a on da.cod_tipo_actividad = a.cod_tipo_actividad
        #       join f4101 i on da.cod_insumo = i.imitm
        #     where cod_actividad in (select cod_actividad from actividad where cod_plantilla_centro_costo = %s)
        #           and a.cuenta_objeto='111904'
        #           and cod_insumo_mo is null
        #           and cod_detalle_actividad_rel is null)
        # """ % (cod_partida, cod_plantilla)
        #
        # self.cursor.execute("begin")
        # try:
        #     self.cursor.execute(sql)
        #     self.cursor.execute("commit")
        #     return 1
        # except Exception as e:
        #     return e


cod_etapa, q_presupuesto, q_pagados = range(3)


class ReportService:
    def __init__(self):
        # print "Generar EEPP: Conectando BPMS"
        self.bodega_cursor = get_bpms_cursor
        # print "Generar EEPP: pyJDE"
        self.pyjde_cursor = get_pyjde_cursor
        self.odoo_cursor = None
        self.HOST = DEFAULT_HOST

    def build_reporte(self, cod_contratista, cod_area, odoo_cursor):
        self.odoo_cursor = odoo_cursor
        import time
        import logging
        _logger = logging.getLogger(__name__)

        report = []

        self.pyjde_cursor.execute("begin")
        self.bodega_cursor.execute("begin")
        self.odoo_cursor.execute("begin")
        try:
            start = time.time()

            partidas_asignadas = self.get_partidas_asignadas_contratista(cod_contratista, cod_area)

            end = time.time()
            _logger.debug('self.get_partidas_asignadas_contratista(cod_contratista) %s' % (end - start))

            start_total = time.time()
            lotes_by_pptos = dict()
            for pa in partidas_asignadas:
                result = {
                    'lotes_no_asignados': pa['lotes_no_asignados'],
                    'desc_presupuesto': pa['desc_presupuesto'],
                    'lotes_asignados': pa['lotes_asignados'],
                    'lotes_recibidos': pa['lotes_recibidos'],
                    'lotes_ep': pa['lotes_ep'],
                    'cod_presupuesto': pa['cod_presupuesto'],
                    'lotes_pagados': pa['lotes_pagados'],
                    'desc_actividad': pa['desc_actividad'],
                    'cod_actividad': pa['cod_actividad'],
                    'desc_partida': pa['desc_partida'].strip(),
                    'lotes_con_entrega': pa['lotes_con_entrega'],
                    'cod_partida': pa['cod_partida'],
                    'secuencia': None
                }

                start = time.time()

                lotes_ppto = redis_cnx.get('lotes_by_ppto_%s' % result['cod_presupuesto'])

                if not lotes_ppto:
                    # para obtener una sola vez en contexto de ejecución
                    lotes_ppto = self.get_lotes_presupuestados(result['cod_presupuesto'])
                    # lotes_by_pptos[result['cod_presupuesto']] = lotes_ppto
                    redis_cnx.set('lotes_by_ppto_%s' % result['cod_presupuesto'], json.dumps(lotes_ppto))
                else:
                    lotes_ppto = json.loads(lotes_ppto)

                end = time.time()
                _logger.debug('self.get_lotes_presupuestados(cod_contratista) %s' % (end - start))

                if not lotes_ppto:
                    continue
                start = time.time()

                partida_pagada = self.partida_pagada_completa(result['cod_presupuesto'], result['cod_actividad'],
                                                              result['cod_partida'],
                                                              lotes_ppto)

                end = time.time()
                _logger.debug('self.partida_pagada_completa %s' % (end - start))

                if partida_pagada:
                    continue
                start = time.time()

                info_partida = self.get_orden_partidas(result['cod_presupuesto'], result['cod_actividad'],
                                                       result['cod_partida'])

                end = time.time()
                _logger.debug('self.get_orden_partidas %s' % (end - start))

                if not info_partida:
                    continue

                result['secuencia'] = info_partida[0]
                result['cod_tipo_actividad'] = info_partida[1]

                start = time.time()
                # LOTES PAGADOS
                lotes_pagados = sorted(self.get_lotes_pagados(result['cod_presupuesto'], result['cod_actividad']
                                                              , result['cod_partida'], cod_contratista))

                end = time.time()
                _logger.debug('sorted(self.get_lotes_pagados %s' % (end - start))

                result['lotes_pagados'] = '-'.join(lotes_pagados)

                start = time.time()
                # LOTES EN EP
                lotes_en_ep = sorted(
                    self.get_lotes_en_ep(result['cod_presupuesto'], str(result['cod_tipo_actividad']).ljust(3),
                                         result['cod_partida']
                                         , cod_contratista))

                end = time.time()
                _logger.debug('sorted(self.get_lotes_en_ep %s' % (end - start))
                result['lotes_ep'] = '-'.join(lotes_en_ep)
                # LOTES RECIBIDOS
                start = time.time()

                lotes_recibidos = sorted(self.get_lotes_recibidos(result['cod_presupuesto'], result['cod_actividad']
                                                                  , result['cod_partida'], cod_contratista))

                end = time.time()
                _logger.debug('sorted(self.get_lotes_recibidos %s' % (end - start))

                lotes_pagados_union_ep = set(lotes_pagados).union(lotes_en_ep)

                lotes_recibidos_no_pagados = [lote for lote in lotes_recibidos if lote not in lotes_pagados_union_ep]

                result['lotes_recibidos'] = '-'.join(lotes_recibidos_no_pagados)
                # END LOTES RECIBIDOS
                # LOTES CON AL MENOS UNA ENTREGA
                start = time.time()

                lotes_entrega = sorted(self.get_lotes_con_entrega(result['cod_presupuesto'], result['cod_actividad']
                                                                  , result['cod_partida'], cod_contratista))

                end = time.time()
                _logger.debug('sorted(self.get_lotes_con_entrega %s' % (end - start))

                # SUMA DE LOS PAGADOS + EN EP + RECIBIDOS
                lotes_pag_union_rec = set(lotes_pagados_union_ep).union(lotes_recibidos_no_pagados)

                lotes_entrega_no_rec_no_pag = [lote for lote in lotes_entrega if lote not in lotes_pag_union_rec]

                result['lotes_con_entrega'] = '-'.join(lotes_entrega_no_rec_no_pag)

                start = time.time()
                # LOTES ASIGNADOS
                lotes_asignados = sorted(self.get_lotes_asignados(result['cod_presupuesto'], result['cod_actividad']
                                                                  , result['cod_partida'], cod_contratista))

                end = time.time()
                _logger.debug('sorted(self.get_lotes_asignados %s' % (end - start))

                # SUMA DE LOS PAGADOS + EN EP + RECIBIDOS + ENTREGADOS
                lotes_asig_union_no_rec_no_pag = set(lotes_pag_union_rec).union(lotes_entrega_no_rec_no_pag)

                lotes_asignados_no_rec_ent_pag = [lote for lote in lotes_asignados if
                                                  lote not in lotes_asig_union_no_rec_no_pag]

                result['lotes_asignados'] = '-'.join(lotes_asignados_no_rec_ent_pag)

                # LOTES NO ASIGNADOS
                # SUMA DE LOS PAGADOS + EN EP + RECIBIDOS + ENTREGADOS + ASIGNADOS
                lotes_union_all = set(lotes_asig_union_no_rec_no_pag).union(lotes_asignados_no_rec_ent_pag)

                # lotes_no_asignados =[lote for lote in lotes_ppto if lote not in lotes_union_all]
                # result['lotes_no_asignados'] = '-'.join(lotes_no_asignados)
                # lotes_noa = sorted(self.get_lotes_no_asignados(result['cod_presupuesto'], result['cod_actividad']
                #                                           , result['cod_partida'], lotes_ppto))
                lotes_noa = [lote for lote in lotes_ppto if lote not in lotes_union_all]

                result['lotes_no_asignados'] = '-'.join(sorted(lotes_noa))
                report.append(result)

            end_total = time.time()
            _logger.debug('total %s' % (end_total - start_total))

            self.pyjde_cursor.execute("commit")
            self.bodega_cursor.execute("commit")
            self.odoo_cursor.execute("commit")
        except Exception as e:
            _logger.debug("Exception on build_reporte mapa de partidas %s" % e)
            self.pyjde_cursor.execute("rollback")
            self.bodega_cursor.execute("rollback")
            self.odoo_cursor.execute("rollback")
        finally:
            return report

    def get_lotes_no_asignados(self, cod_presupuesto, cod_actividad, cod_partida, lotes):
        if lotes:
            str_lotes = ','.join("'%s'" % lote.zfill(4) for lote in lotes)
        sql = """select distinct cast(num_lote::integer as text) lotes_no_asignados
                                      from asignacion a 
                                          where cod_presupuesto = %s 
                                          and cod_actividad = %s
                                          and cod_partida = %s
                                          and num_lote not in (%s)
                                          and a.estado in ('Aprobado', 'Retenido')
                                  """ % (cod_presupuesto, cod_actividad, cod_partida, str_lotes)

        self.bodega_cursor.execute(sql)

        return [l[0] for l in self.bodega_cursor.fetchall()]

    def get_lotes_asignados(self, cod_presupuesto, cod_actividad, cod_partida, cod_contratista):
        sql = """select distinct cast(num_lote::integer as text) lotes_con_entrega
                              from asignacion a
                              left join asignacion_kardexentrega ak on a.persistenceid = ak.asignacion_pid
                              left join recepcionasignacion r on a.persistenceid = r.asignacion_pid 
                                  where cod_presupuesto = %s 
                                  and cod_actividad = %s
                                  and cod_partida = %s
                                  and a.cod_proveedor = %s
                                  and ak.asignacion_pid is null and r.asignacion_pid is null 
                                  and a.estado in ('Aprobado', 'Retenido')
                          """ % (cod_presupuesto, cod_actividad, cod_partida, cod_contratista)

        self.bodega_cursor.execute(sql)

        return [l[0] for l in self.bodega_cursor.fetchall()]

    def get_lotes_con_entrega(self, cod_presupuesto, cod_actividad, cod_partida, cod_contratista):
        sql = """select distinct cast(num_lote::integer as text) lotes_con_entrega
                      from asignacion a
                      join asignacion_kardexentrega ak on a.persistenceid = ak.asignacion_pid 
                          where cod_presupuesto = %s 
                          and cod_actividad = %s
                          and cod_partida = %s
                          and a.cod_proveedor = %s  

                  """ % (cod_presupuesto, cod_actividad, cod_partida, cod_contratista)

        self.bodega_cursor.execute(sql)

        return [l[0] for l in self.bodega_cursor.fetchall()]

    def get_lotes_recibidos(self, cod_presupuesto, cod_actividad, cod_partida, cod_contratista):
        sql = """select distinct cast(num_lote::integer as text)
                  from asignacion a
                  join recepcionasignacion ra on a.persistenceid = ra.asignacion_pid 
                  where cod_presupuesto = %s 
                  and cod_actividad = %s
                  and cod_partida = %s
                  and a.cod_proveedor = %s  
                  and ra.estado in ('A', 'EP')
          """ % (cod_presupuesto, cod_actividad, cod_partida, cod_contratista)

        self.bodega_cursor.execute(sql)

        return [l[0] for l in self.bodega_cursor.fetchall()]

    def get_lotes_en_ep(self, cod_presupuesto, cod_tipo_actividad, cod_partida, cod_contratista):
        # sql = """select distinct cast(lote::integer as text) lote
        #                         from dwh.analisis_eepp
        #                       where seq = %s and cod_actividad = %s and itm = %s and cod_proveedor = %s
        #                       and (q_fac is null and q_fac=0) and (q_com is not null and q_com > 0)
        #                       """ % (cod_presupuesto, cod_actividad, cod_partida, cod_contratista)

        # self.pyjde_cursor.execute(sql)

        sql = """
            select distinct cast(lote::integer as text) from produccion_detalle_estado_pago_lote
              join produccion_detalle_estado_pago pdep on produccion_detalle_estado_pago_lote.detalle_estado_pago_id = pdep.id
              join produccion_estado_pago pago on pdep.estado_pago_id = pago.id and pago.state in ('nuevo', 'retenido', 'validado', 'enviado_matriz', 'recibido_matriz')
              join comun_contratista c3 on pago.contratista_id = c3.id and c3.an8 = '%s' 
              where pdep.codigo_presupuesto=%s and pdep.codigo_partida = %s and pdep.codigo_tipo_actividad = '%s'
            """ % (cod_contratista, cod_presupuesto, cod_partida, cod_tipo_actividad)

        self.odoo_cursor.execute(sql)

        return [l[0] for l in self.odoo_cursor.fetchall()]

    def get_lotes_pagados(self, cod_presupuesto, cod_actividad, cod_partida, cod_contratista):
        sql = """select distinct cast(lote::integer as text) lote
                        from dwh.analisis_eepp 
                            join presupuestos_abiertos on genjob=seq
                      where seq = %s and cod_actividad = %s and itm = %s and cod_proveedor = %s
                      and q_fac is not null and q_fac>0
                      """ % (cod_presupuesto, cod_actividad, cod_partida, cod_contratista)

        self.pyjde_cursor.execute(sql)

        return [l[0] for l in self.pyjde_cursor.fetchall()]

    def get_partidas_asignadas_contratista(self, cod_contratista, cod_area=None):
        if cod_area:
            cod_area = " and a.cod_area='%s' " % cod_area
        else:
            cod_area = ""

        sql = """select distinct cod_presupuesto, cod_actividad, cod_partida, desc_presupuesto, desc_actividad
                          , desc_partida, null lotes_pagados, null lotes_ep, null lotes_recibidos, null lotes_con_entrega
                          , null lotes_asignados, null lotes_no_asignados 
                  from asignacion a
                  join (select * from dblink('%s', 'select genjob as cod_presupuesto from presupuestos_abiertos')
                        vw(cod_presupuesto integer)
                        ) ppto_abierto
                        using (cod_presupuesto)

                  where a.cod_proveedor = %s %s
                  --and cod_presupuesto=6179 and cod_partida=1247363 and cod_actividad=158523 
                   and estado ='Aprobado'
                   order by 1,2,3
                 """ % (self.HOST['pyjde'], cod_contratista, cod_area)
        self.bodega_cursor.execute(sql)
        return self.bodega_cursor.fetchall()

    def partida_pagada_completa(self, cod_presupuesto, cod_actividad, cod_partida, lotes_ppto):
        sql = """select trim(etapa), cant_pre, case when etapa < '900' 
                      then count(distinct lote)
                      else sum(q_fac) end q_pagados 
                from dwh.analisis_eepp 
                    join presupuestos_abiertos on genjob=seq
              where seq = %s and cod_actividad = %s and itm = %s
              and q_fac is not null and q_fac>0 and cant_pre>0
              group by etapa, cant_pre
              """ % (cod_presupuesto, cod_actividad, cod_partida)

        self.pyjde_cursor.execute(sql)

        lote_pagado = self.pyjde_cursor.fetchall()

        if lote_pagado:
            if lote_pagado[0][cod_etapa] <= '999':
                return len(lotes_ppto) <= lote_pagado[0][q_pagados]
            else:
                return lote_pagado[0][q_presupuesto] <= len(q_pagados)

    def get_orden_partidas(self, cod_presupuesto, cod_actividad, cod_partida):
        sql = """select num_actividad, cod_tipo_actividad, desc_tipo_actividad from detalle_actividad 
                      join actividad using (cod_actividad) 
                      join tipo_actividad using (cod_tipo_actividad)
                      where cod_plantilla_centro_costo=%s 
                      and cod_actividad=%s
                      and cod_insumo = %s
                      and activa and en_uso""" % (cod_presupuesto, cod_actividad, cod_partida)
        # print sql
        self.pyjde_cursor.execute(sql)

        result = self.pyjde_cursor.fetchall()
        if result:
            return result[0]

    def get_lotes_presupuestados(self, cod_presupuesto):
        sql = """select distinct cast(num_lote::integer as text) num_lote from plantilla_cc_lote 
              join presupuestos_abiertos on cod_plantilla_centro_costo = genjob
              where cod_plantilla_centro_costo=%s order by 1 asc""" % cod_presupuesto

        self.pyjde_cursor.execute(sql)

        return [l[0] for l in self.pyjde_cursor.fetchall()]
        # return self.pyjde_cursor.fetchall()


bms = BonitaModelService()

pyjde = PyJDEModelService()

reportservice = ReportService()

if __name__ == '__main__':
    import psycopg2

    print('test')

    # pyjde_cxn = psycopg2.connect('dbname=odoopy user=odoo password=odoogsa host=192.168.0.142')
    # pyjde_cxn.autocommit = False
    # pyjde_cursor = pyjde_cxn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    #
    # result = reportservice.build_reporte(4591141, 115, pyjde_cursor)
    # print('ok')