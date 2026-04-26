frappe.ui.form.on("Payroll Entry", {
  refresh(frm) {
    if (frm.doc.docstatus === 1) {
      frm.add_custom_button(__("Télécharger pain.001"), () => {
        const url =
          "/api/method/ledgr_swiss_payroll.api.download_pain001?payroll_entry=" +
          encodeURIComponent(frm.doc.name);
        window.open(url, "_blank");
      });
    }
  },
});
