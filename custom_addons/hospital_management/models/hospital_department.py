from odoo import fields,models

class HospitalDepartment(models.Model):
    _name = 'hospital.department'

    name = fields.Char(string="Name")
    doctor_ids = fields.Many2many('hr.employee', string="Doctors",
                                  domain="[('is_doctor','=',True),('is_available','=',True)]")
    