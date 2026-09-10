# Copyright 2025 Cybrosys Techno Solutions
# License LGPL-3 - See https://www.gnu.org/licenses/lgpl-3.0.html
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class Notification(models.Model):
    _name = 'edu.notification'

    name = fields.Char(stirng="Notification", required=True, help="Name of notification")
    to_partner_ids = fields.Many2many(string="To", comodel_name="res.partner", required=True)
    to_class_ids = fields.Many2many(string="To Class", comodel_name="education.class")
    # to_department_ids = fields.Many2many(string="To Department", comodel_name="education.department")
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
        ("scheduled", "Scheduled"),
        ("sent", "Sent"),
        ("cancel", "Cancel"),
    ], default="draft"  )
    institution_profile_id = fields.Many2one(
        "institution.profile",
        string="Institution Profile",
        default=lambda self: self.env["institution.profile"].search([
            ("company_id", "=", self.env.company.id),
            ("active", "=", True),
        ], limit=1),
        readonly=True,
    )

    @api.onchange('to_class_ids', 'to_department_ids')
    def _onchange_mass_mailing(self):
        self.ensure_one()
        if self.to_class_ids:
            partner_ids =[]
            for class_id in self.to_class_ids:
                [partner_ids.append(enrollment.student_partner_id.id) for enrollment in class_id.enrollment_ids]
            self.to_partner_ids = [fields.Command.set(partner_ids)]

    def action_schedule_notification(self):
        return {
            'type': 'ir.actions.act_window',
            'name':'Notification Scheduler',
            'res_model': 'edu.notification.scheduler',
            'target': 'new',
            'view_mode':'form',
            'context': {'default_notification_id': self.id},
        }

    def action_send_notification(self):
        for rec in self:
            rec._action_send_notification()

    def _action_send_notification(self):
        self.ensure_one()

        template = self.env.ref(
            "education_notification.notification_mail_template"
        )

        email_to = ",".join(
            self.to_partner_ids
            .filtered(lambda partner: partner.email)
            .mapped("email")
        )
        if not email_to:
            raise UserError(_("None of the selected recipients have an email address on file."))

        email_values = {
            "email_to": email_to,
            "email_cc": ",".join(
                self.to_cc_partner_ids
                .filtered(lambda partner: partner.email)
                .mapped("email")
            ),
        }

        template.send_mail(
            self.id,
            force_send=True,
            email_values=email_values,
        )

        self.write({
            "state": "sent",
            "sent_date": fields.Datetime.now(),
        })
    def _scheduled_notification_cron(self):
        ...


class NotificationFooter(models.Model):
    _name = "edu.notification.footer"

    name = fields.Char(string="Footer", help="name of the footer", required=True)
    body = fields.Html(string="Notification Footer", required=True)


