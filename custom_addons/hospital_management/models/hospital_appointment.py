from odoo import fields,models,_,api
from datetime import datetime
from odoo.exceptions import ValidationError


class HospitalAppointment(models.Model):
    _name = 'hospital.appointment'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('consultation', 'Consultation'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='State', default='draft')
    name = fields.Char(string="Sequence", default=_('New'))
    patient_id = fields.Many2one('hospital.patient',string="Patient")
    doctor_id = fields.Many2one('hr.employee',string="Doctor")
    department_id = fields.Many2one('hospital.department',string="Department")
    appointment_datetime = fields.Datetime(string="Datetime")
    consultation_fee = fields.Float(string="Consultation Fee")
    symptoms = fields.Text(string="Symptoms")
    diagnosis = fields.Text(string="Diagnosis")
    prescription_ids = fields.One2many('hospital.prescription.line', inverse_name='appointment_id')

    available_doctor_ids = fields.Many2many('hr.employee',compute='_compute_available_doctor_ids')

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            if val.get('name', _("New")) == _("New"):
                val['name'] = (self.env['ir.sequence'].next_by_code('app.seq') or _("New"))
                print(val['name'])
        return super().create(vals)

    @api.onchange('department_id')
    def _compute_available_doctor_ids(self):
        self.available_doctor_ids = self.department_id.doctor_ids

    @api.onchange('appointment_datetime')
    def _onchange_appointment_datetime(self):
        if self.appointment_datetime:
            if self.appointment_datetime.strftime('"%Y-%m-%d %H:%M:%S"') < datetime.now().strftime('"%Y-%m-%d %H:%M:%S"'):
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Warning!',
                        'message': f'Hello, Please provide a future date.',
                        'type': 'warning',
                        'sticky': False,
                        'next': {
                            'type': 'ir.actions.act_window_close',
                        }
                    }
                }
    @api.constrains('patient_id', 'appointment_datetime')
    def _check_patient_id(self):

        if self.env['hospital.appointment'].search([
            ('patient_id', '=', self.patient_id.id),
            ('state', 'in', ['scheduled', 'draft', 'consultation']),
            ('id','!=',self.id)]):
            raise ValidationError(_('Patient ID already exists in another appointment!'))
        if self.env['hospital.appointment'].search([
            ('appointment_datetime', '=', self.appointment_datetime),
            ('state', 'in', ['scheduled', 'draft', 'consultation']),
            ('id','!=',self.id)]):
            raise ValidationError(_('Another appointment already exists in this datetime!'))
    @api.constrains('doctor_id')
    def _check_doctor_id(self):
        if self.env['hospital.appointment'].search([
            ('doctor_id', '=', self.doctor_id.id),
            ('appointment_datetime', '=', self.appointment_datetime),
            ('state','in',['scheduled','draft','consultation']),
            ('id','!=',self.id)]):
            raise ValidationError(_('Doctor has another appointment on this time!'))

    @api.onchange('state')
    def _check_for_datetime(self):

        if not self.appointment_datetime and self.state != 'draft':
            self.state = 'draft'
            raise ValidationError(_('Datetime is mandatory to confirm the appointment!'))

    def action_schedule(self):
        if not self.patient_id:
            raise ValidationError(_('Patient ID is mandatory to schedule appointment!'))
        if not self.doctor_id:
            raise ValidationError(_('Doctor ID is mandatory to schedule appointment!'))
        self.state = 'scheduled'
        self._check_for_datetime()
    def action_consultation(self):
        self.state = 'consultation'
    def action_completed(self):
        if not self.diagnosis:
            raise ValidationError(_('Diagnosis is mandatory to complete appointment!'))
        if not self.prescription_ids:
            raise ValidationError(_('Prescription IDs is mandatory to complete appointment!'))
        self.state = 'completed'
    def action_cancelled(self):
        self.state = 'cancelled'

    @api.model
    def _prevent_deletion(self,record):
        if record.state == 'completed':
            raise ValidationError(_('Cannot delete completed appointment!'))
