# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import timedelta
import datetime


class Component(models.Model):
    _name = 'component.component'
    _description = 'Component'
    _inherit = ['mail.thread']

    serial = fields.Char('Serial')
    name = fields.Char('Nombre de Componente', track_visibility='onchange')
    assign_date = fields.Date('Fecha de asignación', track_visibility='onchange')
    scrap_date = fields.Date('Fecha de Desecho', track_visibility='onchange')
    status_id = fields.Many2one('maintenance.status', string='Estado')
    # description_text = fields.Char('Descripcion Tecnica', track_visibility='onchange')
    descript = fields.Text('Descripcion')
    capacity = fields.Char('Capacidad')
    speed = fields.Char('Velocidad')
    # stuft_id = fields.One2many('component.stuft', 'components_id', ondelete='restrict', string='Components')
    equipment_id = fields.Many2one("maintenance.equipment", string="Equipo",track_visibility='onchange')
    type_comp_id = fields.Many2one("component.type", string="tipo")
    comp_model_id = fields.Many2one("component.model", string="modelo")
    factura_id = fields.Many2one('maintenance.factura', string='Factura')
    obsolete  = fields.Boolean(string="Obsoleto",default=False)
    bodega  = fields.Boolean(string="Bodega",default=True)
    historial_ids = fields.One2many('component.historial', 'component_id', string="Historial" )
    
    
        # Restricción y creación de un historial:
    @api.model
    def create(self,vals):
        campo = self.env['component.historial']
        registro = super(Component, self).create(vals)
        
        
    
        # Creación de un historial:
        if 'equipment_id' or 'bodega' in registro:
        
            new_historial = campo.create({
                'componente': registro.name,
                'equipo': registro.equipment_id.name,
                'fecha': registro.assign_date,
                'ubicacion': registro.equipment_id.ubicacion_id.nombre,
                'bodega_a': registro.bodega,
                'equipment_id': registro.equipment_id.id,
                'component_id': registro.id
            })
        return registro

    # Si se editan los campos, crea otro registro en el historial:
    @api.multi
    def write(self, vals, context=None):
        cambio = super(Component, self).write(vals)
        models = self.env['maintenance.equipment']
        campo = self.env['component.historial']
        
        if cambio:
            if 'equipment_id' in vals:
              
                new_historial = campo.create({
                    'componente': self.name,
                    'equipo': self.equipment_id.name,
                    'fecha': self.assign_date,
                    'ubicacion': self.equipment_id.ubicacion_id.nombre,
                    'bodega_a': self.bodega,
                    'equipment_id': self.equipment_id.id,
                    'component_id': self.id
                })

        
            elif 'scrap_date' in vals:
                buscador_f = models.search([
                    ('scrap_date', '=', vals['scrap_date'])
                ])
                new_historial = campo.create({
                    'componente': self.name,
                    'equipo': self.equipment_id.name,
                    'fecha': self.assign_date,
                    'ubicacion': self.equipment_id.ubicacion_id.nombre,
                    'bodega_a': self.bodega,
                    'equipment_id': self.equipment_id.id,
                    'component_id': self.id,
                    'fecha_desecho': vals['scrap_date'],
                    
                })
        return cambio
    

    @api.constrains('factura_id')
    def _restriccion(self):
        cantidad_en_equipo = self.env['maintenance.equipment'].search_count(
            [('factura_id.id', '=', self.factura_id.id)])
        cantidad_en_componente = len(self.factura_id.component_ids)
        if self.factura_id.cantidad < (cantidad_en_equipo + cantidad_en_componente):
            raise ValidationError('La factura que intenta ingresar ya está completa')

    @api.onchange('type_comp_id')
    def filtro(self):
        tipo = ""
        modelo = ""
        serial = ""
        if self.type_comp_id.name:
            tipo = self.type_comp_id.name
        if self.comp_model_id.name:
            modelo = self.comp_model_id.name
        if self.comp_model_id.name:
            serial = self.serial
            
        self.name = tipo+"-"+modelo+"-"+serial
        res = {}
        if self.type_comp_id:
            res['domain']={'equipment_id':[('type_id','in',self.type_comp_id.type_maintenance_ids.ids)]}
            return res
    
    @api.onchange('comp_model_id')
    def autcomplete_modelo(self):
        tipo = ""
        modelo = ""
        serial = ""
        if self.type_comp_id.name:
            tipo = self.type_comp_id.name
        if self.comp_model_id.name:
            modelo = self.comp_model_id.name
        if self.comp_model_id.name:
            serial = self.serial
            
        self.name = tipo+"-"+modelo+"-"+serial
    
    @api.onchange('serial')
    def autcomplete_serial(self):
        tipo = ""
        modelo = ""
        serial = ""
        if self.type_comp_id.name:
            tipo = self.type_comp_id.name
        if self.comp_model_id.name:
            modelo = self.comp_model_id.name
        if self.comp_model_id.name:
            serial = self.serial
            
        self.name = tipo+"-"+modelo+"-"+serial
        
    @api.onchange('status_id')
    def estado_obsoleto(self):
        
        if self.status_id:
            if self.status_id.description == 'Obsoleto':
                self.obsolete = True
    
    @api.onchange('equipment_id')
    def cambio_equipo(self):
        
        if self.equipment_id:
            self.bodega = False
        else:
            self.bodega = True

    @api.constrains('type_comp_id')
    
    def _restriccion(self):
        
        if self.equipment_id:
            if self.equipment_id.type_id.id not in self.type_comp_id.type_maintenance_ids.ids:
                raise ValidationError('No coincide con el tipo de equipo')
            
