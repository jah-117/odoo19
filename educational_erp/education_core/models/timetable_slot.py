# -*- coding: utf-8 -*-
"""
education.timetable.slot — Individual period entries within a timetable (S3-T02)
=================================================================================
One slot = one period on one weekday for a class timetable.
Linked to education.timetable (header) via Many2one.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EducationTimetableSlot(models.Model):
    """A single period slot in a class timetable."""

    _name = "education.timetable.slot"
    _description = "Timetable Slot"
    _order = "weekday, period_no"

    timetable_id = fields.Many2one(
        "education.timetable",
        string="Timetable",
        required=True,
        ondelete="cascade",
        index=True,
    )
    class_id = fields.Many2one(
        "education.class",
        string="Class",
        related="timetable_id.class_id",
        store=True,
        readonly=True,
    )
    program_id = fields.Many2one(
        "education.program",
        related="class_id.program_id",
        store=True,
        readonly=True,
    )
    academic_year_id = fields.Many2one(
        "education.academic.year",
        related="timetable_id.academic_year_id",
        store=True,
        readonly=True,
    )

    # ── Slot Details ──────────────────────────────────────────────────────
    weekday = fields.Selection(
        selection=[
            ("0", "Monday"),
            ("1", "Tuesday"),
            ("2", "Wednesday"),
            ("3", "Thursday"),
            ("4", "Friday"),
            ("5", "Saturday"),
            ("6", "Sunday"),
        ],
        string="Day",
        required=True,
    )
    period_no = fields.Integer(
        string="Period",
        required=True,
        help="Period number within the day (1 = first period).",
    )
    start_time = fields.Float(
        string="Start Time",
        help="24-hour format, e.g. 9.5 = 09:30.",
    )
    end_time = fields.Float(
        string="End Time",
    )
    subject_id = fields.Many2one(
        "education.subject",
        string="Subject",
        domain="[('program_id', '=', program_id)]",
        ondelete="set null",
        help="Subject / Course taught in this slot.",
    )
    teacher_id = fields.Many2one(
        "education.faculty",
        string="Teacher",
        ondelete="set null",
        help="Assigned faculty member for this slot.",
    )
    classroom_id = fields.Many2one(
        "edu.classroom",
        string="Room / Lab",
        ondelete="set null",
        help="Assigned classroom, laboratory, or hall for this slot.",
    )
    notes = fields.Char(string="Notes")

    @api.constrains("timetable_id", "weekday", "period_no")
    def _check_slot_unique(self):
        for rec in self:
            if not rec.timetable_id or not rec.weekday or not rec.period_no:
                continue
            duplicate = self.search([
                ("id", "!=", rec.id),
                ("timetable_id", "=", rec.timetable_id.id),
                ("weekday", "=", rec.weekday),
                ("period_no", "=", rec.period_no),
            ], limit=1)
            if duplicate:
                weekday_label = dict(self._fields["weekday"].selection).get(rec.weekday, rec.weekday)
                raise ValidationError(
                    _("A slot for %s, Period %s already exists in this timetable.")
                    % (weekday_label, rec.period_no)
                )


    @api.constrains("start_time", "end_time")
    def _check_times(self):
        for rec in self:
            if rec.start_time and rec.end_time and rec.end_time <= rec.start_time:
                raise ValidationError(
                    _("End Time must be after Start Time for slot %s P%s.")
                    % (dict(self._fields["weekday"].selection).get(rec.weekday), rec.period_no)
                )

    @api.constrains("period_no")
    def _check_period_no(self):
        for rec in self:
            if rec.period_no < 1:
                raise ValidationError(_("Period number must be at least 1."))

    @api.onchange("period_no")
    def _onchange_period_no(self):
        """Auto-populate start/end time from other slots with the same period_no or standard 45-min template."""
        if not self.period_no:
            return
        # 1. Look for existing slot with same period_no in the parent timetable
        if self.timetable_id:
            matching = self.timetable_id.slot_ids.filtered(
                lambda s: s.period_no == self.period_no and s._origin.id != self._origin.id and (s.start_time or s.end_time)
            )
            if matching:
                self.start_time = matching[0].start_time
                self.end_time = matching[0].end_time
                return
        # 2. If no existing slot with times, calculate default 45-min interval starting at 09:00
        if not self.start_time:
            st = 9.0 + (self.period_no - 1) * 0.75
            self.start_time = round(st, 4)
            self.end_time = round(st + 0.75, 4)

    @api.onchange("start_time")
    def _onchange_start_time(self):
        """Auto-set end_time to start_time + 45 minutes if end_time is not set."""
        if self.start_time and not self.end_time:
            self.end_time = round(self.start_time + 0.75, 4)

    def _compute_display_name(self):
        weekday_labels = dict(self._fields["weekday"].selection)
        for rec in self:
            label = f"{weekday_labels.get(rec.weekday, '?')} P{rec.period_no}"
            if rec.subject_id:
                label += f" — {rec.subject_id.name}"
            rec.display_name = label

    def name_get(self):
        """Legacy compatibility — Odoo 19 uses display_name, but kept for safety."""
        result = []
        weekday_labels = dict(self._fields["weekday"].selection)
        for rec in self:
            label = f"{weekday_labels.get(rec.weekday, '?')} P{rec.period_no}"
            if rec.subject_id:
                label += f" — {rec.subject_id.name}"
            result.append((rec.id, label))
        return result
