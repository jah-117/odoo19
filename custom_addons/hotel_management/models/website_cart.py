from odoo import api, fields, models

class WebsiteCart(models.Model):
    _name = 'website.cart'
    _description = 'Website Cart'

    accommodation_id = fields.Many2one('hotel.accommodation', string='Accommodation')
    food_order_line_ids = fields.One2many('food.order.lines', string='order lines',inverse_name='website_cart_id')
    user_id = fields.Many2one('res.users', string='User')
    partner_id = fields.Many2one('res.partner', string='Customer', related='user_id.partner_id')
    total = fields.Float(string='Total Price')
    active = fields.Boolean(string="Active", default=True)

    def confirm_order(self):
        order_lines = self.food_order_line_ids
        print(order_lines)
        self.food_order_line_ids = False
        print(self.food_order_line_ids)
        order_food_id = self.env['order.food'].sudo().create({
            'accommodation_id': self.accommodation_id.id,
            'food_order_line_ids': [fields.Command.link(line.id) for line in order_lines],
            'total_amount':self.total,
        })
        print(order_food_id)
        order_food_id.compute_total()
        print('computed total')
        order_food_id.conform_order()
        print('conformed order')
        self.active = False
        print('active',self.active)
