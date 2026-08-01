from odoo import fields,models
CONDITION = [
    ('none','Always Present'),
    ('property_input','Salary Input'),
    ('input','Other Input'),
    ('domain','Domain'),
    ('python','Python Expression'),
]
AMOUNT = [
    ('percentage','Percentage (%)'),
    ('property_input','Salary Input Value'),
    ('fix','Fixed Amount'),
    ('input','Other Input'),
    ('code','Python Code'),
]
UNIT = [
    ('monetary','Monetary'),
    ('quantity','Quantity'),
    ('percentage','Percentage'),
    ('boolean','Checkbox'),
    ('many2one','Many2One'),
    ('selection','Selection'),
]
class SalaryRule(models.Model):
    _name = 'hr.salary.rule'
    _description = 'Salary Rule'

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    active = fields.Boolean(string="Active",default=True)
    sequence = fields.Integer(string="Sequence",default=10)
    category_ids = fields.Many2many(comodel_name='hr.salary.rule.category', string="Categories")
    struct_ids = fields.Many2many(comodel_name='hr.payroll.structure', string="Pay Structures")
    country_id = fields.Many2one(comodel_name='res.country', string="Country", default=lambda self: self.env.user.company_id.country_id)
    currency_id = fields.Many2one(comodel_name='res.currency', string="Currency", related="country_id.currency_id")

    condition_select = fields.Selection(CONDITION,string="Based on", default='none')

    condition_other_input_id  = fields.Many2one(comodel_name='hr.payslip.input.type', string="Condition Other Input")
    condition_domain = fields.Text(string="Domain")
    condition_python = fields.Text(string="Python Expression")

    input_name = fields.Char(string="Name")
    input_unit = fields.Selection(UNIT,string="Unit")
    input_default_value = fields.Float(string="Default Value")
    input_default_display = fields.Char(string="Input Default Display")
    input_suffix = fields.Char(string="Suffix")
    input_default_boolean = fields.Boolean(string="Selected by Default")
    input_no_transfer = fields.Boolean(string="Input No Transfer")
    input_comodel = fields.Many2one(comodel_name='ir.model', string="Model")
    input_selection_ids = fields.Many2one(comodel_name='hr.salary.rule.input.selection', string="Options")



    amount_select = fields.Selection(AMOUNT,string="Amount Type")

    amount_percentage_base = fields.Char(string="Percentage based on")
    quantity = fields.Char(string="Quantity")
    amount_percentage = fields.Float(string="Percentage based on")
    amount_fix = fields.Float(string="Fixed Amount")
    amount_other_input_id = fields.Many2one(comodel_name='hr.payslip.input.type', string="Amount Other Input")
    amount_python_compute = fields.Text()
