# -*- coding: utf-8 -*-
from odoo import http

# class Consultas(http.Controller):
#     @http.route('/consultas/consultas/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/consultas/consultas/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('consultas.listing', {
#             'root': '/consultas/consultas',
#             'objects': http.request.env['consultas.consultas'].search([]),
#         })

#     @http.route('/consultas/consultas/objects/<model("consultas.consultas"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('consultas.object', {
#             'object': obj
#         })