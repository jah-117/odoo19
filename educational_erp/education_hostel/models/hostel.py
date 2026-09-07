# -*- coding: utf-8 -*-
"""
education_hostel — Hostel Property, Room and Allocation models
==============================================================
Implements:
  - edu.hostel.property  (S6-T09)
  - edu.hostel.room      (S6-T10)
  - edu.hostel.allocation (S6-T11 / S6-T12)
"""
from markupsafe import Markup

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class EduHostelProperty(models.Model):
    """A physical hostel building / block managed by the institution."""

    _name = "edu.hostel.property"
    _description = "Hostel Property"
    _order = "name"

    # ── Basic fields ──────────────────────────────────────────────────────
    name = fields.Char(string="Property Name", required=True)
    block = fields.Char(string="Block / Wing")
    total_capacity = fields.Integer(string="Total Capacity")
    warden_id = fields.Many2one(
        comodel_name="education.faculty",
        string="Warden",
        ondelete="restrict",
        tracking=True,
    )
    active = fields.Boolean(string="Active", default=True)

    # ── Rooms ─────────────────────────────────────────────────────────────
    room_ids = fields.One2many(
        comodel_name="edu.hostel.room",
        inverse_name="property_id",
        string="Rooms",
    )

    # ── Computed counts (stat buttons) ────────────────────────────────────
    room_count = fields.Integer(
        string="Rooms",
        compute="_compute_room_counts",
        store=True,
    )
    occupied_count = fields.Integer(
        string="Occupied",
        compute="_compute_room_counts",
        store=True,
    )

    @api.depends("room_ids", "room_ids.state")
    def _compute_room_counts(self):
        for rec in self:
            rec.room_count = len(rec.room_ids)
            rec.occupied_count = len(
                rec.room_ids.filtered(
                    lambda room: room.state in ("partially_occupied", "occupied")
                )
            )

    def action_view_allocations(self):
        """Open confirmed allocations for rooms in this hostel property."""
        self.ensure_one()
        room_ids = self.room_ids.ids
        return {
            "type": "ir.actions.act_window",
            "name": _("Occupied Allocations — %s") % self.name,
            "res_model": "edu.hostel.allocation",
            "view_mode": "list,form",
            "domain": [
                ("room_id", "in", room_ids),
                ("state", "=", "confirmed"),
            ],
            "context": {
                "default_room_id": room_ids[0] if len(room_ids) == 1 else False,
            },
        }


class EduHostelRoomAmenities(models.Model):
    """ Room types for rooms in the hostel."""

    _name = "edu.hostel.room.amenities"
    _description = "Amenities"

    name = fields.Char("Name", required=True)
    amenity_fee = fields.Float('Fee', required=True, help="Fee for amenity")


class EduHostelRoomType(models.Model):
    """ Room types for rooms in the hostel."""

    _name = "edu.hostel.room.type"
    _description = "Room Types"

    name = fields.Char('Name', required=True)
    fee = fields.Float("Room Fee", required=True, help="Fee for specific room type")


