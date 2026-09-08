# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import AccessError


class DisciplineCase(models.Model):
    _name = "education.discipline.case"
    _description = "Discipline Case"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Reference", required=True, copy=False, readonly=True, default="New"
    )
    student_id = fields.Many2one(
        "education.enrollment", string="Reported Against", required=True, tracking=True
    )
    date = fields.Date(
        string="Date", required=True, default=fields.Date.context_today, tracking=True
    )
    violation_type_id = fields.Many2one(
        "education.violation.type", string="Violation Type", required=True, tracking=True
    )
    description = fields.Text(string="Description/Reason")
    reported_by_id = fields.Many2one(
        "res.users",
        string="Reported By",
        default=lambda self: self.env.user,
        tracking=True,
    )
    severity = fields.Selection(
        [
            ("minor", "Minor"),
            ("moderate", "Moderate"),
            ("major", "Major"),
            ("critical", "Critical"),
        ],
        string="Severity",
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("reported", "Reported"),
            ("under_review", "Under Review"),
            ("action_taken", "Action Taken"),
            ("resolved", "Resolved"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
    )
    action_id = fields.Many2one(
        "education.disciplinary.action", string="Disciplinary Action", tracking=True
    )
    action_date = fields.Date(string="Action Date", tracking=True)
    remarks = fields.Text(string="Remarks")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "education.discipline.case"
                ) or "New"
        return super(DisciplineCase, self).create(vals_list)

    def action_report(self):
        for record in self:
            if record.reported_by_id != self.env.user:
                raise AccessError(
                    "You can only report discipline cases created by you."
                )

            record.sudo().write({
                "state": "reported",
            })

    def action_under_review(self):
        for record in self:
            record.state = "under_review"

    def action_take_action(self):
        for record in self:
            record.state = "action_taken"

    def action_resolve(self):
        for record in self:
            record.state = "resolved"

    def action_draft(self):
        for record in self:
            record.state = "draft"
