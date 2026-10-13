# -*- coding: utf-8 -*-
"""قوالب طباعة ما يُسلَّم للعميل: الفاتورة، عرض السعر، بطاقة العمل، السند.

ما يُسلَّم للعميل — وقد يُقدَّم لجهة حكومية — يجب أن يحمل ما يجعله مستنداً:
اسم المنشأة ورقمها الضريبي، رقم المستند وتاريخه، العميل والمركبة (اللوحة
والشاصي)، كل عمل وقطعة في سطر، ثم الإجمالي قبل الضريبة وضريبة القيمة المضافة
والإجمالي شاملها، والمدفوع والمتبقي.

ما كان قبل هذا الملف بصيغته الحالية:
  • قالب الفاتورة عرض العميل والمركبة والبنود و«الإجمالي» وحده: بلا رقم
    فاتورة، بلا اسم المنشأة، بلا سطر للضريبة ولا رقم ضريبي، والوقت بكسور
    الثانية («17:12:24.335567»)، و«None» مكان الشاصي الفارغ. ولم يكن
    الافتراضي: زرّ «طباعة» أخرج قالب ERPNext العام الذي لا يعرف المركبة.
  • بطاقة العمل طُبعت بالقالب القياسي: كل حقل في النموذج، ومنها تكلفة
    العمالة والعمولات والربح الإجمالي وهامش الربح — في ورقة تُسلَّم للعميل.
  • سند القبض بلا قالب.

رأس الصفحة ليس هنا: هو ترويسة الطباعة الافتراضية (setup/workshop_print_template)
— من «إعدادات الورشة»، أو صورة يرفعها صاحب الورشة — فيظهر الرأس نفسه على هذه
القوالب وعلى كل مستند آخر يُطبع بقالب ERPNext القياسي.

قوالب Jinja. جداول لا flex: wkhtmltopdf الذي يولّد الـPDF محرّك قديم.
"""

import frappe

_STYLE = u"""
<style>
  .kp { direction: rtl; text-align: right; font-size: 12px; line-height: 1.6; color: #1c2430; }
  .kp table { width: 100%; border-collapse: collapse; }
  .kp td, .kp th { vertical-align: top; }
  .kp .muted { color: #5b6675; }
  .kp .ltr { direction: ltr; unicode-bidi: embed; display: inline-block; }
  .kp-title { margin: 4px 0 12px; padding: 7px 0; text-align: center; font-size: 16px; font-weight: bold;
              color: #1a2b4a; border-top: 2px solid #1a2b4a; border-bottom: 1px solid #c9d0da; }
  .kp-box { border: 1px solid #c9d0da; }
  .kp-box td { padding: 3px 9px !important; }
  .kp-box .k { width: 110px; color: #5b6675; white-space: nowrap; }
  .kp-box .cap td { background: #f1f3f6; font-weight: bold; color: #1a2b4a; border-bottom: 1px solid #c9d0da; }
  .kp-sec { margin-top: 12px; }
  .kp-sec .h { padding: 4px 9px; background: #f1f3f6; border: 1px solid #c9d0da; border-bottom: 0;
               font-weight: bold; color: #1a2b4a; }
  .kp-sec .b { padding: 7px 9px; border: 1px solid #c9d0da; min-height: 20px; }
  .kp-items { margin-top: 12px; }
  .kp-items th { padding: 5px 8px !important; background: #1a2b4a; color: #fff; font-weight: bold; border: 1px solid #1a2b4a; }
  .kp-items td { padding: 4px 8px !important; border: 1px solid #c9d0da; }
  .kp-items .n { text-align: center; white-space: nowrap; }
  .kp-items .m { text-align: left; white-space: nowrap; }
  .kp-totals td { padding: 3px 9px !important; border: 1px solid #c9d0da; }
  .kp-totals .k { color: #5b6675; }
  .kp-totals .m { text-align: left; white-space: nowrap; }
  .kp-totals .grand td { background: #1a2b4a; color: #fff; font-weight: bold; font-size: 13px; border-color: #1a2b4a; }
  .kp-words { margin-top: 10px; padding: 6px 9px; background: #f1f3f6; border: 1px solid #c9d0da; }
  .kp-terms { margin-top: 12px; padding: 0 10px; font-size: 11px; }
  .kp-note { margin-top: 6px; padding: 0 10px; font-size: 11px; color: #5b6675; }
  .kp-sign td { padding: 30px 0 0 !important; text-align: center; width: 50%; vertical-align: bottom !important; }
  .kp-sign .line { display: inline-block; min-width: 190px; padding-top: 5px; border-top: 1px solid #5b6675; color: #5b6675; }
  .kp-sign img { max-height: 70px; max-width: 220px; display: block; margin: -24px auto 4px; }
</style>
"""

