# -*- coding: utf-8 -*-
"""
edu.exam.reevaluation.request — Student revaluation requests
============================================================
Students can submit revaluation requests from the portal.
Administrators review requests with approve / reject actions.
Approved requests enable re-evaluation and marks updating.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError, AccessError


class EduExamReevaluationRequest(models.Model):
    """Revaluation request submitted by student for an exam subject result."""

    _name = "edu.exam.reevaluation.request"
    _description = "Exam Revaluation Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"
    _rec_name = "display_name"

    name = fields.Char(
        string="Request Reference",
        readonly=True,
        copy=False,
        default="New",
    )
    result_id = fields.Many2one(
        "edu.exam.result",
        string="Exam Result",
        required=True,
        ondelete="cascade",
        index=True,
        tracking=True,
    )
    enrollment_id = fields.Many2one(
        "education.enrollment",
        string="Student",
        related="result_id.enrollment_id",
        store=True,
        readonly=True,
        index=True,
    )
    student_name = fields.Char(
        string="Student Name",
        related="result_id.student_name",
        store=True,
        readonly=True,
    )
    exam_id = fields.Many2one(
        "edu.exam",
        string="Examination",
        related="result_id.exam_id",
        store=True,
        readonly=True,
        index=True,
    )
    class_id = fields.Many2one(
        "education.class",
        string="Class",
        related="result_id.class_id",
        store=True,
        readonly=True,
    )
    subject_id = fields.Many2one(
        "education.subject",
        string="Subject",
        related="result_id.subject_id",
        store=True,
        readonly=True,
    )
    current_marks = fields.Float(
        string="Original Marks",
        related="result_id.marks_obtained",
        store=True,
        readonly=True,
    )
    max_marks = fields.Float(
        string="Max Marks",
        related="result_id.max_marks",
        store=True,
        readonly=True,
    )
    grade = fields.Char(
        string="Grade",
        related="result_id.grade",
        store=True,
        readonly=True,
    )
    reason = fields.Text(
        string="Reason for Revaluation",
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("revaluated", "Re-evaluated"),
            ("rejected", "Rejected"),
        ],
        string="Status",
        default="pending",
        required=True,
        tracking=True,
        index=True,
    )
    admin_notes = fields.Text(
        string="Admin Remarks",
        tracking=True,
    )
    reviewed_by_id = fields.Many2one(
        "res.users",
        string="Reviewed By",
        readonly=True,
        tracking=True,
    )
    review_date = fields.Datetime(
        string="Reviewed On",
        readonly=True,
    )
    request_date = fields.Datetime(
        string="Request Date",
        default=fields.Datetime.now,
        readonly=True,
    )
    display_name = fields.Char(
        compute="_compute_display_name",
        store=True,
    )

    _sql_constraints = [
        (
            "unique_pending_reevaluation_per_result",
            "CHECK(1=1)",
            "A revaluation request is already recorded.",
        ),
    ]

    @api.constrains("result_id")
    def _check_exam_not_closed(self):
        for rec in self:
            if rec.result_id and rec.result_id.exam_id and rec.result_id.exam_id.state == "closed":
                raise ValidationError(_("Revaluation requests cannot be submitted for a closed examination."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("result_id"):
                result = self.env["edu.exam.result"].browse(vals["result_id"])
                if result.exists() and result.exam_id and result.exam_id.state == "closed":
                    raise ValidationError(_("Revaluation requests cannot be submitted for a closed examination."))
            if vals.get("name", "New") == "New":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("edu.exam.reevaluation.request")
                    or f"REV/{fields.Date.today().year}/{self.search_count([]) + 1:04d}"
                )
        return super().create(vals_list)

    @api.depends("student_name", "subject_id", "name")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.name} — {rec.student_name or '?'} ({rec.subject_id.name or '?'})"

    def action_approve(self):
        """Approve revaluation request and reset result to draft for mark re-entry."""
        for rec in self:
            if rec.state != "pending":
                continue
            rec.write({
                "state": "approved",
                "reviewed_by_id": self.env.uid,
                "review_date": fields.Datetime.now(),
            })
            # Put result back to draft so teacher/admin can update marks
            rec.result_id.write({"state": "draft"})
            # Audit log entry
            self.env["edu.exam.result.history"].sudo().create({
                "result_id": rec.result_id.id,
                "old_marks": rec.result_id.marks_obtained,
                "new_marks": rec.result_id.marks_obtained,
                "changed_by_id": self.env.uid,
                "change_date": fields.Datetime.now(),
                "reason": _("[REVALUATION APPROVED] %s") % (rec.reason or ""),
            })
            rec.message_post(body=_("Revaluation request approved. Result unlocked for mark entry."))

    def action_reject(self):
        """Open rejection wizard to specify reason, or reject if reason provided in context."""
        if not self.env.user.has_group("education_security.group_education_admin"):
            raise AccessError(_("Only administrators can reject revaluation requests."))

        if len(self) == 1 and not self.env.context.get("skip_wizard"):
            return {
                "type": "ir.actions.act_window",
                "name": _("Reject Revaluation Request"),
                "res_model": "edu.exam.reevaluation.reject.wizard",
                "view_mode": "form",
                "target": "new",
                "context": {
                    "default_request_id": self.id,
                    "default_rejection_reason": self.admin_notes or "",
                },
            }

        reason_text = self.env.context.get("rejection_reason") or _("Request rejected by administrator.")
        for rec in self:
            if rec.state != "pending":
                continue
            rec.write({
                "state": "rejected",
                "admin_notes": rec.admin_notes or reason_text,
                "reviewed_by_id": self.env.uid,
                "review_date": fields.Datetime.now(),
            })
            rec.message_post(body=_("Revaluation request rejected. Remarks: %s") % (rec.admin_notes or reason_text))


    result_state = fields.Selection(
        related="result_id.state",
        string="Result State",
        readonly=True,
    )

    def action_revaluate(self):
        """Open the mark entry wizard for this request's exam and class."""
        self.ensure_one()
        return self.result_id.action_revaluate()

    def action_publish_result(self):
        """Publish / re-publish the result after re-evaluation and mark request as revaluated."""
        if not self.env.user.has_group("education_security.group_education_admin"):
            raise AccessError(_("Only administrators can publish examination results."))
        for rec in self:
            rec.result_id.action_publish()
            rec.write({"state": "revaluated"})
            rec.message_post(body=_("Revaluation completed and updated examination result published."))


