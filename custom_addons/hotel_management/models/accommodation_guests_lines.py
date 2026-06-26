from odoo import fields,models

class AccommodationGuestsLines(models.Model):
    _name = "accommodation.guests.lines"

    accommodation_ids = fields.Many2one(comodel_name='hotel.accommodation', ondelete='cascade')
    guest_ids = fields.Many2one(comodel_name='res.partner')

    age = fields.Integer(string='Age')
    gender = fields.Selection([('male', "Male"),('female', "Female")],string="Gender")