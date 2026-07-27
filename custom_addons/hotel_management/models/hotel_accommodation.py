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
    payment_state = fields.Selection(selection=PAYMENT_STATUS, default='to_pay',
                                     compute='_compute_payment_state')
    name = fields.Char(string="Accommodation Number", required=True, copy=False,
                       readonly=True, default=lambda self: _('New'))

    guest = fields.Many2one(comodel_name='res.partner',
                            string='Guest',
                            tracking=True,
                            required=True,
                            help="Accommodating guest, invoice will be issued in this partner's name."
                            )
    is_online_booking = fields.Boolean(string="Is Online Booking",default=False)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.context.get('allowed_company_ids')[0])
    currency_id = fields.Many2one('res.currency', string="Currency", related='company_id.currency_id')
    number_of_guests = fields.Integer(string="Number of Guests", default=1,
                                      help="Total number of guests staying.")
    other_guests = fields.One2many(comodel_name='accommodation.guests.lines',
                                   inverse_name='accommodation_ids',
                                   help="Provide name and details of all other guests.")
    check_in = fields.Datetime(string="Check-In Date & Time", readonly=True,
                               tracking=True, store=True,
                               help="Check In time.")
    check_out = fields.Datetime(string="Check-Out Date & Time", readonly=True,
                                tracking=True, store=True,
                                help="Check out time.")
    bed_type = fields.Selection(default='single',
                                selection=BED_TYPES,tracking=True,
                                string="Bed Type", required=True,
                                help="Type of bed required.")
    facilities = fields.Many2many(string="Facilities", comodel_name='room.facility',
                                  store=True,help="Facilities required in room.")
    room_id = fields.Many2one(comodel_name='hotel.room', string="Room",
                              required=True,
                              readonly=False,
                              help="Available rooms based on the requirements.")
    available_room_ids = fields.Many2many(comodel_name='hotel.room',
                                          compute='_compute_available_room_ids')
    color_code = fields.Selection(selection=[('yellow','Yellow'),('red','Red'),('none','None')],default='none',
                                  compute='_compute_color_code')
    id_proofs = fields.One2many(
        comodel_name='ir.attachment',inverse_name='res_id',
        domain=[('res_model', '=', 'hotel.accommodation')],
        string="ID-Proofs")
    expected_days = fields.Integer(string="Expected Days", default="1",
                                   help="Number of Days the guest is expected to stay.")
    expected_date = fields.Date(string="Expected Date of Check-Out",
                                compute='_compute_expected_date', store=True,
                                help="Expected date of check out based on expected days.")
    payment_line_ids = fields.One2many(comodel_name='payment.line',
                                       inverse_name='accommodation_id',
                                       readonly=True,)
    total_amount = fields.Monetary(currency_field='currency_id', default=0, readonly=True,
                                   help="Total amount to be invoiced(Including rent and food)")
    invoice_id = fields.Many2one(comodel_name='account.move')
    active = fields.Boolean(string='Active',default=True)

    @api.model_create_multi
    def create(self, vals):
        """
        creates sequence number for accommodation once drafted
        :return: trigger parent.create()
        """

        for val in vals:
            if val.get('name', _("New")) == _("New"):

                val['name'] = (self.env['ir.sequence'].with_company(val.get('company_id'))
                               .next_by_code('acc.seq') or _("New"))
        return super().create(vals)

    @api.depends('expected_date', 'check_in')
    def _compute_expected_date(self):
        """
        computes the expected date of check out based on expected days staying
        """
        for rec in self:
            if not rec.check_in:
                continue
            rec.expected_date = rec.check_in + timedelta(days=rec.expected_days)

    def _compute_available_room_ids(self):
        """
        computes the available rooms based on room availablity and bed_type
        """
        self.available_room_ids = self.env['hotel.room'].search([
            ('state', '=', 'available'),
            ('bed', '=', self.bed_type)
        ])

    @api.onchange('facilities', 'bed_type')
    def _calculate_domain(self):
        """
        if facilities or bed_types changes, finds the available rooms
        """
        self.room_id = False
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

    def _compute_color_code(self):
        """
        compute color code based on expected date and state
        """
        for rec in self:
            if rec.expected_date:
                rec.color_code = 'yellow' if rec.expected_date == datetime.today() else 'red' if rec.expected_date == datetime.today() and rec.state != 'check_out' else 'none'
            else:
                rec.color_code = 'none'

    @api.model
    def _send_todays_checkout_mails(self):
        """
        fetch valid records based on state = 'check_in'
        and send email to those having expected_date = today
        """
        valid_accommodations = self.search([('state', '=', 'check_in')])
        mail_template = self.env.ref('hotel_management.checkout_remainder_mail_template')
        for accommodation in valid_accommodations:
            if accommodation.expected_date.strftime('%Y-%m-%d') == datetime.today().strftime('%Y-%m-%d'):
                mail_template.send_mail(accommodation.id, force_send=True)

    @api.model
    def _archive_canceled_records(self):
        """
        fetch all canceled records
        and archive those are canceled for two days
        when an accommodation is canceled that date is marked in check_out
        """

        valid_accommodations = self.search([('state', '=', 'cancel')])
        for accommodation in valid_accommodations:
            if (datetime.today() - accommodation.check_out).days > 1:
                accommodation.active = False

    @api.model
    def _update_rent(self):
        """
        fetch all check_in records and update their rent
        """
        valid_accommodations = self.search([('state', '=', 'check_in')])
        for accommodation in valid_accommodations:
            for payment_line in accommodation.payment_line_ids:
                if payment_line.product_id.id == self.env.ref('hotel_management.room_rent').id:
                    fields.Command.update(payment_line.id,
                                          {'quantity': payment_line.quantity + 1})
                    payment_line.calculate_subtotal()

    def _compute_payment_state(self):
        """
        change payment status based on payment of invoice created
        """
        for accommodation in self:
            if not accommodation.invoice_id:
                accommodation.payment_state = 'to_pay'
                continue
            if accommodation.invoice_id.payment_count > 0:
                accommodation.payment_state = 'paid'
            else:
                accommodation.payment_state = 'to_pay'

    def check_in_guest(self):
        """
        action check_in_guest: check in button action
        verify details of number of guests are available or not
        change the status of accommodation
        change room availability and record check in time
        check for id proofs
        :return: ir.action.client (sticky notification) for mismatch in guest list and id proofs
        """

        if self.number_of_guests > 1 and self.number_of_guests != len(self.other_guests) + 1:
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
        self.state = 'check_in'
        self.check_in = datetime.now()
        self.room_id.state = 'not_available'
        self.payment_state = 'to_pay'
        self.write({'payment_line_ids': [fields.Command.create({
            'product_id': self.env.ref('hotel_management.room_rent').id,
            'description': 'Room Rent',
            'quantity': 1,
            'unit_of_measure': 'Day',
            'unit_price': self.room_id.rent,
            'subtotal': self.room_id.rent
        })]})
        self.total_amount = sum([payment_line.subtotal for payment_line in self.payment_line_ids])
        if not self.id_proofs:
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
        """
        action: check_out_guest, button action for check out
        create rent payment line based stayed number of days and calculate total amount payable
        changes accommodation state to check_out
        changes room availability and record check out time
        :return:
        """
        self.state = 'check_out'
        self.check_out = datetime.now()
        quantity = 1 if (self.check_out - self.check_in).days < 1 else (self.check_out - self.check_in).days
        for payment_line in self.payment_line_ids:
            if payment_line.product_id.id == self.env.ref('hotel_management.room_rent').id:
                fields.Command.update(payment_line.id,
                                      {'quantity': quantity, 'subtotal': quantity * self.room_id.rent})
        self.total_amount = sum([payment_line.subtotal for payment_line in self.payment_line_ids])
        self.room_id.state = 'available'
        self.invoice_id = self.env['account.move'].create([{
            'move_type': 'out_invoice',
            'invoice_date': datetime.now(),
            'partner_id': self.guest.id,
            'currency_id': self.currency_id.id,
            'amount_total': self.total_amount,
        }])
        self.invoice_id.update({'invoice_line_ids': [fields.Command.create({
            'product_id': payment_line.product_id.id,
            'name': payment_line.description,
            'quantity': payment_line.quantity,
            'price_unit': payment_line.unit_price,
            'price_subtotal': payment_line.subtotal,
        }) for payment_line in self.payment_line_ids]})
        return {
            'type': 'ir.actions.act_window',
            'name': 'invoice',
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'target': 'current'
        }

    def action_cancel(self):
        """
        cancel the accommodation
        only draft can be canceled
        """
        self.state = 'cancel'
        self.room_id.state = 'available'
        self.check_out = datetime.now()






class HHotelAccommodation(models.Model):
    _inherit = 'hotel.accommodation'

    order_count = fields.Integer(compute='_compute_order_count')
    invoice_count = fields.Integer(default='1')

    def _compute_order_count(self):
        for accommodation in self:
            accommodation.order_count = self.env['order.food'].search_count(
                [('accommodation_id', '=', accommodation.id)])

    def action_open_orders(self):
        if self.order_count < 1:
            return {
                'name': _('Orders'),
                'type': 'ir.actions.act_window',
                'res_model': 'order.food',
                'view_mode': 'form',
                'context': {
                    'default_accommodation_id': self.id
                }
            }
        return {
            'name': _('Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'order.food',
            'domain': [('accommodation_id', '=', self.id)],
            'view_mode': 'list',
            'context': {
                'default_accommodation_id': self.id
            }
        }

    def action_open_invoices(self):
        if self.invoice_id:
            return {
                'name': _('Invoices'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': self.invoice_id.id
            }
        return False
