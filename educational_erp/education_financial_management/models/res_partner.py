from odoo import api, fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"

    enrollment_ids = fields.One2many(
        "education.enrollment",
        "student_partner_id",
        string="Enrollments",
    )
