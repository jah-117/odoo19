from odoo import models, fields


class MakeOrderFood(models.TransientModel):
    _name = 'make.order.food'
    _description = 'Food order'

    name = fields.Char(readonly=True)
    quantity = fields.Integer(default="1")
    available_quantity = fields.Integer()
    company_id = fields.Many2one('res.company', store=True, copy=False,
                                 string="Company",default=lambda self:
                                 self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  related='company_id.currency_id',
                                  default=lambda self:
                                  self.env.user.company_id.currency_id.id)
    price = fields.Monetary(readonly=True)
    image = fields.Binary()
    description = fields.Char(readonly=True)

    def add_to_list(self):
        """
        Add the clicked food item to the list
        reduce the quantity of the food item
        """
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
        order_food = self.env['order.food'].search([('id', '=', self.env.context.get('food_order_id'))])
        order_food.write({'food_order_line_ids': [(0, 0, {
            'food_item_id': self.env.context.get('food_item_id'),
            'item_name': self.name,
            'description': self.description,
            'quantity': self.quantity,
            'unit_price': self.price,
            'subtotal': self.price * self.quantity
        })]})
        order_food.compute_total()
        self.env['food.items'].search(
            [('id', '=', self.env.context.get('food_item_id'))]
        ).write({'quantity': self.available_quantity - self.quantity})

    def button_discard(self):
        return False
