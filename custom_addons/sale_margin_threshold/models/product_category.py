from odoo import fields, models

class ProductCategory(models.Model):
    _inherit = 'product.category'

    minimum_margin_percent = fields.Float(string="Minimum Margin Percent", default=15.0)