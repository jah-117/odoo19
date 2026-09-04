# -*- coding: utf-8 -*-
"""
edu.exam.result.revaluate.wizard — Dedicated single-result revaluation mark update wizard
========================================================================================
Opens directly from an individual exam result or approved revaluation request.
Displays the exact student, examination, class, and prominent subject context.
Enables the teacher/evaluator to input the revised score, change reason, and save/publish.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class EduExamResultRevaluateWizard(models.TransientModel):
    _name = "edu.exam.result.revaluate.wizard"
    _description = "Revaluate Single Result Wizard"

    result_id = fields.Many2one(
        "edu.exam.result",
        string="Exam Result",
        required=True,
        readonly=True,
    )
    exam_id = fields.Many2one(
        "edu.exam",
        string="Examination",
        related="result_id.exam_id",
        readonly=True,
    )
    student_name = fields.Char(
        string="Student Name",
        related="result_id.student_name",
        readonly=True,
    )
    class_id = fields.Many2one(
        "education.class",
        string="Class",
        related="result_id.class_id",
        readonly=True,
    )
    subject_id = fields.Many2one(
        "education.subject",
        string="Subject",
        related="result_id.subject_id",
        readonly=True,
    )
    current_marks = fields.Float(
        string="Original / Current Marks",
        related="result_id.marks_obtained",
        readonly=True,
    )
    max_marks = fields.Float(
        string="Max Marks",
        related="result_id.max_marks",
        readonly=True,
    )
    pass_marks = fields.Float(
        string="Pass Marks",
        related="result_id.pass_marks",
        readonly=True,
    )
    current_grade = fields.Char(
        string="Current Grade",
        related="result_id.grade",
        readonly=True,
    )
    student_reason = fields.Text(
        string="Student Reason for Revaluation",
        compute="_compute_student_reason",
        readonly=True,
    )
    new_marks = fields.Float(
        string="Revised Marks",
        required=True,
        default=0.0,
    )
    absent = fields.Boolean(
        string="Mark as Absent",
        default=False,
    )
    change_reason = fields.Text(
        string="Reason for Mark Revision",
    )
    publish_result = fields.Boolean(
        string="Publish Result Now",
        default=True,
        help="If checked, marks are saved and result status is set to Published immediately.",
    )

    @api.depends("result_id")
    def _compute_student_reason(self):
        for rec in self:
            approved_req = rec.result_id.reevaluation_ids.filtered(lambda r: r.state == "approved")[:1]
            if approved_req:
                rec.student_reason = approved_req.reason
            else:
                latest_req = rec.result_id.reevaluation_ids.sorted(key=lambda r: r.id, reverse=True)[:1]
                rec.student_reason = latest_req.reason if latest_req else _("No student request text.")

    @api.constrains("new_marks", "absent")
    def _check_new_marks(self):
        for rec in self:
            if not rec.absent:
                if rec.new_marks < 0:
                    raise ValidationError(_("Marks obtained cannot be negative."))
                if rec.max_marks and rec.new_marks > rec.max_marks:
                    raise ValidationError(
                        _("Revised marks (%.1f) cannot exceed maximum marks (%.1f) for %s.")
                        % (rec.new_marks, rec.max_marks, rec.subject_id.name)
                    )

    def action_confirm_revaluation(self):
        """Update result marks, log audit history, and optionally publish."""
        self.ensure_one()
        result = self.result_id
        reason_text = (self.change_reason or "").strip() or _("Revaluation mark update.")
        is_admin = self.env.user.has_group("education_security.group_education_admin")
        should_publish = bool(self.publish_result and is_admin)
        vals = {
            "marks_obtained": 0.0 if self.absent else self.new_marks,
            "absent": self.absent,
            "_change_reason": reason_text,
            "state": "published" if should_publish else "draft",
        }
        result.write(vals)

        # Mark approved revaluation requests as re-evaluated
        approved_requests = result.reevaluation_ids.filtered(lambda r: r.state == "approved")
        if approved_requests:
            approved_requests.sudo().write({"state": "revaluated"})
            for req in approved_requests:
                req.sudo().message_post(
                    body=_(
                        "Revaluation completed by %s. Revised Marks: %.1f (Old: %.1f). Remarks: %s"
                    )
                    % (
                        self.env.user.name,
                        result.marks_obtained,
                        self.current_marks,
                        reason_text,
                    ),
                    author_id=self.env.user.partner_id.id,
                )

        # Post message to exam chatter
        if result.exam_id:
            result.exam_id.sudo().message_post(
                body=_(
                    "Revaluation applied by %s for %s (%s). New Marks: %.1f (Old: %.1f). Remarks: %s"
                )
                % (
                    self.env.user.name,
                    self.student_name,
                    self.subject_id.name,
                    result.marks_obtained,
                    self.current_marks,
                    (self.change_reason or "").strip() or _("None"),
                ),
                author_id=self.env.user.partner_id.id,
            )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Revaluation Saved"),
                "message": _("Marks for %s in %s have been updated.") % (self.student_name, self.subject_id.name),
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
