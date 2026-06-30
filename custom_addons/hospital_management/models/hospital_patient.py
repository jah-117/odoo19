from odoo import models,fields,api
from datetime import date


class HospitalPatient(models.Model):
    _name = 'hospital.patient'
    _description = 'Patient information'

    name = fields.Char(string="Patient Name")
    date_of_birth = fields.Date(string="Date of Birth")
    age =fields.Integer(string="Age",store=True,compute="_compute_age",readonly=True)
    gender = fields.Selection([('male','Male'),('female','Female')],string="Gender")
    blood_group = fields.Selection([
        ('a_posetive','A+'),
        ('a_negetive','A-'),
        ('b_posetive','B+'),
        ('b_negetive','B-'),
        ('o_posetive','O+'),
        ('o_negetive','O-'),
        ('ab_posetive','AB+'),
        ('ab_negetive','AB-'),
    ], string="Blood Group")
    mobile = fields.Char(string="Mobile")
    department_id = fields.Many2one('hospital.department',string="Department")
    appointment_ids =fields.One2many('hospital.appointment','patient_id',string="Appointments")
    state = fields.Selection([
        ('draft','Draft'),
        ('active','Active'),
        ('discharged','Discharged'),
    ],string="State", default="draft")
    appointment_count = fields.Integer(string="Appointment Count", compute="_compute_appointment_count",store=True)


    @api.depends('appointment_ids')
    def _compute_appointment_count(self):
        for patient in self:
            patient.appointment_count = len(patient.appointment_ids)
    @api.depends('date_of_birth')
    def _compute_age(self):
        for patient in self:
            if patient.date_of_birth:
                patient.age = (date.today() - patient.date_of_birth).days//365
