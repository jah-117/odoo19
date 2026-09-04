# -*- coding: utf-8 -*-
"""
education.timetable — Timetable header model.
Full timetable slot lines are implemented in Sprint 3 (Attendance & Faculty).
This Sprint 1 skeleton establishes the model structure and sequence.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


WEEKDAY_SELECTION = [
    ("0", "Monday"),
    ("1", "Tuesday"),
    ("2", "Wednesday"),
    ("3", "Thursday"),
    ("4", "Friday"),
    ("5", "Saturday"),
    ("6", "Sunday"),
]


class EducationTimetable(models.Model):
    """
    Timetable header — one per class per academic year.
    Timetable slots (period × weekday grid) are added in Sprint 3.
    """

    _name = "education.timetable"
    _description = "Class Timetable"
    _order = "academic_year_id desc, class_id"
    _inherit = ["mail.thread"]

    name = fields.Char(
        string="Timetable Reference",
        compute="_compute_name",
        store=True,
    )
    class_id = fields.Many2one(
        "education.class",
        string="Class",
        required=True,
        ondelete="cascade",
        tracking=True,
        index=True,
    )
    academic_year_id = fields.Many2one(
        "education.academic.year",
        string="Academic Year",
        required=True,
        ondelete="restrict",
        tracking=True,
        index=True,
    )
    effective_from = fields.Date(
        string="Effective From",
        help="Date from which this timetable is active.",
    )
    effective_to = fields.Date(
        string="Effective To",
        help="Leave blank if there is no fixed end date.",
    )

    # ── Timetable Slots (Sprint 3) ─────────────────────────────────────────
    slot_ids = fields.One2many(
        "education.timetable.slot",
        "timetable_id",
        string="Timetable Slots",
    )
    slot_count = fields.Integer(
        string="# Slots",
        compute="_compute_slot_count",
    )

    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("published", "Published"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )
    notes = fields.Text(string="Notes")
    active = fields.Boolean(default=True)

    _class_year_uniq =models.Constraint(
            "UNIQUE(class_id, academic_year_id)",
            "A timetable for this class and academic year already exists.",
        )


    @api.constrains("slot_ids")
    def _check_slot_ids_unique(self):
        for rec in self:
            seen = set()
            for slot in rec.slot_ids:
                if not slot.weekday or not slot.period_no:
                    continue
                key = (slot.weekday, slot.period_no)
                if key in seen:
                    weekday_label = dict(slot._fields["weekday"].selection).get(slot.weekday, slot.weekday)
                    raise ValidationError(
                        _("Duplicate slot: %s Period %s is defined more than once.")
                        % (weekday_label, slot.period_no)
                    )
                seen.add(key)

    @api.depends("slot_ids")
    def _compute_slot_count(self):
        for rec in self:
            rec.slot_count = len(rec.slot_ids)

    @api.depends("class_id", "academic_year_id")
    def _compute_name(self):
        for rec in self:
            rec.name = (
                f"TT/{rec.class_id.name or ''}"
                f"/{rec.academic_year_id.code or ''}"
            )

    def action_publish(self):
        self.write({"state": "published"})

    def action_reset_draft(self):
        self.write({"state": "draft"})

    def action_print_timetable(self):
        self.ensure_one()
        return self.env.ref("education_core.action_report_education_timetable").report_action(self, config=False)

    def action_open_generate_wizard(self):
        self.ensure_one()
        return {
            "name": _("Auto-Generate Timetable Slots"),
            "type": "ir.actions.act_window",
            "res_model": "education.timetable.generate.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_timetable_id": self.id},
        }

    def _get_timetable_grid_data(self):
        self.ensure_one()
        all_periods = sorted(list({s.period_no for s in self.slot_ids if s.period_no}))
        if not all_periods:
            all_periods = [1, 2, 3, 4, 5, 6, 7, 8]

        # Extract timing ranges per period
        period_times = {}
        period_raw_times = {}
        for p in all_periods:
            slots_for_p = self.slot_ids.filtered(lambda s: s.period_no == p and (s.start_time or s.end_time))
            if slots_for_p:
                first_slot = slots_for_p[0]
                st = self._format_time(first_slot.start_time)
                et = self._format_time(first_slot.end_time)
                period_times[p] = f"{st} – {et}" if st and et else (st or et or "")
                period_raw_times[p] = (first_slot.start_time or 0.0, first_slot.end_time or 0.0)
            else:
                period_times[p] = ""
                period_raw_times[p] = (0.0, 0.0)

        # Build columns (periods + detected breaks between periods)
        columns = []
        for i, p in enumerate(all_periods):
            columns.append({
                "type": "period",
                "period_no": p,
                "time": period_times.get(p, ""),
            })
            # Check gap with next period
            if i < len(all_periods) - 1:
                next_p = all_periods[i + 1]
                curr_end = period_raw_times.get(p, (0.0, 0.0))[1]
                next_start = period_raw_times.get(next_p, (0.0, 0.0))[0]
                if curr_end and next_start and (next_start - curr_end) >= 0.05:  # >= 3 mins gap
                    gap_mins = int(round((next_start - curr_end) * 60))
                    label = "LUNCH" if gap_mins >= 30 else "BREAK"
                    columns.append({
                        "type": "break",
                        "label": label,
                        "label_chars": list(label),
                        "time": f"{self._format_time(curr_end)} – {self._format_time(next_start)}",
                        "duration": gap_mins,
                    })

        # Build day rows
        weekday_dict = dict(WEEKDAY_SELECTION)
        used_weekdays = {s.weekday for s in self.slot_ids if s.weekday}
        days_to_show = ["0", "1", "2", "3", "4"]
        for extra_day in ["5", "6"]:
            if extra_day in used_weekdays:
                days_to_show.append(extra_day)

        day_rows = []
        for d_code in days_to_show:
            d_name = weekday_dict.get(d_code, "")
            slots_by_period = {}
            for p in all_periods:
                matching_slots = self.slot_ids.filtered(lambda s: s.weekday == d_code and s.period_no == p)
                slots_by_period[p] = matching_slots[0] if matching_slots else None

            day_rows.append({
                "code": d_code,
                "name": d_name,
                "slots": slots_by_period,
            })

        # Summary of subjects and faculty
        subject_summary = []
        seen_subjects = set()
        for slot in self.slot_ids:
            if slot.subject_id and slot.subject_id.id not in seen_subjects:
                seen_subjects.add(slot.subject_id.id)
                teachers = self.slot_ids.filtered(
                    lambda s: s.subject_id == slot.subject_id and s.teacher_id
                ).mapped("teacher_id.name")
                subject_summary.append({
                    "code": slot.subject_id.code or "—",
                    "name": slot.subject_id.name,
                    "teachers": ", ".join(sorted(set(teachers))) if teachers else "Unassigned",
                })

        return {
            "periods": all_periods,
            "columns": columns,
            "period_times": period_times,
            "days": day_rows,
            "subject_summary": subject_summary,
        }

    @api.model
    def _format_time(self, val):
        if val is None or val is False:
            return ""
        hours = int(val)
        minutes = int(round((val - hours) * 60))
        if minutes >= 60:
            hours += 1
            minutes = 0
        return f"{hours:02d}:{minutes:02d}"

