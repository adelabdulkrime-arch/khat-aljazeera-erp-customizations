# -*- coding: utf-8 -*-
"""Header, footer and official stamp on every printed document.

Mazoon's "قوالب الطباعة" screen is three uploads — header image, footer image,
and a round official stamp — that then appear on every printout. Frappe's Letter
Head already carries a header and footer, but only one image each and no stamp,
and its native source/footer_source toggles make combining an image with a
stamp awkward.

So this drives the whole letter head from three custom Attach fields
(setup/workshop_print_template adds them) and composes the header/footer HTML
from them on save. The three fields are the single source of truth; the native
`source`/`footer_source` are forced to HTML so nothing competes with what we
build here.

Two things are handled on save:
  * the images are forced public — wkhtmltopdf fetches them over HTTP while
    rendering the PDF and cannot read a private file, so a private upload would
    print as a broken image;
  * the header and footer HTML are rebuilt, placing the stamp as an overlay
    just above the footer band where a signature stamp normally sits.
"""

from urllib.parse import quote

import frappe

IMG_FIELDS = ("kaj_header_img", "kaj_footer_img", "kaj_stamp_img")


def _src(url):
    """A URL safe to drop into an <img src>. Uploaded names carry spaces and
    Arabic; wkhtmltopdf will not fetch those unless they are percent-encoded."""
    return quote(url, safe="/") if url else url


def _make_public(url):
    """Return a public URL for an uploaded file, flipping it if needed."""
    if not url:
        return url
    fname = frappe.db.get_value("File", {"file_url": url}, "name")
    if not fname:
        return url
    try:
        f = frappe.get_doc("File", fname)
        if f.is_private:
            f.is_private = 0
            f.save(ignore_permissions=True)
            return f.file_url
    except Exception:
        frappe.log_error(title="letter head make_public failed",
                         message=frappe.get_traceback())
    return url


def compose(doc, method=None):
    """Build the letter head header/footer from the three custom images."""
    # Nothing of ours to do on a letter head that uses none of our fields.
    if not any(doc.get(f) for f in IMG_FIELDS):
        return

    header = _make_public(doc.get("kaj_header_img"))
    footer = _make_public(doc.get("kaj_footer_img"))
    stamp = _make_public(doc.get("kaj_stamp_img"))

    # Repoint the fields at their now-public URLs.
    doc.kaj_header_img, doc.kaj_footer_img, doc.kaj_stamp_img = header, footer, stamp

    # Header: a full-width image.
    if header:
        doc.source = "HTML"
        doc.content = (
            '<div style="text-align:center">'
            '<img src="%s" style="width:100%%; max-height:120px; object-fit:contain"></div>'
            % _src(header)
        )

    # Footer: the footer image full width, with the stamp overlaid just above
    # the band, on the left where a signature stamp usually falls. Either image
    # may be absent — the layout holds with just one.
    if footer or stamp:
        doc.footer_source = "HTML"
        parts = ['<div style="position:relative; width:100%">']
        if stamp:
            parts.append(
                '<img src="%s" style="position:absolute; bottom:100%%; left:24px; '
                'width:92px; height:auto; margin-bottom:6px; opacity:.95">'
                % _src(stamp)
            )
        if footer:
            parts.append(
                '<img src="%s" style="width:100%%; max-height:90px; '
                'object-fit:contain; display:block">'
                % _src(footer)
            )
        parts.append('</div>')
        doc.footer = "".join(parts)
