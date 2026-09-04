# -*- coding: utf-8 -*-
"""
edu.fee.plan  — Fee plan header (S5-T01)
edu.fee.line  — Fee component lines within a plan
=========================================================
A fee plan is assigned to an enrollment. On activation the system
auto-generates an account.move (customer invoice) per fee line.
"""
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EduFeePlan(models.Model):
    """Fee structure: collection of chargeable components for a programme/year."""

    _name = "edu.fee.plan"
    _description = "Fee Plan"
    _inherit = ["mail.thread"]
    _order = "academic_year_id desc, name"
    _rec_name = "name"

    currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        depends=["company_id"],
        string="Currency",
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        readonly=True,
    )
    name = fields.Char(string="Plan Name", required=True, tracking=True)
    academic_year_id = fields.Many2one(
        "education.academic.year",
        string="Academic Year",
        required=True,
        index=True,
    )
    program_id = fields.Many2one(
        "education.program",
        string="Programme",
        help="Leave blank to apply to all programmes.",
    )
    class_ids = fields.Many2many(
        "education.class",
        "edu_fee_plan_class_rel",
        "fee_plan_id",
        "class_id",
        string="Applicable Classes",
        help="Leave blank to apply to all classes in the academic year.",
    )
    line_ids = fields.One2many(
        "edu.fee.line",
        "fee_plan_id",
        string="Fee Components",
    )
    total_amount = fields.Float(
        string="Total Amount",
        compute="_compute_total",
        store=True,
    )

    # ── Schedule & Installments ──────────────────────────────────────────
    schedule_type = fields.Selection(
        selection=[
            ("one_time", "One-time / Annual"),
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly / Term"),
            ("semester", "Semester-wise (Bi-annual)"),
            ("custom", "Custom Installments"),
        ],
        string="Schedule Type",
        required=True,
        default="one_time",
        tracking=True,
        help="Configurable payment schedule for invoice generation.",
    )
    auto_generate_invoices = fields.Boolean(
        string="Auto-generate Invoices via Cron",
        default=True,
        help="If enabled, daily cron will automatically generate invoices for scheduled installments when their due date arrives.",
    )
    installment_ids = fields.One2many(
        "edu.fee.plan.installment",
        "fee_plan_id",
        string="Installment Schedule",
        copy=True,
    )
    total_installment_percentage = fields.Float(
        string="Total Percentage",
        compute="_compute_installment_totals",
        store=True,
    )

    active = fields.Boolean(default=True)
    notes = fields.Text(string="Notes")

    @api.depends("line_ids.amount")
    def _compute_total(self):
        for rec in self:
            rec.total_amount = sum(rec.line_ids.mapped("amount"))

    @api.depends("installment_ids.percentage")
    def _compute_installment_totals(self):
        for rec in self:
            rec.total_installment_percentage = sum(rec.installment_ids.mapped("percentage"))

    @api.constrains("line_ids")
    def _check_lines(self):
        for rec in self:
            for line in rec.line_ids:
                if line.amount <= 0:
                    raise ValidationError(
                        _("Amount must be greater than zero for component '%s'.")
                        % line.component
                    )

    @api.constrains("schedule_type", "installment_ids")
    def _check_installment_percentages(self):
        for rec in self:
            if rec.installment_ids and rec.schedule_type != "one_time":
                total_pct = sum(rec.installment_ids.mapped("percentage"))
                if abs(total_pct - 100.0) > 0.05:
                    raise ValidationError(
                        _("Total installment percentage must equal 100%% for plan '%s'. Current total is %.2f%%.")
                        % (rec.name, total_pct)
                    )

    def action_generate_installments(self):
        """Generate default installment template lines based on schedule_type and academic year dates."""
        self.ensure_one()
        start_date = self.academic_year_id.date_start or fields.Date.today()
        end_date = self.academic_year_id.date_end

        lines = []
        if self.schedule_type == "one_time":
            first_due = self.line_ids.sorted("due_date")[:1].due_date or start_date
            lines.append((0, 0, {
                "sequence": 10,
                "name": _("Annual / Full Fee"),
                "percentage": 100.0,
                "due_date": first_due,
            }))
        elif self.schedule_type == "semester":
            sem2_date = start_date + relativedelta(months=6)
            if end_date and sem2_date > end_date:
                sem2_date = start_date + (end_date - start_date) / 2
            lines.append((0, 0, {
                "sequence": 10,
                "name": _("Semester 1 Fee"),
                "percentage": 50.0,
                "due_date": start_date,
            }))
            lines.append((0, 0, {
                "sequence": 20,
                "name": _("Semester 2 Fee"),
                "percentage": 50.0,
                "due_date": sem2_date,
            }))
        elif self.schedule_type == "quarterly":
            for i in range(4):
                due = start_date + relativedelta(months=3 * i)
                if end_date and due > end_date:
                    due = end_date
                lines.append((0, 0, {
                    "sequence": (i + 1) * 10,
                    "name": _("Term %d Fee") % (i + 1),
                    "percentage": 25.0,
                    "due_date": due,
                }))
        elif self.schedule_type == "monthly":
            months_count = 12
            if end_date:
                diff_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
                if 1 <= diff_months <= 24:
                    months_count = diff_months
            pct_per_month = round(100.0 / months_count, 2)
            remaining_pct = 100.0
            for i in range(months_count):
                due = start_date + relativedelta(months=i)
                pct = pct_per_month if i < months_count - 1 else round(remaining_pct, 2)
                remaining_pct -= pct
                month_name = due.strftime("%B %Y")
                lines.append((0, 0, {
                    "sequence": (i + 1) * 10,
                    "name": _("Month %d (%s)") % (i + 1, month_name),
                    "percentage": pct,
                    "due_date": due,
                }))
        elif self.schedule_type == "custom":
            if not self.installment_ids:
                lines.append((0, 0, {
                    "sequence": 10,
                    "name": _("Installment 1"),
                    "percentage": 100.0,
                    "due_date": start_date,
                }))

        if lines:
            self.installment_ids = [(5, 0, 0)] + lines