# الرأس: ترويسة الطباعة (تُرسلها الطباعة في letter_head ما لم يُطلب «بلا ترويسة»)
_HEAD = u"""
  {%- if letter_head and not no_letterhead %}
  <div class="letter-head">{{ letter_head }}</div>
  {%- endif %}
"""

_FOOT = u"""
  {%- if footer and not no_letterhead %}
  <div class="letter-head-footer" style="margin-top: 16px;">{{ footer }}</div>
  {%- endif %}
"""

# المبلغ كتابةً. صيغة ERPNext تخلط رمز العملة واسم كسرها بالإنجليزية داخل الجملة
# العربية («OMR ثمانية و ثلاثون و … Baisa فقط»). للريال العُماني تُكتب هنا.
_WORDS = u"""
{%- macro in_words(amount, currency, fallback) -%}
  {%- set rials = (amount or 0)|abs|int -%}
  {%- set baisa = (((amount or 0)|abs - rials) * 1000)|round|int -%}
  {%- if currency == "OMR" -%}
    {{ in_words_ar(rials) }} ريال عُماني{% if baisa %} و{{ baisa }} بيسة{% endif %} فقط لا غير
  {%- else -%}{{ fallback or "" }}{%- endif -%}
{%- endmacro -%}
"""

# علامة اتجاه قبل القوس: «زيت محرك 5W-30 (4 لتر)» كان يُطبع «4) 5W-30 لتر)».
# تُكتب في القوالب __RLM__ وتُستبدل عند الحفظ: حرف لا يُرى لا يُترك في المصدر.
_RLM = u"‏"

