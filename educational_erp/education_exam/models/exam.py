# -*- coding: utf-8 -*-
"""
edu.exam — Exam scheduling (S4-T01)
====================================
Header record for an examination event.
Holds dates, linked classes, subject schedule lines, seating, invigilators
and a state machine: draft → scheduled → ongoing → result_published → closed.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError, AccessError


class EduExam(models.Model):
    """Exam header — one exam event (e.g. Mid-Term Nov 2026)."""

    _name = "edu.exam"
    _description = "Examination"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_from desc, id desc"
    _rec_name = "name"

    # ── Identity ──────────────────────────────────────────────────────────
    name = fields.Char(
        string="Exam Name",
        required=True,
        tracking=True,
    )
    code = fields.Char(
        string="Exam Code",
        readonly=True,
        copy=False,
        default="New",
    )
    exam_type = fields.Selection(
        selection=[
            ("unit_test", "Unit Test"),
            ("mid_term", "Mid-Term"),
            ("final", "Final Exam"),
            ("practical", "Practical"),
            ("supplementary", "Supplementary"),
        ],
        string="Exam Type",
        required=True,
        default="mid_term",
        tracking=True,
    )
    is_paid_exam = fields.Boolean(
        string="Paid Examination",
        help="Check this, if the exam is a paid examination",
        default=False,
    )
    exam_fee = fields.Float(
        string="Exam Fee",
        help="Cost of attending the examination",
    )
    hall_ticket = fields.Boolean(
        string="Hall Ticket",
        help="Check this, if the candidates need a hall ticket to attend the examination",
        default=False,
    )

    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("scheduled", "Scheduled"),
            ("ongoing", "Ongoing"),
            ("valuation", "Valuation"),
            ("result_published", "Results Published"),
            ("closed", "Closed"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
    )
    published_at = fields.Datetime(
        string="Results Published Date",
        readonly=True,
        copy=False,
        tracking=True,
    )

    # ── Dates & Scope ─────────────────────────────────────────────────────
    academic_year_id = fields.Many2one(
        "education.academic.year",
        string="Academic Year",
        required=True,
        index=True,
    )
    date_from = fields.Date(
        string="Start Date",
        required=True,
    )
    date_to = fields.Date(
        string="End Date",
        required=True,
    )
    class_ids = fields.Many2many(
        "education.class",
        "edu_exam_class_rel",
        "exam_id",
        "class_id",
        string="Classes",
    )
    grade_system_id = fields.Many2one(
        "edu.exam.grade.system",
        string="Grading System",
        required=True,
        help="Grading system scale to evaluate results for this examination. If blank, the default scale is used.",
    )

    # ── Related lines ─────────────────────────────────────────────────────
    subject_line_ids = fields.One2many(
        "edu.exam.subject",
        "exam_id",
        string="Subject Schedule",
    )
    seating_ids = fields.One2many(
        "edu.exam.seating",
        "exam_id",
        string="Seating Plan",
    )
    invigilator_ids = fields.One2many(
        "edu.exam.invigilator",
        "exam_id",
        string="Invigilators",
    )
    result_ids = fields.One2many(
        "edu.exam.result",
        "exam_id",
        string="Results",
    )

    # ── Stats ─────────────────────────────────────────────────────────────
    subject_count = fields.Integer(
        compute="_compute_counts",
        string="Subjects",
    )
    seating_count = fields.Integer(
        compute="_compute_counts",
        string="Seats Assigned",
    )
    result_count = fields.Integer(
        compute="_compute_counts",
        string="Results",
    )
    registered_enrollment_ids = fields.Many2many(comodel_name="education.enrollment", string="Students")
    invoice_ids = fields.One2many(comodel_name="account.move", inverse_name="exam_id", string="Invoices")
    invoice_count = fields.Integer(string="Invoices", compute='_compute_invoice_count')
    enrollment_count = fields.Integer(string="Enrollments", compute='_compute_invoice_count')

    notes = fields.Text(string="Instructions / Notes")
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        readonly=True,
    )

    # ── ORM ───────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "New") == "New":
                vals["code"] = (
                    self.env["ir.sequence"].next_by_code("edu.exam") or "New"
                )
        return super().create(vals_list)

    # ── Computed ──────────────────────────────────────────────────────────
    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)
            rec.enrollment_count = len(rec.registered_enrollment_ids)
    @api.onchange("is_paid_exam")
    def _onchange_is_paid_exam(self):
        self.hall_ticket = self.is_paid_exam
    @api.depends("subject_line_ids", "seating_ids", "result_ids")
    def _compute_counts(self):
        for rec in self:
            rec.subject_count = len(rec.subject_line_ids)
            rec.seating_count = len(rec.seating_ids)
            rec.result_count = len(rec.result_ids)

    def action_view_invoices(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Invoices",
            "res_model": "account.move",
            "view_mode": "list,form",
            "domain": [
                ("id", "in", self.invoice_ids.ids),
                ("invoice_type", "=", "exam_fee"),
            ],
            "context": {
                "default_move_type": "out_invoice",
                "default_exam_id": self.id,
            },
        }

    def action_view_enrollments(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Enrollments",
            "res_model": "education.enrollment",
            "view_mode": "list,form",
            "domain": [
                ("id", "in", self.registered_enrollment_ids.ids),
            ],
        }

    def action_view_seats(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Seats',
            'res_model': 'edu.exam.seating',
            'view_mode': 'list,form',
            'domain': [('exam_id', '=', self.id)],
            'context': {'default_exam_id': self.id},
        }


    # ── Constraints ───────────────────────────────────────────────────────

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_to < rec.date_from:
                raise ValidationError(
                    _("End Date must be on or after Start Date.")
                )
    # ── State machine ─────────────────────────────────────────────────────

    def action_schedule(self):
        self.ensure_one()
        if not self.subject_line_ids or self.state not in ['draft', 'closed_registration']:
            raise UserError(_("Add at least one subject before scheduling exam '%s'.") % self.name)
        self.write({"state": "scheduled"})

    def action_start(self):
        self.filtered(lambda r: r.state == "scheduled").write({"state": "ongoing"})

    def action_start_valuation(self):
        self.filtered(lambda r: r.state == "ongoing").write({"state": "valuation"})

    def action_publish_results(self):
        if not self.env.user.has_group("education_security.group_education_admin"):
            raise AccessError(_("Only administrators can publish examination results."))
        for rec in self.filtered(lambda r: r.state in ("ongoing", "valuation", "result_published", "closed")):
            draft_results = rec.result_ids.filtered(lambda r: r.state == "draft")
            if not rec.result_ids and rec.state in ("ongoing", "valuation"):
                raise UserError(
                    _("No results entered for exam '%s'.") % rec.name
                )
            now = fields.Datetime.now()
            if draft_results:
                draft_results.write({"state": "published", "published_at": now})
            if rec.state in ("ongoing", "valuation"):
                rec.write({"state": "result_published", "published_at": now})
            rec.message_post(
                body=_("Results published / republished (%d record(s)).") % len(draft_results or rec.result_ids)
            )

    def action_close(self):
        self.filtered(
            lambda r: r.state == "result_published"
        ).write({"state": "closed"})

    def action_reset_draft(self):
        for rec in self:
            if rec.state != "scheduled":
                raise UserError(_("Only examinations in 'Scheduled' state can be reset to Draft."))
            rec.write({"state": "draft"})


    def action_enter_marks(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Enter Marks"),
            "res_model": "edu.exam.mark.entry.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_exam_id": self.id,
                "default_class_id": self.class_ids[0].id if self.class_ids else False,
            },
        }

    def action_print_results(self):
        self.ensure_one()
        if not self.result_ids:
            raise UserError(_("No results found for examination '%s'.") % self.name)
        return self.env.ref("education_exam.action_report_exam_results_tabulation").report_action(self, config=False)





class EduExamSubject(models.Model):
    """One subject (paper) within an exam — date, time, marks, room."""

    _name = "edu.exam.subject"
    _description = "Exam Subject Schedule"
    _order = "exam_date, exam_time"

    exam_id = fields.Many2one(
        "edu.exam",
        string="Exam",
        required=True,
        ondelete="cascade",
        index=True,
    )
    subject_id = fields.Many2one(
        "education.subject",
        string="Subject",
        required=True,
        ondelete="restrict",
        index=True,
    )
    exam_date = fields.Date(
        string="Date",
        required=True,
    )
    exam_time = fields.Float(
        string="Start Time",
        required=True,
        default=9.0,
        help="24-hour format, e.g. 9.5 = 09:30",
    )
    duration_hours = fields.Float(
        string="Duration (hrs)",
        default=3.0,
    )
    max_marks = fields.Float(
        string="Max Marks",
        required=True,
        default=100.0,
    )
    pass_marks = fields.Float(
        string="Pass Marks",
        required=True,
        compute="_compute_pass_mark"
    )
    classroom_id = fields.Many2one(
        "edu.classroom",
        string="Exam Hall",
        required=True,
    )

    @api.constrains("pass_marks", "max_marks")
    def _check_marks(self):
        for rec in self:
            if rec.pass_marks > rec.max_marks:
                raise ValidationError(
                    _("Pass marks cannot exceed max marks for subject '%s'.") % rec.subject_id.name
                )
            if rec.max_marks <= 0:
                raise ValidationError(_("Max marks must be greater than zero."))

    @api.depends("exam_id.grade_system_id")
    def _compute_pass_mark(self):
        for rec in self:
            if rec.exam_id:
                least_mark_line =  rec.exam_id.grade_system_id.line_ids.filtered(lambda line: line.pass_fail != 'fail').sorted('grade_point')[0]
                rec.pass_marks = (least_mark_line.min_percentage * rec.max_marks)/100
            else:
                rec.pass_marks = False

    @api.onchange("max_marks")
    def _onchange_max_marks(self):
        self._compute_pass_mark()