class EduFeePlanInstallment(models.Model):
    """Installment schedule template line within a fee plan."""

    _name = "edu.fee.plan.installment"
    _description = "Fee Plan Installment Template"
    _order = "sequence, due_date, id"

    fee_plan_id = fields.Many2one(
        "edu.fee.plan",
        string="Fee Plan",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Installment / Period", required=True)
    percentage = fields.Float(
        string="Percentage (%)",
        required=True,
        default=0.0,
        help="Percentage of the total fee plan allocated to this installment.",
    )
    due_date = fields.Date(string="Due Date")
    amount = fields.Float(
        string="Estimated Amount",
        compute="_compute_amount",
        help="Estimated fee amount based on plan total.",
    )
    currency_id = fields.Many2one(
        related="fee_plan_id.currency_id",
        string="Currency",
    )

    @api.depends("fee_plan_id.total_amount", "percentage")
    def _compute_amount(self):
        for rec in self:
            rec.amount = round((rec.fee_plan_id.total_amount * rec.percentage) / 100.0, 2)


class EduFeeLine(models.Model):
    """One chargeable component within a fee plan."""

    _name = "edu.fee.line"
    _description = "Fee Component"
    _order = "due_date, sequence"

    fee_plan_id = fields.Many2one(
        "edu.fee.plan",
        string="Fee Plan",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10)
    component = fields.Char(string="Component", required=True)
    fee_type = fields.Selection(
        selection=[
            ("tuition", "Tuition Fee"),
            ("lab", "Lab / Practical Fee"),
            ("library", "Library Fee"),
            ("transport", "Transport Fee"),
            ("hostel", "Hostel Fee"),
            ("exam", "Examination Fee"),
            ("activity", "Activity / Sports Fee"),
            ("other", "Other"),
        ],
        string="Type",
        required=True,
        default="tuition",
    )
    amount = fields.Float(string="Amount", required=True, default=0.0)
    due_date = fields.Date(string="Due Date")
    account_id = fields.Many2one(
        "account.account",
        string="Revenue Account",
        help="Income account for this fee component. "
             "If blank, the default income account will be used.",
        domain="[('account_type', 'like', 'income')]",
    )
    tax_ids = fields.Many2many(
        "account.tax",
        string="Taxes",
        domain="[('type_tax_use', '=', 'sale')]",
    )
