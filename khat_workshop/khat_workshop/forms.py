# -*- coding: utf-8 -*-
"""النماذج: ما يُخفى منها، وترتيب نماذجنا. المصدر الوحيد.

نماذج ERPNext مبنية لكل نشاط ممكن: فاتورة المبيعات وحدها تحمل 220 حقلاً وقسماً
— تعدّد العملات، قواعد الشحن الدولي، اقتطاع الضريبة من المنبع، عمولات فرق
المبيعات، برامج الولاء، الاشتراكات، التعاملات بين الشركات، جداول ساعات
المشاريع. ورشة صيانة بشركة واحدة وعملة واحدة لا تستعمل شيئاً من ذلك، وموظف
الاستقبال يبحث عن خمسة حقول بين خمسين.

هنا يُكتب ما يُخفى. يطبّقه setup/workshop_forms بخاصية «hidden» على الحقل
(Property Setter): الطريقة التي يدعمها الإطار، تبقى بعد تحديثه، ولا تمسّ
بيانات ولا منطقاً — الحقل المخفي يحتفظ بقيمته الافتراضية ويُحسب كما كان،
ويعود بحذف اسمه من هذا الملف.

إخفاء فاصل قسم (Section Break) أو تبويب (Tab Break) يخفي كل ما تحته.

ما لا يُخفى أبداً: حقل إلزامي بلا قيمة افتراضية — نموذج يرفض الحفظ بسبب
حقل لا يُرى أسوأ من نموذج مزدحم. الحقول الإلزامية المخفية هنا (الشركة،
العملة، التسلسل) يملؤها النظام عند فتح المستند.
"""

# ── يُخفى في كل نموذج يحمله ────────────────────────────────────────────────
EVERYWHERE = {
    "شركة واحدة وتسلسل واحد": [
        "naming_series", "company", "company_tax_id",
    ],
    "عملة واحدة": [
        "currency_and_price_list", "base_totals_section", "base_total", "base_net_total",
        "base_total_taxes_and_charges", "base_taxes_and_charges_added",
        "base_taxes_and_charges_deducted", "base_discount_amount", "base_grand_total",
        "base_rounding_adjustment", "base_rounded_total", "base_in_words",
    ],
    "شحن وتجارة دولية": [
        "shipping_rule", "incoterm", "named_place", "shipping_address_section",
        "company_address_section", "transporter_info",
    ],
    "اقتطاع الضريبة من المنبع": [
        "section_tax_withholding_entry", "apply_tds", "tax_withholding_category",
        "tax_withholding_group",
    ],
    "قواعد التسعير والكوبونات": [
        "ignore_pricing_rule", "pricing_rule_details", "coupon_code",
        "referral_sales_partner",
    ],
    "عمولات وفرق مبيعات": [
        "commission_section", "sales_team_section", "sales_team_section_break",
    ],
    "اشتراكات وتكرار تلقائي": [
        "subscription_section", "automation_section", "auto_repeat_section",
        "subscription_detail",
    ],
    "تسويق": ["utm_analytics_section"],
    "تعاملات بين شركات المجموعة": [
        "is_internal_customer", "is_internal_supplier", "represents_company",
        "inter_company_invoice_reference", "inter_company_order_reference",
        "inter_company_reference",
    ],
    "مشاريع ومراكز تكلفة": ["project", "cost_center"],
    "باركود وأوزان": ["scan_barcode", "last_scanned_warehouse", "total_net_weight"],
    "تصنيع وتعاقد من الباطن": [
        "is_subcontracted", "supplier_warehouse", "raw_material_details",
        "raw_materials_supplied", "subcontracting_receipt", "apply_putaway_rule",
        "rejected_warehouse", "set_from_warehouse", "set_reserve_warehouse",
        "reserve_stock", "set_target_warehouse",
    ],
    "تفاصيل لا تُدخَل يدوياً": [
        "set_posting_time", "posting_time", "transaction_time", "title", "tax_category",
        "sec_tax_breakup", "packing_list", "bundle_items_section", "customer_po_details",
        "disable_rounded_total", "rounding_adjustment", "rounded_total",
        # «المبلغ كتابةً» (in_words) يبقى: يُقرأ في الفاتورة العربية، وظهوره
        # يقرّره Global Defaults لا هذا الملف.
    ],
    "طباعة: يكفي اختيار الترويسة": [
        "select_print_heading", "group_same_items", "language",
    ],
    "إضافة الضرائب وخصمها: يكفي إجماليها": [
        "taxes_and_charges_added", "taxes_and_charges_deducted",
    ],
}