INVOICE = _STYLE + _WORDS + u"""
{%- set is_invoice = doc.doctype == "Sales Invoice" -%}
{%- set ws = frappe.get_doc("Workshop Settings") -%}
{%- set party = doc.get("customer") or doc.get("party_name") -%}
{%- set mobile = frappe.db.get_value("Customer", party, "mobile_no") if party else None -%}
{%- set veh = frappe.db.get_value("Customer Vehicle", doc.vehicle,
      ["plate_number", "chassis_no", "brand", "model", "year"], as_dict=True) if doc.get("vehicle") else None -%}
{%- set model_name = frappe.db.get_value("Vehicle Model", veh.model, "model_name") if veh and veh.model else None -%}
{%- set mileage = frappe.db.get_value("Work Card", doc.work_card, "mileage") if doc.get("work_card") else None -%}
{%- if is_invoice and doc.is_return -%}{%- set title = "إشعار دائن (مرتجع)" -%}
{%- elif is_invoice -%}{%- set title = "فاتورة ضريبية" -%}
{%- else -%}{%- set title = "عرض سعر" -%}{%- endif -%}
{%- set doc_date = doc.get("posting_date") or doc.get("transaction_date") -%}

<div class="kp">
""" + _HEAD + u"""
  <div class="kp-title">{{ title }}</div>

  <table>
    <tr>
      <td style="width: 50%; padding-left: 6px;">
        <table class="kp-box">
          <tr class="cap"><td colspan="2">العميل</td></tr>
          <tr><td class="k">الاسم</td><td>{{ doc.customer_name or party or "" }}</td></tr>
          {%- if mobile %}<tr><td class="k">الجوال</td><td><span class="ltr">{{ mobile }}</span></td></tr>{% endif %}
          {%- if doc.get("tax_id") %}<tr><td class="k">الرقم الضريبي</td><td><span class="ltr">{{ doc.tax_id }}</span></td></tr>{% endif %}
          {%- if veh %}
          <tr><td class="k">رقم اللوحة</td><td>{{ veh.plate_number or "" }}</td></tr>
          <tr><td class="k">المركبة</td><td>{{ model_name or veh.brand or "" }}{% if veh.year %} — {{ veh.year }}{% endif %}</td></tr>
          {%- if veh.chassis_no %}<tr><td class="k">رقم الشاصي</td><td><span class="ltr">{{ veh.chassis_no }}</span></td></tr>{% endif %}
          {%- if mileage %}<tr><td class="k">قراءة العداد</td><td>{{ "{:,}".format(mileage) }} كم</td></tr>{% endif %}
          {%- endif %}
        </table>
      </td>
      <td style="width: 50%; padding-right: 6px;">
        <table class="kp-box">
          <tr class="cap"><td colspan="2">{{ "الفاتورة" if is_invoice else "العرض" }}</td></tr>
          <tr><td class="k">الرقم</td><td><span class="ltr"><b>{{ doc.name }}</b></span></td></tr>
          <tr><td class="k">التاريخ</td><td>{{ frappe.utils.formatdate(doc_date) }}{% if doc.get("posting_time") %} — <span class="ltr">{{ (doc.posting_time|string)[:5] }}</span>{% endif %}</td></tr>
          {%- if is_invoice and doc.due_date and not doc.is_return %}<tr><td class="k">تاريخ الاستحقاق</td><td>{{ frappe.utils.formatdate(doc.due_date) }}</td></tr>{% endif %}
          {%- if not is_invoice and doc.get("valid_till") %}<tr><td class="k">صالح حتى</td><td>{{ frappe.utils.formatdate(doc.valid_till) }}</td></tr>{% endif %}
          {%- if is_invoice and doc.get("return_against") %}<tr><td class="k">مرتجع عن</td><td><span class="ltr">{{ doc.return_against }}</span></td></tr>{% endif %}
          {%- if doc.get("work_card") %}<tr><td class="k">بطاقة العمل</td><td><span class="ltr">{{ doc.work_card }}</span></td></tr>{% endif %}
          {%- if doc.get("service_line") %}<tr><td class="k">خط الخدمة</td><td>{{ doc.service_line }}</td></tr>{% endif %}
        </table>
      </td>
    </tr>
  </table>

  <table class="kp-items">
    <thead>
      <tr>
        <th class="n" style="width: 34px;">م</th>
        <th>العمل / القطعة</th>
        <th class="n" style="width: 64px;">الكمية</th>
        <th class="m" style="width: 105px;">سعر الوحدة</th>
        <th class="m" style="width: 115px;">المبلغ</th>
      </tr>
    </thead>
    <tbody>
      {%- for row in doc.items %}
      <tr>
        <td class="n">{{ loop.index }}</td>
        <td>{{ (row.item_name or row.description or row.item_code)|replace("(", "__RLM__(") }}</td>
        <td class="n">{{ row.get_formatted("qty", doc) }}</td>
        <td class="m">{{ row.get_formatted("rate", doc) }}</td>
        <td class="m">{{ row.get_formatted("amount", doc) }}</td>
      </tr>
      {%- endfor %}
    </tbody>
  </table>

  <table style="margin-top: 10px;">
    <tr>
      <td style="padding-left: 12px;">
        {%- set words = in_words(doc.grand_total, doc.currency, doc.get("in_words")) %}
        {%- if words|trim %}
        <div class="kp-words"><span class="muted">المبلغ كتابةً:</span> {{ words }}</div>
        {%- endif %}
        {%- set terms = doc.get("terms") or ws.invoice_terms %}
        {%- if terms %}
        <div class="kp-terms"><b>الشروط والملاحظات</b><br>{{ terms }}</div>
        {%- endif %}
      </td>
      <td style="width: 300px;">
        <table class="kp-totals">
          <tr><td class="k">الإجمالي قبل الضريبة</td><td class="m">{{ doc.get_formatted("total") }}</td></tr>
          {%- if doc.discount_amount %}
          <tr><td class="k">الخصم</td><td class="m">{{ doc.get_formatted("discount_amount") }}</td></tr>
          <tr><td class="k">الصافي بعد الخصم</td><td class="m">{{ doc.get_formatted("net_total") }}</td></tr>
          {%- endif %}
          {%- for tax in doc.taxes %}
          <tr><td class="k">{{ tax.description }}</td><td class="m">{{ tax.get_formatted("tax_amount", doc) }}</td></tr>
          {%- endfor %}
          <tr class="grand"><td>الإجمالي شامل الضريبة</td><td class="m">{{ doc.get_formatted("grand_total") }}</td></tr>
          {%- if is_invoice and not doc.is_return %}
          <tr><td class="k">المدفوع</td><td class="m">{{ frappe.utils.fmt_money((doc.grand_total or 0) - (doc.outstanding_amount or 0), currency=doc.currency) }}</td></tr>
          <tr><td class="k"><b>المتبقي</b></td><td class="m"><b>{{ doc.get_formatted("outstanding_amount") }}</b></td></tr>
          {%- endif %}
        </table>
      </td>
    </tr>
  </table>

  <table class="kp-sign">
    <tr>
      <td><span class="line">توقيع العميل</span></td>
      <td><span class="line">المحاسب / الختم</span></td>
    </tr>
  </table>
""" + _FOOT + u"""
</div>
"""

