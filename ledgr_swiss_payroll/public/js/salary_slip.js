frappe.ui.form.on("Salary Slip", {
  refresh(frm) {
    if (
      frm.doc.docstatus === 0 &&
      !frm.doc.ledgr_owner_validated_by &&
      frappe.user.has_role("LEDGR Business Owner")
    ) {
      frm.add_custom_button(__("Valider en tant qu'employeur"), () => {
        frm.set_value("ledgr_owner_validated_by", frappe.session.user);
        frm.set_value("ledgr_owner_validated_on", frappe.datetime.now_datetime());
        frm.save();
      });
    }
  },
});
