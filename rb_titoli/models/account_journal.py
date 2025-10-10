from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    rb_titolo = fields.Boolean(
        string="RB Titolo",
        help="Mark the journal to be used for RB Titolo records",
        default=False,
    )
