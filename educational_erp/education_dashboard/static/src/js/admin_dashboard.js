/** @odoo-module **/
/**
 * education_dashboard — Admin Dashboard (OWL client action)
 * Live institution-wide KPIs, charts and quick actions.
 */
import { registry } from "@web/core/registry";
import { Component, onWillStart, onMounted, onPatched, onWillUnmount, useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

export class EduAdminDashboard extends Component {
    static template = "education_dashboard.AdminDashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ loading: true, data: {} });

        // Chart.js canvases (only rendered once scholarships/hostel data exists)
        this.scholarshipChartRef = useRef("scholarshipChart");
        this.hostelChartRef = useRef("hostelChart");
        this._scholarshipChart = null;
        this._hostelChart = null;

        onWillStart(async () => {
            // Chart.js ships with Odoo's web assets already — just load it.
            await loadJS("/web/static/lib/Chart/Chart.js");
            await this.load();
        });
        onMounted(() => this._renderCharts());
        onPatched(() => this._renderCharts());
        onWillUnmount(() => {
            this._scholarshipChart?.destroy();
            this._hostelChart?.destroy();
        });
    }

    async load() {
        this.state.loading = true;
        this.state.data = await this.orm.call("edu.dashboard", "get_admin_dashboard", []);
        this.state.loading = false;
    }

    /** Bars scaled to the largest value in the series (used by the simple div-bars). */
    _bars(series) {
        const max = Math.max(1, ...series.map((r) => r.value));
        return series.map((r) => ({ ...r, pct: Math.round((r.value / max) * 100) }));
    }
    get programBars() {
        return this._bars(this.state.data.by_program || []);
    }
    get funnelBars() {
        return this._bars(this.state.data.funnel || []);
    }
    get examBars() {
        const k = this.state.data.kpis || {};
        return this._bars([
            { label: "Upcoming", value: k.upcoming_exams || 0 },
            { label: "Ongoing", value: k.ongoing_exams || 0 },
            { label: "Under Valuation", value: k.under_valuation || 0 },
            { label: "Result Published", value: k.result_published || 0 },
        ]);
    }
    get scholarshipBars() {
        const k = this.state.data.kpis || {};
        return this._bars([
            { label: "Open Scholarships", value: k.total_active_scholarships || 0 },
            { label: "Applications Received", value: k.total_applications || 0 },
            { label: "Approved Applications", value: k.total_approved_scholarship || 0 },
            { label: "Applications To Review", value: k.total_applications_to_review || 0 },
        ]);
    }
    get hostelBars() {
        const k = this.state.data.kpis || {};
        return this._bars([
            { label: "Rooms", value: k.total_rooms || 0 },
            { label: "Unoccupied Rooms", value: k.total_rooms_with_unoccupied_bed || 0 },
        ]);
    }

    /** Parse a "1234.0$"-style formatted amount (number + currency symbol) back to a number. */
    _num(value) {
        const n = parseFloat(value);
        return isNaN(n) ? 0 : n;
    }

    get scholarshipHasChartData() {
        if (!this.state.data.scholarships) return false;
        const k = this.state.data.kpis || {};
        return this._num(k.total_scholarship_budget) > 0 || this._num(k.total_approved_amount) > 0;
    }
    get hostelHasChartData() {
        if (!this.state.data.hostel) return false;
        const k = this.state.data.kpis || {};
        return (k.total_beds || 0) > 0;
    }

    _renderCharts() {
        if (!window.Chart || this.state.loading) return;
        this._renderScholarshipChart();
        this._renderHostelChart();
    }

    _renderScholarshipChart() {
        if (!this.scholarshipHasChartData) {
            this._scholarshipChart?.destroy();
            this._scholarshipChart = null;
            return;
        }
        const canvas = this.scholarshipChartRef.el;
        if (!canvas) return;
        const k = this.state.data.kpis;
        const budget = this._num(k.total_scholarship_budget);
        const approved = this._num(k.total_approved_amount);
        const remaining = Math.max(budget - approved, 0);

        // Canvas gets re-created whenever the t-if toggles, so make sure
        // we're not holding a chart bound to a stale/removed canvas.
        if (this._scholarshipChart && this._scholarshipChart.canvas !== canvas) {
            this._scholarshipChart.destroy();
            this._scholarshipChart = null;
        }
        if (this._scholarshipChart) {
            this._scholarshipChart.data.datasets[0].data = [approved, remaining];
            this._scholarshipChart.update();
            return;
        }
        this._scholarshipChart = new Chart(canvas, {
            type: "doughnut",
            data: {
                labels: ["Approved Amount", "Remaining Budget"],
                datasets: [{
                    data: [approved, remaining],
                    backgroundColor: ["#5b6fd8", "#e3e7f3"],
                    borderWidth: 0,
                }],
            },
            options: {
                maintainAspectRatio: false,
                cutout: "65%",
                plugins: { legend: { display: false } },
            },
        });
    }

    _renderHostelChart() {
        if (!this.hostelHasChartData) {
            this._hostelChart?.destroy();
            this._hostelChart = null;
            return;
        }
        const canvas = this.hostelChartRef.el;
        if (!canvas) return;
        const k = this.state.data.kpis;
        const capacity = k.total_beds || 0;
        const occupied = k.total_beds_occupied || 0;

        if (this._hostelChart && this._hostelChart.canvas !== canvas) {
            this._hostelChart.destroy();
            this._hostelChart = null;
        }
        if (this._hostelChart) {
            this._hostelChart.data.datasets[0].data = [capacity, occupied];
            this._hostelChart.update();
            return;
        }
        this._hostelChart = new Chart(canvas, {
            type: "bar",
            data: {
                labels: ["Total Capacity", "Occupied Beds"],
                datasets: [{
                    data: [capacity, occupied],
                    backgroundColor: ["#e3e7f3", "#5b6fd8"],
                    borderRadius: 4,
                    maxBarThickness: 56,
                }],
            },
            options: {
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
            },
        });
    }

    openList(name, model, domain) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: model,
            views: [[false, "list"], [false, "form"]],
            domain: domain || [],
            target: "current",
        });
    }
    openRecord(model, resId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: model,
            res_id: resId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    onStudents() { this.openList("Students", "education.enrollment", [["state", "=", "active"]]); }
    onApplications() { this.openList("Pending Applications", "education.application", [["state", "=", "submitted"]]); }
    onUpcomingExams() { this.openList("Exams", "edu.exam", [["state", "in", ["scheduled"]]]); }
    onOngoingExams() { this.openList("Exams", "edu.exam", [["state", "in", ["ongoing"]]]); }
    onUnderValuationExams() { this.openList("Exams", "edu.exam", [["state", "in", ["valuation"]]]); }
    onResultPublishedExams() { this.openList("Exams", "edu.exam", [["state", "in", ["result_published"]]]); }
    onFaculty() { this.openList("Faculty", "education.faculty", []); }
    onPrograms() { this.openList("Programs", "education.program", []); }
    onClasses() { this.openList("Classes", "education.class", []); }
    onDepartments() { this.openList("Departments", "education.department", []); }
    onFees() {
        // Drill into the related unpaid fee invoices
        this.openList("Outstanding Fee Invoices", "account.move", [
            ["move_type", "=", "out_invoice"],
            ["enrollment_id", "!=", false],
            ["payment_state", "in", ["not_paid", "partial"]],
        ]);
    }
    onActiveScholarships() { this.openList("Scholarships", "education.scholarship", [["state", "=", "active"]]); }
    onTotalApplications() { this.openList("Applications", "education.scholarship.application", [["scholarship_id", "in", this.state.data.active_ids]]); }
    onApprovedApplications() { this.openList("Approved Applications", "education.scholarship.application", [["state", "in", ["approved"]]]); }
    onApplicationReview() { this.openList("Exams", "education.scholarship.application", [["state", "in", ["submitted","review"]]]); }
    onProperties() { this.openList("Properties", "edu.hostel.property", []); }
    onRooms() { this.openList("Rooms", "edu.hostel.room", []); }
    onUnoccupiedRoom() { this.openList("Unoccupied Rooms", "edu.hostel.room", [["state", "in", ["available","partially_occupied"]]]); }
    onInvoicedAmount() { this.openList("Hostel Fees", "education.scholarship.application", [["state", "in", ["submitted","review"]]]); }
}

