from odoo import api, fields,models

class FoodOrderLines(models.Model):
    _name = 'food.order.lines'

    food_order_id = fields.Many2one(comodel_name='order.food')
    food_item_id = fields.Many2one(comodel_name='food.items')

    country_id = fields.Many2one(comodel_name='res.country', default=lambda self: self.env.user.company_id.country_id.id)
    currency_id = fields.Many2one(comodel_name='res.currency', related='country_id.currency_id')


    item_name = fields.Char(string="Item Name",
                            related='food_item_id.item')
    description = fields.Char(string="Description",
                              related='food_item_id.description')
    quantity = fields.Integer(string="Quantity")
    unit_price = fields.Monetary(string="Unit Price",
                                 related='food_item_id.price')
    subtotal = fields.Monetary(string="Subtotal Price",
                               currency_field="currency_id",
                               store=True)

