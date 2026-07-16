from odoo import fields, models,api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_location = fields.Many2one(comodel_name='stock.location', string="POS Location",
                                   help="The available quantity displayed in pos will be the quantity available at this location")

    @api.model
    def get_values(self):
        """Get the value from settings."""
        res = super(ResConfigSettings, self).get_values()
        icp_sudo = self.env['ir.config_parameter'].sudo()
        pos_location = icp_sudo.get_param('res.config.settings.pos_location')
        res.update(pos_location=self.env['stock.location'].browse(int(pos_location)))
        return res

    def set_values(self):
        """Set the value. The new value stored in the configuration parameters."""
        res = super(ResConfigSettings, self).set_values()
        # pos_config_id = (self.env['ir.config_parameter'].sudo().get_param('point_of_sale.pos_config_id'))
        print(self.pos_config_id.picking_type_id.location_id)
        print(self.pos_location)
        self.pos_config_id.picking_type_id.location_id = self.pos_location.id
        self.env['ir.config_parameter'].sudo().set_param(
            'res.config.settings.pos_location',
            self.pos_location.id)
        return res