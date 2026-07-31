from odoo import fields, models

class HrPayrollStructureType(models.Model):
    _name = 'hr.payroll.structure.type'

    name = fields.Char(string='Structure Type')
    country_id = fields.Many2one(comodel_name='res.country', string='Country')
    wage_type = fields.Selection([('monthly','Fixed Wage'),('hourly','Hourly Wage')], string='Wage Type',default='monthly')
    default_resource_calender_id = fields.Many2one(comodel_name='resource.calendar', string='Working Hours')
    default_structure_id = fields.Many2one(comodel_name='hr.payroll.structure', string='Pay Structure')
    default_work_entry_type_id = fields.Many2one(comodel_name='hr.work.entry.type', string='Work Entry Type')