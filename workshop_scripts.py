# -*- coding: utf-8 -*-
"""Client Scripts (live totals) + Server Script (payment -> invoice update)."""
import frappe

# When adding a NEW Customer Vehicle and a returning customer is selected who
# already has vehicle(s) on file, surface them so staff can jump to the
# existing record instead of accidentally creating a duplicate -- rather than
# silently letting a second record for the same car get created.
CUSTOMER_VEHICLE_JS = r"""
frappe.ui.form.on('Customer Vehicle', {
    customer: (frm)=>{
        if(!frm.is_new() || !frm.doc.customer) return;
        frappe.db.get_list('Customer Vehicle', {
            filters: { customer: frm.doc.customer },
            fields: ['name', 'plate_number', 'brand', 'model'],
            limit: 20,
        }).then(vehicles=>{
            if(!vehicles || !vehicles.length) return;
            let rows = vehicles.map(v=>
                '<li style="margin-bottom:4px;">' +
                '<a data-name="' + encodeURIComponent(v.name) + '" class="kaj-existing-vehicle-link">' +
                (v.plate_number || v.name) + (v.brand ? ' — ' + v.brand : '') + (v.model ? ' ' + v.model : '') +
                '</a></li>'
            ).join('');
            let d = new frappe.ui.Dialog({
                title: __('هذا العميل لديه مركبات مسجلة مسبقاً'),
                fields: [{
                    fieldname: 'existing_html', fieldtype: 'HTML',
                    options: '<p>' + __('تأكد أنك لا تُنشئ مركبة مكررة. مركبات هذا العميل المسجلة حالياً:') + '</p><ul>' + rows + '</ul>',
                }],
                primary_action_label: __('متابعة إضافة مركبة جديدة'),
                primary_action: ()=> d.hide(),
            });
            d.show();
            d.$wrapper.find('.kaj-existing-vehicle-link').on('click', function(e){
                e.preventDefault();
                d.hide();
                frappe.set_route('Form', 'Customer Vehicle', decodeURIComponent($(this).data('name')));
            });
        });
    },
});
"""

# List-view enhancement for Customer Vehicle: show a clickable WhatsApp icon
# + the customer's phone number under the customer name in the "العميل"
# column, matching the Mazoon reference UI. customer_phone is a fetched
# Custom Field (see execute()) pulled in via add_fields so it's available on
# each list row without extra per-row queries.
CUSTOMER_VEHICLE_LIST_JS = r"""
frappe.listview_settings['Customer Vehicle'] = {
    add_fields: ["customer_phone"],
    formatters: {
        customer: function(value, df, doc){
            if(!value) return '';
            let html = '<div>' + frappe.utils.escape_html(value) + '</div>';
            let phone = doc.customer_phone;
            if(phone){
                let digits = (phone + '').replace(/[^0-9]/g, '');
                let full;
                if(digits.indexOf('967') === 0 || digits.indexOf('968') === 0){
                    full = digits;
                } else if(digits.length === 8){
                    full = '968' + digits;
                } else if(digits.length === 9 && digits.indexOf('7') === 0){
                    full = '967' + digits;
                } else {
                    full = '968' + digits;
                }
                let url = 'https://wa.me/' + full;
                html += '<div style="margin-top:2px;">' +
                    '<a href="' + url + '" target="_blank" onclick="event.stopPropagation();" ' +
                    'style="color:#25D366;text-decoration:none;display:inline-flex;align-items:center;gap:4px;font-size:12px;">' +
                    '<svg width="14" height="14" viewBox="0 0 24 24" fill="#25D366"><path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.45 1.32 4.95L2 22l5.29-1.39c1.45.79 3.08 1.21 4.75 1.21h.01c5.46 0 9.9-4.45 9.9-9.91C21.96 6.45 17.5 2 12.04 2zm5.85 14.03c-.24.68-1.19 1.25-1.96 1.42-.52.11-1.2.2-3.48-.75-2.92-1.21-4.8-4.17-4.94-4.36-.14-.19-1.19-1.58-1.19-3.01 0-1.44.75-2.14 1.02-2.43.27-.29.58-.36.78-.36h.56c.18 0 .42-.02.65.51.24.55.81 1.9.88 2.04.07.14.11.3.02.48-.09.19-.14.3-.28.46-.14.16-.29.36-.42.48-.14.14-.28.29-.12.57.16.28.71 1.19 1.53 1.93 1.05.95 1.94 1.24 2.22 1.38.28.14.44.12.61-.07.16-.19.7-.82.89-1.1.19-.28.37-.23.62-.14.26.09 1.63.79 1.91.93.28.14.47.21.53.33.07.12.07.68-.17 1.36z"/></svg>' +
                    frappe.utils.escape_html(phone) +
                    '</a></div>';
            }
            return html;
        },
    },
};
"""