# ── صفوف البنود ─────────────────────────────────────────────────────────────
# فتح صف في فاتورة يعرض نحو ثمانين حقلاً: أوزان، قوائم مواد التصنيع، أوامر
# شاملة، إيرادات مؤجلة، أرقام تسلسلية، والمبلغ نفسه خمس مرات بعملات وصيغ.
# الورشة تحتاج من الصف: الصنف، الكمية، الوحدة، السعر، الخصم، المستودع.
ROW_EVERYWHERE = {
    "عملة واحدة": [
        "base_price_list_rate", "base_rate_with_margin", "base_rate", "base_amount",
        "base_net_rate", "base_net_amount", "base_tax_amount", "base_total",
        "base_tax_amount_after_discount_amount", "base_payment_amount",
        "base_outstanding", "base_paid_amount", "account_currency", "exchange_rate",
        "exchange_gain_loss",
    ],
    "الصافي يساوي السعر ما دامت الضريبة تُضاف فوقه": [
        "net_rate", "net_amount", "tax_amount_after_discount_amount",
        "item_tax_template", "stock_uom_rate",
    ],
    "وحدة المخزون ومعامل التحويل: تُحسب من الصنف": [
        "stock_uom", "conversion_factor", "stock_qty", "received_stock_qty",
        "company_total_stock",
    ],
    "هوامش وتسعير آلي": [
        "margin_type", "margin_rate_or_amount", "rate_with_margin",
        "distributed_discount_amount", "is_free_item", "grant_commission",
        "is_alternative",
    ],
    "أوزان وباركود": [
        "item_weight_details", "weight_per_unit", "total_weight", "weight_uom",
        "barcode", "has_item_scanned",
    ],
    "أرقام تسلسلية وتشغيلات: لا صنف في الورشة يُتتبَّع بها": [
        "pick_serial_and_batch", "add_serial_batch_bundle", "serial_and_batch_bundle",
        "use_serial_batch_fields", "serial_no", "batch_no", "actual_batch_qty",
        "add_serial_batch_for_rejected_qty", "rejected_serial_and_batch_bundle",
        "rejected_serial_no", "reconcile_all_serial_batch",
        "current_serial_and_batch_bundle", "current_serial_no",
    ],
    "تصنيع وتعاقد من الباطن": [
        "fg_item", "fg_item_qty", "subcontracted_qty", "manufacture_details",
        "manufacturing_section_section", "manufacturer", "manufacturer_part_no",
        "bom_no", "bom", "include_exploded_items", "subcontract_bom_section",
        "production_plan", "production_plan_qty", "material_request_plan_item",
        "job_card", "work_order_qty", "wip_composite_asset", "is_finished_item",
        "is_legacy_scrap_item", "type", "subcontracted_item", "against_fg",
        "customer_provided_item_cost", "retain_sample", "sample_quantity",
    ],
    "أوامر شاملة وشحن مباشر ومتجر إلكتروني": [
        "against_blanket_order", "blanket_order", "blanket_order_rate", "drop_ship",
        "drop_ship_section", "delivered_by_supplier", "shopping_cart_section",
        "additional_notes", "sales_order_packed_item", "supplier_quotation",
        "product_bundle",
    ],
    "إيرادات ومصروفات مؤجلة، أصول، اقتطاع ضريبي": [
        "deferred_revenue", "deferred_expense_section", "asset", "finance_book",
        "asset_location", "asset_category", "is_fixed_asset", "apply_tds",
        "tax_withholding_category", "is_tax_withholding_account",
        "included_in_paid_amount", "allocate_full_amount_to_stock_items",
    ],
    "فحص جودة وتكاليف وصول وقواعد تخزين": [
        "quality_inspection", "allow_zero_valuation_rate", "putaway_rule",
        "landed_cost_voucher_amount", "amount_difference_with_purchase_invoice",
        "rejected_warehouse", "return_qty_from_rejected_warehouse",
        "provisional_expense_account",
    ],
    "حجز وتجهيز وتحويل داخلي": [
        "internal_transfer_section", "inter_transfer_reference_section",
        "sales_order_schedule_section", "ensure_delivery_based_on_produced_serial_no",
        "reserve_stock", "stock_reserved_qty", "picked_qty", "against_pick_list",
        "packed_qty", "installed_qty", "page_break",
    ],
    "مشاريع ومراكز تكلفة": ["project", "cost_center"],
    "ربط بدفعات مقدمة وطلبات دفع": [
        "advance_voucher_type", "advance_voucher_no", "payment_request",
        "payment_request_outstanding", "reconcile_effect_on",
    ],
}

