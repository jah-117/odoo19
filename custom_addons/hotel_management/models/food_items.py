from odoo import models, fields, api


class FoodItem(models.Model):
    _name = 'food.items'
    _description = 'Details of food item'

    name = fields.Char(string="Name", required=True, help="Name of food.")
    image = fields.Image(string="Image",  help="Image of food.")
    item = fields.Char(string="Item", help="Item of food.")
    category_id = fields.Many2one("food.categories", string="Category", required=True, help="Category of food item.")
    quantity = fields.Integer(string="Quantity", help="Quantity of food item available.")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string="Currency", related='company_id.currency_id')
    price = fields.Monetary(string="Price", currency_field="currency_id", help="Price of food item.")
    description = fields.Char(string="Description")

    def get_item_in_cart(self, cart_id):
        cart = self.env['website.cart'].sudo().browse(int(cart_id))
        if self.id in [order.food_item_id.id for order in cart.food_order_line_ids]:
            return False
        return True


    @api.model
    def _create_lunch_product(self, record):
        category = self.env['lunch.product.category'].search([('name', '=', record.category_id.name)])
        if not category:
            category = self.env['lunch.product.category'].create({'name': record.category_id.name})
        self.env['lunch.product'].create({
            'name': record.name,
            'price': record.price,
            'product_image': record.image,
            'category_id': category.id,
            'supplier_id': 1
        })

    def action_order_food(self):
        return {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'view_mode': 'form',
            'res_model': 'make.order.food',
            'target': 'new',
            'context': {
                'food_order_id': self.env.context.get('order_food_id'),
                'food_item_id': self.id,
                'default_name': self.item,
                'default_price': self.price,
                'default_image': self.image,
                'default_available_quantity': self.quantity,
                'default_description': self.description
            }
        }

    @api.model
    def get_food_items(self):
        return [{
            'id':item.id,
            'name': item.name,
            'image':f'data:image/jpeg;charset=utf-8;base64,{item.image.decode("utf-8")}' if item.image else False,
            'item':item.item,
            'category':item.category_id.name,
            'available_quantity':item.quantity,
            'price':item.price,
            'description':item.description,
            } for item in self.search([]) ]
    def get_image_url(self):
        if self.image:
            return f'data:image/jpeg;charset=utf-8;base64,{self.image.decode("utf-8")}'
        else:
            return ''