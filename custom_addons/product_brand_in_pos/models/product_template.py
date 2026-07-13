# -*- coding: utf-8 -*-
from odoo import models,fields,api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    brand = fields.Char(string="Brand")

    @api.model
    def _load_pos_data_fields(self, config_id):
        data = super()._load_pos_data_fields(config_id)
        data += ['brand']
        return data