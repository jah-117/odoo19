# -*- coding: utf-8 -*-
from odoo import fields, models, api

class NotificationScheduler(models.TransientModel):
    _name = "edu.notification.scheduler"

    notification_id = fields.Many2one(comodel_name="edu.notification", string="Notification", required=True)
    date = fields.Date(string="Date", help="Date of the notification to be scheduled", required=True)
    time = fields.Float(string="Time", help="Time of the notification to be scheduled", required=True)

    def action_confirm_schedule(self):
        ...