# -*- coding: utf-8 -*-
# by fmorales
from odoo.tools.jdbc_services import OracleQuery, HOST


class JDEORM(object):
    pass


class JDETable(JDEORM):
    __tblname__ = None

    def __init__(self, table_name=None):
        if table_name:
            self.__tblname__ = table_name
        else:
            raise ValueError('table_name arg is required!!')

        self.cols_as_string = None
        self.fields = []
        self.index = []
        self.required_values = []
        print ("TABLE %s"%self.__tblname__)
        self.jde = OracleQuery()
        attrs = self.__get_columns__()
        self.__build_attrs__(attrs)
        self.has_attrs = False
#        self.required_values = []


    def __get_columns__(self):
        sql = """select COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE, COLUMN_ID, INDEX_
            from ALL_TAB_COLUMNS
            left join (select ai.OWNER, ai.TABLE_NAME, COLUMN_NAME, COLUMN_POSITION, 'Y' INDEX_ 
                from ALL_INDEXES ai 
                join ALL_IND_COLUMNS ac using (INDEX_NAME) 
                where INDEX_OWNER=upper('%(schema)s')) 
                    using (OWNER, TABLE_NAME, COLUMN_NAME)
            
            where owner=upper ('%(schema)s') and table_name =upper('%(tblname)s') order by column_id
            """ % dict(schema=HOST['jde']['schema'], tblname=self.__tblname__)

        cols = self.jde.do_query(sql)
        return cols

    def get_schema(self):
        return HOST['jde']['schema']
    def __build_attrs__(self, attrs):
        #cols = ()
        #print cols
        self.cols_as_string = ''
        print (attrs)
        for row in attrs:
            if row['data_type'] == 'NUMBER':
                _type = int()
                format = '%(v)s'
            else:
                _type = str()
                format = '\'%(v)s\''
            self.__setattr__(row['column_name'].lower(), _type)
            self.has_attrs = True
            #self.cols_as_string += '%s,' % row['column_name'].upper()

            if row['nullable'] == 'N':
                self.required_values.append(row['column_name'].lower())
            if row['index_'] == 'Y':
                self.index.append(dict(field=row['column_name'].lower(), format=format))
            self.fields.append(dict(field=row['column_name'].lower(), format=format))

        #self.cols_as_string = self.cols_as_string[:len(self.cols_as_string)-1]
    def __validate_values__(self):
        for rv in self.required_values:
            value = self.__getattribute__(rv)
            if value in ('', 0):
                raise ValueError('%s es obligatorio' % value)
        for idx in self.index:
            value = self.__getattribute__(idx['field'])
            if value in ('', 0):
                raise ValueError('el campo %s es indice por tanto obligatorio : valor pasado %s' % (idx['field'], idx['field']))

    def sql_insert(self, with_insert=True):
        self.__validate_values__()
        #if
        attrs = []
        for f in self.fields:
            attrs.append((f['field'], f['format'], self.__getattribute__(f['field'])))
        insert = ''
        if with_insert:
            insert = 'INSERT'
        sql = '%s INTO %s.%s (%s) VALUES (%s)' % (
            insert,
            HOST['jde']['schema'],
            self.__tblname__,
            ','.join([attr[0] for attr in attrs]),
            ','.join([attr[1] % dict(v=attr[2]) for attr in attrs])
        )
        return sql

    def sql_update(self):
        for_update = []
        where = []
        self.__validate_values__()
       # for f in self.fields:

            #attrs.append((f['field'], f['format'], self.__getattribute__(f['field'])))

if __name__ == '__main__':
    f = JDETable('F0101')
    f.aban8 = 234823
    f.abab3 = 1
    f.abalph = 'weon 1'
    f.aban8 = 2

    sql = f.sql_insert()
    sql_upate = f.sql_update()
    print (sql)
