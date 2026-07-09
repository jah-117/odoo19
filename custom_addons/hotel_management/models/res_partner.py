from odoo import models,fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_hotel_guest = fields.Boolean(string="Hotel Guest")
    channel_ids = fields.Many2many(relation='mail_channel_hotel_management_partner')
