from datetime import timedelta, datetime
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
PAYMENT_STATUS = [
    ('to_pay', "to_pay"),
    ('paid', "paid")
]


invoice_line_ids =[]

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
    payment_state = fields.Selection(selection=PAYMENT_STATUS, default='to_pay')
    name = fields.Char(string="Accommodation Number", required=True, copy=False,
                       readonly=True, default=lambda self: _('New'))

    guest = fields.Many2one(comodel_name='res.partner',
                            string='Guest',
                            tracking=True,
                            required=True
                            )
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency',string="Currency", related='company_id.currency_id')
    number_of_guests = fields.Integer(string="Number of Guests", default=1)

    other_guests = fields.One2many(comodel_name='accommodation.guests.lines', inverse_name='accommodation_ids')

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

    payment_line_ids = fields.One2many(comodel_name='payment.line',
                                       inverse_name='accommodation_id',
                                       readonly=True)
    total_amount = fields.Monetary(currency_field='currency_id')
    invoice_id = fields.Many2one(comodel_name='account.move')

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
        if len(self.facilities) > 0:
            rooms = self.env['hotel.room'].search([
                ('state', '=', 'available'),
                ('bed', '=', self.bed_type),
                ('facility_ids', 'in', self.facilities)
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

    def _calculate_total_and_create_invoice_lines(self):
        invoice_line_ids.clear()
        sum = 0
        for payment_line in self.payment_line_ids:
            invoice_line = (0, None, {
                'product_id': payment_line.product_id.id,
                'name': payment_line.description,
                'quantity': payment_line.quantity,
                'price_unit': payment_line.unit_price,
                'price_subtotal': payment_line.subtotal,
            })
            invoice_line_ids.append(invoice_line)
            sum += payment_line.subtotal

        self.total_amount = sum
        print(sum)
        print(invoice_line_ids)

    def check_out_guest(self):
        self.state = 'check_out'
        self.check_out = datetime.now()
        check_in = self.check_in
        check_out = self.check_out
        number_of_days = (check_out - check_in).days
        quantity = 1
        if not number_of_days < 1:
            quantity = number_of_days

        rent_product = self.env['product.product'].search([('name', '=', 'Room Rent')])
        # self.write({'payment_line_ids': [(0, 0, {
        #     'product_id': rent_product.id,
        #     'description': 'Room Rent',
        #     'quantity': quantity,
        #     'unit_of_measure': 'Day',
        #     'unit_price': self.room_id.rent,
        #     'subtotal': quantity * self.room_id.rent
        # })]})
        self.room_id.state = 'available'
        self.payment_state = 'paid'
        self._calculate_total_and_create_invoice_lines()
        print("jf", invoice_line_ids)
        self.invoice_id = self.env['account.move'].create([{
            'move_type': 'out_invoice',
            'invoice_date': datetime.now(),
            'partner_id': self.guest.id,
            'currency_id': self.currency_id.id,
            'amount_total':self.total_amount,
            'invoice_line_ids':invoice_line_ids
        }])

        return {
            'type':'ir.actions.act_window',
            'name':'invoice',
            'res_model':'account.move',
            'res_id':self.invoice_id.id,
            'target':'current'
        }

