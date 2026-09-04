# -*- coding: utf-8 -*-
"""Student-facing hostel accommodation portal."""

from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class HostelPortal(CustomerPortal):
    """Expose only the logged-in student's own hostel allocations."""

    def _get_own_allocations(self):
        """Return allocations owned by the current portal user's enrollment.

        The domain performs the primary server-side restriction.  Keep the
        explicit ownership filter as a second guard before records are handed
        to the template, following the other student portal controllers.
        """
        partner = request.env.user.partner_id
        allocations = request.env["edu.hostel.allocation"].sudo().search(
            [("enrollment_id.student_partner_id", "=", partner.id)],
            order="date_from desc, id desc",
        )
        return allocations.filtered(
            lambda allocation: allocation.enrollment_id.student_partner_id == partner
        )

    @http.route(["/my/hostel"], type="http", auth="user", website=True)
    def portal_my_hostel(self, **_kwargs):
        print('fakldfjalkdsfa')
        print(**_kwargs)
        """Render the current/pending accommodation and vacated history."""
        allocations = self._get_own_allocations()
        print('fakldfjalkdsfa')
        print(**_kwargs)
        current_allocation = allocations.filtered(
            lambda allocation: allocation.state == "confirmed"
        )[:1]
        pending_allocation = allocations.filtered(
            lambda allocation: allocation.state == "draft"
        )[:1]
        previous_allocations = allocations.filtered(
            lambda allocation: allocation.state == "vacated"
        ).sorted(
            key=lambda allocation: (
                allocation.date_to or allocation.date_from,
                allocation.id,
            ),
            reverse=True,
        )

        return request.render(
            "education_hostel.portal_my_hostel",
            {
                "current_allocation": current_allocation,
                "pending_allocation": pending_allocation,
                "previous_allocations": previous_allocations,
                "page_name": "hostel",
            },
        )
