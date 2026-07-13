from odoo import fields, models,api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    credit_limit = fields.Float(string="POS credit limit",default=100)

    @api.model
    def _load_pos_data_fields(self, config_id):
        data = super()._load_pos_data_fields(config_id)
        data += ['credit_limit']
        return data