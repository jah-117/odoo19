from odoo import models,fields,api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_margin_threshold = fields.Float(related='categ_id.minimum_margin_percent')
    margin_threshold = fields.Float(string='Margin Threshold',compute='_compute_margin_threshold',readonly=True,store=True)

    @api.depends('price_unit','product_id.standard_price','discount')
    def _compute_margin_threshold(self):
        for order in self:
            if order.price_unit:
                print(order.product_uom_id.factor>order.product_id.uom_id.factor)
                if order.product_id.standard_price:
                    unit_price = order.price_unit
                    if order.product_uom_id.factor > order.product_id.uom_id.factor:
                        unit_price = order.price_unit / (order.product_uom_id.factor / order.product_id.uom_id.factor)
                    if order.product_uom_id.factor < order.product_id.uom_id.factor:
                        unit_price = order.price_unit * (order.product_id.uom_id.factor / order.product_uom_id.factor)
                    unit_price = unit_price if not order.discount else  unit_price - ((unit_price * order.discount)/100)
                    order.margin_threshold = ((unit_price - order.product_id.standard_price)/order.product_id.standard_price)*100
                else:
                    order.price_unit = order.product_id.list_price
                    order.margin_threshold = 0
            else:
                order.margin_threshold = 0