# بطاقة العمل كما تُسلَّم للعميل عند الاستلام: ما اتُّفق عليه وحالة مركبته.
# لا تكلفة ولا عمولات ولا هامش ربح — تلك لصاحب الورشة، في النموذج.
WORK_CARD = _STYLE + u"""
{%- set ws = frappe.get_doc("Workshop Settings") -%}
{%- set cname = frappe.db.get_value("Customer", doc.customer, "customer_name") if doc.customer else "" -%}
{%- set veh = frappe.db.get_value("Customer Vehicle", doc.vehicle,
      ["chassis_no", "year", "color"], as_dict=True) if doc.get("vehicle") else None -%}
{%- set model_name = frappe.db.get_value("Vehicle Model", doc.model, "model_name") if doc.get("model") else None -%}
{%- set tax_template = frappe.db.get_value("Sales Taxes and Charges Template", {"is_default": 1, "disabled": 0}, "name") -%}
{%- set vat = (frappe.db.get_value("Sales Taxes and Charges",
      {"parent": tax_template, "parenttype": "Sales Taxes and Charges Template"}, "rate") or 0) if tax_template else 0 -%}
{%- set lines = [] -%}
{%- for r in doc.services %}{% set _ = lines.append((r.description or r.service, r.qty, r.rate, r.amount)) %}{% endfor -%}
{%- for r in doc.parts %}{% set _ = lines.append((r.part_name or r.item, r.qty, r.rate, r.amount)) %}{% endfor -%}
{%- set money = frappe.utils.fmt_money -%}
{%- set cur = frappe.db.get_default("currency") -%}

<div class="kp">
""" + _HEAD + u"""
  <div class="kp-title">بطاقة عمل — استلام مركبة</div>

  <table>
    <tr>
      <td style="width: 50%; padding-left: 6px;">
        <table class="kp-box">
          <tr class="cap"><td colspan="2">العميل والمركبة</td></tr>
          <tr><td class="k">العميل</td><td>{{ cname or doc.customer or "" }}</td></tr>
          {%- if doc.customer_phone %}<tr><td class="k">الجوال</td><td><span class="ltr">{{ doc.customer_phone }}</span></td></tr>{% endif %}
          <tr><td class="k">رقم اللوحة</td><td>{{ doc.plate_number or "" }}</td></tr>
          <tr><td class="k">المركبة</td><td>{{ model_name or doc.brand or "" }}{% if veh and veh.year %} — {{ veh.year }}{% endif %}{% if veh and veh.color %} — {{ veh.color }}{% endif %}</td></tr>
          {%- if veh and veh.chassis_no %}<tr><td class="k">رقم الشاصي</td><td><span class="ltr">{{ veh.chassis_no }}</span></td></tr>{% endif %}
          {%- if doc.mileage %}<tr><td class="k">قراءة العداد</td><td>{{ "{:,}".format(doc.mileage) }} كم</td></tr>{% endif %}
        </table>
      </td>
      <td style="width: 50%; padding-right: 6px;">
        <table class="kp-box">
          <tr class="cap"><td colspan="2">البطاقة</td></tr>
          <tr><td class="k">الرقم</td><td><span class="ltr"><b>{{ doc.name }}</b></span></td></tr>
          {%- if doc.entry_date %}<tr><td class="k">تاريخ الدخول</td><td>{{ frappe.utils.formatdate(doc.entry_date) }} — <span class="ltr">{{ (doc.entry_date|string)[11:16] }}</span></td></tr>{% endif %}
          {%- if doc.expected_delivery %}<tr><td class="k">التسليم المتوقع</td><td>{{ frappe.utils.formatdate(doc.expected_delivery) }}</td></tr>{% endif %}
          {%- if doc.service_line %}<tr><td class="k">خط الخدمة</td><td>{{ doc.service_line }}</td></tr>{% endif %}
          {%- if doc.status %}<tr><td class="k">الحالة</td><td>{{ doc.status }}</td></tr>{% endif %}
        </table>
      </td>
    </tr>
  </table>

  <div class="kp-sec">
    <div class="h">شكوى العميل</div>
    <div class="b">{{ doc.complaint or "—" }}</div>
  </div>

  <div class="kp-sec">
    <div class="h">حالة المركبة عند الاستلام</div>
    <div class="b">
      {%- if doc.fuel_level %}<span class="muted">مستوى الوقود:</span> {{ doc.fuel_level }} &nbsp;·&nbsp; {% endif %}
      {%- if doc.damages %}
        <span class="muted">أضرار مسجّلة:</span>
        {%- for d in doc.damages %} {{ d.zone }}{% if d.condition %} ({{ d.condition }}){% endif %}{% if d.note %}: {{ d.note }}{% endif %}{% if not loop.last %}،{% endif %}{% endfor %}
      {%- elif doc.no_visible_damage %}لا توجد أضرار ظاهرة
      {%- else %}<span class="muted">لم تُسجَّل أضرار</span>{% endif %}
      {%- if doc.intake_notes %}<br><span class="muted">ملاحظات:</span> {{ doc.intake_notes }}{% endif %}
    </div>
  </div>

  {%- if doc.diagnosis %}
  <div class="kp-sec">
    <div class="h">التشخيص</div>
    <div class="b">{{ doc.diagnosis }}</div>
  </div>
  {%- endif %}

  {%- if lines %}
  <table class="kp-items">
    <thead>
      <tr>
        <th class="n" style="width: 34px;">م</th>
        <th>العمل / القطعة</th>
        <th class="n" style="width: 64px;">الكمية</th>
        <th class="m" style="width: 105px;">سعر الوحدة</th>
        <th class="m" style="width: 115px;">المبلغ</th>
      </tr>
    </thead>
    <tbody>
      {%- for name, qty, rate, amount in lines %}
      <tr>
        <td class="n">{{ loop.index }}</td>
        <td>{{ (name or "")|replace("(", "__RLM__(") }}</td>
        <td class="n">{{ "%g"|format(qty or 0) }}</td>
        <td class="m">{{ money(rate or 0, currency=cur) }}</td>
        <td class="m">{{ money(amount or 0, currency=cur) }}</td>
      </tr>
      {%- endfor %}
    </tbody>
  </table>

  <table style="margin-top: 10px;">
    <tr>
      <td style="padding-left: 12px;">
        {%- if doc.notes %}<div class="kp-terms"><b>ملاحظات</b><br>{{ doc.notes }}</div>{% endif %}
        {%- if ws.invoice_terms %}<div class="kp-terms"><b>الشروط</b><br>{{ ws.invoice_terms }}</div>{% endif %}
      </td>
      <td style="width: 300px;">
        <table class="kp-totals">
          <tr><td class="k">إجمالي الأعمال</td><td class="m">{{ money(doc.services_total or 0, currency=cur) }}</td></tr>
          <tr><td class="k">إجمالي القطع</td><td class="m">{{ money(doc.parts_total or 0, currency=cur) }}</td></tr>
          {%- if doc.discount %}<tr><td class="k">الخصم</td><td class="m">{{ money(doc.discount, currency=cur) }}</td></tr>{% endif %}
          {%- if vat %}
          <tr><td class="k">الإجمالي قبل الضريبة</td><td class="m">{{ money(doc.grand_total or 0, currency=cur) }}</td></tr>
          <tr><td class="k">ضريبة القيمة المضافة {{ "%g"|format(vat) }}%</td><td class="m">{{ money((doc.grand_total or 0) * vat / 100, currency=cur) }}</td></tr>
          <tr class="grand"><td>الإجمالي التقديري</td><td class="m">{{ money((doc.grand_total or 0) * (1 + vat / 100), currency=cur) }}</td></tr>
          {%- else %}
          <tr class="grand"><td>الإجمالي التقديري</td><td class="m">{{ money(doc.grand_total or 0, currency=cur) }}</td></tr>
          {%- endif %}
        </table>
      </td>
    </tr>
  </table>
  <div class="kp-note">الإجمالي تقديري؛ المبلغ النهائي ما يرد في الفاتورة.</div>
  {%- endif %}

  <div class="kp-note" style="margin-top: 12px;">أقرّ باستلام الورشة لمركبتي بالحالة الموضّحة أعلاه، وأوافق على تنفيذ الأعمال المذكورة.</div>
  <table class="kp-sign">
    <tr>
      <td>{% if doc.customer_signature %}<img src="{{ doc.customer_signature }}" alt="">{% endif %}<span class="line">توقيع العميل</span></td>
      <td><span class="line">موظف الاستقبال</span></td>
    </tr>
  </table>
""" + _FOOT + u"""
</div>
"""