WORK_CARD_JS = r"""
frappe.ui.form.on('Work Card Service', {
    qty: calc_service, rate: calc_service,
    services_remove: (frm) => totals(frm),
});
frappe.ui.form.on('Work Card Part', {
    qty: calc_part, rate: calc_part,
    parts_remove: (frm) => totals(frm),
});
function calc_service(frm, cdt, cdn){
    let r = locals[cdt][cdn];
    frappe.model.set_value(cdt, cdn, 'amount', (r.qty||0)*(r.rate||0));
    totals(frm);
}
function calc_part(frm, cdt, cdn){
    let r = locals[cdt][cdn];
    frappe.model.set_value(cdt, cdn, 'amount', (r.qty||0)*(r.rate||0));
    totals(frm);
}
function totals(frm){
    let s=0,p=0;
    (frm.doc.services||[]).forEach(r=> s+=(r.amount||0));
    (frm.doc.parts||[]).forEach(r=> p+=(r.amount||0));
    frm.set_value('services_total', s);
    frm.set_value('parts_total', p);
    frm.set_value('grand_total', s+p-(frm.doc.discount||0));
}
frappe.ui.form.on('Work Card', {
    discount: (frm)=> totals(frm),
    validate: (frm)=> totals(frm),
    customer: (frm)=> autofill_returning_customer(frm),
});
function autofill_returning_customer(frm){
    if(!frm.doc.customer) return;
    frappe.db.get_value('Customer', frm.doc.customer, 'mobile_no').then(r=>{
        let phone = r.message && r.message.mobile_no;
        if(phone) frm.set_value('customer_phone', phone);
    });
    frappe.db.get_list('Customer Vehicle', {
        filters: { customer: frm.doc.customer },
        fields: ['name', 'plate_number', 'brand', 'model'],
        limit: 20,
    }).then(vehicles=>{
        if(!vehicles || !vehicles.length) return;
        if(vehicles.length === 1){
            apply_vehicle(frm, vehicles[0]);
        } else {
            let options = vehicles.map(v=>
                (v.plate_number || v.name) + (v.brand ? ' — ' + v.brand : '') + (v.model ? ' ' + v.model : '')
            );
            let d = new frappe.ui.Dialog({
                title: __('اختر مركبة العميل'),
                fields: [{
                    fieldname: 'vehicle_choice', fieldtype: 'Select',
                    label: __('هذا العميل لديه أكثر من مركبة مسجلة — اختر المركبة الحالية'),
                    options: options, reqd: 1,
                }],
                primary_action_label: __('تعبئة'),
                primary_action: (values)=>{
                    let idx = options.indexOf(values.vehicle_choice);
                    if(idx > -1) apply_vehicle(frm, vehicles[idx]);
                    d.hide();
                },
            });
            d.show();
        }
    });
}
function apply_vehicle(frm, v){
    frm.set_value('vehicle', v.name);
    frm.set_value('plate_number', v.plate_number || v.name);
    if(v.brand) frm.set_value('brand', v.brand);
    if(v.model) frm.set_value('model', v.model);
}
frappe.ui.form.on('Work Card Technician', {
    technician: function(frm, cdt, cdn){
        let r = locals[cdt][cdn];
        if(r.technician && !r.commission){
            frappe.db.get_value('Workshop Technician', r.technician, 'commission_rate').then(res=>{
                let rate = (res.message && res.message.commission_rate) || 0;
                if(rate){ frappe.model.set_value(cdt, cdn, 'commission', ((frm.doc.services_total||0)*rate/100)); }
            });
        }
    }
});
"""

