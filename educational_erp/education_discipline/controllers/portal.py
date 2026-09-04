# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError


class DisciplinePortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "school_rule_count" in counters:
            values["school_rule_count"] = request.env["education.school.rule"].sudo().search_count(
                [("active", "=", True)])

        if "discipline_case_count" in counters:
            partner = request.env.user.partner_id
            values["discipline_case_count"] = request.env["education.discipline.case"].search_count([
                ("student_id.student_partner_id", "=", partner.id)
            ])

        return values

    CATEGORY_LABELS = {
        "general": "General",
        "academic": "Academic",
        "uniform": "Uniform",
        "conduct": "Conduct",
        "other": "Other",
    }

    @http.route(["/my/school_rules"], type="http", auth="user", website=True)
    def portal_my_school_rules(self, **kw):
        rules = request.env["education.school.rule"].sudo().search([("active", "=", True)])

        # Group rules by category
        categories = {}
        for rule in rules:
            cat = rule.category
            if cat not in categories:
                categories[cat] = {
                    "key": cat,
                    "label": self.CATEGORY_LABELS.get(cat, cat.capitalize()),
                    "count": 0,
                }
            categories[cat]["count"] += 1

        values = {
            "categories": list(categories.values()),
            "page_name": "school_rules",
        }
        return request.render("education_discipline.portal_my_school_rules", values)

    @http.route(["/my/school_rules/<string:category>"], type="http", auth="user", website=True)
    def portal_school_rules_category(self, category, **kw):
        label = self.CATEGORY_LABELS.get(category, category.capitalize())
        rules = request.env["education.school.rule"].sudo().search([
            ("active", "=", True),
            ("category", "=", category),
        ])
        values = {
            "rules": rules,
            "category_label": label,
            "page_name": "school_rules",
        }
        return request.render("education_discipline.portal_school_rules_category", values)

    @http.route(["/my/discipline_cases", "/my/discipline_cases/page/<int:page>"], type="http", auth="user",
                website=True)
    def portal_my_discipline_cases(self, page=1, **kw):
        partner = request.env.user.partner_id

        domain = [("student_id.student_partner_id", "=", partner.id)]

        case_count = request.env["education.discipline.case"].search_count(domain)
        pager = portal_pager(
            url="/my/discipline_cases",
            total=case_count,
            page=page,
            step=10
        )

        cases = request.env["education.discipline.case"].search(
            domain, limit=10, offset=pager["offset"], order="date desc, id desc"
        )

        values = {
            "cases": cases,
            "page_name": "discipline_cases",
            "pager": pager,
        }
        return request.render("education_discipline.portal_my_discipline_cases", values)

    @http.route(["/my/discipline_cases/report"], type="http", auth="user", website=True)
    def portal_report_discipline_case(self, **post):
        partner = request.env.user.partner_id

        # We need an active enrollment to link the case to the reporting student
        enrollment = request.env["education.enrollment"].sudo().search([
            ("student_partner_id", "=", partner.id),
            ("state", "=", "active")
        ], limit=1)

        if request.httprequest.method == "POST":
            # Process form
            violation_type_id = int(post.get("violation_type_id"))
            date = post.get("date")
            description = post.get("description")
            remarks = post.get("remarks")

            request.env["education.discipline.case"].sudo().create({
                "student_id": enrollment.id if enrollment else False,
                "violation_type_id": violation_type_id,
                "date": date,
                "description": description,
                "remarks": remarks,
                "severity": "minor",  # Defaulting severity, admin handles the rest
                "state": "reported",
            })

            return request.redirect("/my/discipline_cases")

        violation_types = request.env["education.violation.type"].sudo().search([])

        values = {
            "violation_types": violation_types,
            "page_name": "report_discipline_case",
            "has_enrollment": bool(enrollment)
        }

        return request.render("education_discipline.portal_discipline_case_report", values)
