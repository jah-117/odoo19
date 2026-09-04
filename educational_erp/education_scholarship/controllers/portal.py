# -*- coding: utf-8 -*-
"""
education_scholarship — Portal Controller
==========================================
Extends the student portal to show available scholarships that match
the student's academic year, and allows one-click application.

URL scheme:  /student/scholarship/apply/<id>  — apply for a scholarship
"""
import logging

from markupsafe import Markup
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError

from odoo.addons.education_core.controllers.portal import EducationPortal


class ScholarshipPortal(EducationPortal):
    """Extend EducationPortal with scholarship listing and application."""

    def _prepare_home_portal_values(self, counters):
        """Add scholarship count to portal home page."""
        values = super()._prepare_home_portal_values(counters)
        if "scholarship_count" in counters:
            partner = request.env.user.partner_id
            enrollments = request.env['education.enrollment'].sudo().search([
                ('student_partner_id', '=', partner.id),
                ('state', '=', 'active'),
            ])
            active_enrollment = enrollments[:1]
            if active_enrollment:
                count = request.env['education.scholarship'].sudo().search_count([
                    ('state', '=', 'active'),
                    ('academic_year_id', '=', active_enrollment.academic_year_id.id),
                ])
                values["scholarship_count"] = count
            else:
                values["scholarship_count"] = 0

        if "admin_scholarship_count" in counters or "admin_scholarship_app_count" in counters:
            if request.env.user.has_group('education_security.group_education_admin') or request.env.user._is_admin():
                values["admin_scholarship_count"] = request.env['education.scholarship'].sudo().search_count([])
                values["admin_scholarship_app_count"] = request.env[
                    'education.scholarship.application'].sudo().search_count([])
            else:
                values["admin_scholarship_count"] = 0
                values["admin_scholarship_app_count"] = 0

        return values

    @http.route(['/student/scholarships', '/student/scholarships/page/<int:page>'], type='http',
                auth='user', website=True)
    def scholarship_dashboard(self, page=1, **kw):
        """Scholarship portal dashboard — available scholarships."""
        partner = request.env.user.partner_id

        # All enrollments for the student (matches parent behaviour)
        enrollments = request.env['education.enrollment'].sudo().search([
            ('student_partner_id', '=', partner.id),
        ])

        # The active enrollment determines which academic year to filter by
        active_enrollment = enrollments.filtered(lambda e: e.state == 'active')[:1]

        # Scholarships matching student's academic year
        scholarships = request.env['education.scholarship'].sudo().browse([])
        if active_enrollment:
            scholarships = request.env['education.scholarship'].sudo().search([
                ('state', '=', 'active'),
                ('academic_year_id', '=', active_enrollment.academic_year_id.id),
            ])

        # Already-applied scholarship IDs
        existing_applications = request.env['education.scholarship.application'].sudo().search([
            ('student_id', '=', active_enrollment.id if active_enrollment else 0),
        ])
        applied_scholarship_ids = existing_applications.mapped('scholarship_id').ids

        return request.render(
            'education_scholarship.portal_scholarships_dashboard',
            {
                'page_name': 'scholarship_dashboard',
                'scholarships': scholarships,
                'applied_scholarship_ids': applied_scholarship_ids,
                'enrollment': active_enrollment,
            },
        )

    @http.route(['/student/scholarship/<int:scholarship_id>'], type='http', auth='user', website=True)
    def scholarship_detail(self, scholarship_id, **kw):
        """Show scholarship details and application form."""
        scholarship = request.env['education.scholarship'].sudo().browse(scholarship_id)
        if not scholarship.exists() or scholarship.state != 'active':
            return request.redirect('/student/scholarships')

        partner = request.env.user.partner_id
        enrollment = request.env['education.enrollment'].sudo().search([
            ('student_partner_id', '=', partner.id),
            ('state', '=', 'active'),
        ], limit=1)

        existing = False
        if enrollment:
            existing = request.env['education.scholarship.application'].sudo().search_count([
                ('student_id', '=', enrollment.id),
                ('scholarship_id', '=', scholarship_id),
            ]) > 0

        return request.render('education_scholarship.portal_scholarship_detail', {
            'scholarship': scholarship,
            'page_name': 'scholarship_detail',
            'already_applied': existing,
            'has_enrollment': bool(enrollment),
        })

    @http.route(['/student/scholarship/apply/<int:scholarship_id>'], type='http',
                auth='user', website=True, methods=['POST'])
    def apply_scholarship(self, scholarship_id, **kw):
        """Create a scholarship application for the logged-in student."""
        partner = request.env.user.partner_id
        enrollment = request.env['education.enrollment'].sudo().search([
            ('student_partner_id', '=', partner.id),
            ('state', '=', 'active'),
        ], limit=1)

        if not enrollment:
            return request.redirect('/student/scholarships?error=no_enrollment')

        scholarship = request.env['education.scholarship'].sudo().browse(scholarship_id)
        if not scholarship.exists() or scholarship.state != 'active':
            return request.redirect('/student/scholarships?error=invalid_scholarship')

        # Check for duplicate application
        existing = request.env['education.scholarship.application'].sudo().search_count([
            ('student_id', '=', enrollment.id),
            ('scholarship_id', '=', scholarship_id),
        ])
        if existing:
            return request.redirect('/student/scholarships?error=already_applied')

        try:
            import base64
            attachment_ids = []
            criteria_data = []

            for criterion in scholarship.eligibility_ids:
                val = kw.get(f'criteria_val_{criterion.id}')
                if not val:
                    return request.redirect(f'/student/scholarship/{scholarship_id}?error=missing_documents')

                doc_attachment_ids = []
                if criterion.is_require_document:
                    file_field = f'criteria_doc_{criterion.id}'
                    if file_field in request.httprequest.files:
                        files = request.httprequest.files.getlist(file_field)
                        for f in files:
                            if f.filename:
                                data = f.read()
                                attachment = request.env['ir.attachment'].sudo().create({
                                    'name': f.filename,
                                    'type': 'binary',
                                    'datas': base64.b64encode(data),
                                })
                                doc_attachment_ids.append(attachment.id)
                                attachment_ids.append(attachment.id)
                    if not doc_attachment_ids:
                        return request.redirect(f'/student/scholarship/{scholarship_id}?error=missing_documents')

                criteria_data.append((0, 0, {
                    'eligibility_criteria_id': criterion.id,
                    'student_value': val,
                    'document_ids': [(6, 0, doc_attachment_ids)] if doc_attachment_ids else []
                }))

            if 'documents' in request.httprequest.files:
                files = request.httprequest.files.getlist('documents')
                for f in files:
                    if f.filename:
                        data = f.read()
                        attachment = request.env['ir.attachment'].sudo().create({
                            'name': f.filename,
                            'type': 'binary',
                            'datas': base64.b64encode(data),
                        })
                        attachment_ids.append(attachment.id)

            app = request.env['education.scholarship.application'].sudo().create({
                'student_id': enrollment.id,
                'scholarship_id': scholarship_id,
                'document_ids': [(6, 0, attachment_ids)] if attachment_ids else False,
                'submitted_criteria_ids': criteria_data
            })

            # Update attachments with res_model and res_id so they appear in the record
            if attachment_ids:
                request.env['ir.attachment'].sudo().browse(attachment_ids).write({
                    'res_model': 'education.scholarship.application',
                    'res_id': app.id,
                })

            # Build a rich chatter message listing each criterion with its submitted
            # value and the names of any documents uploaded for that criterion.
            body_lines = ["<p><strong>Application submitted via portal.</strong></p>",
                          "<table style='width:100%;border:none;'>",
                          ]

            for sub in app.submitted_criteria_ids:
                doc_links = ""
                if sub.document_ids:
                    doc_links = ", ".join(
                        f"<a href='/web/content/{doc.id}?download=true' target='_blank'>{doc.name}</a>"
                        for doc in sub.document_ids
                    )
                else:
                    doc_links = "<em>None</em>"
                body_lines.append(
                    f"<tr>"
                    f"<td style='border:none;padding:4px;'>{sub.eligibility_criteria_id.criteria_id.name}</td>"
                    f"<td style='border:none;padding:4px;'>{doc_links}</td>"
                    f"</tr>"
                )
            body_lines.append("</table>")

            # Post the message; pass attachment_ids so files appear inline in chatter
            app.sudo().message_post(
                body=Markup("".join(body_lines)),
                attachment_ids=attachment_ids or [],
            )

        except ValidationError:
            return request.redirect('/student/scholarships?error=already_applied')

        return request.redirect('/student/scholarships?success=applied')

    @http.route(['/my/admin/scholarships', '/my/admin/scholarships/page/<int:page>'], type='http', auth="user",
                website=True)
    def admin_scholarships_dashboard(self, page=1, **kw):
        if not (request.env.user.has_group('education_security.group_education_admin') or request.env.user._is_admin()):
            return request.redirect('/my')

        scholarships = request.env['education.scholarship'].sudo().search([])
        return request.render(
            'education_scholarship.portal_admin_scholarships_dashboard',
            {
                'page_name': 'admin_scholarship_dashboard',
                'scholarships': scholarships,
            },
        )

    @http.route(['/my/admin/scholarship/<int:scholarship_id>'], type='http', auth="user", website=True)
    def admin_scholarship_detail(self, scholarship_id, **kw):
        if not (request.env.user.has_group('education_security.group_education_admin') or request.env.user._is_admin()):
            return request.redirect('/my')

        scholarship = request.env['education.scholarship'].sudo().browse(scholarship_id)
        if not scholarship.exists():
            return request.redirect('/my/admin/scholarships')

        return request.render('education_scholarship.portal_admin_scholarship_detail', {
            'scholarship': scholarship,
            'page_name': 'admin_scholarship_detail',
        })

    @http.route(['/my/admin/scholarship/applications', '/my/admin/scholarship/applications/page/<int:page>'],
                type='http', auth="user", website=True)
    def admin_scholarship_apps_dashboard(self, page=1, **kw):
        if not (request.env.user.has_group('education_security.group_education_admin') or request.env.user._is_admin()):
            return request.redirect('/my')

        applications = request.env['education.scholarship.application'].sudo().search([])
        return request.render(
            'education_scholarship.portal_admin_scholarship_apps_dashboard',
            {
                'page_name': 'admin_scholarship_apps_dashboard',
                'applications': applications,
            },
        )

    @http.route(['/my/admin/scholarship/application/<int:app_id>'], type='http', auth="user", website=True)
    def admin_scholarship_app_detail(self, app_id, **kw):
        if not (request.env.user.has_group('education_security.group_education_admin') or request.env.user._is_admin()):
            return request.redirect('/my')

        application = request.env['education.scholarship.application'].sudo().browse(app_id)
        if not application.exists():
            return request.redirect('/my/admin/scholarship/applications')

        return request.render('education_scholarship.portal_admin_scholarship_app_detail', {
            'application': application,
            'page_name': 'admin_scholarship_app_detail',
        })
