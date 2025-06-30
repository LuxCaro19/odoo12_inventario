# -*- coding: utf-8 -*-

from odoo import models, fields, api
import requests
from stdnum.util import clean


class Partner(models.Model):

    _inherit = ['res.partner']

    #sucursales_ids = fields.Many2many('comun.sucursal', string='Sucursales')
    buk_id = fields.Integer(string="Id de usuario en BUK")
    
    def get_listado_superiores(self, usuario=None):
        if not usuario:
            usuario = self.env.user.partner_id
        
        superiores = []
        boss = self._get_boss_id(user_id=usuario.buk_id)
        superiores.append(boss)
        while boss:
            boss = self._get_boss_id(boss)
            if boss in superiores:
                break
            superiores.append(boss)
        return self.get_internal_id(superiores)

    def get_internal_id(self, buk_user_list):
        lista = []
        for user in buk_user_list:
            user_ids = self.env['res.partner'].search([
                ('buk_id', '=', user)                
            ])
            for user_id in user_ids:
                res_user = self.env['res.users'].search([
                    ('partner_id', '=', user_id.id)
                ], limit=1) or None
                if res_user:
                    lista.append(user_id.id)
                    break
        return lista
        

    def _get_boss_id(self, user_id):
        url = 'https://galilea.buk.cl/api/v1/employees/%s' % user_id
        
        headers = {
            'Content-Type': 'application/json',
            'auth_token': self.env['comun.parametro'].search([
                ('nombre', '=', 'buk_users_api_key')
            ]).valor
        }
        user = requests.get(url, headers=headers)                
        if user: 
            print(user.json()['data']['email'])
            return user.json()['data']['current_job']['boss']['id']            
        return None

    @api.model    
    def sincronizar_usuarios_buk(self):
        data = self.get_buk_info()
        for usuario in data:            
            usuario_id = self.buscar_usuario(usuario=usuario)
            if usuario_id:
                usuario_id.write({
                    'buk_id': usuario['id']
                })
        
    @api.model
    def buscar_usuario(self, usuario):        
        usuario_id = None
        if usuario['email']:
            usuario_id = self.env['res.partner'].search([
                ('email', '=', usuario['email'])
            ]) or None
        if not usuario_id:   
            rut = clean(usuario['rut'], ' .').strip().upper()
            usuario_id = self.env['res.partner'].search([
                ('vat', '=', rut)
            ])
                    
        return usuario_id
        

    def get_buk_info(self):
        '''
        https://galilea.buk.cl/api/v1/employees/active
        --header 'Content-Type: application/json' \
        --header 'auth_token: ------'
        '''
        url = 'https://galilea.buk.cl/api/v1/employees/active'
        headers = {
            'Content-Type': 'application/json',
            'auth_token': self.env['comun.parametro'].search([
                ('nombre', '=', 'buk_users_api_key')
            ]).valor
        }
        data = []        
        while True:
            response = requests.get(url, headers=headers)
            data = data + response.json()['data']
            if not response.json()['pagination']['next']:
                break
            url = response.json()['pagination']['next']

        return data