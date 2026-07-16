from odoo import  models

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def get_product_info_pos(self,price, quantity, pos_config_id, product_variant_id=False):
        res = super().get_product_info_pos(price, quantity, pos_config_id, product_variant_id=False)
        loc_id = int(self.env['ir.config_parameter'].sudo().get_param('res.config.settings.pos_location'))
        location= self.env['stock.location'].browse(loc_id)
        quantity = self.env['stock.quant'].search([('location_id', '=', loc_id),('product_id','=',self.product_variant_id)]).inventory_quantity_auto_apply
        print(location.complete_name)
        print(quantity)

        res.update({
            'location': location.complete_name,
            'available_quantity': quantity,
        })
        return res