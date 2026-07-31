from odoo import fields, models, api

CLOSING_DATE = [
    ('22', "22 of the pay month"),
    ('23', "23 of the pay month"),
    ('24', "24 of the pay month"),
    ('25', "25 of the pay month"),
    ('26', "26 of the pay month"),
    ('27', "27 of the pay month"),
    ('28', "28 of the pay month"),
    ('29', "29 of the pay month"),
    ('30', "30 of the pay month"),
    ('0', 'Last day of the pay month'),
    ('1', '1 of the next month'),
    ('2', '2 of the next month'),
    ('3', '3 of the next month'),
    ('4', '4 of the next month'),
    ('5', '5 of the next month'),
    ('6', '6 of the next month'),
    ('7', '7 of the next month'),
    ('8', '8 of the next month'),
    ('9', '9 of the next month'),
]

class HrEmployeeType(models.Model):
    _name = 'hr.employee.type'

    sequence = fields.Integer(string="Sequence")
    code = fields.Char(string="Code")
    country_id = fields.Many2one(comodel_name='res.country',string='Country')
    company_id = fields.Many2one(comodel_name='res.company',string='Company')
    employees_count = fields.Integer(string='Employees',readonly=True)
    name = fields.Char(string='Name',required=True)
    payroll_closing_date = fields.Selection(CLOSING_DATE,string='Closing Date')
    payroll_auto_post = fields.Boolean(string='Auto Post',default=False)


    def action_open_employees(self):
        print("opening employees")