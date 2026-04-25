app_name = "ledgr_swiss_payroll"
app_title = "LEDGR Swiss Payroll"
app_publisher = "LEDGR"
app_description = "Swiss payroll automation app for Frappe v15 / ERPNext v15 / HRMS v15 — multi-mandate, AHV/AC + IS cantonal, certificat de salaire formulaire 11, pain.001 ISO 20022."
app_email = "kevinvarelamoreira@gmail.com"
app_license = "gpl-3.0"

required_apps = ["ledgr_core", "ledgr_chart_of_accounts_ch"]

doctype_js = {
    "Salary Slip": "public/js/salary_slip.js",
}

doc_events = {
    "Salary Slip": {
        "validate": [
            "ledgr_swiss_payroll.calculator.apply_swiss_payroll_calculations",
            "ledgr_swiss_payroll.validators.refresh_anomalies",
        ],
        "before_submit": "ledgr_swiss_payroll.validators.validate_owner_approval",
    },
    "Company": {
        "after_insert": "ledgr_swiss_payroll.setup.seed_payroll_mappings.seed_payroll_mappings",
    },
}

permission_query_conditions = {
    "Employee": "ledgr_swiss_payroll.permissions.employee_filter",
    "Salary Slip": "ledgr_swiss_payroll.permissions.salary_slip_filter",
    "Salary Structure": "ledgr_swiss_payroll.permissions.salary_structure_filter",
    "Salary Structure Assignment": "ledgr_swiss_payroll.permissions.salary_structure_assignment_filter",
    "Payroll Entry": "ledgr_swiss_payroll.permissions.payroll_entry_filter",
    "LEDGR Salary Certificate": "ledgr_swiss_payroll.permissions.salary_certificate_filter",
    "LEDGR LPP Institution": "ledgr_swiss_payroll.permissions.lpp_institution_filter",
}

fixtures = [
    "LEDGR Payroll Canton Config",
    "LEDGR AHV Rate",
    "LEDGR Cantonal IS Tax Slab",
    {
        "dt": "Custom Field",
        "filters": [
            ["dt", "in", ["Salary Slip", "Employee", "LEDGR Mandate Settings"]],
            ["fieldname", "in", [
                "ledgr_section",
                "ledgr_owner_validated_by",
                "ledgr_owner_validated_on",
                "ledgr_anomalies",
                "ledgr_canton_residence",
                "ledgr_tax_code",
                "ledgr_iban",
                "ledgr_lpp_institution",
                "ledgr_thirteenth_month_mode",
                "payroll_iban",
            ]],
        ],
    },
    {
        "dt": "Salary Component",
        "filters": [["salary_component", "in", [
            "Salaire de base", "13e Salaire", "Heures supplémentaires",
            "Allocations familiales", "Frais professionnels",
            "AVS/AI/AC Employé", "AVS/AI/AC Employeur",
            "LPP Employé", "LPP Employeur",
            "IS Retenue", "Avance / Remboursement",
        ]]],
    },
]
