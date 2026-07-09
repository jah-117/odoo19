from odoo import models,fields

class ProductProduct(models.Model):
    _inherit = 'product.template'

    brand = fields.Char(string="Brand")
