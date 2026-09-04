# -*- coding: utf-8 -*-
"""
Unit tests — edu.exam, edu.exam.result (S4-T11)
================================================
Covers: exam creation, state machine, mark entry, grade computation,
history logging, rank calculation, and re-evaluation wizard.
"""
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError, UserError


@tagged("post_install", "-at_install")
class TestEduExam(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Academic year
        cls.academic_year = cls.env["education.academic.year"].create({
            "name": "Test Year 2026",
            "code": "TEST2026",
            "date_start": "2026-01-01",
            "date_end": "2026-12-31",
        })

        # Department & program
        dept = cls.env["education.department"].create({
            "name": "Test Dept",
            "code": "TDEPT",
        })
        cls.program = cls.env["education.program"].create({
            "name": "Test Program",
            "code": "TEST",
            "department_id": dept.id,
        })

        # Subjects
        cls.subj_math = cls.env["education.subject"].create({
            "name": "Mathematics",
            "code": "MATH",
            "program_id": cls.program.id,
        })
        cls.subj_english = cls.env["education.subject"].create({
            "name": "English",
            "code": "ENG",
            "program_id": cls.program.id,
        })
        cls.subj_science = cls.env["education.subject"].create({
            "name": "Science",
            "code": "SCI",
            "program_id": cls.program.id,
        })

        # Class
        cls.edu_class = cls.env["education.class"].create({
            "section": "A",
            "academic_year_id": cls.academic_year.id,
            "program_id": cls.program.id,
        })

        # Classroom
        cls.classroom = cls.env["edu.classroom"].create({
            "room_no": "H101",
            "block": "Exam",
            "capacity": 40,
            "room_type": "hall",
        })

        # Application → enrollment helper
        def _make_enrollment(first_name, email):
            app = cls.env["education.application"].create({
                "first_name": first_name,
                "date_of_birth": "2000-06-15",
                "gender": "male",
                "email": email,
                "phone": "9999999999",
                "academic_year_id": cls.academic_year.id,
                "program_id": cls.program.id,
            })
            app.action_submit()
            app.action_approve()
            enr = app.enrollment_id
            enr.write({"class_id": cls.edu_class.id})
            return enr

        cls.enr1 = _make_enrollment("Alice", "alice.test@exam.com")
        cls.enr2 = _make_enrollment("Bob", "bob.test@exam.com")
        cls.enr3 = _make_enrollment("Carol", "carol.test@exam.com")

    # ── Exam CRUD ──────────────────────────────────────────────────────────

    def _make_exam(self):
        return self.env["edu.exam"].create({
            "name": "Mid-Term Nov 2026",
            "exam_type": "mid_term",
            "academic_year_id": self.academic_year.id,
            "date_from": "2026-11-01",
            "date_to": "2026-11-10",
            "class_ids": [(4, self.edu_class.id)],
            "subject_line_ids": [
                (0, 0, {
                    "subject_id": self.subj_math.id,
                    "exam_date": "2026-11-01",
                    "classroom_id": self.classroom.id,
                    "max_marks": 100.0,
                    "pass_marks": 40.0,
                }),
                (0, 0, {
                    "subject_id": self.subj_english.id,
                    "exam_date": "2026-11-03",
                    "classroom_id": self.classroom.id,
                    "max_marks": 100.0,
                    "pass_marks": 40.0,
                }),
            ],
        })

    def test_exam_creation_auto_code(self):
        exam = self._make_exam()
        self.assertNotEqual(exam.code, "New")
        self.assertTrue(exam.code.startswith("EXAM/"))

    def test_exam_date_constraint(self):
        with self.assertRaises(ValidationError):
            self.env["edu.exam"].create({
                "name": "Bad Dates",
                "exam_type": "unit_test",
                "academic_year_id": self.academic_year.id,
                "date_from": "2026-11-10",
                "date_to": "2026-11-01",  # end before start
            })

    def test_subject_schedule_mandatory_fields(self):
        # Missing exam_date, exam_time or classroom_id should fail
        with self.assertRaises(Exception):
            self.env["edu.exam.subject"].create({
                "subject_id": self.subj_math.id,
                "exam_date": False,
                "classroom_id": self.classroom.id,
            })
        with self.assertRaises(Exception):
            self.env["edu.exam.subject"].create({
                "subject_id": self.subj_math.id,
                "exam_date": "2026-11-01",
                "classroom_id": False,
            })
        with self.assertRaises(Exception):
            self.env["edu.exam.subject"].create({
                "subject_id": self.subj_math.id,
                "exam_date": "2026-11-01",
                "exam_time": False,
                "classroom_id": self.classroom.id,
            })


    # ── State Machine ──────────────────────────────────────────────────────

    def test_state_machine_full_cycle(self):
        exam = self._make_exam()
        self.assertEqual(exam.state, "draft")

        exam.action_schedule()
        self.assertEqual(exam.state, "scheduled")

        exam.action_start()
        self.assertEqual(exam.state, "ongoing")

        exam.action_start_valuation()
        self.assertEqual(exam.state, "valuation")

        # Add a result before publishing
        self.env["edu.exam.result"].create({
            "exam_id": exam.id,
            "enrollment_id": self.enr1.id,
            "subject_id": self.subj_math.id,
            "marks_obtained": 75.0,
            "max_marks": 100.0,
            "pass_marks": 40.0,
            "state": "draft",
        })
        exam.action_publish_results()
        self.assertEqual(exam.state, "result_published")

        exam.action_close()
        self.assertEqual(exam.state, "closed")

    def test_schedule_without_subjects_raises(self):
        exam = self.env["edu.exam"].create({
            "name": "No Subjects",
            "exam_type": "unit_test",
            "academic_year_id": self.academic_year.id,
            "date_from": "2026-11-01",
            "date_to": "2026-11-02",
        })
        with self.assertRaises(UserError):
            exam.action_schedule()

    # ── Mark Entry & Grade Computation ───────────────────────────────────

    def _make_result(self, exam, enrollment, subject, marks, max_marks=100.0, pass_marks=40.0):
        return self.env["edu.exam.result"].create({
            "exam_id": exam.id,
            "enrollment_id": enrollment.id,
            "subject_id": subject.id,
            "marks_obtained": marks,
            "max_marks": max_marks,
            "pass_marks": pass_marks,
        })

    def test_grade_computation(self):
        exam = self._make_exam()
        r_aplus = self._make_result(exam, self.enr1, self.subj_math, 95)
        r_a = self._make_result(exam, self.enr2, self.subj_math, 82)
        r_fail = self._make_result(exam, self.enr3, self.subj_math, 35)

        self.assertEqual(r_aplus.grade, "A+")
        self.assertEqual(r_aplus.pass_fail, "pass")
        self.assertAlmostEqual(r_aplus.percentage, 95.0)

        self.assertEqual(r_a.grade, "A")
        self.assertEqual(r_a.pass_fail, "pass")

        self.assertEqual(r_fail.grade, "F")
        self.assertEqual(r_fail.pass_fail, "fail")

    def test_absent_result(self):
        exam = self._make_exam()
        r = self._make_result(exam, self.enr1, self.subj_english, 0)
        r.write({"absent": True})
        self.assertEqual(r.pass_fail, "absent")
        self.assertEqual(r.grade, "AB")

    def test_marks_exceeds_max_raises(self):
        exam = self._make_exam()
        with self.assertRaises(ValidationError):
            self._make_result(exam, self.enr1, self.subj_science, 105, max_marks=100)

    def test_marks_negative_raises(self):
        exam = self._make_exam()
        with self.assertRaises(ValidationError):
            self._make_result(exam, self.enr1, self.subj_science, -5)

    # ── Rank Computation ─────────────────────────────────────────────────

    def test_rank_calculation(self):
        exam = self._make_exam()
        r1 = self._make_result(exam, self.enr1, self.subj_math, 90)
        r2 = self._make_result(exam, self.enr2, self.subj_math, 75)
        r3 = self._make_result(exam, self.enr3, self.subj_math, 60)

        # Force recompute
        (r1 | r2 | r3)._compute_rank()

        self.assertEqual(r1.rank, 1)
        self.assertEqual(r2.rank, 2)
        self.assertEqual(r3.rank, 3)

    # ── History Logging ───────────────────────────────────────────────────

    def test_marks_change_logged_in_history(self):
        exam = self._make_exam()
        result = self._make_result(exam, self.enr1, self.subj_math, 70)
        initial_history = len(result.history_ids)

        result.write({"marks_obtained": 80.0})

        self.assertEqual(len(result.history_ids), initial_history + 1)
        latest = result.history_ids.sorted("change_date", reverse=True)[0]
        self.assertEqual(latest.old_marks, 70.0)
        self.assertEqual(latest.new_marks, 80.0)
        self.assertEqual(latest.delta, 10.0)

    # ── Re-evaluation Wizard ──────────────────────────────────────────────

    def test_reevaluation_resets_to_draft(self):
        exam = self._make_exam()
        result = self._make_result(exam, self.enr1, self.subj_math, 65)
        result.write({"state": "published"})

        wizard = self.env["edu.exam.reevaluation.wizard"].create({
            "result_id": result.id,
            "reason": "Marks tallied incorrectly by teacher",
        })
        wizard.action_submit()

        self.assertEqual(result.state, "draft")
        history = result.history_ids.filtered(
            lambda h: "RE-EVALUATION" in (h.reason or "")
        )
        self.assertTrue(history)

    def test_reevaluation_blocked_when_exam_closed(self):
        exam = self._make_exam()
        exam.action_schedule()
        exam.action_start()
        exam.action_start_valuation()

        result = self._make_result(exam, self.enr1, self.subj_math, 65)
        result.write({"state": "published"})
        exam.write({"state": "closed"})

        # Creating revaluation request directly on a closed exam must raise ValidationError
        with self.assertRaises(ValidationError):
            self.env["edu.exam.reevaluation.request"].create({
                "result_id": result.id,
                "reason": "Request after exam is closed",
            })

        # Wizard submit on a closed exam must raise ValidationError
        wizard = self.env["edu.exam.reevaluation.wizard"].create({
            "result_id": result.id,
            "reason": "Requesting after closure check",
        })
        with self.assertRaises(ValidationError):
            wizard.action_submit()

    def test_action_enter_marks(self):
        exam = self._make_exam()
        action = exam.action_enter_marks()
        self.assertEqual(action.get("type"), "ir.actions.act_window")
        self.assertEqual(action.get("res_model"), "edu.exam.mark.entry.wizard")
        self.assertEqual(action.get("target"), "new")
        self.assertEqual(action.get("context", {}).get("default_exam_id"), exam.id)
        self.assertEqual(
            action.get("context", {}).get("default_class_id"), self.edu_class.id
        )

    def test_teacher_read_only_and_mark_entry(self):
        from odoo.exceptions import AccessError
        teacher_group = self.env.ref("education_security.group_education_teacher")
        teacher_user = self.env["res.users"].create({
            "name": "Teacher User",
            "login": "teacher_user_test",
            "email": "teacher_user_test@example.com",
            "group_ids": [(6, 0, [self.env.ref("base.group_user").id, teacher_group.id])],
        })

        exam = self._make_exam()
        exam.action_schedule()
        exam.action_start()
        exam.action_start_valuation()

        # Direct write to edu.exam by teacher must raise AccessError (read-only for teacher)
        with self.assertRaises(AccessError):
            exam.with_user(teacher_user).write({"name": "Tampered Name"})

        # But teacher can use the mark entry wizard to enter student scores without AccessError
        wiz = self.env["edu.exam.mark.entry.wizard"].with_user(teacher_user).create({
            "exam_id": exam.id,
            "class_id": self.edu_class.id,
        })
        wiz.with_user(teacher_user)._onchange_load()
        self.assertTrue(len(wiz.line_ids) > 0)
        wiz.line_ids[0].marks_obtained = 88.0
        wiz.with_user(teacher_user).action_save_marks()

        # Verify result was created/updated
        res = self.env["edu.exam.result"].search([
            ("exam_id", "=", exam.id),
            ("enrollment_id", "=", self.enr1.id),
            ("subject_id", "=", self.subj_math.id),
        ])
        self.assertTrue(res)
        self.assertEqual(res.marks_obtained, 88.0)

        # Teacher cannot publish results
        with self.assertRaises(AccessError):
            exam.with_user(teacher_user).action_publish_results()
        with self.assertRaises(AccessError):
            res.with_user(teacher_user).action_publish()

        # Admin can publish results
        exam.action_publish_results()
        self.assertEqual(exam.state, "result_published")
        self.assertEqual(res.state, "published")


    def test_reevaluation_request_flow(self):
        exam = self._make_exam()
        result = self._make_result(exam, self.enr1, self.subj_math, 60)
        result.write({"state": "published"})

        req = self.env["edu.exam.reevaluation.request"].create({
            "result_id": result.id,
            "reason": "Section B marks omitted",
        })
        self.assertEqual(req.state, "pending")
        self.assertEqual(result.latest_reevaluation_state, "pending")

        req.action_approve()
        self.assertEqual(req.state, "approved")
        self.assertEqual(result.state, "draft")
        self.assertTrue(result.has_approved_reevaluation)

        # Test action_revaluate returns dedicated result revaluate wizard
        action = req.action_revaluate()
        self.assertEqual(action.get("type"), "ir.actions.act_window")
        self.assertEqual(action.get("res_model"), "edu.exam.result.revaluate.wizard")
        self.assertEqual(action.get("context", {}).get("default_result_id"), result.id)

        # Test action_revaluate directly on result record
        res_action = result.action_revaluate()
        self.assertEqual(res_action.get("res_model"), "edu.exam.result.revaluate.wizard")

        # Test executing the revaluation wizard
        wiz = self.env["edu.exam.result.revaluate.wizard"].with_context(res_action["context"]).create({
            "result_id": result.id,
            "new_marks": 78.0,
            "change_reason": "Corrected recalculation in Q4",
            "publish_result": True,
        })
        self.assertEqual(wiz.subject_id.id, self.subj_math.id)
        self.assertEqual(wiz.student_name, self.enr1.student_name)
        wiz.action_confirm_revaluation()
        self.assertEqual(result.marks_obtained, 78.0)
        self.assertEqual(result.state, "published")
        self.assertEqual(req.state, "revaluated")
        self.assertEqual(result.latest_reevaluation_state, "revaluated")
        self.assertFalse(result.has_approved_reevaluation)

        # Test that a new request can be created and approved later
        req2 = self.env["edu.exam.reevaluation.request"].create({
            "result_id": result.id,
            "reason": "Second review request for practical marks",
        })
        self.assertEqual(req2.state, "pending")
        req2.action_approve()
        self.assertEqual(req2.state, "approved")
        self.assertTrue(result.has_approved_reevaluation)

        # Save without publishing in wizard
        wiz2 = self.env["edu.exam.result.revaluate.wizard"].create({
            "result_id": result.id,
            "new_marks": 82.0,
            "change_reason": "Practical marks added",
            "publish_result": False,
        })
        wiz2.action_confirm_revaluation()
        self.assertEqual(req2.state, "revaluated")
        self.assertEqual(result.state, "draft")

        # Publish result from revaluation request
        req2.action_publish_result()
        self.assertEqual(result.state, "published")
        self.assertEqual(req2.state, "revaluated")

    def test_portal_result_history_access(self):
        exam = self._make_exam()
        result1 = self._make_result(exam, self.enr1, self.subj_math, 60)
        result1.write({"state": "published"})

        # Change marks to generate history
        result1.write({"marks_obtained": 75.0, "_change_reason": "Re-evaluation mark increase"})

        self.assertEqual(len(result1.history_ids), 1)
        history = result1.history_ids[0]
        self.assertEqual(history.old_marks, 60.0)
        self.assertEqual(history.new_marks, 75.0)
        self.assertEqual(history.delta, 15.0)
        self.assertEqual(history.reason, "Re-evaluation mark increase")

        # Create portal user for enr1
        portal_user = self.env["res.users"].create({
            "name": "Alice Portal",
            "login": "alice.portal.test",
            "email": "alice.portal.test@example.com",
            "partner_id": self.enr1.student_partner_id.id,
            "group_ids": [(6, 0, [self.env.ref("base.group_portal").id])],
        })

        # Portal user can read own history
        history_portal = self.env["edu.exam.result.history"].with_user(portal_user).search([
            ("result_id", "=", result1.id)
        ])
        self.assertTrue(history_portal)
        self.assertEqual(history_portal.id, history.id)

        # Portal user cannot see another student's history
        result2 = self._make_result(exam, self.enr2, self.subj_math, 50)
        result2.write({"marks_obtained": 65.0, "_change_reason": "Bob re-evaluation"})
        history2_portal = self.env["edu.exam.result.history"].with_user(portal_user).search([
            ("result_id", "=", result2.id)
        ])
        self.assertFalse(history2_portal)

    def test_individual_result_report_pdf(self):
        exam = self._make_exam()
        r1 = self._make_result(exam, self.enr1, self.subj_math, 88.0)
        r2 = self._make_result(exam, self.enr1, self.subj_english, 92.0)
        (r1 | r2).write({"state": "published"})

        # Render individual result PDF report
        pdf, _ = self.env["ir.actions.report"]._render_qweb_pdf(
            "education_exam.action_report_individual_result",
            [r1.id, r2.id],
        )
        self.assertTrue(pdf)
        self.assertTrue(len(pdf) > 100)

    def test_exam_results_tabulation_report_and_action(self):
        exam = self._make_exam()
        r1 = self._make_result(exam, self.enr1, self.subj_math, 85.0)
        r2 = self._make_result(exam, self.enr2, self.subj_math, 92.0)
        (r1 | r2).write({"state": "published"})

        # Test action_print_results returns report action dict
        res_action = exam.action_print_results()
        self.assertEqual(res_action.get("type"), "ir.actions.report")
        self.assertEqual(res_action.get("report_name"), "education_exam.report_exam_results_tabulation_template")

        # Test rendering PDF
        pdf, _ = self.env["ir.actions.report"]._render_qweb_pdf(
            "education_exam.action_report_exam_results_tabulation",
            [exam.id],
        )
        self.assertTrue(pdf)
        self.assertTrue(len(pdf) > 100)

    def test_published_at_timestamp_and_ordering(self):
        from datetime import datetime, timedelta

        exam = self._make_exam()
        exam.action_schedule()
        exam.action_start()
        exam.action_start_valuation()

        r1 = self._make_result(exam, self.enr1, self.subj_math, 85.0)
        r2 = self._make_result(exam, self.enr1, self.subj_english, 90.0)

        # Before publish, published_at is empty
        self.assertFalse(r1.published_at)
        self.assertFalse(exam.published_at)

        # Publish results via exam
        exam.action_publish_results()
        self.assertTrue(exam.published_at)
        self.assertTrue(r1.published_at)
        self.assertTrue(r2.published_at)

        # Explicitly test portal sorting order with distinct timestamps
        time_old = datetime(2026, 1, 1, 10, 0, 0)
        time_new = datetime(2026, 2, 1, 10, 0, 0)
        r1.write({"published_at": time_old})
        r2.write({"published_at": time_new})

        results = self.env["edu.exam.result"].search([
            ("enrollment_id.student_partner_id", "=", self.enr1.student_partner_id.id),
            ("state", "=", "published"),
            ("exam_id.state", "in", ["result_published", "closed"]),
        ], order="published_at desc, write_date desc, id desc")

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].id, r2.id)
        self.assertEqual(results[1].id, r1.id)

    def test_portal_exam_list_ordering_by_published_at(self):
        """Test multiple exams are ordered by published_at desc in portal."""
        from datetime import datetime

        # Exam 1 - older publish date
        exam1 = self._make_exam()
        exam1.write({"name": "Exam 1 (Older)"})
        exam1.action_schedule()
        exam1.action_start()
        exam1.action_start_valuation()
        r1 = self._make_result(exam1, self.enr1, self.subj_math, 80.0)
        exam1.action_publish_results()
        time_old = datetime(2026, 1, 15, 10, 0, 0)
        exam1.write({"published_at": time_old})
        r1.write({"published_at": time_old})

        # Exam 2 - newer publish date
        exam2 = self._make_exam()
        exam2.write({"name": "Exam 2 (Newer)"})
        exam2.action_schedule()
        exam2.action_start()
        exam2.action_start_valuation()
        r2 = self._make_result(exam2, self.enr1, self.subj_math, 95.0)
        exam2.action_publish_results()
        time_new = datetime(2026, 3, 20, 10, 0, 0)
        exam2.write({"published_at": time_new})
        r2.write({"published_at": time_new})

        # Distinct exams
        exams = results.mapped("exam_id")
        exam_summaries = []
        for exam in exams:
            exam_res = results.filtered(lambda r: r.exam_id == exam)
            pub_dates = [r.published_at for r in exam_res if r.published_at]
            if exam.published_at:
                pub_dates.append(exam.published_at)
            latest_pub = max(pub_dates) if pub_dates else (exam.write_date or False)
            exam_summaries.append({
                "exam": exam,
                "published_at": latest_pub,
            })

        min_dt = datetime.min
        exam_summaries.sort(
            key=lambda item: (
                item["published_at"] or min_dt,
                item["exam"].write_date or min_dt,
                item["exam"].id or 0,
            ),
            reverse=True,
        )

        self.assertEqual(len(exam_summaries), 2)
        self.assertEqual(exam_summaries[0]["exam"].id, exam2.id)
        self.assertEqual(exam_summaries[1]["exam"].id, exam1.id)

    def test_portal_exam_is_new_tag_indicator(self):
        """Test 'New' tag is flagged for recent publish and re-evaluated results."""
        from datetime import datetime, timedelta

        now = fields.Datetime.now()
        exam = self._make_exam()
        exam.action_schedule()
        exam.action_start()
        exam.action_start_valuation()
        r = self._make_result(exam, self.enr1, self.subj_math, 70.0)
        exam.action_publish_results()

        # Newly published exam (today)
        is_recent = bool(r.published_at and (now - r.published_at).total_seconds() / 86400.0 <= 7)
        self.assertTrue(is_recent)

        # After re-evaluation with mark change and history creation
        r.write({"marks_obtained": 82.0, "_change_reason": "Re-evaluation mark change"})
        has_reval = bool(r.history_ids)
        self.assertTrue(has_reval)
        is_new = bool(is_recent or has_reval)
        self.assertTrue(is_new)

    def test_portal_exam_visible_during_revaluation(self):
        """Test exam remains visible in portal results list and detail when result is reset to draft."""
        exam = self._make_exam()
        exam.action_schedule()
        exam.action_start()
        exam.action_start_valuation()
        r = self._make_result(exam, self.enr1, self.subj_math, 65.0)
        exam.action_publish_results()
        self.assertEqual(r.state, "published")
        self.assertEqual(exam.state, "result_published")

        # Create and approve revaluation request -> result is reset to draft
        req = self.env["edu.exam.reevaluation.request"].create({
            "result_id": r.id,
            "reason": "Requesting paper recheck",
        })
        req.action_approve()
        self.assertEqual(r.state, "draft")

        # Portal query for student's results in published exams must still find the exam
        results = self.env["edu.exam.result"].search([
            ("enrollment_id.student_partner_id", "=", self.enr1.student_partner_id.id),
            ("exam_id.state", "in", ["result_published", "closed"]),
        ])
        self.assertIn(r.id, results.ids)
        self.assertIn(exam.id, results.mapped("exam_id").ids)

        # Update marks while in draft (re-evaluation in progress)
        r.write({"marks_obtained": 90.0, "_change_reason": "Teacher updated score"})
        self.assertEqual(r.state, "draft")

        # Effective published marks for portal display should remain original (65.0) while in draft
        disp_marks = r.history_ids.sorted("id")[0].old_marks if (r.state == "draft" and r.history_ids) else r.marks_obtained
        self.assertEqual(disp_marks, 65.0)

        # Once published, disp_marks becomes the new revised marks (90.0)
        r.action_publish()
        self.assertEqual(r.state, "published")
        disp_marks_published = r.history_ids.sorted("id")[0].old_marks if (r.state == "draft" and r.history_ids) else r.marks_obtained
        self.assertEqual(disp_marks_published, 90.0)

    def test_reevaluation_rejection_with_reason_wizard(self):
        """Test admin rejection wizard captures reason and reflects on request record."""
        exam = self._make_exam()
        exam.action_schedule()
        exam.action_start()
        exam.action_start_valuation()
        r = self._make_result(exam, self.enr1, self.subj_math, 55.0)
        exam.action_publish_results()

        req = self.env["edu.exam.reevaluation.request"].create({
            "result_id": r.id,
            "reason": "Requesting remarking for question 4",
        })
        self.assertEqual(req.state, "pending")

        # Action reject returns the wizard action
        act = req.action_reject()
        self.assertEqual(act.get("res_model"), "edu.exam.reevaluation.reject.wizard")

        # Admin completes rejection wizard with mandatory reason
        wizard = self.env["edu.exam.reevaluation.reject.wizard"].create({
            "request_id": req.id,
            "rejection_reason": "Grading rubrics verified. Score accurately awarded.",
        })
        wizard.action_confirm_reject()

        # Request state is rejected and reason is saved in admin_notes
        self.assertEqual(req.state, "rejected")
        self.assertEqual(req.admin_notes, "Grading rubrics verified. Score accurately awarded.")
        self.assertTrue(req.review_date)

    def test_result_company_and_report_rendering(self):
        """Test company_id field on edu.exam.result and rendering of individual result report."""
        exam = self._make_exam()
        exam.action_schedule()
        exam.action_start()
        exam.action_start_valuation()
        r = self._make_result(exam, self.enr1, self.subj_math, 88.0)
        exam.action_publish_results()

        # company_id is populated from exam
        self.assertEqual(r.company_id, exam.company_id)
        self.assertEqual(r.company_id, self.env.company)

        # Render report qweb
        report = self.env.ref("education_exam.action_report_individual_result")
        content, content_type = report._render_qweb_pdf(report.report_name, res_ids=r.ids)
        self.assertTrue(content)
        self.assertEqual(content_type, "pdf")

    def test_exam_reset_draft_only_when_scheduled(self):
        """Test reset to draft is only permitted when examination is in scheduled state."""
        exam = self._make_exam()
        self.assertEqual(exam.state, "draft")

        # In draft, reset to draft raises UserError
        with self.assertRaises(UserError):
            exam.action_reset_draft()

        # In scheduled, reset to draft succeeds
        exam.action_schedule()
        self.assertEqual(exam.state, "scheduled")
        exam.action_reset_draft()
        self.assertEqual(exam.state, "draft")

        # Move to ongoing -> reset to draft must fail
        exam.action_schedule()
        exam.action_start()
        self.assertEqual(exam.state, "ongoing")
        with self.assertRaises(UserError):
            exam.action_reset_draft()

    def test_configurable_grading_system_custom_scale(self):
        """Test custom grading scale creation, assignment to exam, and dynamic grade point computation."""
        # 1. Create a custom 4-tier grading scale
        custom_scale = self.env["edu.exam.grade.system"].create({
            "name": "Custom Honors Scale",
            "code": "HONORS",
            "is_default": False,
            "line_ids": [
                (0, 0, {
                    "sequence": 1,
                    "name": "Distinction",
                    "min_percentage": 75.0,
                    "max_percentage": 100.0,
                    "grade_point": 4.0,
                    "pass_fail": "pass",
                    "description": "Passed with Distinction",
                }),
                (0, 0, {
                    "sequence": 2,
                    "name": "First Class",
                    "min_percentage": 60.0,
                    "max_percentage": 74.99,
                    "grade_point": 3.0,
                    "pass_fail": "pass",
                    "description": "First Class",
                }),
                (0, 0, {
                    "sequence": 3,
                    "name": "Second Class",
                    "min_percentage": 50.0,
                    "max_percentage": 59.99,
                    "grade_point": 2.0,
                    "pass_fail": "pass",
                    "description": "Second Class",
                }),
                (0, 0, {
                    "sequence": 4,
                    "name": "Fail",
                    "min_percentage": 0.0,
                    "max_percentage": 49.99,
                    "grade_point": 0.0,
                    "pass_fail": "fail",
                    "description": "Needs Improvement",
                }),
            ],
        })

        # 2. Create exam using this custom scale
        exam = self._make_exam()
        exam.grade_system_id = custom_scale.id
        exam.action_schedule()
        exam.action_start()
        exam.action_start_valuation()

        # 3. Create results
        r_distinction = self._make_result(exam, self.enr1, self.subj_math, 85.0)
        self.assertEqual(r_distinction.grade, "Distinction")
        self.assertEqual(r_distinction.grade_point, 4.0)
        self.assertEqual(r_distinction.grade_remarks, "Passed with Distinction")
        self.assertEqual(r_distinction.pass_fail, "pass")

        r_first = self._make_result(exam, self.enr2, self.subj_math, 68.0)
        self.assertEqual(r_first.grade, "First Class")
        self.assertEqual(r_first.grade_point, 3.0)
        self.assertEqual(r_first.grade_remarks, "First Class")
        self.assertEqual(r_first.pass_fail, "pass")

        r_second = self._make_result(exam, self.enr1, self.subj_english, 52.0)
        self.assertEqual(r_second.grade, "Second Class")
        self.assertEqual(r_second.grade_point, 2.0)
        self.assertEqual(r_second.grade_remarks, "Second Class")
        self.assertEqual(r_second.pass_fail, "pass")

        r_fail = self._make_result(exam, self.enr2, self.subj_english, 35.0)
        self.assertEqual(r_fail.grade, "Fail")
        self.assertEqual(r_fail.grade_point, 0.0)
        self.assertEqual(r_fail.grade_remarks, "Needs Improvement")
        self.assertEqual(r_fail.pass_fail, "fail")

    def test_grading_system_percentage_validation(self):
        """Test validation constraints on grading system percentage brackets."""
        scale = self.env["edu.exam.grade.system"].create({
            "name": "Invalid Bracket Scale",
        })
        # Min > Max should raise ValidationError
        with self.assertRaises(ValidationError):
            self.env["edu.exam.grade.line"].create({
                "grade_system_id": scale.id,
                "name": "Invalid",
                "min_percentage": 80.0,
                "max_percentage": 50.0,
            })
        # Negative percentage should raise ValidationError
        with self.assertRaises(ValidationError):
            self.env["edu.exam.grade.line"].create({
                "grade_system_id": scale.id,
                "name": "Negative",
                "min_percentage": -10.0,
                "max_percentage": 50.0,
            })








