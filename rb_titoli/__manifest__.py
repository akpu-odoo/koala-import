# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Rb Titoli - Import Koala Data",
    "version": "19.0.1.0.0",
    "summary": "Import Data from Koala API's",
    "description": """
        Andrea Mottola - Prenotazione || Task Id - 5138121
        =====================================================
        Module to Import data from Koala API's.
    """,
    "category": "custom",
    # Author
    "author": "Odoo PS",
    "website": "https://www.odoo.com",
    "license": "LGPL-3",
    # Dependency
    "depends": ['account', 'mail'],
    "data": [
        "security/ir.model.access.csv",
        "data/service_cron.xml",
        "data/mail_activity_type_data.xml",
        "views/account_journal_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
}
