from odoo import fields,models

class HrEmployee(models.Model):
    _inherit = 'hr.employee'


    employee_type_id = fields.Many2one('hr.employee.type',string='Employee Type')
