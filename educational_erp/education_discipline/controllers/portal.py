# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError


class DisciplinePortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        is_admin = request.env.user._is_admin() or request.env.user.has_group(
            'education_security.group_education_admin')

        if "school_rule_count" in counters:
            values["school_rule_count"] = request.env["education.school.rule"].sudo().search_count(
                [("active", "=", True)])

        if "discipline_case_count" in counters:
            partner = request.env.user.partner_id
            if is_admin:
                domain = []
            else:
                domain = [
                    "|",
                    ("student_id.student_partner_id", "=", partner.id),
                    ("reported_by_id", "=", request.env.user.id),
                ]
            values["discipline_case_count"] = request.env["education.discipline.case"].search_count(domain)

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
        is_admin = request.env.user.has_group(
            'education_security.group_education_admin') or request.env.user._is_admin()
        values = {
            "rules": rules,
            "category_label": label,
            "page_name": "school_rules",
            "is_admin": is_admin,
        }
        return request.render("education_discipline.portal_school_rules_category", values)

    @http.route(["/my/school_rules/edit/<int:rule_id>"], type="http", auth="user", website=True, methods=["POST"])
    def portal_school_rule_edit(self, rule_id, **kw):
        is_admin = request.env.user.has_group(
            'education_security.group_education_admin') or request.env.user._is_admin()
        if not is_admin:
            raise AccessError(_("You are not allowed to edit school rules."))

        rule = request.env["education.school.rule"].sudo().browse(rule_id)
        if rule.exists():
            rule.write({
                'name': kw.get('name'),
                'description': kw.get('description')
            })
            return request.redirect("/my/school_rules/%s" % rule.category)
        return request.redirect("/my/school_rules")

    @http.route(["/my/discipline_cases", "/my/discipline_cases/page/<int:page>"], type="http", auth="user",
                website=True)
    def portal_my_discipline_cases(self, page=1, **kw):
        partner = request.env.user.partner_id

        if request.env.user.has_group('education_security.group_education_admin') or request.env.user._is_admin():
            domain = []
        else:
            domain = [
                "|",
                ("student_id.student_partner_id", "=", partner.id),
                ("reported_by_id", "=", request.env.user.id),
            ]

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
            reported_against_id = int(post.get("student_id"))

            request.env["education.discipline.case"].sudo().create({
                "student_id": reported_against_id,
                "violation_type_id": violation_type_id,
                "date": date,
                "description": description,
                "remarks": remarks,
                "severity": "minor",  # Defaulting severity, admin handles the rest
                "state": "reported",
            })

            return request.redirect("/my/discipline_cases")

        violation_types = request.env["education.violation.type"].sudo().search([])
        # Exclude the current student's own enrollment from the reported against list
        student_domain = [("state", "=", "active")]
        if enrollment:
            student_domain.append(("id", "!=", enrollment.id))
        students = request.env["education.enrollment"].sudo().search(student_domain)

        values = {
            "violation_types": violation_types,
            "students": students,
            "page_name": "report_discipline_case",
            "has_enrollment": bool(enrollment)
        }

        return request.render("education_discipline.portal_discipline_case_report", values)

    @http.route(["/my/discipline_cases/<int:case_id>"], type="http", auth="user", website=True)
    def portal_discipline_case_detail(self, case_id, **kw):
        case = request.env["education.discipline.case"].sudo().browse(case_id)
        if not case.exists():
            return request.redirect("/my/discipline_cases")

        is_admin = request.env.user.has_group(
            'education_security.group_education_admin') or request.env.user._is_admin()
        partner = request.env.user.partner_id

        if not is_admin and case.student_id.student_partner_id != partner and case.reported_by_id != request.env.user:
            raise AccessError(_("You are not allowed to access this disciplinary case."))

        if request.httprequest.method == "POST" and is_admin:
            action_id = kw.get("action_id")
            action_date = kw.get("action_date")
            update_vals = {}
            if action_id:
                update_vals["action_id"] = int(action_id)
            if action_date:
                update_vals["action_date"] = action_date

            if update_vals:
                case.write(update_vals)
                if case.state in ['draft', 'reported', 'under_review']:
                    case.state = 'action_taken'
            return request.redirect("/my/discipline_cases/%s" % case_id)

        actions = request.env["education.disciplinary.action"].sudo().search([]) if is_admin else []

        values = {
            "case": case,
            "actions": actions,
            "is_admin": is_admin,
            "page_name": "discipline_case_detail",
        }

        return request.render("education_discipline.portal_discipline_case_detail", values)

    @http.route(["/my/discipline_cases/<int:case_id>/review"], type="http", auth="user", website=True, methods=["POST"])
    def portal_discipline_case_set_review(self, case_id, **kw):
        is_admin = request.env.user.has_group(
            'education_security.group_education_admin') or request.env.user._is_admin()
        if not is_admin:
            raise AccessError(_("Only administrators can set a case to Under Review."))

        case = request.env["education.discipline.case"].sudo().browse(case_id)
        if case.exists() and case.state == 'reported':
            case.state = 'under_review'

        return request.redirect("/my/discipline_cases/%s" % case_id)