class EduHostelRoom(models.Model):
    """A single room inside a hostel property."""

    _name = "edu.hostel.room"
    _description = "Hostel Room"
    _rec_name = "room_no"
    _order = "property_id, room_no"

    property_id = fields.Many2one(
        comodel_name="edu.hostel.property",
        string="Property",
        required=True,
        ondelete="cascade",
    )
    room_no = fields.Char(string="Room No.", required=True)
    room_type_id = fields.Many2one('edu.hostel.room.type', string="Type", required=True)
    capacity = fields.Integer(string="Capacity", default=1)
    allocation_ids = fields.One2many(
        comodel_name="edu.hostel.allocation",
        inverse_name="room_id",
        string="Allocations",
    )
    occupied_beds = fields.Integer(
        string="Occupied Beds",
        compute="_compute_occupancy",
        store=True,
    )
    available_beds = fields.Integer(
        string="Available Beds",
        compute="_compute_occupancy",
        store=True,
    )
    allocated_student_ids = fields.One2many(
        string="Students",
        comodel_name='education.enrollment',
        inverse_name='room_id',
        compute="__compute_occupancy",
        store=True,
    )
    invoice_ids = fields.One2many(comodel_name='account.move', inverse_name='room_id')
    invoice_count = fields.Integer(compute='_compute_invoice_count')
    is_maintenance = fields.Boolean(string="Under Maintenance")
    amenity_ids = fields.Many2many('edu.hostel.room.amenities', string="Amenities", help=" Amenities in the room")
    state = fields.Selection(
        selection=[
            ("available", "Available"),
            ("partially_occupied", "Partially Occupied"),
            ("occupied", "Occupied"),
            ("maintenance", "Maintenance"),
        ],
        string="State",
        default="available",
        compute="_compute_occupancy",
        store=True,
        required=True,
        tracking=True,
    )
    active = fields.Boolean(string="Active", default=True)

    _unique_room_per_property = models.Constraint(
        "UNIQUE(property_id, room_no)",
        "Room number must be unique within the same property.", )
    base_fee = fields.Float('Base Fee', related="room_type_id.fee", store=True, help="base fee for room type")
    total_fee = fields.Float('Total Fee', compute="_compute_total_fee", store=True,
                             help="total fee for room (base_fee + amenity_fee)")

    @api.depends("capacity", "is_maintenance", "allocation_ids.state")
    def _compute_occupancy(self):
        """Derive availability from confirmed student allocations."""
        for room in self:
            confirmed_allocation = room.allocation_ids.filtered(
                lambda allocation: allocation.state == "confirmed"
            )
            room.allocated_student_ids = [allocation.enrollment_id.id for allocation in confirmed_allocation]
            occupied_beds = len(confirmed_allocation)
            room.occupied_beds = occupied_beds
            room.available_beds = max(room.capacity - occupied_beds, 0)
            if room.is_maintenance:
                room.state = "maintenance"
            elif not occupied_beds:
                room.state = "available"
            elif occupied_beds < room.capacity:
                room.state = "partially_occupied"
            else:
                room.state = "occupied"

    @api.depends('base_fee', 'amenity_ids')
    def _compute_total_fee(self):
        """ compute total fee from base fee and amenities"""
        for room in self:
            room.total_fee = room.base_fee + sum(amenity.amenity_fee for amenity in room.amenity_ids)

    @api.constrains("capacity")
    def _check_capacity(self):
        for room in self:
            if room.capacity < 1:
                raise ValidationError(_("Room capacity must be at least one."))

    def action_view_students(self):
        """ View student details of current room"""
        self.ensure_one()
        return {
            "name": _("Students"),
            "type": "ir.actions.act_window",
            "res_model": "education.enrollment",
            "view_mode": "list,form",
            "domain": [("id", "in", self.allocated_student_ids.ids)],
        }
    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)

    def action_view_invoice(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'invoice',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain':[('id', 'in', self.invoice_ids.ids ), ('allocation_state', '==',"confirmed")],
            'target': 'current'
        }


from datetime import datetime
from dateutil.relativedelta import relativedelta


