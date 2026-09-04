# -*- coding: utf-8 -*-
"""
edu.exam.result — Mark entry, grade computation, rank (S4-T04, S4-T05)
=======================================================================
One result record per student per subject per exam.
Grade, percentage, pass/fail and class rank are all computed fields.
Every marks change is recorded in edu.exam.result.history.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError


# ── Grade helper ──────────────────────────────────────────────────────────

def _compute_grade(percentage):
    """Return letter grade from percentage score."""
    if percentage >= 90:
        return "A+"
    elif percentage >= 80:
        return "A"
    elif percentage >= 70:
        return "B"
    elif percentage >= 60:
        return "C"
    elif percentage >= 50:
        return "D"
    else:
        return "F"


class EduExamResult(models.Model):
    """Single exam result: one student, one subject, one exam."""

    _name = "edu.exam.result"
    _description = "Exam Result"
    _order = "exam_id, class_id, student_name"
    _rec_name = "display_name"

    display_name = fields.Char(
        compute="_compute_display_name",
        store=True,
    )

    # ── Core links ────────────────────────────────────────────────────────
    exam_id = fields.Many2one(
        "edu.exam",
        string="Exam",
        required=True,
        ondelete="cascade",
        index=True,
    )
    enrollment_id = fields.Many2one(
        "education.enrollment",
        string="Student",
        required=True,
        ondelete="restrict",
        index=True,
    )
    student_name = fields.Char(
        related="enrollment_id.student_name",
        store=True,
        readonly=True,
    )
    class_id = fields.Many2one(
        "education.class",
        related="enrollment_id.class_id",
        store=True,
        readonly=True,
    )
    subject_id = fields.Many2one(
        "education.subject",
        string="Subject",
        required=True,
        ondelete="restrict",
        index=True,
    )

    # ── Marks ─────────────────────────────────────────────────────────────
    marks_obtained = fields.Float(
        string="Marks Obtained",
        default=0.0,
        tracking=True,
    )
    max_marks = fields.Float(
        string="Max Marks",
        required=True,
        default=100.0,
    )
    pass_marks = fields.Float(
        string="Pass Marks",
        required=True,
        default=40.0,
    )

    # ── Computed grade fields ─────────────────────────────────────────────
    percentage = fields.Float(
        string="Percentage (%)",
        compute="_compute_grade_fields",
        store=True,
        digits=(5, 2),
    )
    grade = fields.Char(
        string="Grade",
        compute="_compute_grade_fields",
        store=True,
    )
    grade_point = fields.Float(
        string="Grade Point",
        compute="_compute_grade_fields",
        store=True,
        digits=(4, 2),
    )
    grade_remarks = fields.Char(
        string="Remarks",
        compute="_compute_grade_fields",
        store=True,
    )
    pass_fail = fields.Selection(
        selection=[
            ("pass", "Pass"),
            ("fail", "Fail"),
            ("absent", "Absent"),
        ],
        string="Result",
        compute="_compute_grade_fields",
        store=True,
    )
    rank = fields.Integer(
        string="Rank",
        compute="_compute_rank",
        store=True,
        help="Rank within the same exam, class and subject.",
    )

    # ── Status ────────────────────────────────────────────────────────────
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("published", "Published"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
    )
    published_at = fields.Datetime(
        string="Published Date",
        readonly=True,
        copy=False,
        index=True,
    )
    absent = fields.Boolean(
        string="Absent",
        default=False,
        help="Check if student was absent for this paper.",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        related="exam_id.company_id",
        store=True,
        readonly=True,
    )


    history_ids = fields.One2many(
        "edu.exam.result.history",
        "result_id",
        string="Change History",
    )
    history_count = fields.Integer(
        compute="_compute_history_count",
    )
    reevaluation_ids = fields.One2many(
        "edu.exam.reevaluation.request",
        "result_id",
        string="Revaluation Requests",
    )
    reevaluation_count = fields.Integer(
        compute="_compute_reevaluation_count",
        string="Revaluations",
    )
    has_approved_reevaluation = fields.Boolean(
        compute="_compute_reevaluation_status",
        string="Approved for Revaluation",
    )
    latest_reevaluation_state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("revaluated", "Re-evaluated"),
            ("rejected", "Rejected"),
        ],
        compute="_compute_reevaluation_status",
        string="Revaluation Status",
    )

    _exam_enrollment_subject_uniq = models.Constraint(
        "UNIQUE(exam_id, enrollment_id, subject_id)",
        "A result for this student and subject already exists in this exam.",
    )

    @api.depends("reevaluation_ids", "reevaluation_ids.state")
    def _compute_reevaluation_status(self):
        for rec in self:
            latest = rec.reevaluation_ids.sorted(key=lambda r: r.id, reverse=True)[:1]
            rec.latest_reevaluation_state = latest.state if latest else False
            rec.has_approved_reevaluation = any(r.state == "approved" for r in rec.reevaluation_ids)

    @api.depends("reevaluation_ids")
    def _compute_reevaluation_count(self):
        for rec in self:
            rec.reevaluation_count = len(rec.reevaluation_ids)

    def action_revaluate(self):
        """Open the dedicated revaluation mark update wizard for this result."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Revaluate Marks — %s") % self.subject_id.name,
            "res_model": "edu.exam.result.revaluate.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_result_id": self.id,
                "default_new_marks": self.marks_obtained,
                "default_absent": self.absent,
            },
        }

    def action_publish(self):
        """Publish or re-publish result after revaluation and mark approved requests as revaluated."""
        if not self.env.user.has_group("education_security.group_education_admin"):
            raise AccessError(_("Only administrators can publish examination results."))
        self.write({
            "state": "published",
            "published_at": fields.Datetime.now(),
        })
        self.reevaluation_ids.filtered(lambda r: r.state == "approved").write({"state": "revaluated"})

    def action_view_reevaluations(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Revaluation Requests"),
            "res_model": "edu.exam.reevaluation.request",
            "view_mode": "list,form",
            "domain": [("result_id", "=", self.id)],
            "context": {"default_result_id": self.id},
        }

    # ── ORM overrides ─────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        now = fields.Datetime.now()
        for vals in vals_list:
            if vals.get("state") == "published" and not vals.get("published_at"):
                vals["published_at"] = now
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("state") == "published" and not vals.get("published_at"):
            vals["published_at"] = fields.Datetime.now()
        change_reason = vals.pop("_change_reason", None) or self.env.context.get("change_reason", "")
        if "marks_obtained" in vals:
            for rec in self:
                old = rec.marks_obtained
                new = vals["marks_obtained"]
                if old != new:
                    self.env["edu.exam.result.history"].sudo().create({
                        "result_id": rec.id,
                        "old_marks": old,
                        "new_marks": new,
                        "changed_by_id": self.env.uid,
                        "change_date": fields.Datetime.now(),
                        "reason": change_reason or "",
                    })
        return super().write(vals)

    # ── Computed ──────────────────────────────────────────────────────────

    @api.depends("marks_obtained", "max_marks", "pass_marks", "absent", "exam_id.grade_system_id")
    def _compute_grade_fields(self):
        grade_system_model = self.env["edu.exam.grade.system"]
        for rec in self:
            if rec.absent:
                rec.percentage = 0.0
                rec.grade = "AB"
                rec.grade_point = 0.0
                rec.grade_remarks = "Absent"
                rec.pass_fail = "absent"
                continue

            pct = (rec.marks_obtained / rec.max_marks * 100) if rec.max_marks else 0.0
            rec.percentage = pct

            scale = rec.exam_id.grade_system_id
            if not scale:
                domain = [("is_default", "=", True)]
                if rec.company_id:
                    domain = [("is_default", "=", True), "|", ("company_id", "=", rec.company_id.id), ("company_id", "=", False)]
                scale = grade_system_model.search(domain, limit=1)
                if not scale:
                    scale = grade_system_model.search([], limit=1)

            if scale:
                info = scale.get_grade_info(pct)
                rec.grade = info["grade"]
                rec.grade_point = info["grade_point"]
                rec.grade_remarks = info["description"]
                rec.pass_fail = "pass" if rec.marks_obtained >= rec.pass_marks and info["pass_fail"] == "pass" else "fail"
            else:
                rec.grade = _compute_grade(pct)
                rec.grade_point = 4.0 if pct >= 90 else (3.7 if pct >= 80 else (3.0 if pct >= 70 else (2.0 if pct >= 60 else (1.0 if pct >= 50 else 0.0))))
                rec.grade_remarks = "Outstanding" if pct >= 90 else ("Excellent" if pct >= 80 else ("Very Good" if pct >= 70 else ("Good" if pct >= 60 else ("Satisfactory" if pct >= 50 else "Fail"))))
                rec.pass_fail = "pass" if rec.marks_obtained >= rec.pass_marks else "fail"

    @api.depends("exam_id", "class_id", "subject_id", "marks_obtained", "absent")
    def _compute_rank(self):
        """Rank within exam + class + subject, highest marks = rank 1."""
        groups = {}
        for rec in self:
            key = (rec.exam_id.id, rec.class_id.id, rec.subject_id.id)
            groups.setdefault(key, []).append(rec)

        for key, records in groups.items():
            sorted_recs = sorted(
                records,
                key=lambda r: (-r.marks_obtained if not r.absent else -9999),
            )
            rank = 1
            for r in sorted_recs:
                r.rank = rank if not r.absent else 0
                rank += 1

    @api.depends("student_name", "subject_id", "exam_id")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = (
                f"{rec.student_name or '?'} / {rec.subject_id.name or '?'}"
            )

    @api.depends("history_ids")
    def _compute_history_count(self):
        for rec in self:
            rec.history_count = len(rec.history_ids)

    # ── Constraints ───────────────────────────────────────────────────────

    @api.constrains("marks_obtained", "max_marks")
    def _check_marks(self):
        for rec in self:
            if not rec.absent:
                if rec.marks_obtained < 0:
                    raise ValidationError(_("Marks obtained cannot be negative."))
                if rec.marks_obtained > rec.max_marks:
                    raise ValidationError(
                        _(
                            "Marks obtained (%.1f) cannot exceed max marks (%.1f) "
                            "for %s — %s."
                        ) % (
                            rec.marks_obtained,
                            rec.max_marks,
                            rec.student_name,
                            rec.subject_id.name,
                        )
                    )


class EduExamResultHistory(models.Model):
    """Audit log — every marks change is recorded here (S4-T06)."""

    _name = "edu.exam.result.history"
    _description = "Exam Result Change History"
    _order = "change_date desc"

    result_id = fields.Many2one(
        "edu.exam.result",
        string="Result",
        required=True,
        ondelete="cascade",
        index=True,
    )
    old_marks = fields.Float(string="Old Marks")
    new_marks = fields.Float(string="New Marks")
    changed_by_id = fields.Many2one(
        "res.users",
        string="Changed By",
    )
    change_date = fields.Datetime(
        string="Changed On",
        default=fields.Datetime.now,
    )
    reason = fields.Text(string="Reason / Note")
    delta = fields.Float(
        string="Change",
        compute="_compute_delta",
        store=True,
    )

    @api.depends("old_marks", "new_marks")
    def _compute_delta(self):
        for rec in self:
            rec.delta = rec.new_marks - rec.old_marks
