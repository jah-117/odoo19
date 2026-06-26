from odoo import models, fields, api
from datetime import datetime


class OrderFood(models.Model):
    _name = 'order.food'
    _rec_name = ''

    state = fields.Selection(selection=[('draft', 'Draft'),('conform','Conform')], default='draft')

    accommodation_id = fields.Many2one(comodel_name='hotel.accommodation',
                                       domain="[('state','=','check_in')]",
                                       string="Accommodation",
                                       required=True,
                                       ondelete='cascade',
                                       help="Accommodation this order will be invoiced.")
    name = fields.Char(default=f"Order {datetime.now().strftime("%b %d %Y %H:%M:%S")}")
    room_id = fields.Many2one(comodel_name='hotel.room',
                              related='accommodation_id.room_id',
                              string="Room",
                              help="Room Number of the accommodation.")
    guest_id = fields.Many2one(comodel_name='res.partner',
                               related='accommodation_id.guest',
                               string="Guest")
    order_time = fields.Datetime(default=datetime.now(),
                                 string="Order Time")
    food_category_ids = fields.Many2many(comodel_name="food.categories",
                                         string="Food Category",
                                         help="Select a category to list available food items.")

    food_item_ids = fields.Many2many(comodel_name='food.items',
                                     domain="[('category_id','in',food_category_ids)]")

    food_order_line_ids = fields.One2many(comodel_name='food.order.lines',
                                          inverse_name='food_order_id',
                                          readonly=True)
    country_id = fields.Many2one(comodel_name='res.country', default=lambda self: self.env.user.country_id.id)
    currency_id = fields.Many2one(comodel_name='res.currency', related='country_id.currency_id')
    total_amount = fields.Monetary(string="Total Amount",
                                   currency_field='currency_id',
                                   readonly=True,
                                   help="Total amount of the order.")


    @api.onchange('food_category_ids')
    def _compute_food_items(self):
        if self.food_category_ids:
            food_items = (self.env['food.items'].
                          search([('category_id', 'in', self.food_category_ids)]))
            self.food_item_ids = food_items

    def compute_total(self):
        self.total_amount = sum([order_line.subtotal for order_line in self.food_order_line_ids])
    def conform_order(self):
        if self.accommodation_id:
            order_product = self.env.ref('hotel_management.restaurant_expenses')
            (self.env['hotel.accommodation'].
            search([('id', '=', self.accommodation_id.id)]).
            write({
                'payment_line_ids': [(0, 0, {
                    'order_food_id': self.id,
                    'product_id': order_product.id,
                    'description': self.name,
                    'quantity': 1,
                    'unit_of_measure': 'Order',
                    'unit_price':self.total_amount,
                    'subtotal':self.total_amount
                })]
            }))
            self.state ='conform'