class EduHostelAllocation(models.Model):
    """Allocation of a student to a hostel room."""

    _name = "edu.hostel.allocation"
    _description = "Hostel Allocation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_from desc, id desc"
    _rec_name = "enrollment_id"

    enrollment_id = fields.Many2one(
        comodel_name="education.enrollment",
        string="Enrollment",
        required=True,
        tracking=True,
    )
    room_id = fields.Many2one(
        comodel_name="edu.hostel.room",
        string="Room",
        required=True,
        tracking=True,
    )

    property_id = fields.Many2one(
        comodel_name="edu.hostel.property",
        string="Property",
        related="room_id.property_id",
        store=True,
        readonly=True,
        tracking=True,
    )

    date_from = fields.Date(
        string="From Date",
        required=True,
        default=fields.Date.today,
        tracking=True,
    )
    date_to = fields.Date(
        string="To Date",
        tracking=True,
    )
    hostel_fee = fields.Float(
        string="Hostel Fee",
        compute="_compute_hostel_fee",
        default=0.0,
        tracking=True,
        help="Total hostel fee amount per person"
    )
    fee_due = fields.Float(
        string="Fee Due",
        compute='_compute_fee_due',
        store=True)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("vacated", "Vacated"),
        ],
        string="State",
        default="draft",
        required=True,
        tracking=True,
    )
    notes = fields.Text(string="Notes")
    current_invoice_id = fields.Many2one(
        comodel_name="account.move",
        string="Current Invoice",
    )
    overdue_invoice_id = fields.Many2one(
        comodel_name="account.move",
        string="Due Invoice",
    )
    invoice_ids = fields.One2many(
        comodel_name='account.move',
        inverse_name="allocation_id",
        string="Invoices"
    )
    previous_invoice_date = fields.Date(
        string="Previous Invoice Date"
    )
    notification_ids = fields.One2many(
        string="Notifications",
        comodel_name='edu.notification.queue',
        inverse_name="allocation_id",
        compute="_send_invoice_notification",
        store=True,
    )

    # ── Constraints ───────────────────────────────────────────────────────
    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for rec in self:
            if rec.date_to and rec.date_from and rec.date_to < rec.date_from:
                raise ValidationError(
                    _("End date (%s) must be on or after start date (%s).")
                    % (rec.date_to, rec.date_from)
                )

    @api.constrains("room_id", "state")
    def _check_room_capacity(self):
        """Protect capacity when allocations are changed outside the UI."""
        for rec in self.filtered(lambda allocation: allocation.state == "confirmed"):
            room = rec.room_id
            if room.is_maintenance:
                raise ValidationError(
                    _("Room '%s' is under maintenance.") % room.room_no
                )
            confirmed_allocations = self.search_count([
                ("room_id", "=", room.id),
                ("state", "=", "confirmed"),
            ])
            if confirmed_allocations > room.capacity:
                raise ValidationError(
                    _("Room '%s' has reached its capacity.") % room.room_no
                )

    @api.depends()
    def _compute_hostel_fee(self):
        """ compute fee for the room"""
        for rec in self:
            rec.hostel_fee = rec.room_id.total_fee
    @api.depends('invoice_ids')
    def _compute_fee_due(self):
        """compute due for allocation"""
        for rec in self:
            rec.fee_due = sum([invoice.amount_residual for invoice in rec.invoice_ids if rec.invoice_ids])

    @api.depends('invoice_ids.state')
    def _send_invoice_notification(self):
        for rec in self:
            if rec.state != "confirmed":
                continue
            invoices = rec.invoice_ids.filtered(lambda invoice: invoice.state == "posted" and  invoice.payment_state == "not_paid")
            if not invoices:
                continue
            rec.current_invoice_id = invoices[0].id
            self.env.ref("education_hostel.invoice_generated").send_mail(rec.id, force_send=True)
