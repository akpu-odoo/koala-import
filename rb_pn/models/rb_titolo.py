from odoo import fields, models


class RBTitolo(models.Model):
    _name = 'rb.titolo'
    _inherit = ['rb.titolo', 'mail.activity.mixin']

    rb_pn_line_id = fields.Many2one("rb.pn.line", string="Prima Note")
