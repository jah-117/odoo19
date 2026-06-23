from odoo import models, fields, api
from datetime import datetime


class OrderFood(models.Model):
    _name = 'order.food'
    _rec_name = 'accommodation_id'

    accommodation_id = fields.Many2one(comodel_name='hotel.accommodation',
                                       domain="[('state','=','check_in')]",
                                       string="Accommodation")
    room_id = fields.Many2one(comodel_name='hotel.room',
                              related='accommodation_id.room_id',
                              string="Room")
    guest_id = fields.Many2one(comodel_name='res.partner',
                               related='accommodation_id.guest',
                               string="Guest")
    order_time = fields.Datetime(default=datetime.now(),
                                 string="Order Time")
    food_category_ids = fields.Many2many(comodel_name="food.categories",
                                         string="Food Category")

    food_item_ids = fields.Many2many(comodel_name='food.items',
                                     domain="[('category_id','in',food_category_ids)]")

    food_order_line_ids = fields.One2many(comodel_name='food.order.lines',
                                          inverse_name='food_order_id',
                                          readonly=True)
    country_id = fields.Many2one(comodel_name='res.country',default=lambda  self: self.env.user.country_id.id)
    currency_id = fields.Many2one(comodel_name='res.currency', related='country_id.currency_id')
    total_amount = fields.Monetary(string="Total Amount",
                                   currency_field='currency_id',
                                   readonly=True)

    @api.onchange('food_category_ids')
    def _compute_food_items(self):
        if self.food_category_ids:
            food_items = (self.env['food.items'].
                          search([('category_id', 'in', self.food_category_ids)]))
            self.food_item_ids = food_items

    def compute_total(self):
        sum = 0
        for order_lines in self.food_order_line_ids:
            sum += order_lines.subtotal
        print(sum)
        self.total_amount = sum
