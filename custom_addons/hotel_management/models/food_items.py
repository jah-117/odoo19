from odoo import models, fields


class FoodItem(models.Model):
    _name = 'food.items'
    _description = 'Details of food item'

    name = fields.Char(string="Name", required=True)
    image = fields.Image(string="Image", max_width=10, max_height=10)
    item = fields.Char(string="Item")
    category_id = fields.Many2one("food.categories", string="Category", required=True)
    quantity = fields.Integer(string="Quantity")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string="Currency", related='company_id.currency_id')
    price = fields.Monetary(string="Price", currency_field="currency_id")
    description = fields.Char(string="Description")

    def action_order_food(self):
        order_id = self.env.context.get('order_food_id')
        res = {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'view_mode': 'form',
            'res_model': 'order.food.transient',
            'target': 'new',
            'context': {
                'default_food_order_id':order_id,
                'default_food_item_id': self.id,
                'default_name': self.item,
                'default_price': self.price,
                'default_image': self.image,
                'default_available_quantity': self.quantity,
                'default_description': self.description
            }
        }
        return res
