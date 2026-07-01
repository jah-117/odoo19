from odoo import models,fields

class HrDepartment(models.Model):
    _inherit = 'hr.department'

    is_under_staffed = fields.Boolean(default=False,store=True)


