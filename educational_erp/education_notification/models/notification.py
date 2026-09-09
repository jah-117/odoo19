# Copyright 2025 Cybrosys Techno Solutions
# License LGPL-3 - See https://www.gnu.org/licenses/lgpl-3.0.html

from odoo import models, fields

class Notification(models.Model):
    _name = 'edu.notification'

    name = fields.Char(stirng="Notification", required=True, help="Name of notification")
    to_partner_ids = fields.Many2many(string="To", comodel_name="res.partner", required=True)
    to_class_ids = fields.Many2many(string="To Class", comodel_name="edu.classroom")
    to_department_ids = fields.Many2many(string="To Department", comodel_name="education.department")
    to_cc_partner_ids = fields.Many2many(string="CC", comodel_name="res.partner", relation="notification_cc_partners")
    subject_id = fields.Char(string="Subject", help="Subject of the notification", required=True)
    body = fields.Html(string="Body", help="Body of the notification",required=True)
    is_scheduled = fields.Boolean(string="Scheduled", default=False)
    footer_id = fields.Many2one(string="Footer",comodel_name="edu.notification.footer", help="Footer of the notification")
    schedule_date = fields.Date(string="Scheduled Date", help="Date of scheduled notification")
    time = fields.Float(string="Time", help="Time of the scheduled notification")
    sent_date = fields.Datetime(string="Send Date", help="Date and time of the notification sent")
    state = fields.Selection([
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("scheduled", "Scheduled"),
        ("cancel", "Cancel"),
    ])


    def action_schedule_notification(self):
        ...

    def action_send_notification(self):
        ...

    def _action_send_notification(self):
        ...
    def _scheduled_notification_cron(self):
        ...


class NotificationFooter(models.Model):
    _name = "edu.notification.footer"

    name = fields.Char(string="Footer", help="name of the footer", required=True)
    content = fields.Html(string="Notification Footer", required=True)