RECEIPT = _STYLE + _WORDS + u"""
{%- set receive = doc.payment_type == "Receive" -%}
{%- if receive -%}{%- set title = "سند قبض" -%}
{%- elif doc.payment_type == "Pay" -%}{%- set title = "سند صرف" -%}
{%- else -%}{%- set title = "سند تحويل داخلي" -%}{%- endif -%}

<div class="kp">
""" + _HEAD + u"""
  <div class="kp-title">{{ title }}</div>

  <table>
    <tr>
      <td style="width: 50%; padding-left: 6px;">
        <table class="kp-box">
          <tr class="cap"><td colspan="2">{{ "استلمنا من" if receive else "صرفنا إلى" }}</td></tr>
          <tr><td class="k">الاسم</td><td>{{ doc.party_name or doc.party or "" }}</td></tr>
          <tr><td class="k">المبلغ</td><td><b>{{ doc.get_formatted("paid_amount") }}</b></td></tr>
          {%- if doc.mode_of_payment %}<tr><td class="k">طريقة الدفع</td><td>{{ _(doc.mode_of_payment) }}</td></tr>{% endif %}
        </table>
      </td>
      <td style="width: 50%; padding-right: 6px;">
        <table class="kp-box">
          <tr class="cap"><td colspan="2">السند</td></tr>
          <tr><td class="k">الرقم</td><td><span class="ltr"><b>{{ doc.name }}</b></span></td></tr>
          <tr><td class="k">التاريخ</td><td>{{ frappe.utils.formatdate(doc.posting_date) }}</td></tr>
          {%- if doc.reference_no %}<tr><td class="k">رقم المرجع</td><td>{{ doc.reference_no }}</td></tr>{% endif %}
          {%- if doc.reference_date %}<tr><td class="k">تاريخ المرجع</td><td>{{ frappe.utils.formatdate(doc.reference_date) }}</td></tr>{% endif %}
        </table>
      </td>
    </tr>
  </table>

  {%- set words = in_words(doc.paid_amount, doc.paid_from_account_currency or doc.paid_to_account_currency, "") %}
  {%- if words|trim %}
  <div class="kp-words"><span class="muted">المبلغ كتابةً:</span> {{ words }}</div>
  {%- endif %}

  {%- if doc.references %}
  <table class="kp-items">
    <thead>
      <tr>
        <th class="n" style="width: 34px;">م</th>
        <th>وذلك عن</th>
        <th class="m" style="width: 125px;">قيمة المستند</th>
        <th class="m" style="width: 125px;">المسدَّد بهذا السند</th>
      </tr>
    </thead>
    <tbody>
      {%- for row in doc.references %}
      <tr>
        <td class="n">{{ loop.index }}</td>
        <td>{{ _(row.reference_doctype) }} <span class="ltr">{{ row.reference_name }}</span></td>
        <td class="m">{{ row.get_formatted("total_amount", doc) }}</td>
        <td class="m">{{ row.get_formatted("allocated_amount", doc) }}</td>
      </tr>
      {%- endfor %}
    </tbody>
  </table>
  {%- endif %}

  {%- if doc.remarks and not doc.references %}
  <div class="kp-sec"><div class="h">البيان</div><div class="b">{{ doc.remarks }}</div></div>
  {%- endif %}

  <table class="kp-sign">
    <tr>
      <td><span class="line">{{ "الدافع" if receive else "المستلم" }}</span></td>
      <td><span class="line">المحاسب / الختم</span></td>
    </tr>
  </table>
""" + _FOOT + u"""
</div>
"""

