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
