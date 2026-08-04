from odoo import fields, models

class HrPayslip(models.Model):
    _name = 'hr.payslip'

    employee_id = fields.Many2one(comodel_name='hr.employee', string="Employee")
    employee_type_id = fields.Many2one(comodel_name='hr.employee.type', string="Employee Type",
                                       related='employee_id.employee_type_id')
    struct_id = fields.Many2one(comodel_name='hr.payroll.structure', string="Structure")
    expense_ids = fields.One2many(comodel_name='hr.expense', inverse_name='payslip_id')
    expense_count = fields.Integer(string="Expense Count")
    line_ids = fields.One2many(comodel_name='hr.payslip.line', inverse_name='payslip_id')
    journal_id = fields.Many2one(comodel_name='account.journal', related='struct_id.journal_id',string="Journal")
    date_from = fields.Date(string='From Date', required=True)
    date_to = fields.Date(string='To Date', required=True)
    code = fields.Char(string="Code", readonly=True)
    compute_date = fields.Date(string="Compute Date")
    company_id = fields.Many2one(comodel_name='res.company', string="Company")
    country_id = fields.Many2one(comodel_name='res.country', string="Country",related='struct_id.country_id')
    currency_id = fields.Many2one(comodel_name='res.currency', string="Currency",related='country_id.currency_id')
    department_id = fields.Many2one(comodel_name='hr.department',string='Department', related='employee_id.department_id')
    country_code = fields.Char(string="Country Code", related='country_id.code')
    avatar_128 = fields.Binary(string="Avatar 128", related='employee_id.avatar_128')
    avatar_1920 = fields.Binary(string="Avatar", related='employee_id.avatar_1920')
    basic_wage = fields.Monetary(string="Basic Wage", currency_field='currency_id')
    structure_code = fields.Char(string="Structure Code", related='struct_id.code')
    related_payslip_count = fields.Integer(string="Related Payslip Count")
    salary_attachment_ids = fields.Many2one(comodel_name='hr.salary.attachment', string="Salary Attachments")
    salary_attachment_count = fields.Integer(string="Salary Attachment Count")
    version_id = fields.Many2one(comodel_name='hr.version', string="Version",related='employee_id.version_id')
    # wage_type =fields.Selection(string="Wage Type",related='version_id.wage_type')
    net_wage = fields.Monetary(string="Net Wage", currency_field='currency_id')
    sum_worked_hours = fields.Float(string="Sum of Worked Hours")
    worked_days_line_ids = fields.One2many(comodel_name='hr.payslip.worked_days',string="Worked Days",inverse_name='payslip_id')
    ytd = fields.Boolean(string="YTD",related='struct_id.ytd_computation')
    state_display = fields.Selection([
        ('01_error', 'Blocked'),
        ('02_warning', 'Warning'),
        ('03_draft', 'Draft'),
        ('04_validated', 'Done'),
        ('05_paid', 'Paid'),
        ('06_cancel', 'Canceled')
    ],string="Status")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('validated', 'Validated'),
        ('paid', 'Paid'),
        ('cancel', 'Canceled')
    ])
    input_line_ids = fields.Many2one(comodel_name='hr.payslip.input', string="Salary Input")

    def action_validate(self):
        pass
    def compute_sheet(self):
        pass
    def action_payslip_paid(self):
        pass

    def action_print_payslip(self):
        pass
    def action_payslip_done(self):
        pass
    def action_payslip_payment_report(self):
        pass
    def refund_sheet(self):
        pass
    def action_payslip_draft(self):
        pass
    def action_payslip_unpaid(self):
        pass
    def action_payslip_cancel(self):
        pass
    def action_open_related_payslips(self):
        pass
    def action_open_salary_attachments(self):
        pass