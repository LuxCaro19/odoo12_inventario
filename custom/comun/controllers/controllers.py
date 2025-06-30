# -*- coding: utf-8 -*-
from odoo import http

# class Comun(http.Controller):
#     @http.route('/comun/comun/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/comun/comun/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('comun.listing', {
#             'root': '/comun/comun',
#             'objects': http.request.env['comun.comun'].search([]),
#         })

#     @http.route('/comun/comun/objects/<model("comun.comun"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('comun.object', {
#             'object': obj
#         })