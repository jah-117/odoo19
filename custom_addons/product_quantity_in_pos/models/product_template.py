from odoo import  models,fields,api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pos_quantity_available = fields.Integer(string="Available Quantity", default=0)


    def get_product_info_pos(self,price, quantity, pos_config_id, product_variant_id=False):
        res = super().get_product_info_pos(price, quantity, pos_config_id, product_variant_id=False)
        loc_id = int(self.env['ir.config_parameter'].sudo().get_param('res.config.settings.pos_location'))
        location = self.env['stock.location'].browse(loc_id)
        quantity = self.env['stock.quant'].search(
            [('location_id', '=', loc_id), ('product_id', '=', self.product_variant_id)]).inventory_quantity_auto_apply
        res.update({
            'location': location.complete_name,
            'available_quantity': quantity,
        })
        return res

    @api.model
    def _load_pos_data_fields(self, config_id):
        data = super()._load_pos_data_fields(config_id)
        data.append('pos_quantity_available')
        return data