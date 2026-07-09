from odoo import fields, models
from odoo.exceptions import ValidationError


class EmployeeTransfers(models.Model):
    _name = 'employee.transfers'


    employee_id = fields.Many2one('hr.employee',string='Employee')
    old_company_id = fields.Many2one('res.company',string='Old Company')
    new_company_id = fields.Many2one('res.company',string='New Company')
    is_approved =fields.Boolean(string='Is Approved',default=False)

    def action_approve(self):
        user_employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
        print(self.employee_id.parent_id.id)
        print(user_employee_id.id)
        if user_employee_id.id == self.employee_id.parent_id.id:
            self.employee_id.company_id = self.new_company_id
            self.is_approved = True
        else:
            raise ValidationError('You cannot approve this employee')