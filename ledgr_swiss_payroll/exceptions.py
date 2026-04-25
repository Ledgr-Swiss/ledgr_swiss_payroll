class ISBracketNotFound(Exception):
    """Raised when no IS tax slab matches (canton, code_tarif, revenue, date)."""

    def __init__(self, canton, code_tarif, monthly_revenue, slip_date):
        self.canton = canton
        self.code_tarif = code_tarif
        self.monthly_revenue = monthly_revenue
        self.slip_date = slip_date
        super().__init__(
            f"Pas de barème IS pour canton={canton}, code={code_tarif}, "
            f"revenu={monthly_revenue}, date={slip_date}"
        )


class NoSlipsForCertificate(Exception):
    """Raised when generate_certificate finds no submitted Salary Slip for the year."""

    def __init__(self, employee, year, company):
        self.employee = employee
        self.year = year
        self.company = company
        super().__init__(
            f"Aucun Salary Slip submitted pour employee={employee}, year={year}, company={company}"
        )


class InvalidPain001(Exception):
    """Raised when pain.001 XML fails XSD validation or input validation."""
    pass
