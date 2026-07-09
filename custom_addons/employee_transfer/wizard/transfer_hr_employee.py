from odoo import fields, models

class TransferHrEmployee(models.TransientModel):
    _name = 'transfer.hr.employee'

    employee_id = fields.Many2one('hr.employee', readonly=True,string='Employee')
    old_company_id = fields.Many2one('res.company', readonly=True,string='Old Company')
    new_company_id = fields.Many2one('res.company', required=True,string="Select new Company")


    def action_transfer_employee(self):
        self.env['employee.transfers'].create({
            'employee_id': self.employee_id.id,
            'old_company_id': self.old_company_id.id,
            'new_company_id': self.new_company_id.id,
        })