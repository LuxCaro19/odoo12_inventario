# -*- coding: utf-8 -*-
{
    'name': "comun",

    'summary': """
        Base sistemas Galilea S.A.""",

    'description': """
        Sistema base para desarrollos en sistemas.  
    """,

    'author': "Galilea S.A.",
    'website': "http://www.galilea.cl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Galilea S.A.',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',  'mail', 'web'],

    # always loaded
    'data': [
        
        #'security/ir.rule.csv',
        'security/ir.model.access.csv',
        #'data/ir.cron.csv',
        #'data/l10n_cl_counties_data.xml',
        #'data/comun.tipo_documento.csv',
        #'data/comun.sucursal.csv',
        #'data/comun.empresa.csv',
        #'data/comun.parametro.csv',
        #'views/contratista.xml',
        #'views/obra.xml',
        #'views/especialidad.xml',
        'views/parametro.xml',
        #'views/ir_attachment_tipo.xml',
        #'views/res_users_view.xml',
        #'views/res_partner_view.xml',
        #'data/comun.tipo_modelo.csv',
        #'data/comun.adicional.csv',
        #'data/comun.estado_proyecto.csv',
        #'data/comun.modelo.csv',
        #'data/comun.tipo_mcu.csv',
        #'data/comun.adicional_modelo.csv',
        #'data/comun.parametro.csv',
        #'data/res.partner.category.csv',
    ],
}
