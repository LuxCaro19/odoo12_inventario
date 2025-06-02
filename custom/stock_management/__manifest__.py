# -*- encoding: utf-8 -*-
##############################################################################
#
#    For this module the user can make the following options:
#    * Create a Equipment
#    * Create a Team
#    * Assign Equipment to People
#    * Make a maintenance request
#    * Perform control and management equipment and request
#
#    Preferences (only with Maintenance installed)
#
###############################################################################
{
    'name': "Stock Inventory Management",
    'summary': """Stock Inventory Management""",
    'description': """
        Extend the odoo Stock Inventory Management module.
    """,
    'version': '12.0.0.0.0',
    'category': 'Human Resources',
    'license': 'LGPL-3',
    'author': "Grupo Faster (www.faster.es)",
    'website': "http://faster.es/",
    'contributors': [
        "Tatiana Rosabal Gonzalez <tatiana.rosabal@faster.es>",
        "Edgar Naranjo Fuentes <edgar.naranjo@faster.es>",
        "Miguel Campos del Portillo <miguel.campos@faster.es>",
        "Miguel Fernandez Santano <miguel.fernandez@faster.es>",
        "Juan Jose San Martin <peco@faster.es>",
    ],
    'support': 'apps@faster.es',
    'depends': [
        'base',
        'maintenance',
        'hr',
        'mantencion'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/component_stuft.xml',
        'views/inventory_views.xml',
        'views/inventory_manufacturer.xml',
        'views/inventory_type.xml',
        'views/inventory_historial.xml',
        'views/inventory_model.xml',
        'views/templates.xml',
        'data/inventory_data.xml',
    ],
    'images': [
        'static/description/screenshot_stock.png'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
