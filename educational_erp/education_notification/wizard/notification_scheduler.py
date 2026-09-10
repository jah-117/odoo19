# -*- coding: utf-8 -*-
from odoo import fields, models, api,_
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time
import pytz

class NotificationScheduler(models.TransientModel):
    _name = "edu.notification.scheduler"

    notification_id = fields.Many2one(comodel_name="edu.notification", string="Notification", required=True)
    date = fields.Date(string="Date", help="Date of the notification to be scheduled", required=True)
    time = fields.Float(string="Time", help="Time of the notification to be scheduled", required=True)
    scheduled_date = fields.Datetime(string="Scheduled date", compute="_compute_scheduled_date")

    @api.depends("date", "time")
    def _compute_scheduled_date(self):
        ist = pytz.timezone("Asia/Kolkata")

        for record in self:
            record.scheduled_date = False
            if record.date and record.time is not False:
                hours = int(record.time)
                minutes = int(round((record.time - hours) * 60))
                if minutes >= 60:
                    hours += 1
                    minutes = 0
                if hours > 23:
                    raise ValidationError(
                        "Time must be between 00:00 and 23:59."
                    )
                local_datetime = datetime.combine(
                    record.date,
                    time(hour=hours, minute=minutes),
                )
                ist_datetime = ist.localize(local_datetime)
                utc_datetime = ist_datetime.astimezone(pytz.UTC)
                record.scheduled_date = utc_datetime.replace(
                    tzinfo=None
                )
            else:
                record.scheduled_date = False


    def action_confirm_schedule(self):
        self.ensure_one()

        template = self.env.ref(
            "education_notification.notification_mail_template"
        )

        email_to = ",".join(
            self.notification_id.to_partner_ids
            .filtered(lambda partner: partner.email)
            .mapped("email")
        )
        if not email_to:
            raise UserError(_("None of the selected recipients have an email address on file."))

        email_values = {
            "email_to": email_to,
            "email_cc": ",".join(
                self.notification_id.to_cc_partner_ids
                .filtered(lambda partner: partner.email)
                .mapped("email")
            ),
            "scheduled_date": self.scheduled_date,
        }

        template.send_mail(
            self.notification_id.id,
            force_send=False,
            email_values=email_values,
        )

        self.notification_id.write({
            "state": "scheduled",
            "sent_date": self.scheduled_date,
        })