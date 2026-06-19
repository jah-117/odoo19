from datetime import timedelta, datetime
from odoo import fields, models, api, _
from odoo.exceptions import UserError

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
                            )
    number_of_guests = fields.Integer(string="Number of Guests", default=1)

    other_guests = fields.Many2many(comodel_name='hotel.guest', )

    check_in = fields.Datetime(string="Check-In Date & Time", readonly=True,
                               tracking=True, store=True)
    check_out = fields.Datetime(string="Check-Out Date & Time", readonly=True,
                                tracking=True, store=True)
    bed_type = fields.Selection(default='single',
                                selection=BED_TYPES,
                                tracking=True,
                                string="Bed Type", required=True)

    facilities = fields.Many2many(comodel_name='room.facility')

    room_id = fields.Many2one(comodel_name='hotel.room', string="Room",
                              # compute = '_compute_domains',
                              # domain="['bed','=', bed_type]",
                              readonly=False,
                              precompute=True,
                              )

    available_room_ids = fields.Many2many(
        comodel_name='hotel.room',
        compute='_compute_available_room_ids',
    )
    room_filter_domain_types = fields.Char(compute='_compute_room_filter_domain_types')

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

    @api.onchange('facilities', 'bed_type', )
    def _compute_domains(self):
        for acc in self:

    @api.depends('bed_type')
    def _compute_room_filter_domain_types(self):
        for acc in self:
            acc.room_filter_domain_types = self._get_room_filter_domain_type(acc.bed_type)

    @api.model
    def _get_room_filter_domain_type(self, bed_type):
        if bed_type == 'single':
            return 'single'
        elif bed_type == 'double':
            return 'double'
        elif bed_type == 'dormitory':
            return 'dormitory'
        else:
            return False


    def check_in_guest(self):
        for rec in self:
            if rec.number_of_guests > 1:
                if rec.number_of_guests != len(rec.other_guests) + 1:
                    raise UserError(_("Number of guests does not match number of other guests"))
            if not rec.id_proof:
                raise UserError(_('No attachments found'))
            rec.state = 'check_in'
            rec.check_in = datetime.now()

    def check_out_guest(self):
        for rec in self:
            rec.state = 'check_out'
            rec.check_out = datetime.now()
