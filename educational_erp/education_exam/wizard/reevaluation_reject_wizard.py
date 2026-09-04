# -*- coding: utf-8 -*-
"""
edu.exam.reevaluation.reject.wizard — Revaluation rejection reason popup wizard
================================================================================
Prompts the administrator to specify a mandatory reason/remarks when rejecting
a student revaluation request, which will be visible to the student on the portal.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError, AccessError


class EduExamReevaluationRejectWizard(models.TransientModel):
    _name = "edu.exam.reevaluation.reject.wizard"
    _description = "Reject Revaluation Request Wizard"

    request_id = fields.Many2one(
        "edu.exam.reevaluation.request",
        string="Revaluation Request",
        required=True,
        readonly=True,
    )
    student_name = fields.Char(
        string="Student Name",
        related="request_id.student_name",
        readonly=True,
    )
    exam_id = fields.Many2one(
        "edu.exam",
        string="Examination",
        related="request_id.exam_id",
        readonly=True,
    )
    subject_id = fields.Many2one(
        "education.subject",
        string="Subject",
        related="request_id.subject_id",
        readonly=True,
    )
    student_reason = fields.Text(
        string="Student Request Reason",
        related="request_id.reason",
        readonly=True,
    )
    rejection_reason = fields.Text(
        string="Rejection Reason",
        required=True,
        help="Provide the reason for rejection. This will be shown to the student on the portal.",
    )

    def action_confirm_reject(self):
        """Confirm rejection with mandatory admin reason."""
        self.ensure_one()
        if not self.env.user.has_group("education_security.group_education_admin"):
            raise AccessError(_("Only administrators can reject revaluation requests."))

        reason_text = (self.rejection_reason or "").strip()
        if not reason_text:
            raise ValidationError(_("Please provide a reason for rejecting this revaluation request."))

        request_rec = self.request_id
        if request_rec.state != "pending":
            raise UserError(_("Only pending revaluation requests can be rejected."))

        request_rec.write({
            "state": "rejected",
            "admin_notes": reason_text,
            "reviewed_by_id": self.env.uid,
            "review_date": fields.Datetime.now(),
        })

        request_rec.message_post(
            body=_("Revaluation request rejected by %s. Reason: %s")
            % (self.env.user.name, reason_text),
            author_id=self.env.user.partner_id.id,
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Revaluation Rejected"),
                "message": _("The revaluation request for %s (%s) has been rejected.")
                % (self.student_name, self.subject_id.name),
                "type": "warning",
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