QUOTATION_JS = r"""
frappe.ui.form.on('Workshop Quotation Item', {
    qty: calc, rate: calc, items_remove: (frm)=> totals(frm),
});
function calc(frm, cdt, cdn){
    let r=locals[cdt][cdn];
    frappe.model.set_value(cdt,cdn,'amount',(r.qty||0)*(r.rate||0));
    totals(frm);
}
function totals(frm){
    let t=0; (frm.doc.items||[]).forEach(r=> t+=(r.amount||0));
    frm.set_value('total', t);
    frm.set_value('grand_total', t-(frm.doc.discount||0));
}
frappe.ui.form.on('Workshop Quotation', {
    discount:(frm)=>totals(frm), validate:(frm)=>totals(frm),
});
"""

INVOICE_JS = r"""
frappe.ui.form.on('Repair Invoice Item', {
    qty: calc, rate: calc, items_remove: (frm)=> totals(frm),
});
function calc(frm, cdt, cdn){
    let r=locals[cdt][cdn];
    frappe.model.set_value(cdt,cdn,'amount',(r.qty||0)*(r.rate||0));
    totals(frm);
}
function totals(frm){
    let t=0; (frm.doc.items||[]).forEach(r=> t+=(r.amount||0));
    frm.set_value('total', t);
    let g = t-(frm.doc.discount||0);
    frm.set_value('grand_total', g);
    frm.set_value('outstanding', g-(frm.doc.paid_amount||0));
}
frappe.ui.form.on('Repair Invoice', {
    discount:(frm)=>totals(frm), validate:(frm)=>totals(frm),
    onload:(frm)=>{ if(frm.is_new() && frm.doc.work_card && !(frm.doc.items||[]).length){ pull_wc(frm); } },
    work_card:(frm)=>{ if(frm.doc.work_card){ pull_wc(frm); } },
    refresh:(frm)=>{
        if(!frm.is_new() && frm.doc.customer){
            frm.add_custom_button(__('إرسال عبر واتساب'), ()=>send_whatsapp(frm));
        }
    },
});
function send_whatsapp(frm){
    frappe.dom.freeze(__('جاري تجهيز الفاتورة...'));
    Promise.all([
        frappe.db.get_value('Customer', frm.doc.customer, 'mobile_no'),
        frappe.db.get_single_value('Workshop Settings', 'country_code'),
        frappe.call('frappe.workshop_invoice_whatsapp.get_invoice_pdf_url', {invoice: frm.doc.name}),
    ]).then(([customerRes, countryCode, pdfRes])=>{
        frappe.dom.unfreeze();
        let phone = (customerRes.message && customerRes.message.mobile_no || '').replace(/[^0-9]/g, '');
        if(!phone){
            frappe.msgprint({message: __('لا يوجد رقم جوال مسجل لهذا العميل — أضف رقم الجوال في بطاقة العميل أولاً.'), indicator: 'red'});
            return;
        }
        // Already includes a country code (long enough / already starts with 967 or 968) -> use as-is.
        // Otherwise infer from local number length: Oman mobiles are 8 digits (968),
        // Yemen mobiles are 9 digits starting with 7 (967) -- this business serves both.
        // Falls back to Workshop Settings.country_code only when the length is ambiguous.
        if(phone.length <= 10 && !phone.startsWith('967') && !phone.startsWith('968')){
            let inferred = phone.length === 8 ? '968'
                : (phone.length === 9 && phone.startsWith('7')) ? '967'
                : (countryCode || '968').replace(/[^0-9]/g, '');
            phone = inferred + phone.replace(/^0+/, '');
        }
        let pdfUrl = pdfRes && pdfRes.message;
        let text = 'مرحباً ' + frm.doc.customer + '،\n'
            + 'فاتورتكم رقم ' + frm.doc.name + ' من ورشة خط الجزيرة.\n'
            + 'الإجمالي: ' + format_currency(frm.doc.grand_total) + '\n'
            + 'المتبقي: ' + format_currency(frm.doc.outstanding) + '\n'
            + (pdfUrl ? ('لعرض/تحميل الفاتورة:\n' + pdfUrl + '\n') : '')
            + 'شكراً لتعاملكم معنا.';
        window.open('https://wa.me/' + phone + '?text=' + encodeURIComponent(text), '_blank');
    }).catch((e)=>{
        frappe.dom.unfreeze();
        frappe.msgprint({message: __('تعذّر تجهيز رابط الفاتورة'), indicator: 'red'});
        console.error(e);
    });
}
function pull_wc(frm){
    frappe.db.get_doc('Work Card', frm.doc.work_card).then(wc=>{
        frm.set_value('customer', wc.customer);
        frm.set_value('vehicle', wc.vehicle);
        frm.clear_table('items');
        (wc.services||[]).forEach(s=>{
            let r=frm.add_child('items');
            r.description=s.service; r.qty=s.qty; r.rate=s.rate; r.amount=s.amount;
        });
        (wc.parts||[]).forEach(p=>{
            let r=frm.add_child('items');
            r.description=p.part_name||(p.item||''); r.qty=p.qty; r.rate=p.rate; r.amount=p.amount;
        });
        frm.set_value('discount', wc.discount||0);
        frm.refresh_field('items');
        totals(frm);
    });
}
"""

