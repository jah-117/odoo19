from odoo import fields, models,api,_
from odoo.exceptions import ValidationError
from datetime import datetime

class EmployeeLoan(models.Model):
    _name = 'employee.loan'
    _inherit = ['mail.thread']
    _description = 'Employee Loan'


    name = fields.Char(string="Name", default=lambda self: _('New'),required=True, copy=False,
                       readonly=True)
    employee_id = fields.Many2one('hr.employee',string="Employee", domain="[('loan_not_allowed','=',False)]")
    loan_amount = fields.Float(string="Loan Amount")
    installment_count = fields.Integer(string="Installment Count")
    start_date = fields.Datetime(string="Start Date",tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('ongoing', 'Ongoing'),
        ('paid', 'Paid')], tracking=True,default='draft')

    loan_line_ids = fields.One2many('employee.loan.line', 'loan_id')
    line_count = fields.Integer(string="Loan Lines", compute='_compute_line_count')
    installment_amount = fields.Float(string="Installment Amount")
    total_payable = fields.Float(string="Total Payable",compute='_compute_total_payable')
    paid_amount = fields.Float(string="Paid Amount", compute='_compute_paid_amount')
    balance_amount = fields.Float(string="Balance Amount", compute='_compute_balance_amount')

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            if val.get('name', _("New")) == _("New"):
                val['name'] = (self.env['ir.sequence']
                               .next_by_code('loan.seq') or _("New"))
        return super().create(vals)

    @api.onchange('installment_count','loan_amount')
    def _compute_installment_amount(self):
        if self.installment_count and self.loan_amount:
            self.installment_amount = self.loan_amount / self.installment_count
        else:
            self.installment_amount = 0

    @api.depends('loan_line_ids')
    def _compute_total_payable(self):
        for rec in self:
            if rec.loan_line_ids:
                rec.total_payable = sum([line.amount for line in rec.loan_line_ids])
            else:
                rec.total_payable = 0

    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.loan_line_ids)

    def action_approve(self):
        if self.loan_amount:
            self.state = 'approved'
        else:
            raise ValidationError(_('Loan not approved'))
        #     return {
        #     'type': 'ir.actions.client',
        #     'tag': 'display_notification',
        #     'params': {
        #         'title': 'Warning!',
        #         'message': f'Hello, Loan amount must grater than 0!.',
        #         'type': 'danger',
        #         'sticky': False,
        #         'next': {
        #             'type': 'ir.actions.act_window_close',
        #         }
        #     }
        # }
    def action_open_lines(self):
        return {
                'name': _('Lines'),
                'type': 'ir.actions.act_window',
                'res_model': 'employee.loan.line',
                'view_mode': 'list,form',
                'context': {
                    'default_loan_id': self.id
                },
                'domain': [('loan_id','=',self.id)],
            }

    def action_generate_installment(self):
        self.update({
            'loan_line_ids': [fields.Command.create({
                    'loan_id': self.id,
                    'amount': self.installment_amount,
                })for index in range(self.installment_count)]
        })
        self.state = 'ongoing'
    def action_pay_installment(self):
        unpaid = self.loan_line_ids.filtered(lambda line:not line.paid)
        unpaid[0].date=datetime.now()
        unpaid[0].paid = True
        if len(unpaid) > 1:
            self.state = 'paid'
    @api.depends('loan_line_ids.paid')
    def _compute_paid_amount(self):
        for rec in self:
            rec.paid_amount = sum([line.amount for line in rec.loan_line_ids.filtered(lambda line: line.paid)])

    @api.depends('loan_line_ids.paid')
    def _compute_balance_amount(self):
        for rec in self:
            rec.balance_amount = sum([line.amount for line in rec.loan_line_ids.filtered(lambda line: not line.paid)])