# -*- coding: utf-8 -*-

from odoo import models, fields, api
#from servicios import get_bpms_cursor, bms  # BonitaModelService
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Field





class Parametro(models.Model):
    _name = 'comun.parametro'
    _rec_name = 'nombre'

    nombre = fields.Char("Nombre", required=True, help="Debe ir en minúsculas", index=True)
    valor = fields.Char("Valor", required=True)
    descripcion = fields.Text("Descripción", required=True)
    modulo = fields.Char("Módulo", required=True,
                         help="""Debe escribirse el nombre del módulo al que hace referencia
                         y el modelo seguido por un punto.
                         Ejemplo: comun.parametro""", index=True)











# class HistorialCambios(models.Model):
#     _name = 'comun.historia_cambios'
#     _rec_name = "modelo"
#
#     usuario = fields.Many2one('res.users', 'Usuario')
#
#     modelo = fields.Char(string="Modelo")
#     id_modelo = fields.Integer(string="ID modelo")
#     parametro = fields.Char(string="Nombre Parametro")
#     descripcion = fields.Char(string="Descripción")
#     valor_inicial = fields.Text(string=" Valor Inicial")
#     valor_final = fields.Text(string="Valor Final")
#     fecha_modificacion = fields.Date(string="Fecha")