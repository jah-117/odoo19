# -*- coding: utf-8 -*-
"""
Extends education.enrollment with fee management (S5-T02, S5-T03, S5-T04)
=========================================================================
- Adds fee_plan_id, invoice_ids, fee_state to enrollment
- Auto-generates account.move on generate_invoice() action
- Scholarship deduction applied as a credit line on the invoice
- Outstanding fee SQL view (S5-T08)
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class EducationEnrollmentFee(models.Model):
    """Extend enrollment with fee plan + installment schedule + invoice link."""

    _inherit = "education.enrollment"

    # ── Fee plan ─────────────────────────────────────────────────────────
    fee_plan_id = fields.Many2one(
        "edu.fee.plan",
        string="Fee Plan",
        index=True,
        tracking=True,
    )
    scholarship_amount = fields.Float(
        string="Scholarship Deduction",
        default=0.0,
        help="Amount deducted from invoice as scholarship credit. (S5-T04)",
    )

    # ── Scheduled Installments ───────────────────────────────────────────
    installment_ids = fields.One2many(
        "edu.enrollment.installment",
        "enrollment_id",
        string="Fee Installments",
        copy=True,
    )
    installment_count = fields.Integer(
        compute="_compute_installment_count",
        string="Installment Count",
    )

    # ── Invoice link ──────────────────────────────────────────────────────
    invoice_ids = fields.One2many(
        "account.move",
        "enrollment_id",
        string="Fee Invoices",
        domain=[("move_type", "=", "out_invoice")],
    )
    invoice_count = fields.Integer(
        compute="_compute_invoice_info",
        string="Invoices",
    )
    fee_state = fields.Selection(
        selection=[
            ("not_invoiced", "Not Invoiced"),
            ("invoiced", "Invoiced"),
            ("partial", "Partially Paid"),
            ("paid", "Fully Paid"),
            ("overdue", "Overdue"),
        ],
        string="Fee Status",
        compute="_compute_invoice_info",
        store=True,
        default="not_invoiced",
    )
    total_fee = fields.Float(
        compute="_compute_invoice_info",
        string="Total Fee",
        store=True,
    )
    amount_paid = fields.Float(
        compute="_compute_invoice_info",
        string="Amount Paid",
        store=True,
    )
    amount_due = fields.Float(
        compute="_compute_invoice_info",
        string="Amount Due",
        store=True,
    )

    # ── Computed ──────────────────────────────────────────────────────────

    def _compute_installment_count(self):
        for rec in self:
            rec.installment_count = len(rec.installment_ids)

    @api.depends(
        "invoice_ids",
        "invoice_ids.state",
        "invoice_ids.payment_state",
        "invoice_ids.amount_total",
        "invoice_ids.amount_residual",
        "installment_ids",
        "installment_ids.fee_state",
    )
    def _compute_invoice_info(self):
        today = fields.Date.today()
        for rec in self:
            invoices = rec.invoice_ids.filtered(
                lambda i: i.state != "cancel"
            )
            rec.invoice_count = len(invoices)
            total = sum(invoices.mapped("amount_total"))
            residual = sum(invoices.mapped("amount_residual"))
            rec.total_fee = total
            rec.amount_paid = total - residual
            rec.amount_due = residual
            if not invoices:
                rec.fee_state = "not_invoiced"
            elif residual == 0:
                rec.fee_state = "paid"
            elif residual < total:
                rec.fee_state = "partial"
            elif any(
                i.invoice_date_due and i.invoice_date_due < today
                for i in invoices
                if i.payment_state not in ("paid", "in_payment")
            ) or any(inst.fee_state == "overdue" for inst in rec.installment_ids):
                rec.fee_state = "overdue"
            else:
                rec.fee_state = "invoiced"

    # ── Onchange & Sync ───────────────────────────────────────────────────

    @api.onchange("fee_plan_id")
    def _onchange_fee_plan_id(self):
        if self.fee_plan_id:
            self.action_sync_installments()

    def action_sync_installments(self):
        """Synchronize installment schedule from fee plan to enrollment."""
        for rec in self:
            if not rec.fee_plan_id:
                continue
            # Keep existing installments that already have an active invoice
            existing_invoiced = rec.installment_ids.filtered(
                lambda inst: inst.invoice_id and inst.invoice_id.state != "cancel"
            )
            invoiced_template_ids = existing_invoiced.mapped("plan_installment_id").ids

            new_lines = []
            if rec.fee_plan_id.installment_ids:
                for plan_inst in rec.fee_plan_id.installment_ids:
                    if plan_inst.id not in invoiced_template_ids:
                        new_lines.append((0, 0, {
                            "plan_installment_id": plan_inst.id,
                            "sequence": plan_inst.sequence,
                            "name": plan_inst.name,
                            "percentage": plan_inst.percentage,
                            "due_date": plan_inst.due_date,
                        }))
            else:
                first_due = (
                    rec.fee_plan_id.line_ids.sorted("due_date")[:1].due_date
                    if rec.fee_plan_id.line_ids
                    else fields.Date.today()
                )
                new_lines.append((0, 0, {
                    "sequence": 10,
                    "name": _("Annual / Full Fee"),
                    "percentage": 100.0,
                    "due_date": first_due,
                }))

            # Remove uninvoiced installments and add fresh lines
            uninvoiced = rec.installment_ids.filtered(
                lambda inst: not inst.invoice_id or inst.invoice_id.state == "cancel"
            )
            commands = [(2, inst.id) for inst in uninvoiced] + new_lines
            rec.installment_ids = commands

    # ── Actions ───────────────────────────────────────────────────────────

    def action_generate_invoice(self):
        """Generate invoice for the next pending installment (or all if single-installment)."""
        self.ensure_one()
        if not self.fee_plan_id:
            raise UserError(_("Assign a Fee Plan before generating an invoice."))
        if not self.student_partner_id:
            raise UserError(
                _("Student does not have a portal account. "
                  "Approve the application first.")
            )

        if not self.installment_ids:
            self.action_sync_installments()

        pending_installments = self.installment_ids.filtered(
            lambda inst: not inst.invoice_id or inst.invoice_id.state == "cancel"
        )
        if not pending_installments:
            raise UserError(
                _("All installments are already invoiced for this enrollment. "
                  "Cancel existing invoices first to re-generate.")
            )

        # Generate invoice for the first pending installment
        target_installment = pending_installments[0]
        return target_installment.action_generate_invoice()

    def action_generate_all_invoices(self):
        """Generate invoices for all pending installments for this enrollment."""
        self.ensure_one()
        if not self.fee_plan_id:
            raise UserError(_("Assign a Fee Plan before generating an invoice."))
        if not self.student_partner_id:
            raise UserError(
                _("Student does not have a portal account. "
                  "Approve the application first.")
            )

        if not self.installment_ids:
            self.action_sync_installments()

        pending_installments = self.installment_ids.filtered(
            lambda inst: not inst.invoice_id or inst.invoice_id.state == "cancel"
        )
        if not pending_installments:
            raise UserError(_("No pending installments to invoice."))

        generated_invoices = self.env["account.move"]
        for inst in pending_installments:
            res = inst.action_generate_invoice()
            if res and res.get("res_id"):
                generated_invoices |= self.env["account.move"].browse(res["res_id"])

        return {
            "type": "ir.actions.act_window",
            "name": _("Fee Invoices"),
            "res_model": "account.move",
            "view_mode": "list,form",
            "domain": [("id", "in", generated_invoices.ids)],
            "context": {"default_partner_id": self.student_partner_id.id, "default_move_type": "out_invoice"},
        }

    def action_view_invoices(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Fee Invoices"),
            "res_model": "account.move",
            "view_mode": "list,form",
            "domain": [("enrollment_id", "=", self.id), ("move_type", "=", "out_invoice")],
            "context": {"default_partner_id": self.student_partner_id.id, "default_move_type": "out_invoice", "default_enrollment_id": self.id},
        }

    def _get_default_income_account(self):
        """Return a sensible default income account."""
        account = self.env["account.account"].search([
            ("account_type", "=", "income"),
            ("company_ids", "in", self.env.company.id),
        ], limit=1)
        if not account:
            raise UserError(
                _("No income account found. Please configure your Chart of Accounts.")
            )
        return account


class EduEnrollmentInstallment(models.Model):
    """Specific scheduled installment for an enrollment."""

    _name = "edu.enrollment.installment"
    _description = "Student Fee Installment"
    _order = "sequence, due_date, id"

    enrollment_id = fields.Many2one(
        "education.enrollment",
        string="Enrollment",
        required=True,
        ondelete="cascade",
        index=True,
    )
    plan_installment_id = fields.Many2one(
        "edu.fee.plan.installment",
        string="Fee Plan Installment Template",
        ondelete="set null",
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Installment / Period", required=True)
    due_date = fields.Date(string="Due Date")
    percentage = fields.Float(string="Percentage (%)", default=0.0)
    currency_id = fields.Many2one(
        related="enrollment_id.fee_plan_id.currency_id",
        string="Currency",
        readonly=True,
    )
    amount = fields.Float(
        string="Amount",
        compute="_compute_amount",
        store=True,
        help="Net installment fee amount after scholarship deduction.",
    )
    invoice_id = fields.Many2one(
        "account.move",
        string="Invoice",
        ondelete="set null",
        domain=[("move_type", "=", "out_invoice")],
    )
    fee_state = fields.Selection(
        selection=[
            ("draft", "Pending"),
            ("invoiced", "Invoiced"),
            ("partial", "Partially Paid"),
            ("paid", "Paid"),
            ("overdue", "Overdue"),
        ],
        string="Status",
        compute="_compute_fee_state",
        store=True,
        default="draft",
    )

    @api.depends("enrollment_id.fee_plan_id.total_amount", "enrollment_id.scholarship_amount", "percentage")
    def _compute_amount(self):
        for rec in self:
            if rec.enrollment_id and rec.enrollment_id.fee_plan_id:
                base_fee = rec.enrollment_id.fee_plan_id.total_amount
                scholarship = rec.enrollment_id.scholarship_amount or 0.0
                net_total = max(0.0, base_fee - scholarship)
                rec.amount = round((net_total * rec.percentage) / 100.0, 2)
            else:
                rec.amount = 0.0

    @api.depends("invoice_id", "invoice_id.state", "invoice_id.payment_state", "invoice_id.amount_residual", "due_date")
    def _compute_fee_state(self):
        today = fields.Date.today()
        for rec in self:
            inv = rec.invoice_id
            if not inv or inv.state == "cancel":
                if rec.due_date and rec.due_date < today:
                    rec.fee_state = "overdue"
                else:
                    rec.fee_state = "draft"
            elif inv.payment_state in ("paid", "in_payment"):
                rec.fee_state = "paid"
            elif inv.amount_residual < inv.amount_total:
                rec.fee_state = "partial"
            elif (inv.invoice_date_due and inv.invoice_date_due < today) or (rec.due_date and rec.due_date < today):
                rec.fee_state = "overdue"
            else:
                rec.fee_state = "invoiced"

    def action_generate_invoice(self):
        """Generate customer invoice (account.move) for this specific installment."""
        self.ensure_one()
        enrollment = self.enrollment_id
        if not enrollment.fee_plan_id:
            raise UserError(_("Assign a Fee Plan to the enrollment first."))
        if not enrollment.student_partner_id:
            raise UserError(
                _("Student does not have a portal account. "
                  "Approve the application first.")
            )
        if self.invoice_id and self.invoice_id.state != "cancel":
            raise UserError(
                _("An invoice already exists for installment '%s'. "
                  "Cancel it first to re-generate.") % self.name
            )

        pct = self.percentage / 100.0 if self.percentage > 0 else 1.0
        move_lines = []
        for line in enrollment.fee_plan_id.line_ids:
            line_amount = round(line.amount * pct, 2)
            if line_amount > 0:
                move_lines.append((0, 0, {
                    "name": f"{line.component} — {self.name}",
                    "quantity": 1,
                    "price_unit": line_amount,
                    "account_id": (
                        line.account_id.id
                        or enrollment._get_default_income_account().id
                    ),
                    "tax_ids": [(6, 0, line.tax_ids.ids)],
                }))

        # Scholarship deduction proportional to installment percentage
        if enrollment.scholarship_amount > 0:
            scholarship_part = round(enrollment.scholarship_amount * pct, 2)
            if scholarship_part > 0:
                move_lines.append((0, 0, {
                    "name": _("Scholarship Deduction — %s") % self.name,
                    "quantity": 1,
                    "price_unit": -scholarship_part,
                    "account_id": enrollment._get_default_income_account().id,
                }))

        invoice = self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": enrollment.student_partner_id.id,
            "enrollment_id": enrollment.id,
            "installment_id": self.id,
            "invoice_date": fields.Date.today(),
            "invoice_date_due": self.due_date or fields.Date.today(),
            "narration": _("Fee invoice for %s — %s (%s)") % (
                enrollment.student_name,
                enrollment.fee_plan_id.name,
                self.name,
            ),
            "invoice_line_ids": move_lines,
        })
        self.invoice_id = invoice.id
        enrollment.message_post(
            body=_("Fee invoice %s generated for installment '%s' (total: %.2f).")
            % (invoice.name, self.name, invoice.amount_total)
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Fee Invoice"),
            "res_model": "account.move",
            "res_id": invoice.id,
            "view_mode": "form",
            "target": "current",
        }


class AccountMove(models.Model):
    """Extend account.move with enrollment link (S5-T02)."""

    _inherit = "account.move"

    enrollment_id = fields.Many2one(
        "education.enrollment",
        string="Student Enrollment",
        index=True,
        ondelete="set null",
    )
    installment_id = fields.Many2one(
        "edu.enrollment.installment",
        string="Fee Installment",
        index=True,
        ondelete="set null",
    )
    student_name = fields.Char(
        related="enrollment_id.student_name",
        store=True,
        readonly=True,
        string="Student",
    )
    class_id = fields.Many2one(
        "education.class",
        related="enrollment_id.class_id",
        store=True,
        readonly=True,
    )
    academic_year_id = fields.Many2one(
        "education.academic.year",
        related="enrollment_id.academic_year_id",
        store=True,
        readonly=True,
    )
    invoice_line_labels = fields.Char(
        string="Invoice Line Labels",
        compute="_compute_invoice_line_labels",
        store=True,
        readonly=True,
        help="Unique labels/descriptions from all invoice lines, comma-separated.",
    )

    @api.depends("invoice_line_ids", "invoice_line_ids.name", "invoice_line_ids.display_type")
    def _compute_invoice_line_labels(self):
        """Collect unique, non-empty invoice-line names (preserving first-seen order)."""
        for move in self:
            seen = []
            for line in move.invoice_line_ids:
                # Skip section/note lines and lines with blank labels
                if line.display_type in ("line_section", "line_note"):
                    continue
                label = (line.name or "").strip()
                if label and label not in seen:
                    seen.append(label)
            move.invoice_line_labels = ", ".join(seen) if seen else False


class EduFeeOutstandingReport(models.Model):
    """SQL view — all active enrollments with outstanding fees (S5-T08)."""

    _name = "edu.fee.outstanding"
    _description = "Outstanding Fee Report"
    _auto = False
    _order = "amount_due desc"

    enrollment_id = fields.Many2one("education.enrollment", string="Enrollment", readonly=True)
    student_name = fields.Char(string="Student", readonly=True)
    class_id = fields.Many2one("education.class", string="Class", readonly=True)
    academic_year_id = fields.Many2one("education.academic.year", string="Year", readonly=True)
    fee_plan_id = fields.Many2one("edu.fee.plan", string="Fee Plan", readonly=True)
    total_fee = fields.Float(string="Total Fee", readonly=True)
    amount_paid = fields.Float(string="Paid", readonly=True)
    amount_due = fields.Float(string="Outstanding", readonly=True)
    fee_state = fields.Char(string="Status", readonly=True)
    invoice_date_due = fields.Date(string="Due Date", readonly=True)

    def init(self):
        self.env.cr.execute("""
            DROP VIEW IF EXISTS edu_fee_outstanding;
            CREATE VIEW edu_fee_outstanding AS (
                SELECT
                    e.id                        AS id,
                    e.id                        AS enrollment_id,
                    e.student_name              AS student_name,
                    e.class_id                  AS class_id,
                    e.academic_year_id          AS academic_year_id,
                    e.fee_plan_id               AS fee_plan_id,
                    COALESCE(e.total_fee, 0)    AS total_fee,
                    COALESCE(e.amount_paid, 0)  AS amount_paid,
                    COALESCE(e.amount_due, 0)   AS amount_due,
                    e.fee_state                 AS fee_state,
                    MIN(am.invoice_date_due)    AS invoice_date_due
                FROM education_enrollment e
                LEFT JOIN account_move am
                    ON am.enrollment_id = e.id
                    AND am.move_type = 'out_invoice'
                    AND am.state != 'cancel'
                WHERE e.state = 'active'
                  AND COALESCE(e.amount_due, 0) > 0
                GROUP BY e.id, e.student_name, e.class_id,
                         e.academic_year_id, e.fee_plan_id,
                         e.total_fee, e.amount_paid, e.amount_due, e.fee_state
            )
        """)
