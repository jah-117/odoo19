from odoo import api, fields, models, _


class HrLeaveRestriction(models.Model):
    _inherit = 'hr.leave'

    employees_on_leave = fields.Many2many(
        'hr.employee',
        compute='_compute_employees_on_leave',
    )



    @api.onchange('employee_id')
    def _compute_employees_on_leave(self):
        self.employees_on_leave = self.env['hr.employee'].search([('department_id','=',self.department_id.id),('is_absent','=',True)])
        total_employees = self.env['hr.employee'].search_count([('department_id','=',self.department_id.id)])
        if total_employees>0:
            if  len(self.employees_on_leave)/total_employees > 0.5:
                self.department_id.is_under_staffed = True

    def action_approve(self):
        print('is triggerd???')
        print(self.department_id.is_under_staffed)
        print(self.env.context)
        if self.env.context.get('is_an_admin'):
            mail_template = self.env.ref('hr_holidays.leave_approved_mail')
            mail_template.send_mail(self.id, force_send=True)

        if self.department_id.is_under_staffed:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Oops! We are low on staff',
                'view_mode': 'form',
                'res_model': 'low.on.staff.wizard',
                'target': 'new',
                'context': {
                    'default_message': _('The department is currently low on staff\nStaffs on leave:\n%(name)s',
                                             name='\n'.join([staff.name for staff in self.employees_on_leave])),
                    'leave_id': self.id,
                    'is_an_admin': self.env.user.has_group('hr_holidaysgroup_hr_holidays_manager')
                }
            }
        return super().action_approve()
            # raise ValidationError(self.env._('The department is currently low on staff\nStaffs on leave:\n%(name)s',
            #                                  name='\n'.join([staff.name for staff in self.employees_on_leave])))
    def action_refuse(self):
        template = self.env.ref('hr_holidays.leave_refused_mail')
        template.send_mail(self.id,force_send=True)
        return super().action_refuse()