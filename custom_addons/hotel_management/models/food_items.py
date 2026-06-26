from odoo import models, fields


class FoodItem(models.Model):
    _name = 'food.items'
    _description = 'Details of food item'

    name = fields.Char(string="Name", required=True, help="Name of food.")
    image = fields.Image(string="Image", max_width=10, max_height=10, help="Image of food.")
    item = fields.Char(string="Item", help="Item of food.")
    category_id = fields.Many2one("food.categories", string="Category", required=True,help="Category of food item.")
    quantity = fields.Integer(string="Quantity",help="Quantity of food item available.")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string="Currency", related='company_id.currency_id')
    price = fields.Monetary(string="Price", currency_field="currency_id",help="Price of food item.")
    description = fields.Char(string="Description")

    def action_order_food(self):
        return {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'view_mode': 'form',
            'res_model': 'order.food.transient',
            'target': 'new',
            'context': {
                'food_order_id':self.env.context.get('order_food_id'),
                'food_item_id': self.id,
                'default_name': self.item,
                'default_price': self.price,
                'default_image': self.image,
                'default_available_quantity': self.quantity,
                'default_description': self.description
            }
        }