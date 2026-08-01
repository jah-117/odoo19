from odoo import fields, models


class EmployeeLoanLine(models.Model):
    _name = 'employee.loan.line'
    _description = 'Employee Loan Lines'


    loan_id = fields.Many2one('employee.loan')
    amount = fields.Float(string="Amount")
    date = fields.Datetime(string="Date")
    paid = fields.Boolean('Paid', default=False)
