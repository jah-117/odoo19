from odoo import api, fields, models

class WebsiteCart(models.Model):
    _name = 'website.cart'
    _description = 'Website Cart'

    accommodation_id = fields.Many2one('hotel.accommodation', string='Accommodation')
    food_order_line_ids = fields.One2many('food.order.lines', string='order lines')
    user_id = fields.Many2one('res.users', string='User')
    partner_id = fields.Many2one('res.partner', string='Customer', related='user_id.partner_id')
    active = fields.Boolean(string="Active", default=True)

    def confirm_order(self):
        pass
    # self.env['order.food'].create({
    #     'accommodation_id':self.accommodation_id,
    #     'food_order_line_ids': [fields.Command.create({
    #         'item_name': item.name,
    #         'description':item.item,
    #         'quantity':
    #     })]
    # })

