# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Prima Nota",
    "version": "19.0.1.0.0",
    "summary": "First Note lines for reconciled bank moves",
    "description": """
        Andrea Mottola - Prenotazione || Task Id - 5138121
        =====================================================
        First Note lines for reconciled bank moves.
    """,
    "category": "custom",
    # Author
    "author": "Odoo PS",
    "website": "https://www.odoo.com",
    "license": "LGPL-3",
    # Dependency
    "depends": ["rb_titoli", "account_accountant"],
    "data": [
        'security/ir.model.access.csv',
        'views/rb_pn_line_views.xml',
    ],
    "installable": True,
    "application": True,
}
