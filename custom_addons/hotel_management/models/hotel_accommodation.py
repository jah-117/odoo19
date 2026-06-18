import trace

from odoo import fields, models, api, _

ACCOMMODATION_STATES = [
    ('draft', "Draft"),
    ('check_in', "Check-In"),
    ('check_out', "Check-Out"),
    ('cancel', "Cancel")
]
BED_TYPES = [
    ('single', "Single"),
    ('double', "Double"),
    ('dormitory', "Dormitory")
]


class Accommodation(models.Model):
    _name = 'hotel.accommodation'
    _inherit = ['mail.thread']



    state = fields.Selection(
        selection=ACCOMMODATION_STATES,
        default='draft',
        string="state",
        tracking=True,
    )
    name = fields.Char(string="Accommodation Number", required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))

    guest = fields.Many2one(comodel_name='res.partner',
                            string='Guest',
                            tracking = True,
                            )
    number_of_guests = fields.Integer(string="Number of Guests", default=1)

    other_guests = fields.Many2many(comodel_name='res.partner',)

    check_in = fields.Datetime(string="Check-In Date & Time", required = True, tracking = True,)
    check_out = fields.Datetime(string="Check-Out Date & Time",)
    bedType = fields.Selection(default='single',
                               selection=BED_TYPES,
                               tracking = True,
                               string="Bed Type", required=True)

    facilities = fields.Many2many(comodel_name='room.facility' )
    room = fields.Many2many(comodel_name='hotel.room')
    id_proof = fields.Binary(string="ID proof", tracking = True,)
    expected_days = fields.Integer(string="Expected Days")
    expected_date = fields.Date(string="Expected Date of Check-Out")


    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            if val.get('name', _("New")) == _("New"):
                val['name'] = self.env['ir.sequence'].next_by_code('acc.seq') or _("New")
        return super().create(vals)
