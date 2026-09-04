# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class EducationScholarshipApplication(models.Model):
    _name = "education.scholarship.application"
    _description = "Scholarship Application"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Application Number", required=True, copy=False, readonly=True, default="New")
    student_id = fields.Many2one("education.enrollment", string="Student", required=True, tracking=True)
    scholarship_id = fields.Many2one("education.scholarship", string="Scholarship", required=True, tracking=True)
    application_date = fields.Date(string="Application Date", default=fields.Date.context_today, tracking=True)
    academic_year_id = fields.Many2one("education.academic.year", string="Academic Year", related="student_id.academic_year_id", store=True, readonly=True, tracking=True)
    family_income = fields.Float(string="Family Income", tracking=True)
    document_ids = fields.Many2many("ir.attachment", string="Supporting Documents")
    remarks = fields.Text(string="Remarks")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("review", "Under Review"),
            ("approved", "Approved"),
            ("rejected", "Rejected")
        ], string="Status", default="draft", tracking=True, required=True
    )
    rejection_reason = fields.Text(string="Rejection Reason", tracking=True)
    submitted_criteria_ids = fields.One2many(
        "education.scholarship.application.criteria",
        "application_id",
        string="Submitted Criteria"
    )

    @api.constrains('student_id', 'scholarship_id')
    def _check_unique_application(self):
        for rec in self:
            domain = [
                ('student_id', '=', rec.student_id.id),
                ('scholarship_id', '=', rec.scholarship_id.id),
                ('id', '!=', rec.id),
            ]
            if self.search_count(domain) > 0:
                raise ValidationError("A student cannot apply for the same scholarship twice!")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('education.scholarship.application') or 'New'
        return super(EducationScholarshipApplication, self).create(vals_list)

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_review(self):
        self.write({'state': 'review'})

    def action_approve(self):
        self.write({'state': 'approved'})
        for rec in self:
            if rec.scholarship_id.available_scholarships > 0:
                approved_count = self.search_count([
                    ('scholarship_id', '=', rec.scholarship_id.id),
                    ('state', '=', 'approved')
                ])
                if approved_count >= rec.scholarship_id.available_scholarships:
                    if rec.scholarship_id.state == 'active':
                        rec.scholarship_id.action_close_scholarship()

    def action_reject(self):
        # Could be enhanced to open a wizard to enter reason, but a simple write for now or relying on user to fill it before clicking
        self.write({'state': 'rejected'})
