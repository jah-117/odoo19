from odoo import models, fields

class ScholarshipApplicationCriteria(models.Model):
    _name = 'education.scholarship.application.criteria'
    _description = 'Scholarship Application Submitted Criteria'

    application_id = fields.Many2one(
        'education.scholarship.application',
        string='Application',
        required=True,
        ondelete='cascade'
    )
    eligibility_criteria_id = fields.Many2one(
        'scholarship.eligibility.criteria',
        string='Eligibility Criterion',
        required=True
    )
    student_value = fields.Char(
        string='Submitted Value',
        required=True
    )
    document_ids = fields.Many2many(
        'ir.attachment',
        string='Supporting Documents'
    )
