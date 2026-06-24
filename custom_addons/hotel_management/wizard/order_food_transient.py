from odoo import models, fields


class OrderFoodTransient(models.TransientModel):
    _name = 'order.food.transient'
    _description = 'Food order'

    name = fields.Char(readonly=True)
    quantity = fields.Integer(default="1")

    available_quantity = fields.Integer()
    company_id = fields.Many2one('res.company', store=True, copy=False,
                                 string="Company",
                                 default=lambda self:
                                 self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  related='company_id.currency_id',
                                  default=lambda self:
                                  self.env.user.company_id.currency_id.id)
    price = fields.Monetary(readonly=True)
    image = fields.Binary()
    description = fields.Char(readonly=True)
    food_item_id = fields.Integer()
    food_order_id = fields.Integer()

    def add_to_list(self):
        """qwertyui"""
        if self.quantity > self.available_quantity:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Warning!',
                    'message': f'Hello, Quantity exceeds on hand stock.',
                    'type': 'danger',
                    'sticky': False,
                }
            }
        food_item = self.env['food.items'].search([('id', '=', self.food_item_id)])
        subt = self.price * self.quantity
        order_food = self.env['order.food'].search([('id','=',self.food_order_id)])
        order_food.write({ 'food_order_line_ids':[(0, 0, {
            'food_item_id':self.food_item_id,
            'item_name': self.name,
            'description': self.description,
            'quantity': self.quantity,
            'unit_price': self.price,
            'subtotal': subt
        })]})
        order_food.compute_total()
        remaining_quantity = self.available_quantity - self.quantity
        food_item.write({'quantity': remaining_quantity})


    def button_discard(self):
        pass
