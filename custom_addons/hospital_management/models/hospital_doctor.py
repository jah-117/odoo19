from odoo import fields, models

class HospitalDoctor(models.Model):
    _inherit = 'hr.employee'

    is_doctor = fields.Boolean(default=False,string='Is a doctor')
    is_available = fields.Boolean(default=False,string='Is available')
    specialization = fields.Char(string="Specialization")