MODULE = "Khat Workshop"

# الاسم، نوع المستند، القالب
FORMATS = [
    ("فاتورة تشغيل مفصّلة - خط الجزيرة", "Sales Invoice", INVOICE),
    ("عرض سعر مفصّل - خط الجزيرة", "Quotation", INVOICE),
    ("بطاقة عمل - خط الجزيرة", "Work Card", WORK_CARD),
    ("سند قبض وصرف - خط الجزيرة", "Payment Entry", RECEIPT),
]


def _ensure_print_format(name, doctype, template):
    html = template.replace("__RLM__", _RLM)
    if frappe.db.exists("Print Format", name):
        doc = frappe.get_doc("Print Format", name)
        if doc.html == html and not doc.disabled:
            return "ok"
        doc.html = html
        doc.disabled = 0
        doc.save(ignore_permissions=True)
        return "updated"
    frappe.get_doc({
        "doctype": "Print Format",
        "name": name,
        "doc_type": doctype,
        "module": MODULE,
        "standard": "No",
        "custom_format": 1,
        "print_format_type": "Jinja",
        "disabled": 0,
        "html": html,
    }).insert(ignore_permissions=True)
    return "created"


def _make_default(name, doctype):
    """زرّ «طباعة» يفتح بهذا القالب. كان الافتراضي قالب ERPNext العام، والقالب
    المفصّل يُختار يدوياً من قائمة في كل مرة."""
    current = frappe.db.get_value(
        "Property Setter",
        {"doc_type": doctype, "property": "default_print_format", "field_name": ["is", "not set"]},
        "value")
    if current == name:
        return 0
    frappe.make_property_setter({
        "doctype": doctype, "doctype_or_field": "DocType",
        "property": "default_print_format", "value": name, "property_type": "Data",
    }, validate_fields_for_doctype=False)
    return 1


def execute():
    results, defaults = {}, 0
    for name, doctype, template in FORMATS:
        if not frappe.db.exists("DocType", doctype):
            continue
        results[doctype] = _ensure_print_format(name, doctype, template)
        defaults += _make_default(name, doctype)
    frappe.db.commit()
    frappe.clear_cache()
    print("OPERATIONS_PRINT_FORMAT %s defaults_set=%d" % (results, defaults))