ROW_TABLES = [
    "Quotation Item", "Sales Order Item", "Delivery Note Item", "Sales Invoice Item",
    "Material Request Item", "Purchase Order Item", "Purchase Receipt Item",
    "Purchase Invoice Item", "Stock Entry Detail", "Stock Reconciliation Item",
    "Sales Taxes and Charges", "Purchase Taxes and Charges", "Payment Schedule",
    "Journal Entry Account", "Payment Entry Reference", "Item Default",
]

# المستندات التي يُطبَّق عليها ما سبق
TRANSACTIONS = [
    "Quotation", "Sales Order", "Delivery Note", "Sales Invoice",
    "Material Request", "Purchase Order", "Purchase Receipt", "Purchase Invoice",
    "Payment Entry", "Journal Entry", "Stock Entry", "Stock Reconciliation",
]

# ── لكل نموذج ───────────────────────────────────────────────────────────────
# hide     حقول وأقسام تُخفى (فوق EVERYWHERE للمعاملات)
# defaults قيم افتراضية
# labels   تسميات — لمستنداتنا فقط؛ تسميات ERPNext تُصحَّح في glossary.py
#          لتبقى الواجهة الإنجليزية سليمة
# props    خصائص أخرى للحقل: {الحقل: {الخاصية: القيمة}}
# buttons  أزرار يضيفها ERPNext إلى رأس المستند ولا مكان لها في ورشة، بنصّها
#          الإنجليزي. يحجبها public/js/kaj_forms.js عند إضافتها.
# layout   ترتيب النموذج كاملاً (لمستنداتنا). عنصر نصّي = حقل قائم؛ ثلاثية
#          (الاسم، النوع، التسمية) = فاصل جديد يُنشأ
FORMS = {
    # ── بطاقة العمل: من عمود واحد طويل إلى أربع مراحل ──
    # كانت البطاقة تبدأ بـ«التسلسل» ثم تسرد في عمود واحد: الاستلام، الفحص،
    # البلاغ، الفنيين، الخدمات، القطع، الإجماليات، التكلفة. الشكوى — أول ما
    # يُسأل عنه العميل — تأتي بعد قسمَي الاستلام والفحص. التبويبات تتبع ما
    # يجري فعلاً: يُستلم المركب، يُفحص، يُنفَّذ العمل، ثم تُراجَع التكلفة.
    "Work Card": {
        "hide": ["naming_series", "odometer_km"],   # عداد مكرَّر: «قراءة العداد» أعلى البطاقة
        # بطاقة جديدة تبدأ «بانتظار الفحص». كانت تُفتح بلا حالة، فتظهر في القائمة
        # بخانة حالة فارغة إلى أن ينتبه الموظف.
        "defaults": {"status": "بانتظار الفحص"},
        "labels": {
            "sec_complaint": "شكوى العميل",
            "complaint": "ما يشكو منه العميل",
            "customer_phone": "جوال العميل",
            "sec_tech": "الفنيون",
            "sec_notes": "ملاحظات",
        },
        # القسمان كانا مطويَّين في العمود الطويل اختصاراً له. لكلٍّ الآن تبويبه،
        # وقسم مطويّ في تبويب خاص به يُظهر التبويب فارغاً.
        "props": {
            "sec_inspection": {"collapsible": 0},
            "sec_costing": {"collapsible": 0, "print_hide": 1},
            # التكلفة والعمولات وهامش الربح لا تُطبع بأي قالب: البطاقة ورقة
            # تُسلَّم للعميل. القالب الافتراضي لا يعرضها أصلاً
            # (setup/workshop_operations_print_format)؛ هذا للقالب القياسي.
            "labour_hours": {"print_hide": 1},
            "labour_cost": {"print_hide": 1},
            "commission_total": {"print_hide": 1},
            "parts_cost": {"print_hide": 1},
            "total_cost": {"print_hide": 1},
            "gross_profit": {"print_hide": 1},
            "margin_pct": {"print_hide": 1},
            "technicians": {"print_hide": 1},
            "stock_entry": {"print_hide": 1},
            "naming_series": {"print_hide": 1},
        },
        "layout": [
            ("tab_reception", "Tab Break", "الاستلام"),
            "naming_series", "customer", "customer_phone", "vehicle", "plate_number",
            "brand", "model", "mileage",
            "cb1",
            "status", "entry_date", "expected_delivery", "service_line",
            "sec_complaint", "complaint",
            "sec_intake", "fuel_level", "no_visible_damage", "intake_notes",
            "cb_intake", "damages", "intake_photos",
            ("sec_signature", "Section Break", "إقرار العميل"),
            "customer_signature",

            ("tab_inspection", "Tab Break", "الفحص والتشخيص"),
            "sec_inspection", "odometer_km", "cb_inspection", "inspection_result",
            "sec_inspection_items", "inspection_items", "inspection_notes",
            ("sec_diagnosis", "Section Break", "التشخيص"),
            "diagnosis",

            ("tab_work", "Tab Break", "الأعمال والقطع"),
            "sec_services", "services",
            "sec_parts", "warehouse", "parts",
            "sec_tech", "technicians",
            "sec_totals", "services_total", "parts_total", "cb3", "discount", "grand_total",

            ("tab_more", "Tab Break", "التكلفة والملاحظات"),
            "sec_costing", "labour_hours", "labour_cost", "commission_total", "parts_cost",
            "cb_costing", "total_cost", "gross_profit", "margin_pct",
            "sec_notes", "notes", "cb2", "stock_entry", "amended_from",
        ],
    },

    # صف الخدمة كان يعرض رمز الصنف وحده («WS-AC-003»). اسم الخدمة يُجلب عند
    # اختيارها (سكربت بطاقة العمل) ويظهر بجانب الرمز.
    "Work Card Service": {
        "labels": {"service": "الخدمة", "description": "اسم الخدمة"},
        "props": {
            "service": {"columns": 2},
            "description": {"in_list_view": 1, "columns": 4},
        },
    },
    "Work Card Part": {
        "labels": {"item": "القطعة"},
        "props": {
            "item": {"columns": 2},
            "part_name": {"columns": 4},
        },
    },

    # ── المبيعات ──
    "Quotation": {
        "hide": ["quotation_to", "order_type", "crm_deal", "lost_reasons_section",
                 "opportunity", "supplier_quotation", "territory"],
        "buttons": ["Opportunity"],
    },
    "Sales Order": {
        "hide": ["order_type", "skip_delivery_note", "tax_id", "section_break1",
                 "po_no", "po_date", "per_picked", "territory",
                 "shipping_address_column", "col_break46", "company_address",
                 "company_address_display", "company_contact_person"],
    },
    "Delivery Note": {
        "hide": ["tax_id", "issue_credit_note", "section_break1", "per_installed",
                 "print_without_amount", "territory"],
    },
    "Sales Invoice": {
        "hide": ["tax_id", "is_consolidated", "is_debit_note",
                 "update_outstanding_for_self", "update_billed_amount_in_sales_order",
                 "update_billed_amount_in_delivery_note", "time_sheet_list",
                 "section_break_104", "unrealized_profit_loss_account", "is_discounted",
                 "use_company_roundoff_cost_center", "territory",
                 # الدفع داخل الفاتورة يتطلب إعداد نقطة بيع؛ السداد بسند قبض
                 # من زر «إنشاء» في الفاتورة
                 "is_pos", "pos_profile", "payments_tab"],
        # المرتجع يُخصم من المستحق على فاتورته. القيمة القياسية (1) تُبقيه رصيداً
        # مستقلاً على المرتجع نفسه، والفاتورة الأصلية بكامل مبلغها، وتعرض عند
        # الحفظ رسالة تطلب إلغاء خيارٍ في حقل مخفي.
        "defaults": {"update_outstanding_for_self": "0"},
        "buttons": ["Timesheet"],
    },
    "Payment Entry": {
        "hide": ["party_bank_account", "bank_account",
                 "book_advance_payments_in_separate_party_account", "contact_person",
                 "contact_email", "paid_from_account_currency", "paid_to_account_currency",
                 "source_exchange_rate", "target_exchange_rate", "base_paid_amount",
                 "base_received_amount", "received_amount", "taxes_and_charges_section",
                 "section_break_60", "deductions_or_loss_section", "custom_remarks",
                 "is_opening", "print_heading", "payment_order",
                 "base_total_allocated_amount", "difference_amount",
                 "write_off_difference_amount", "clearance_date", "bank",
                 "bank_account_no", "get_outstanding_orders"],
    },

    # ── المشتريات ──
    "Material Request": {
        "hide": ["customer", "buying_price_list", "reference", "transfer_status"],
    },
    "Purchase Order": {
        "hide": ["order_confirmation_no", "order_confirmation_date", "drop_ship", "mps",
                 "ref_sq", "company_billing_address_section", "section_break_48"],
    },
    "Purchase Receipt": {
        "hide": ["billing_address_section", "section_break_98"],
        "buttons": ["Landed Cost Voucher", "Make Stock Entry", "Retention Stock Entry",
                    "Asset", "Asset Movement"],
    },
    "Purchase Invoice": {
        "hide": ["tax_id", "is_paid", "update_outstanding_for_self",
                 "update_billed_amount_in_purchase_order",
                 "update_billed_amount_in_purchase_receipt", "claimed_landed_cost_amount",
                 "use_company_roundoff_cost_center", "payments_tab",
                 "company_shipping_address_section", "company_billing_address_section",
                 "unrealized_profit_loss_account", "sb_14", "supplier_group", "sender",
                 "is_opening"],
        # كما في فاتورة المبيعات: المرتجع يُخصم من فاتورته
        "defaults": {"update_outstanding_for_self": "0"},
    },

    # ── المخزون ──
    "Stock Entry": {
        "hide": ["reference_section", "bom_info_section", "section_break_7qsm",
                 "source_warehouse_address", "source_address_display",
                 "target_warehouse_address", "target_address_display",
                 "additional_costs_section", "supplier_info_tab",
                 "reference_details_section", "is_opening", "per_transferred"],
    },
    "Stock Reconciliation": {
        "hide": ["section_break_22"],
    },
    "Item": {
        "hide": ["is_fixed_asset", "auto_create_assets", "is_grouped_asset",
                 "asset_category", "asset_naming_series", "allow_alternative_item",
                 "has_variants", "is_customer_provided_item", "section_break_znra",
                 "deferred_accounting_section", "item_tax_section_break", "end_of_life",
                 "default_material_request_type", "weight_per_unit", "weight_uom",
                 "serial_nos_and_batches", "variants_section", "supplier_details",
                 "foreign_trade_details", "grant_commission", "customer_details",
                 "manufacturing", "quality_tab", "sb_barcodes", "safety_stock",
                 "lead_time_days", "warranty_period"],
        # السعر والرصيد الافتتاحي في نافذة الإضافة السريعة: كان الصنف يُنشأ بلا
        # سعر، ثم يُبحث عن مكان إدخاله
        "props": {
            "standard_rate": {"allow_in_quick_entry": 1},
            # ERPNext يخفي «الرصيد الافتتاحي» في إصداره الحالي، ومنطقه يعمل: يُنشئ
            # رصيد الصنف عند حفظه. بدونه يُدخَل رصيد كل قطعة بحركة مخزون مستقلة.
            "opening_stock": {"allow_in_quick_entry": 1, "hidden": 0},
            "valuation_rate": {"allow_in_quick_entry": 1},
        },
    },
    "Warehouse": {
        "hide": ["is_rejected_warehouse", "customer", "transit_section",
                 "address_and_contact", "warehouse_contact_info", "tree_details"],
    },

    # ── المحاسبة ──
    "Journal Entry": {
        "hide": ["multi_currency", "is_system_generated", "section_break_tcvw",
                 "tax_withholding_tab", "inter_company_journal_entry_reference",
                 "process_deferred_accounting", "payment_order", "write_off",
                 "finance_book", "from_template", "reference", "pay_to_recd_from",
                 "custom_remark", "clearance_date"],
    },
    "Bank Account": {
        "hide": ["account_subtype", "is_credit_card", "section_break_11",
                 "integration_details_section", "statement_password", "branch_code"],
    },

    # ── صفوف بعينها ──
    "Payment Schedule": {
        # الدفعة: تاريخها ومبلغها. خصم السداد المبكر وأيام الائتمان لمن يبيع بالآجل
        "hide": ["due_date_based_on", "credit_days", "credit_months", "discount_date",
                 "discount", "discount_type", "discount_validity_based_on",
                 "discount_validity", "discounted_amount", "mode_of_payment"],
    },
    "Payment Entry Reference": {
        "hide": ["payment_term", "payment_term_outstanding", "account_type",
                 "payment_type", "account"],
    },
    "Stock Entry Detail": {
        "hide": ["reference_section", "set_basic_rate_manually", "additional_cost",
                 "transferred_qty"],
    },
    "Material Request Item": {
        "hide": ["more_info", "accounting_details_section"],
    },
    "Sales Order Item": {
        "hide": ["planning_section"],
    },
    "Item Default": {
        # يبقى: المستودع، قائمة الأسعار، المورد، حسابات المخزون والمصروف والإيراد
        "hide": ["default_discount_account", "buying_cost_center", "selling_cost_center",
                 "default_provisional_account", "purchase_expense_account",
                 "purchase_expense_contra_account", "deferred_expense_account",
                 "deferred_revenue_account", "inventory_account_currency"],
    },
    "Item Group": {
        "hide": ["sec_break_taxes"],
    },
    "UOM": {
        "hide": ["common_code", "category"],
    },

    # ── العملاء والموردون ──
    "Customer": {
        "hide": ["alias", "gender", "customer_group", "territory", "section_break_hwkr",
                 "loyalty_points_tab", "internal_customer_section", "section_break_nrvh",
                 "tax_withholding_group", "tax_withholding_category", "tax_category",
                 "so_required", "dn_required", "sales_team_tab", "portal_users_tab",
                 "references_section", "market_segment", "industry", "customer_pos_id",
                 "supplier_numbers_section", "website", "language"],
        # عملاء الورشة أفراد في الغالب؛ القيمة القياسية «شركة»
        "defaults": {"customer_type": "Individual"},
        "buttons": ["Opportunity", "Pricing Rule"],
    },
    "Supplier": {
        "hide": ["alias", "gender", "defaults_section", "internal_supplier_section",
                 "section_break_pgad", "tax_withholding_group", "tax_withholding_category",
                 "tax_category", "is_transporter",
                 "allow_purchase_invoice_creation_without_purchase_order",
                 "allow_purchase_invoice_creation_without_purchase_receipt",
                 "block_supplier_section", "portal_users_tab", "section_break_jqla",
                 "supplier_group", "country", "website", "language"],
        "buttons": ["Request for Quotation", "Supplier Quotation", "Pricing Rule"],
    },

    # ── الإعدادات العامة ──
    "User": {
        "hide": ["middle_name", "username", "time_zone", "sb_allow_modules", "short_bio",
                 "desk_settings_section", "navigation_settings_section",
                 "list_settings_section", "form_settings_section",
                 "document_follow_notifications_section", "email_settings",
                 "workspace_section", "app_section", "sb3", "third_party_authentication",
                 "api_access", "sessions_tab", "role_profiles"],
        # لا خادم بريد مُعدّ: الترحيب بالبريد يفشل ويُظهر خطأً عند كل إضافة
        "defaults": {"send_welcome_email": "0"},
    },
    "Company": {
        "hide": ["is_group", "default_holiday_list", "domain", "parent_company",
                 "reporting_currency", "date_of_establishment", "date_of_incorporation",
                 "date_of_commencement", "fax", "registration_info",
                 "exchange_gain__loss_section", "deferred_accounting_section",
                 "advance_payments_section",
                 "exchange_rate_revaluation_settings_section", "budget_detail",
                 "fixed_asset_defaults", "monthly_sales_target", "total_monthly_sales",
                 "purchase_expense_section", "hr_and_payroll_tab", "manufacturing_section",
                 "enable_provisional_accounting_for_non_stock_items",
                 "default_provisional_account", "default_in_transit_warehouse",
                 "section_break_28", "allow_account_creation_against_child_company",
                 "unrealized_profit_loss_account", "default_finance_book",
                 "enable_item_wise_inventory_account", "default_sales_contact"],
    },
    "Role": {
        "hide": ["home_page", "restrict_to_domain", "two_factor_auth"],
    },
    # «الحالة الافتراضية للبطاقة» حقل لا يقرؤه شيء في النظام: من يغيّره ينتظر
    # أثراً لا يحدث. الحالة الافتراضية معرَّفة في نموذج البطاقة أعلاه.
    "Workshop Settings": {
        "hide": ["default_status"],
        # كان النموذج يبدأ برمز الدولة ورابط النظام (حقلان أُضيفا لاحقاً فوقعا
        # في أوله)، واسم الورشة تحتهما. يبدأ الآن بما يُسأل عنه أولاً.
        "layout": [
            "workshop_name", "phone", "tax_number", "cb1", "logo", "default_status",
            "sec1", "address",
            "sec2", "invoice_terms",
            ("sec_whatsapp", "Section Break", "واتساب"),
            "country_code", "public_url",
        ],
    },
    "Activity Log": {
        "hide": ["timeline_doctype", "timeline_name", "link_doctype", "link_name",
                 "reference_owner"],
    },
    # ترويسة الطباعة عند صاحب الورشة ثلاث صور: رأس الصفحة وذيلها والختم. منها
    # يُبنى الباقي (print_template.compose): مصدر الترويسة، وشيفرتها HTML التي
    # كانت تملأ أسفل النموذج، وصورة الإطار ومقاساتها — حقول يكتبها النظام.
    "Letter Head": {
        "hide": ["scripts_section", "source", "footer_source",
                 "letter_head_image_section", "image", "image_height", "image_width", "align",
                 "header_section", "content", "footer_section", "footer",
                 "footer_image_section", "footer_image", "footer_image_height",
                 "footer_image_width", "footer_align", "instructions"],
    },
    # «الشعار والهوية»: من إعدادات موقع كاملة يبقى ما يخصّ هوية النظام
    "Website Settings": {
        "hide": ["sb0", "disable_signup", "show_footer_on_login", "section_break_6",
                 "banner_image", "brand_html", "set_banner_from_image", "top_bar",
                 "navbar_template_section", "banner", "footer_tab", "integrations",
                 "section_break_38", "redirects_tab"],
    },
}


def hidden_fields(doctype):
    """كل ما يُخفى في نموذج: المشترك (للمعاملات وصفوفها) وما يخصّه."""
    names = list(FORMS.get(doctype, {}).get("hide", []))
    shared = EVERYWHERE if doctype in TRANSACTIONS else ROW_EVERYWHERE if doctype in ROW_TABLES else {}
    for group in shared.values():
        names += [f for f in group if f not in names]
    return names


def doctypes():
    return sorted(set(FORMS) | set(TRANSACTIONS) | set(ROW_TABLES))


def for_boot():
    """ما يحتاجه المتصفح: الحقول المخفية والأزرار المحجوبة لكل نموذج.

    الإخفاء نفسه خاصية على الحقل يطبّقها الخادم. لكن سكربتات ERPNext تُظهر
    بعض الحقول بنفسها عند فتح النموذج — التسلسل في كل مستند جديد، ومجاميع
    عملة الشركة — فتعود للظهور. kaj_forms.js يمنع إظهار ما في هذه القائمة.
    """
    return {
        "hidden": {dt: hidden_fields(dt) for dt in doctypes() if hidden_fields(dt)},
        "buttons": {dt: conf["buttons"] for dt, conf in FORMS.items() if conf.get("buttons")},
    }
