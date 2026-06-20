
from odoo import fields, models

class FoodCategory(models.Model):
    _name = "food.categories"

    name = fields.Char(string="Name", required=True)