from odoo import models,fields

class FoodItem(models.Model):
    _name = 'food.items'
    _description = 'Details of food item'

    name = fields.Char(string="Name", required=True)
    image = fields.Image(string="Image", max_width=10, max_height=10)
    item = fields.Char(string="Item",)
    category_id = fields.Many2one("food.categories", string="Category", required=True)
    quantity = fields.Integer(string="Quantity")
    currency_id = fields.Many2one("res.currency", string="Currency")
    price = fields.Monetary(string="Price",currency_field="currency_id")
    description = fields.Char(string="Description")