from odoo import  models, fields, api
class MrpProductionMaterialLine(models.Model):
    _name = 'mrp.production.material.line'

    production_id = fields.Many2one(comodel_name='mrp.production.ext',string='Production')
    product_id = fields.Many2one(
        'product.product',
        string='Product',
    )
    required_qty = fields.Integer(string='Required Qty')
    available_qty = fields.Integer(string='Available Qty', compute='_compute_available_qty')
    consumed_qty = fields.Integer(string='Consumed Qty')

    def _compute_available_qty(self):
        for materail in self:
            if materail.product_id:
                materail.available_qty = materail.product_id.qty_available
            else:
                materail.available_qty = 0
