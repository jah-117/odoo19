from odoo import fields, models

class HrContractSalaryBenefit(models.Model):
    _name = 'hr.contract.salary.benefit'

    name = fields.Char(string="Benefits")
    active = fields.Boolean(default=True,string="Active")
    salary_rule_id = fields.Many2one(comodel_name='hr.salary.rule',)
    structure_type_id = fields.Many2one('hr.payroll.structure.type',string="Salary Structure Type")