#             notification = self.env["edu.notification.queue"].create({
#                 'notif_type': "email",
#                 'recipient_id': self.enrollment_id.student_partner_id.id,
#                 'template_id': self.env.ref("education_financial_management.mail_template_fee_overdue").id,
#                 'subject': "Hostel Fee Payment",
#                 'body' : """
# Your hostel fee invoice is generated. Please make the outstanding payment at the earliest to avoid payment due.
# """,
#             })
#             notification.action_send(),
#             rec.notification_ids = [fields.Command.link(notification.id)]

    def _send_overdue_notifications(self):
        """Send notifications for overdue hostel invoices."""
        today = fields.Date.today()

        allocations = self.search([
            ('state', '=', 'confirmed'),
        ])

        for rec in allocations:
            overdue_invoices = rec.invoice_ids.filtered(
                lambda invoice:
                invoice.state == 'posted'
                and invoice.payment_state in ('not_paid', 'partial')
                and invoice.invoice_date_due
                and invoice.invoice_date_due <= today
            )

            if not overdue_invoices:
                continue
            print(overdue_invoices)
            rec.overdue_invoice_id = overdue_invoices[0].id
            print(rec.overdue_invoice_id)

            self.env.ref(
                'education_hostel.hostel_fee_overdue'
            ).send_mail(rec.id, force_send=True)
    #         notification = self.env['edu.notification.queue'].create({
    #             'notif_type': "email",
    #             'recipient_id': rec.enrollment_id.student_partner_id.id,
    #             'template_id': self.env.ref(
    #                 'education_financial_management.mail_template_fee_overdue'
    #             ).id,
    #             'subject': 'Hostel Fee Payment Overdue',
    #             'body': """
    # Your hostel fee invoice is overdue. Please make the outstanding payment at the earliest to avoid any inconvenience or late payment consequences.
    #
    # If you have already made the payment, please ignore this notification.
    # """
    #         })
    #         notification.action_send()
    #         rec.notification_ids = [fields.Command.link(notification.id)]

    def _create_invoice(self):
        """create invoice"""
        product = self.env.ref("education_hostel.hostel_fee_product")
        invoice_id = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'invoice_date': datetime.now(),
            'partner_id': self.enrollment_id.student_partner_id.id,
            'invoice_date_due': ((self.previous_invoice_date if self.previous_invoice_date else self.date_from) + relativedelta(months=1))
        })

        invoice_id.update({'invoice_line_ids': [fields.Command.create({
            'product_id': product.id,
            'name': "Hostel fee",
            'quantity': 1,
            'price_unit': self.room_id.total_fee,
            'price_subtotal': self.room_id.total_fee})]
        })
        self.invoice_ids = [fields.Command.link(invoice_id.id)]
        self.previous_invoice_date = invoice_id.invoice_date
        return invoice_id.id


    def _check_create_invoice(self):
        """scheduled action to create invoices"""
        today = fields.Date.today()
        for rec in self.search([('state','=','confirmed')]):
            if rec.date_to and rec.date_to > today:
                continue
            if rec.date_from and today < rec.date_from:
                continue
            if not rec.previous_invoice_date:
                # Create the first invoice when allocation starts
                if today >= rec.date_from:
                    rec._create_invoice()
                continue
            next_invoice_date = (rec.previous_invoice_date + relativedelta(months=1))
            if today < next_invoice_date:
                continue
            if rec.date_to and next_invoice_date > rec.date_to:
                continue
            rec._create_invoice()
    # ── Workflow actions ──────────────────────────────────────────────────

    def action_confirm(self):
        """Confirm an allocation if the room has a free bed."""
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("Only draft allocations can be confirmed."))

            # Check the student does not already have an active allocation
            duplicate = self.search(
                [
                    ("enrollment_id", "=", rec.enrollment_id.id),
                    ("state", "=", "confirmed"),
                    ("id", "!=", rec.id),
                ]
            )
            if duplicate:
                raise UserError(
                    _(
                        "Student '%s' already has a confirmed hostel allocation."
                    )
                    % rec.enrollment_id.display_name
                )

            if rec.room_id.is_maintenance:
                raise UserError(
                    _("Room '%s' is under maintenance.") % rec.room_id.room_no
                )
            if rec.room_id.occupied_beds >= rec.room_id.capacity:
                raise UserError(
                    _("Room '%s' has reached its capacity.") % rec.room_id.room_no
                )

            rec.state = "confirmed"
            rec.message_post(
                body=Markup(_(
                    "Allocation confirmed. Room <b>%s</b> occupancy was updated."
                )
                            % rec.room_id.room_no
                            ))

    def action_vacate(self):
        """Vacate allocation and update room occupancy."""
        for rec in self:
            if rec.state != "confirmed":
                raise UserError(_("Only confirmed allocations can be vacated."))
            rec.state = "vacated"
            rec.message_post(
                body=Markup(_(
                    "Allocation vacated. Room <b>%s</b> occupancy was updated."
                )
                            % rec.room_id.room_no
                            ))

    def action_reset_draft(self):
        """Reset allocation back to draft."""
        for rec in self:
            if rec.state == "confirmed":
                # The room occupancy is recomputed when the state changes.
                rec.state = "draft"
                rec.message_post(body=_("Allocation reset to draft."))

    def action_create_invoice(self):
        """Create an invoice."""
        for rec in self:
            invoice_id  = rec._create_invoice()
            return {
                'type': 'ir.actions.act_window',
                'name': 'invoice',
                'view_mode': 'form',
                'res_model': 'account.move',
                'res_id': invoice_id,
                'target': 'current'
            }
