from odoo import models, fields


class HrPayslipWorkedDays(models.Model):
    _name = 'hr.payslip.worked_days'


    company_id = fields.Many2one(string="Company", comodel_name='res.company',
                                 default=lambda self: self.env.company_id.id, readonly=True)
    sequence =fields.Integer(string="Sequence",default=10)
    name = fields.Char(string="Description", readonly=True)
    payslip_id = fields.Many2one(comodel_name='hr.payslip', string="Payslip")
    work_entry_type_id = fields.Many2one(string="Type", comodel_name='hr.work.entry.type')
    employee_id = fields.Many2one(comodel_name='hr.employee', string="Employee", related='payslip_id.employee_id')
    employee_type_id = fields.Many2one(comodel_name='hr.employee.type', string="Employee Type",
                                       related='employee_id.employee_type_id')
    currency_id = fields.Many2one(comodel_name='res.currency', string="Currency", related='company_id.currency_id')
    payslip_id = fields.Many2one(comodel_name='hr.payslip', string="Payslip")
    date_from = fields.Datetime(string="From Date")
    version_id = fields.Many2one(comodel_name='hr.version', string="Version",related='payslip_id.version_id')
    department_id = fields.Many2one(comodel_name='hr.department', string="Department",
                                    related='payslip_id.department_id')
    number_of_days = fields.Float(string="Number of Days")
    number_of_hours = fields.Float(string="Number of Hours")
    amount = fields.Monetary(string="Amount",currency_field='currency_id')
    ytd = fields.Boolean(string="YTD",related='payslip_id.ytd')
    is_paid = fields.Boolean(string="Is Paid")
    resource_calendar_id = fields.Many2one(comodel_name='resource.calendar', string="Working Hours")