registry.category("actions").add("education_dashboard.admin_dashboard", EduAdminDashboard);

// /** @odoo-module **/
// /**
//  * education_dashboard — Admin Dashboard (OWL client action)
//  * Live institution-wide KPIs, charts and quick actions.
//  */
// import { registry } from "@web/core/registry";
// import { Component, onWillStart, onMounted, onPatched, onWillUnmount, useState, useRef } from "@odoo/owl";
// import { useService } from "@web/core/utils/hooks";
// import { loadJS } from "@web/core/assets";
//
// export class EduAdminDashboard extends Component {
//     static template = "education_dashboard.AdminDashboard";
//     static props = ["*"];
//
//     setup() {
//         this.orm = useService("orm");
//         this.action = useService("action");
//         this.state = useState({ loading: true, data: {} });
//
//         // Chart.js canvases (only rendered once scholarships/hostel data exists)
//         this.scholarshipChartRef = useRef("scholarshipChart");
//         this.hostelChartRef = useRef("hostelChart");
//         this._scholarshipChart = null;
//         this._hostelChart = null;
//
//         onWillStart(async () => {
//             // Chart.js ships with Odoo's web assets already — just load it.
//             await loadJS("/web/static/lib/Chart/Chart.js");
//             await this.load();
//         });
//         onMounted(() => this._renderCharts());
//         onPatched(() => this._renderCharts());
//         onWillUnmount(() => {
//             this._scholarshipChart?.destroy();
//             this._hostelChart?.destroy();
//         });
//     }
//
//     async load() {
//         this.state.loading = true;
//         this.state.data = await this.orm.call("edu.dashboard", "get_admin_dashboard", []);
//         this.state.loading = false;
//     }
//
//     /** Bars scaled to the largest value in the series (used by the simple div-bars). */
//     _bars(series) {
//         const max = Math.max(1, ...series.map((r) => r.value));
//         return series.map((r) => ({ ...r, pct: Math.round((r.value / max) * 100) }));
//     }
//     get programBars() {
//         return this._bars(this.state.data.by_program || []);
//     }
//     get funnelBars() {
//         return this._bars(this.state.data.funnel || []);
//     }
//     get examBars() {
//         const k = this.state.data.kpis || {};
//         return this._bars([
//             { label: "Upcoming", value: k.upcoming_exams || 0 },
//             { label: "Ongoing", value: k.ongoing_exams || 0 },
//             { label: "Under Valuation", value: k.under_valuation || 0 },
//             { label: "Result Published", value: k.result_published || 0 },
//         ]);
//     }
//     get scholarshipBars() {
//         const k = this.state.data.kpis || {};
//         return this._bars([
//             { label: "Active", value: k.total_active_scholarships || 0 },
//             { label: "Applications", value: k.total_applications || 0 },
//             { label: "Approved", value: k.total_approved_scholarship || 0 },
//             { label: "To Review", value: k.total_applications_to_review || 0 },
//         ]);
//     }
//     get hostelBars() {
//         const k = this.state.data.kpis || {};
//         return this._bars([
//             { label: "Rooms", value: k.total_rooms || 0 },
//             { label: "Unoccupied Rooms", value: k.total_rooms_with_unoccupied_bed || 0 },
//         ]);
//     }
//
//     /** Parse a "1234.0$"-style formatted amount (number + currency symbol) back to a number. */
//     _num(value) {
//         const n = parseFloat(value);
//         return isNaN(n) ? 0 : n;
//     }
//
//     _renderCharts() {
//         if (!window.Chart || this.state.loading) return;
//         this._renderScholarshipChart();
//         this._renderHostelChart();
//     }
//
//     _renderScholarshipChart() {
//         const canvas = this.scholarshipChartRef.el;
//         if (!canvas || !this.state.data.scholarships) return;
//         const k = this.state.data.kpis;
//         const budget = this._num(k.total_scholarship_budget);
//         const approved = this._num(k.total_approved_amount);
//         const remaining = Math.max(budget - approved, 0);
//
//         if (this._scholarshipChart) {
//             this._scholarshipChart.data.datasets[0].data = [approved, remaining];
//             this._scholarshipChart.update();
//             return;
//         }
//         this._scholarshipChart = new Chart(canvas, {
//             type: "doughnut",
//             data: {
//                 labels: ["Approved Amount", "Remaining Budget"],
//                 datasets: [{
//                     data: [approved, remaining],
//                     backgroundColor: ["#5b6fd8", "#e3e7f3"],
//                     borderWidth: 0,
//                 }],
//             },
//             options: {
//                 maintainAspectRatio: false,
//                 cutout: "65%",
//                 plugins: { legend: { position: "bottom", labels: { boxWidth: 10, font: { size: 11 } } } },
//             },
//         });
//     }
//
//     _renderHostelChart() {
//         const canvas = this.hostelChartRef.el;
//         if (!canvas || !this.state.data.hostel) return;
//         const k = this.state.data.kpis;
//         const capacity = k.total_beds || 0;
//         const occupied = k.total_beds_occupied || 0;
//
//         if (this._hostelChart) {
//             this._hostelChart.data.datasets[0].data = [capacity, occupied];
//             this._hostelChart.update();
//             return;
//         }
//         this._hostelChart = new Chart(canvas, {
//             type: "bar",
//             data: {
//                 labels: ["Total Capacity", "Occupied Beds"],
//                 datasets: [{
//                     data: [capacity, occupied],
//                     backgroundColor: ["#e3e7f3", "#5b6fd8"],
//                     borderRadius: 4,
//                     maxBarThickness: 56,
//                 }],
//             },
//             options: {
//                 maintainAspectRatio: false,
//                 plugins: { legend: { display: false } },
//                 scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
//             },
//         });
//     }
//
//     openList(name, model, domain) {
//         this.action.doAction({
//             type: "ir.actions.act_window",
//             name,
//             res_model: model,
//             views: [[false, "list"], [false, "form"]],
//             domain: domain || [],
//             target: "current",
//         });
//     }
//     openRecord(model, resId) {
//         this.action.doAction({
//             type: "ir.actions.act_window",
//             res_model: model,
//             res_id: resId,
//             views: [[false, "form"]],
//             target: "current",
//         });
//     }
//
//     onStudents() { this.openList("Students", "education.enrollment", [["state", "=", "active"]]); }
//     onApplications() { this.openList("Pending Applications", "education.application", [["state", "=", "submitted"]]); }
//     onUpcomingExams() { this.openList("Exams", "edu.exam", [["state", "in", ["scheduled"]]]); }
//     onOngoingExams() { this.openList("Exams", "edu.exam", [["state", "in", ["ongoing"]]]); }
//     onUnderValuationExams() { this.openList("Exams", "edu.exam", [["state", "in", ["valuation"]]]); }
//     onResultPublishedExams() { this.openList("Exams", "edu.exam", [["state", "in", ["result_published"]]]); }
//     onFaculty() { this.openList("Faculty", "education.faculty", []); }
//     onPrograms() { this.openList("Programs", "education.program", []); }
//     onClasses() { this.openList("Classes", "education.class", []); }
//     onDepartments() { this.openList("Departments", "education.department", []); }
//     onFees() {
//         // Drill into the related unpaid fee invoices
//         this.openList("Outstanding Fee Invoices", "account.move", [
//             ["move_type", "=", "out_invoice"],
//             ["enrollment_id", "!=", false],
//             ["payment_state", "in", ["not_paid", "partial"]],
//         ]);
//     }
//     onActiveScholarships() { this.openList("Scholarships", "education.scholarship", [["state", "=", "active"]]); }
//     onTotalApplications() { this.openList("Applications", "education.scholarship.application", [["scholarship_id", "in", this.state.data.active_ids]]); }
//     onApprovedApplications() { this.openList("Approved Applications", "education.scholarship.application", [["state", "in", ["approved"]]]); }
//     onApplicationReview() { this.openList("Exams", "education.scholarship.application", [["state", "in", ["submitted","review"]]]); }
//     onProperties() { this.openList("Properties", "edu.hostel.property", []); }
//     onRooms() { this.openList("Rooms", "edu.hostel.room", []); }
//     onUnoccupiedRoom() { this.openList("Unoccupied Rooms", "edu.hostel.room", [["state", "in", ["available","partially_occupied"]]]); }
//     onInvoicedAmount() { this.openList("Hostel Fees", "education.scholarship.application", [["state", "in", ["submitted","review"]]]); }
// }
//
// registry.category("actions").add("education_dashboard.admin_dashboard", EduAdminDashboard);