# General "contact via WhatsApp" button on the Customer form itself -- for
# reaching out without needing a specific invoice open (e.g. reminders,
# general questions). Same country-code inference as the invoice button.
CUSTOMER_JS = r"""
frappe.ui.form.on('Customer', {
    refresh:(frm)=>{
        if(!frm.is_new() && frm.doc.mobile_no){
            frm.add_custom_button(__('تواصل عبر واتساب'), ()=>contact_whatsapp(frm));
        }
    },
});
function contact_whatsapp(frm){
    frappe.db.get_single_value('Workshop Settings', 'country_code').then(countryCode=>{
        let phone = (frm.doc.mobile_no || '').replace(/[^0-9]/g, '');
        if(!phone){
            frappe.msgprint({message: __('لا يوجد رقم جوال مسجل لهذا العميل'), indicator: 'red'});
            return;
        }
        if(phone.length <= 10 && !phone.startsWith('967') && !phone.startsWith('968')){
            let inferred = phone.length === 8 ? '968'
                : (phone.length === 9 && phone.startsWith('7')) ? '967'
                : (countryCode || '968').replace(/[^0-9]/g, '');
            phone = inferred + phone.replace(/^0+/, '');
        }
        let text = 'مرحباً ' + (frm.doc.customer_name || frm.doc.name) + '،\nنتواصل معكم من ورشة خط الجزيرة.';
        window.open('https://wa.me/' + phone + '?text=' + encodeURIComponent(text), '_blank');
    });
}
"""

# Server Script: when a Workshop Payment is created, recompute its invoice.
# paid_amount is capped at grand_total and outstanding floored at 0 so an
# overpayment/duplicate entry can't display a negative amount owed -- it
# instead shows fully paid, matching what the real linked Sales Invoice
# actually reflects (see workshop_gl_stock_integration.py's own capping).
PAYMENT_SERVER = r"""
inv = frappe.get_doc("Repair Invoice", doc.invoice)
paid_raw = frappe.db.sql(
    "select coalesce(sum(amount),0) from `tabWorkshop Payment` where invoice=%s",
    inv.name)[0][0]
paid = min(paid_raw, inv.grand_total or 0)
inv.db_set("paid_amount", paid)
outstanding = max((inv.grand_total or 0) - paid, 0)
inv.db_set("outstanding", outstanding)
if paid <= 0:
    status = "غير مدفوعة"
elif outstanding > 0:
    status = "مدفوعة جزئياً"
else:
    status = "مدفوعة"
inv.db_set("status", status)
"""


