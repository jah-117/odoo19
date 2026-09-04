from odoo import models, fields

class ProductProduct(models.Model):
    _inherit = 'product.product'

    # restricted_inverse_id = fields.Many2one(comodel_name='product.product', )
    # restricted_product_ids = fields.One2many(comodel_name='product.product', inverse_name='restricted_inverse_id',readonly=1)
    restricted_product_ids = fields.Many2many(comodel_name='product.product',relation='product_restriction',column1="product_id",
                                     column2="restricted_product_id",)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    restricted_product_ids = fields.Many2many(related='product_id.restricted_product_ids')