// /** @odoo-module **/
// /**
//  * education_dashboard — Admin Dashboard (OWL client action)
//  * Live institution-wide KPIs, charts and quick actions.
//  */
// import { registry } from "@web/core/registry";
// import { Component, onWillStart, useState } from "@odoo/owl";
// import { useService } from "@web/core/utils/hooks";
//
// export class EduAdminDashboard extends Component {
//     static template = "education_dashboard.AdminDashboard";
//     static props = ["*"];
//
//     setup() {
//         this.orm = useService("orm");
//         this.action = useService("action");
//         this.state = useState({ loading: true, data: {} });
//         onWillStart(async () => {
//             await this.load();
//         });
//     }
//
//     async load() {
//         this.state.loading = true;
//         this.state.data = await this.orm.call("edu.dashboard", "get_admin_dashboard", []);
//         this.state.loading = false;
//     }
//
//     /** Bars scaled to the largest value in the series. */
//     _bars(series) {
//         const max = Math.max(1, ...series.map((r) => r.value));
//         return series.map((r) => ({ ...r, pct: Math.round((r.value / max) * 100) }));
//     }
//     get programBars() {
//         return this._bars(this.state.data.by_program || []);
//     }
//     get funnelBars() {
//         return this._bars(this.state.data.funnel || []);
//     }
//     get examBars() {
//         const k = this.state.data.kpis || {};
//         return this._bars([
//             { label: "Upcoming", value: k.upcoming_exams || 0 },
//             { label: "Ongoing", value: k.ongoing_exams || 0 },
//             { label: "Under Valuation", value: k.under_valuation || 0 },
//             { label: "Result Published", value: k.result_published || 0 },
//         ]);
//     }
//     get scholarshipBars() {
//         const k = this.state.data.kpis || {};
//         return this._bars([
//             { label: "Active", value: k.total_active_scholarships || 0 },
//             { label: "Applications", value: k.total_applications || 0 },
//             { label: "Approved", value: k.total_approved_scholarship || 0 },
//             { label: "To Review", value: k.total_applications_to_review || 0 },
//         ]);
//     }
//     get hostelBars() {
//         const k = this.state.data.kpis || {};
//         return this._bars([
//             { label: "Rooms", value: k.total_rooms || 0 },
//             { label: "Beds", value: k.total_beds || 0 },
//             { label: "Beds Occupied", value: k.total_beds_occupied || 0 },
//             { label: "Unoccupied Rooms", value: k.total_rooms_with_unoccupied_bed || 0 },
//         ]);
//     }
//
//     openList(name, model, domain) {
//         this.action.doAction({
//             type: "ir.actions.act_window",
//             name,
//             res_model: model,
//             views: [[false, "list"], [false, "form"]],
//             domain: domain || [],
//             target: "current",
//         });
//     }
//     openRecord(model, resId) {
//         this.action.doAction({
//             type: "ir.actions.act_window",
//             res_model: model,
//             res_id: resId,
//             views: [[false, "form"]],
//             target: "current",
//         });
//     }
//
//     onStudents() { this.openList("Students", "education.enrollment", [["state", "=", "active"]]); }
//     onApplications() { this.openList("Pending Applications", "education.application", [["state", "=", "submitted"]]); }
//     onUpcomingExams() { this.openList("Exams", "edu.exam", [["state", "in", ["scheduled"]]]); }
//     onOngoingExams() { this.openList("Exams", "edu.exam", [["state", "in", ["ongoing"]]]); }
//     onUnderValuationExams() { this.openList("Exams", "edu.exam", [["state", "in", ["valuation"]]]); }
//     onResultPublishedExams() { this.openList("Exams", "edu.exam", [["state", "in", ["result_published"]]]); }
//     onFaculty() { this.openList("Faculty", "education.faculty", []); }
//     onPrograms() { this.openList("Programs", "education.program", []); }
//     onClasses() { this.openList("Classes", "education.class", []); }
//     onDepartments() { this.openList("Departments", "education.department", []); }
//     onFees() {
//         // Drill into the related unpaid fee invoices
//         this.openList("Outstanding Fee Invoices", "account.move", [
//             ["move_type", "=", "out_invoice"],
//             ["enrollment_id", "!=", false],
//             ["payment_state", "in", ["not_paid", "partial"]],
//         ]);
//     }
//     onActiveScholarships() { this.openList("Scholarships", "education.scholarship", [["state", "=", "active"]]); }
//     onTotalApplications() { this.openList("Applications", "education.scholarship.application", [["scholarship_id", "in", this.state.data.active_ids]]); }
//     onApprovedApplications() { this.openList("Approved Applications", "education.scholarship.application", [["state", "in", ["approved"]]]); }
//     onApplicationReview() { this.openList("Exams", "education.scholarship.application", [["state", "in", ["submitted","review"]]]); }
//     onProperties() { this.openList("Properties", "edu.hostel.property", []); }
//     onRooms() { this.openList("Rooms", "edu.hostel.room", []); }
//     onUnoccupiedRoom() { this.openList("Unoccupied Rooms", "edu.hostel.room", [["state", "in", ["available","partially_occupied"]]]); }
//     onInvoicedAmount() { this.openList("Hostel Fees", "education.scholarship.application", [["state", "in", ["submitted","review"]]]); }
// }
//
// registry.category("actions").add("education_dashboard.admin_dashboard", EduAdminDashboard);
// /** @odoo-module **/
// /**
//  * education_dashboard — Admin Dashboard (OWL client action)
//  * Live institution-wide KPIs, charts and quick actions.
//  */
// import { registry } from "@web/core/registry";
// import { Component, onWillStart, useState } from "@odoo/owl";
// import { useService } from "@web/core/utils/hooks";
//
// export class EduAdminDashboard extends Component {
//     static template = "education_dashboard.AdminDashboard";
//     static props = ["*"];
//
//     setup() {
//         this.orm = useService("orm");
//         this.action = useService("action");
//         this.state = useState({ loading: true, data: {} });
//         onWillStart(async () => {
//             await this.load();
//         });
//     }
//
//     async load() {
//         this.state.loading = true;
//         this.state.data = await this.orm.call("edu.dashboard", "get_admin_dashboard", []);
//         this.state.loading = false;
//     }
//
//     /** Bars scaled to the largest value in the series. */
//     _bars(series) {
//         const max = Math.max(1, ...series.map((r) => r.value));
//         return series.map((r) => ({ ...r, pct: Math.round((r.value / max) * 100) }));
//     }
//     get programBars() {
//         return this._bars(this.state.data.by_program || []);
//     }
//     get funnelBars() {
//         return this._bars(this.state.data.funnel || []);
//     }
//
//     openList(name, model, domain) {
//         this.action.doAction({
//             type: "ir.actions.act_window",
//             name,
//             res_model: model,
//             views: [[false, "list"], [false, "form"]],
//             domain: domain || [],
//             target: "current",
//         });
//     }
//     openRecord(model, resId) {
//         this.action.doAction({
//             type: "ir.actions.act_window",
//             res_model: model,
//             res_id: resId,
//             views: [[false, "form"]],
//             target: "current",
//         });
//     }
//
//     onStudents() { this.openList("Students", "education.enrollment", [["state", "=", "active"]]); }
//     onApplications() { this.openList("Pending Applications", "education.application", [["state", "=", "submitted"]]); }
//     onUpcomingExams() { this.openList("Exams", "edu.exam", [["state", "in", ["scheduled"]]]); }
//     onOngoingExams() { this.openList("Exams", "edu.exam", [["state", "in", ["ongoing"]]]); }
//     onUnderValuationExams() { this.openList("Exams", "edu.exam", [["state", "in", ["valuation"]]]); }
//     onResultPublishedExams() { this.openList("Exams", "edu.exam", [["state", "in", ["result_published"]]]); }
//     onFaculty() { this.openList("Faculty", "education.faculty", []); }
//     onPrograms() { this.openList("Programs", "education.program", []); }
//     onClasses() { this.openList("Classes", "education.class", []); }
//     onDepartments() { this.openList("Departments", "education.department", []); }
//     onFees() {
//         // Drill into the related unpaid fee invoices
//         this.openList("Outstanding Fee Invoices", "account.move", [
//             ["move_type", "=", "out_invoice"],
//             ["enrollment_id", "!=", false],
//             ["payment_state", "in", ["not_paid", "partial"]],
//         ]);
//     }
//     onActiveScholarships() { this.openList("Scholarships", "education.scholarship", [["state", "=", "active"]]); }
//     onTotalApplications() { this.openList("Applications", "education.scholarship.application", [["scholarship_id", "in", this.state.data.active_ids]]); }
//     onApprovedApplications() { this.openList("Approved Applications", "education.scholarship.application", [["state", "in", ["approved"]]]); }
//     onApplicationReview() { this.openList("Exams", "education.scholarship.application", [["state", "in", ["submitted","review"]]]); }
//     onProperties() { this.openList("Properties", "edu.hostel.property", []); }
//     onRooms() { this.openList("Rooms", "edu.hostel.room", []); }
//     onUnoccupiedRoom() { this.openList("Unoccupied Rooms", "edu.hostel.room", [["state", "in", ["available","partially_occupied"]]]); }
//     onInvoicedAmount() { this.openList("Hostel Fees", "education.scholarship.application", [["state", "in", ["submitted","review"]]]); }
// }
//
// registry.category("actions").add("education_dashboard.admin_dashboard", EduAdminDashboard);
