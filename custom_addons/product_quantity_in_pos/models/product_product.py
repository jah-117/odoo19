from odoo import fields, models, api

class ProductProduct(models.Model):
    _inherit = 'product.product'

    pos_quantity_available= fields.Integer(string="Available Quantity",compute='_compute_pos_quantity_available',store=True)

    @api.depends('list_price')
    def _compute_pos_quantity_available(self):
        self.pos_quantity_available=0
        location_id = int(self.env['ir.config_parameter'].sudo().get_param('res.config.settings.pos_location'))
        for product in self:
            stock = self.env['stock.quant'].search_fetch(
                [('location_id', '=', location_id),('product_id','=',product.id)],
                ['inventory_quantity_auto_apply'])
            product.pos_quantity_available = stock.inventory_quantity_auto_apply if stock.inventory_quantity_auto_apply else 0
            print(stock.inventory_quantity_auto_apply)
    
    @api.model
    def _load_pos_data_fields(self, config_id):
        data = super()._load_pos_data_fields(config_id)
        data += ['pos_quantity_available']
        return data