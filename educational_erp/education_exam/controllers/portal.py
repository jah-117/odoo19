from datetime import datetime
from odoo import http, fields, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class ExamPortal(CustomerPortal):
    """Customer Portal controller for Examinations, Results, and Revaluations."""

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        enrollment = request.env["education.enrollment"].sudo().search([
                ("student_partner_id", "=", partner.id),
            ])
        if "exam_result_count" in counters:
            values["exam_result_count"] = len(enrollment)
        if "scheduled_exam_count" in counters:
            values["scheduled_exam_count"] = len(enrollment)
        return values

    # ── Scheduled Examinations ──────────────────────────────────────────

    @http.route(["/my/examinations"], type="http", auth="user", website=True)
    def portal_my_examinations(self, **kw):
        partner = request.env.user.partner_id
        enrollment = request.env["education.enrollment"].sudo().search([
            ("student_partner_id", "=", partner.id)
        ])
        exams = request.env["edu.exam"].sudo().search([
            ("class_ids", "in", [enrollment.class_id.id]),
            ('state', 'in', ["scheduled","ongoing","valuation","result_published"]),
        ], order="date_from desc, id asc")
        seating = request.env["edu.exam.seating"].sudo().search([
            ("enrollment_id", "in", enrollment.ids),
            ("exam_id", "in", exams.ids),
        ])
        seating_map = {s.exam_id.id: s for s in seating}
        registration_map = {
            exam.id: enrollment.id in exam.registered_enrollment_ids.ids
            for exam in exams
        }
        return request.render(
            "education_exam.portal_my_examinations",
            {
                "exams": exams,
                "seating_map": seating_map,
                "page_name": "examinations",
                "registration_map": registration_map
            },
        )

    @http.route(["/my/exam/register/<int:exam_id>",], type="http", auth="user", website=True)
    def portal_exam_registration(self, exam_id):
        exam = request.env['edu.exam'].sudo().browse(exam_id)
        return request.render(
            "education_exam.portal_exam_register",{'exam':exam}
        )
    @http.route(["/my/exam/register/<int:exam_id>/generate_payment_url"])
    def portal_exam_register_generate_payment_url(self, exam_id):
        exam = request.env['edu.exam'].sudo().browse(exam_id)
        partner = request.env.user.partner_id
        invoice = request.env["account.move"].sudo().create({
            'move_type': 'out_invoice',
            'invoice_date': datetime.now(),
            'partner_id': partner.id,
            'invoice_type': "exam_fee",
        })
        invoice.update({'invoice_line_ids': [fields.Command.create({
            'product_id': request.env.ref('education_exam.exam_fee_product').id,
            'name': "Exam fee",
            'quantity': 1,
            'price_unit': exam.exam_fee,
            'price_subtotal': exam.exam_fee})]
        })
        invoice.action_post()
        exam.invoice_ids = [fields.Command.link(invoice.id)]
        exam.registered_enrollment_ids = [fields.Command.link(request.env["education.enrollment"].sudo().search([
            ("student_partner_id", "=", partner.id)
        ]).id)]
        return request.redirect(invoice.get_portal_url(anchor='portal_pay', query_string='&amp;payment=True'))



    @http.route(["/my/exam/admit_card/<int:exam_id>"], type="http", auth="user", website=True)
    def portal_exam_admit_card(self, exam_id, **kw):
        partner = request.env.user.partner_id
        enrollments = request.env["education.enrollment"].sudo().search([
            ("student_partner_id", "=", partner.id),
            ("state", "=", "active"),
        ])
        seating = request.env["edu.exam.seating"].sudo().search([
            ("exam_id", "=", exam_id),
            ("enrollment_id", "in", enrollments.ids),
        ], limit=1)
        if not seating:
            return request.redirect("/my/examinations")

        pdf, _ = request.env["ir.actions.report"].sudo()._render_qweb_pdf(
            "education_exam.action_report_admit_card", [seating.id]
        )
        pdfhttpheaders = [
            ("Content-Type", "application/pdf"),
            ("Content-Length", len(pdf)),
            ("Content-Disposition", f"attachment; filename=Admit_Card_{seating.student_name}.pdf"),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)

    # ── Examination Results & Revaluation ───────────────────────────────

    @http.route(["/my/exam/results"], type="http", auth="user", website=True)
    def portal_my_exam_results(self, **kw):
        partner = request.env.user.partner_id
        # Retrieve all student results for exams that are published or closed
        results = request.env["edu.exam.result"].sudo().search([
            ("enrollment_id.student_partner_id", "=", partner.id),
            ("exam_id.state", "in", ["result_published", "closed"]),
        ])

        # Group results by exam
        exams = results.mapped("exam_id")

        # Build summary statistics per exam for the list view
        now = fields.Datetime.now()
        exam_summaries = []
        for exam in exams:
            exam_res = results.filtered(lambda r: r.exam_id == exam)

            def _get_published_marks(r):
                if r.state == "draft" and r.history_ids:
                    return r.history_ids.sorted("id")[0].old_marks
                return r.marks_obtained

            total_obt = sum(_get_published_marks(r) for r in exam_res)
            total_max = sum(exam_res.mapped("max_marks"))
            pct = (total_obt / total_max * 100) if total_max else 0.0
            has_failed = any(
                (_get_published_marks(r) < r.pass_marks if r.pass_marks else False)
                for r in exam_res
            )
            has_under_reval = any(r.state == "draft" for r in exam_res)

            pub_dates = [r.published_at for r in exam_res if r.published_at]
            if exam.published_at:
                pub_dates.append(exam.published_at)
            latest_pub = max(pub_dates) if pub_dates else (exam.write_date or False)

            # Check if newly published (e.g. within 7 days) or updated after revaluation
            is_recent_publish = False
            if latest_pub:
                delta_days = (now - latest_pub).total_seconds() / 86400.0
                if 0 <= delta_days <= 7:
                    is_recent_publish = True

            all_histories = exam_res.mapped("history_ids")
            has_revaluation = bool(
                all_histories
                or any(req.state in ("approved", "revaluated") for req in exam_res.mapped("reevaluation_ids"))
            )

            is_new = bool(is_recent_publish or has_revaluation)

            exam_summaries.append({
                "exam": exam,
                "subject_count": len(exam_res),
                "total_obtained": total_obt,
                "total_max": total_max,
                "percentage": pct,
                "has_failed": has_failed,
                "has_under_reval": has_under_reval,
                "published_at": latest_pub,
                "is_new": is_new,
                "has_revaluation": has_revaluation,
            })

        # Explicitly sort exam_summaries by results published date descending
        min_dt = datetime.min
        exam_summaries.sort(
            key=lambda item: (
                item["published_at"] or min_dt,
                item["exam"].write_date or min_dt,
                item["exam"].id or 0,
            ),
            reverse=True,
        )

        return request.render(
            "education_exam.portal_my_exam_results",
            {
                "exams": [item["exam"] for item in exam_summaries],
                "exam_summaries": exam_summaries,
                "results": results,
                "reval_success": kw.get("reval_success"),
                "reval_error": kw.get("reval_error"),
                "page_name": "exam_results",
            },
        )

    @http.route(["/my/exam/result/<int:exam_id>", "/my/exam/results/<int:exam_id>"], type="http", auth="user", website=True)
    def portal_my_exam_result_detail(self, exam_id, **kw):
        partner = request.env.user.partner_id
        exam = request.env["edu.exam"].sudo().browse(exam_id)
        if not exam.exists() or exam.state not in ["result_published", "closed"]:
            return request.redirect("/my/exam/results")

        enrollments = request.env["education.enrollment"].sudo().search([("student_partner_id", "=", partner.id)])
        results = request.env["edu.exam.result"].sudo().search([
            ("exam_id", "=", exam.id),
            ("enrollment_id", "in", enrollments.ids),
        ], order="subject_id asc, id asc")

        if not results:
            return request.redirect("/my/exam/results")

        # Fetch student's revaluation requests and map by result_id
        revaluations = request.env["edu.exam.reevaluation.request"].sudo().search([
            ("enrollment_id.student_partner_id", "=", partner.id),
            ("result_id", "in", results.ids),
        ], order="id desc")
        reval_map = {}
        for rev in revaluations:
            if rev.result_id.id not in reval_map:
                reval_map[rev.result_id.id] = rev

        now = fields.Datetime.now()
        pub_dates = [r.published_at for r in results if r.published_at]
        if exam.published_at:
            pub_dates.append(exam.published_at)
        latest_pub = max(pub_dates) if pub_dates else (exam.write_date or False)
        is_recent_publish = bool(latest_pub and 0 <= (now - latest_pub).total_seconds() / 86400.0 <= 7)
        has_revaluation = bool(results.mapped("history_ids") or any(req.state in ("approved", "revaluated") for req in results.mapped("reevaluation_ids")))
        is_new = bool(is_recent_publish or has_revaluation)

        return request.render(
            "education_exam.portal_my_exam_result_detail",
            {
                "exam": exam,
                "results": results,
                "reval_map": reval_map,
                "is_new": is_new,
                "has_revaluation": has_revaluation,
                "reval_success": kw.get("reval_success"),
                "reval_error": kw.get("reval_error"),
                "page_name": "exam_result_detail",
            },
        )

    @http.route(["/my/exam/revaluation/submit"], type="http", auth="user", methods=["POST"], website=True, csrf=True)
    def portal_submit_revaluation(self, result_id=None, reason=None, **kw):
        partner = request.env.user.partner_id
        if not result_id or not reason or not reason.strip():
            target_url = f"/my/exam/result/{result_id}" if result_id else "/my/exam/results"
            return request.redirect(f"{target_url}?reval_error=Reason+is+required")

        result = request.env["edu.exam.result"].sudo().browse(int(result_id))
        if not result.exists() or result.enrollment_id.student_partner_id != partner:
            return request.redirect("/my/exam/results?reval_error=Invalid+result+selection")

        exam_id = result.exam_id.id
        if result.exam_id.state == "closed":
            return request.redirect(f"/my/exam/result/{exam_id}?reval_error=Revaluation+cannot+be+requested+for+a+closed+examination")

        # Check if already has a pending revaluation request
        existing_pending = request.env["edu.exam.reevaluation.request"].sudo().search([
            ("result_id", "=", result.id),
            ("state", "=", "pending"),
        ], limit=1)
        if existing_pending:
            return request.redirect(f"/my/exam/result/{exam_id}?reval_error=A+revaluation+request+is+already+pending+for+this+subject")

        # Create new revaluation request
        request.env["edu.exam.reevaluation.request"].sudo().create({
            "result_id": result.id,
            "reason": reason.strip(),
            "state": "pending",
        })

        return request.redirect(f"/my/exam/result/{exam_id}?reval_success=1")

    @http.route(["/my/exam/result/pdf/<int:exam_id>"], type="http", auth="user", website=True)
    def portal_exam_result_pdf(self, exam_id, **kw):
        partner = request.env.user.partner_id
        enrollments = request.env["education.enrollment"].sudo().search([
            ("student_partner_id", "=", partner.id),
            ("state", "=", "active"),
        ])
        exam = request.env["edu.exam"].sudo().browse(exam_id)
        if not exam.exists() or exam.state not in ["result_published", "closed"]:
            return request.redirect("/my/exam/results")

        results = request.env["edu.exam.result"].sudo().search([
            ("exam_id", "=", exam.id),
            ("enrollment_id", "in", enrollments.ids),
        ], order="subject_id asc, id asc")
        if not results:
            return request.redirect("/my/exam/results")

        enrollment = results[0].enrollment_id

        pdf, _ = request.env["ir.actions.report"].sudo()._render_qweb_pdf(
            "education_exam.action_report_individual_result",
            results.ids,
        )
        safe_student_name = (enrollment.student_name or "Student").replace(" ", "_")
        safe_exam_name = (exam.name or "Exam").replace(" ", "_")
        pdfhttpheaders = [
            ("Content-Type", "application/pdf"),
            ("Content-Length", len(pdf)),
            ("Content-Disposition", f"attachment; filename=Result_{safe_exam_name}_{safe_student_name}.pdf"),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)

    @http.route(["/my/exam/result/single/pdf/<int:result_id>"], type="http", auth="user", website=True)
    def portal_exam_single_result_pdf(self, result_id, **kw):
        partner = request.env.user.partner_id
        result = request.env["edu.exam.result"].sudo().browse(result_id)
        if not result.exists() or result.enrollment_id.student_partner_id != partner or result.state != "published":
            return request.redirect("/my/exam/results")

        pdf, _ = request.env["ir.actions.report"].sudo()._render_qweb_pdf(
            "education_exam.action_report_individual_result",
            [result.id],
        )
        safe_name = f"{result.student_name}_{result.subject_id.name}".replace(" ", "_")
        pdfhttpheaders = [
            ("Content-Type", "application/pdf"),
            ("Content-Length", len(pdf)),
            ("Content-Disposition", f"attachment; filename=Result_{safe_name}.pdf"),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)

