from datetime import timedelta, datetime

from addons.web.controllers import domain
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError

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


class HotelAccommodation(models.Model):
    _name = 'hotel.accommodation'
    _inherit = ['mail.thread']
    _description = 'Accommodation'

    state = fields.Selection(
        selection=ACCOMMODATION_STATES,
        default='draft',
        string="state",
        tracking=True,
    )
    name = fields.Char(string="Accommodation Number", required=True, copy=False,
                       readonly=True, default=lambda self: _('New'))

    guest = fields.Many2one(comodel_name='res.partner',
                            string='Guest',
                            tracking=True,
                            required=True
                            )
    number_of_guests = fields.Integer(string="Number of Guests", default=1)

    other_guests = fields.One2many(comodel_name='accommodation.guests.lines',inverse_name='accommodation_ids')

    check_in = fields.Datetime(string="Check-In Date & Time", readonly=True,
                               tracking=True, store=True)
    check_out = fields.Datetime(string="Check-Out Date & Time", readonly=True,
                                tracking=True, store=True)
    bed_type = fields.Selection(default='single',
                                selection=BED_TYPES,
                                tracking=True,
                                string="Bed Type", required=True)

    facilities = fields.Many2many(string="Facilities", comodel_name='room.facility',
                                  store=True)
    room_id = fields.Many2one(comodel_name='hotel.room', string="Room",
                              required=True,
                              readonly=False)

    available_room_ids = fields.Many2many(comodel_name='hotel.room',
                                          compute='_compute_available_room_ids')

    id_proofs = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        domain=[('res_model', '=', 'hotel.accommodation')],
        string="ID-Proofs", )
    expected_days = fields.Integer(string="Expected Days", default="1")
    expected_date = fields.Date(string="Expected Date of Check-Out",
                                compute='_compute_expected_date', store=True)

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            if val.get('name', _("New")) == _("New"):
                val['name'] = self.env['ir.sequence'].next_by_code('acc.seq') or _("New")
        return super().create(vals)

    @api.depends('expected_date', 'check_in')
    def _compute_expected_date(self):
        for rec in self:
            if not rec.check_in:
                continue
            rec.expected_date = rec.check_in + timedelta(days=rec.expected_days)

    def _compute_available_room_ids(self):
        self.available_room_ids = self.env['hotel.room'].search([
            ('state', '=', 'available'),
            ('bed', '=', self.bed_type)
        ])

    @api.onchange('facilities', 'bed_type')
    def _calculate_domain(self):
        rooms = self.env['hotel.room'].search([
            ('state', '=', 'available'),
            ('bed', '=', self.bed_type)
        ])
        if len(self.facilities)>0:
            rooms = self.env['hotel.room'].search([
                ('state', '=', 'available'),
                ('bed', '=', self.bed_type),
                ('facility_ids','in',self.facilities)
            ])
        self.available_room_ids = rooms

    def check_in_guest(self):
        for rec in self:
            if rec.number_of_guests > 1 and rec.number_of_guests != len(rec.other_guests) + 1:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Warning!',
                        'message': f'Hello, Please provide details of all guests.',
                        'type': 'danger',
                        'sticky': True,
                    }
                }
            rec.state = 'check_in'
            rec.check_in = datetime.now()
            rec.room_id.state = 'not_available'
            if not rec.id_proofs:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Warning!',
                        'message': f'Hello, Please attach ID-proofs.',
                        'type': 'warning',
                        'sticky': False,
                        'next': {
                            'type': 'ir.actions.act_window_close',
                        }
                    }
                }

    def check_out_guest(self):
        for rec in self:
            rec.state = 'check_out'
            rec.check_out = datetime.now()
            rec.room_id.state = 'available'