def _client_script(name, dt, js, view="Form"):
    if frappe.db.exists("Client Script", name):
        frappe.delete_doc("Client Script", name, force=1, ignore_permissions=True)
    frappe.get_doc({
        "doctype": "Client Script", "name": name,
        "dt": dt, "view": view, "enabled": 1, "script": js,
    }).insert(ignore_permissions=True)


def execute():
    _client_script("Work Card Totals", "Work Card", WORK_CARD_JS)
    _client_script("Workshop Quotation Totals", "Workshop Quotation", QUOTATION_JS)
    _client_script("Repair Invoice Totals", "Repair Invoice", INVOICE_JS)
    _client_script("Customer WhatsApp Button", "Customer", CUSTOMER_JS)
    _client_script("Customer Vehicle Duplicate Check", "Customer Vehicle", CUSTOMER_VEHICLE_JS)
    _client_script("Customer Vehicle List WhatsApp", "Customer Vehicle", CUSTOMER_VEHICLE_LIST_JS, view="List")

    # Fetched field so the list view formatter has the customer's phone
    # number available per-row without an extra query per vehicle.
    if not frappe.db.exists("Custom Field", "Customer Vehicle-customer_phone"):
        frappe.get_doc({
            "doctype": "Custom Field", "dt": "Customer Vehicle",
            "fieldname": "customer_phone", "label": "جوال العميل",
            "fieldtype": "Data", "fetch_from": "customer.mobile_no",
            "read_only": 1, "hidden": 1,
        }).insert(ignore_permissions=True)

    # Country code used to build wa.me WhatsApp links from local phone numbers
    # (mobile_no is stored without a country code) -- editable per-business.
    if not frappe.db.exists("Custom Field", "Workshop Settings-country_code"):
        frappe.get_doc({
            "doctype": "Custom Field", "dt": "Workshop Settings",
            "fieldname": "country_code", "label": "رمز الدولة (لواتساب)",
            "fieldtype": "Data", "default": "968",
            "description": "يُستخدم لإرسال الفواتير عبر واتساب عندما لا يحتوي رقم الجوال على رمز الدولة",
        }).insert(ignore_permissions=True)
        if not frappe.db.get_single_value("Workshop Settings", "country_code"):
            frappe.db.set_single_value("Workshop Settings", "country_code", "968")

    # Server script for payment -> invoice
    if frappe.db.exists("Server Script", "Update Invoice On Payment"):
        frappe.delete_doc("Server Script", "Update Invoice On Payment",
                          force=1, ignore_permissions=True)
    frappe.get_doc({
        "doctype": "Server Script",
        "name": "Update Invoice On Payment",
        "script_type": "DocType Event",
        "reference_doctype": "Workshop Payment",
        "doctype_event": "After Insert",
        "disabled": 0,
        "script": PAYMENT_SERVER,
    }).insert(ignore_permissions=True)

    # Also recompute on payment delete/cancel via On Trash
    if frappe.db.exists("Server Script", "Update Invoice On Payment Delete"):
        frappe.delete_doc("Server Script", "Update Invoice On Payment Delete",
                          force=1, ignore_permissions=True)
    frappe.get_doc({
        "doctype": "Server Script",
        "name": "Update Invoice On Payment Delete",
        "script_type": "DocType Event",
        "reference_doctype": "Workshop Payment",
        "doctype_event": "After Delete",
        "disabled": 0,
        "script": PAYMENT_SERVER,
    }).insert(ignore_permissions=True)

    frappe.db.commit()
    frappe.clear_cache()
    print("SCRIPTS_DONE")