class MaintenanceHistorial (models.Model):
    _name = 'component.historial'
    _description = 'Historial de Equipos'

    # Atributos:
    equipo = fields.Char(string='Equipo')
    componente = fields.Char(string='Componente')
    fecha = fields.Date(string='Fecha asignacion')
    fecha_hoy = fields.Date (string='Fecha de registro', default=datetime.date.today())
    ubicacion = fields.Char(string='Ubicacion')
    login_ids= fields.Many2one('res.users', default=lambda self: self.env.user, string='Registrado por') # Este campo guarda el usuario que está logeado.
    bodega_a = fields.Boolean(string='En bodega')# Campo que tendrá el "bodega" de equipo.
    fecha_desecho = fields.Date(string='Fecha de desecho')

    # Relaciones:
    equipment_id = fields.Many2one('maintenance.equipment', string='Equipo')
    component_id = fields.Many2one('component.component', string='Componente')


class ComponentStuft(models.Model):
    _name = 'component.stuft'
    _description = 'Component'

    name = fields.Char('Component Name', required=True, track_visibility='onchange')
    description_text = fields.Char('Technical Description', required=True, track_visibility='onchange')
    descript = fields.Text('Technical Description')
    equipment_id = fields.Many2one("maintenance.equipment", string="Equipo")
    components_id = fields.Many2one("component.component", string="Componente")
    type_comp = fields.Many2one("maintenance.type", string="Component")

    @api.onchange('components_id', 'name', 'type_comp_id', 'description_text')
    def onchange_component_id(self):
        if self.components_id:
            self.name = self.components_id.name
            self.type_comp = self.components_id.type_comp_id
            self.description_text = self.components_id.description_text


class SystemOp(models.Model):
    _name = 'system.op'
    _description = 'Operative System'

    name = fields.Char('Operative System', required=True)
    version_so = fields.Char('Version')
    descript = fields.Text('Descripcion')


class ComponentManufacturer(models.Model):
    _name = 'component.manufacturer'
    _description = 'Fabricante de Componente'

    name = fields.Char('Nombre Fabricante', required=True)
    descript = fields.Text('Descripcion')


class ComponentType(models.Model):
    _name = 'component.type'
    _description = 'Tipo de Componente'

    name = fields.Char('Nombre Tipo', required=True)
    descript = fields.Text('Descripcion')
    type_maintenance_ids = fields.Many2many('maintenance.type', string="Tipo Equipo")


class ComponentModel(models.Model):
    _name = 'component.model'
    _description = 'Modelo de Componentes'

    name = fields.Char('Nombre del Modelo', required=True)
    descript = fields.Text('Descripcion')
    marca = fields.Many2one("component.manufacturer", string="Marca")


class MaintenanceEquipment(models.Model):
    _name = 'maintenance.equipment'
    _inherit = ['maintenance.equipment']

    # name = fields.Char('Equipment Name', required=True)
    # uuid = fields.Char('UUID', help="Unique codes GLPI System")
    # benchmark = fields.Float('Performance')
    # address_ip = fields.Char('IP/Terminal Number')
    # sistema_operativo = fields.Char('Operative System')
    # version_os = fields.Char('OS Version')
    # owner_user_id = fields.Many2one('res.users', string='Owner',track_visibility='onchange')
    # owner_user_ids = fields.Many2many('res.users', 'owner_inventory_user_rel', 'owner_id', 'user_id', string='Other Owners', track_visibility='onchange')
    component_ids = fields.One2many('component.component', 'equipment_id', ondelete='restrict', string='Componentes')
    # system_id = fields.Many2one("system.op", string="Operative System")
    # invoice_id = fields.Char('Ref. Invoice')
    # address_mac = fields.Char('MAC')
    # calculator
    # todo_equip_ids = fields.One2many('res.users', copy=False, compute='_compute_todo_equip')
    todo_comp_ids = fields.One2many('component.component', copy=False, compute='_compute_todo_equip')
    # todo_equip_count = fields.Integer(compute='_compute_todo_equip')
    todo_comp_count = fields.Integer(compute='_compute_todo_equip')


    @api.one
    @api.depends('component_ids')
    def _compute_todo_equip(self):
        # self.todo_equip_ids = self.owner_user_ids
        self.todo_comp_ids = self.component_ids
        # self.todo_equip_count = len(self.todo_equip_ids)
        self.todo_comp_count = len(self.todo_comp_ids)
        
        
    @api.constrains('component_ids')
    
    def _restriccion(self):
        
        if self.component_ids:
            for component in self.component_ids:
                if self.type_id.id not in component.type_comp_id.type_maintenance_ids.ids:
                    raise ValidationError('No coincide con el tipo de equipo')


    # _sql_constraints = [('address_mac_unique', 'unique(address_mac)', 'MAC already exists.')]

class MaintenanceType(models.Model):
    _name = 'maintenance.type'
    _inherit = 'maintenance.type'
    _description = 'Tipo de Equipos Informáticos'

    # Atributos:
    type_comp_ids = fields.Many2many('component.type', string="Tipo de Componentes")


class ResUsers(models.Model):
    _name = 'res.users'
    _inherit = ['res.users']

    equipment_ids = fields.One2many('maintenance.equipment', 'owner_user_id', ondelete='restrict', string='Users')


class ComponentFactura(models.Model):
    _name = 'maintenance.factura'
    _inherit = ['maintenance.factura']

    component_ids = fields.One2many('component.component', 'factura_id', string='Componente')
