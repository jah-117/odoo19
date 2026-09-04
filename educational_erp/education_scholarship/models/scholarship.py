# -*- coding: utf-8 -*-
from datetime import date
from odoo import api, models, fields
from odoo.exceptions import UserError

class EducationScholarship(models.Model):
    _name = "education.scholarship"
    _description = "Scholarship Program"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Scholarship Name", required=True, tracking=True)
    academic_year_id = fields.Many2one(
        "education.academic.year", string="Academic Year", required=True, tracking=True
    )
    scholarship_type = fields.Selection(
        [
            ("merit", "Merit-based"),
            ("need", "Need-based"),
            ("sports", "Sports/Athletics"),
            ("other", "Other")
        ], string="Scholarship Type", required=True, tracking=True
    )
    description = fields.Text(string="Description")
    amount = fields.Float(string="Scholarship Amount", tracking=True)
    available_scholarships = fields.Integer(string="Number of Available Scholarships", tracking=True)
    start_date = fields.Date(string="Application Start Date", tracking=True)
    end_date = fields.Date(string="Application End Date", tracking=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("closed", "Closed")
        ], string="Status", default="draft", tracking=True, required=True
    )
    eligibility_ids = fields.Many2many(
        'scholarship.eligibility.criteria',
        'scholarship_criteria_rel',
        'scholarship_id',
        'criteria_id',
        string='Eligibility Criteria'
    )
    application_count = fields.Integer(
        string="Application Count",
        compute="_compute_application_count"
    )

    @api.constrains('name')
    def _check_unique_name(self):
        for rec in self:
            if rec.name:
                domain = [('name', '=ilike', rec.name.strip()), ('id', '!=', rec.id)]
                if self.search_count(domain) > 0:
                    raise UserError("Scholarship with this name already exists!")

    def copy(self, default=None):
        raise UserError("Duplicating a scholarship record is not allowed.")

    def _compute_application_count(self):
        for rec in self:
            rec.application_count = self.env['education.scholarship.application'].search_count([
                ('scholarship_id', '=', rec.id)
            ])

    def action_view_applications(self):
        self.ensure_one()
        return {
            'name': 'Scholarship Applications',
            'type': 'ir.actions.act_window',
            'res_model': 'education.scholarship.application',
            'view_mode': 'list,form',
            'domain': [('scholarship_id', '=', self.id)],
            'context': {'default_scholarship_id': self.id},
        }

    def action_open_scholarship(self):
        """Open Scholarship button handler.
        - Sets state to 'active'.
        - If start_date is not set, or is set to a future date,
          it is updated to today (the actual opening date).
        """
        for rec in self:
            if rec.state == 'closed':
                raise UserError("A closed scholarship cannot be re-opened.")
            today = date.today()
            # Always set start_date to today when manually opening:
            # covers both the case where it was not set and the case
            # where a future date had been pre-filled.
            if not rec.start_date or rec.start_date > today:
                rec.start_date = today
            rec.state = 'active'
            rec.message_post(body="Scholarship opened and set to Active.")

    def action_close_scholarship(self):
        """Close Scholarship button handler.
        Transitions state from active to closed.
        """
        for rec in self:
            if rec.state != 'active':
                raise UserError("Only active scholarships can be closed.")
            rec.state = 'closed'
            rec.message_post(body="Scholarship closed.")

    @api.constrains('start_date')
    def _check_start_date(self):
        """Prevent saving a start_date in the past."""
        today = date.today()
        for rec in self:
            if rec.start_date and rec.start_date < today and rec.state == 'draft':
                raise UserError(
                    "The Application Start Date cannot be set to a past date. "
                    "Please select today or a future date."
                )

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise UserError("Application End Date cannot be earlier than Start Date.")

    @api.model
    def _cron_update_scholarship_state(self):
        """Scheduled action: activate scholarships whose start_date is today,
        and close scholarships whose end_date has passed."""
        today = date.today()
        # Activate scholarships that should start today
        to_activate = self.search([
            ('state', '=', 'draft'),
            ('start_date', '<=', today),
            ('start_date', '!=', False),
        ])
        to_activate.write({'state': 'active'})
        for rec in to_activate:
            rec.message_post(body="Scholarship automatically activated on start date.")

        # Close scholarships whose end_date has passed
        to_close = self.search([
            ('state', '=', 'active'),
            ('end_date', '<', today),
            ('end_date', '!=', False),
        ])
        to_close.write({'state': 'closed'})
        for rec in to_close:
            rec.message_post(body="Scholarship automatically closed after application end date.")

