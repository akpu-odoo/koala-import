# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Review",
    "version": "19.0.1.0.0",
    "summary": "Review module ensures consistency between the First Note and reconciled Titles.",
    "description": """
        Andrea Mottola - Prenotazione || Task Id - 5138121
        ===========================================================================================
        The module allows reviewers to mark Titles as reviewed, flagged for verification, or reset
        to pending. By default, it displays only Titles that are unreviewed or require checking.
    """,
    "category": "custom",
    # Author
    "author": "Odoo PS",
    "website": "https://www.odoo.com",
    "license": "LGPL-3",
    # Dependency
    "depends": ['rb_pn', 'rb_titoli'],
    "data": [
        # 'security/rb_titolo_groups.xml',
        # "security/ir.model.access.csv",
        "views/rb_titoli_views.xml",
    ],
    "installable": True,
}
