from odoo import fields, models, api

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def update_quantity_in_product(self):
        loc_id = int(self.env['ir.config_parameter'].sudo().get_param('res.config.settings.pos_location'))
        for quant in self.search([('location_id', '=', loc_id)]):
            quant.product_tmpl_id.pos_quantity_available = quant.inventory_quantity_auto_apply
