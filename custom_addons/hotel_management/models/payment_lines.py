from email.policy import default

from odoo import fields, models, api


class PaymentLine(models.Model):
    _name = "payment.line"

    accommodation_id = fields.Many2one(comodel_name='hotel.accommodation', ondelete='cascade')
    order_food_id = fields.Many2one(comodel_name='order.food')

    country_id = fields.Many2one(comodel_name='res.country', default=lambda self: self.env.user.country_id.id)
    currency_id = fields.Many2one(comodel_name='res.currency', related='country_id.currency_id')

    description = fields.Char(string="Description")
    product_id = fields.Many2one(comodel_name='product.product')
    quantity = fields.Integer(string="Quantity")
    unit_of_measure = fields.Char(string="Uom")
    unit_price = fields.Monetary(string="Price",
                                 currency_field='currency_id'
                                 )
    subtotal = fields.Monetary(string="Subtotal",
                               currency_field='currency_id',
                               )

