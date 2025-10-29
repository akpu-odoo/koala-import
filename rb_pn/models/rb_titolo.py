from odoo import fields, models


class RBTitolo(models.Model):
    _inherit = 'rb.titolo'

    rb_pn_line_id = fields.Many2one("rb.pn.line", string="Prima Note")
