from odoo import  models,api,_, fields
from odoo.exceptions import ValidationError


class CrmLead(models.Model):
    _inherit = 'crm.lead'


    completed_meetings = fields.Integer(string="Completed Meetings", compute='_compute_completed_meetings')


    @api.depends('activity_ids')
    def _compute_completed_meetings(self):
        for rec in self:
            rec.completed_meetings = self.env['mail.activity'].search_count([('active', '=', False),('activity_category','=','meeting'), ('res_id', '=', rec.id)])

    @api.model
    def _prevent_lead_winning(self,record):
        if record.stage_id.is_won and not self.env.user.has_group('sales_team.group_sale_manager'):
            if record.completed_meetings < 1:
                raise ValidationError(_('Cannot Mark a lead as win without completing atleast one meeting'))