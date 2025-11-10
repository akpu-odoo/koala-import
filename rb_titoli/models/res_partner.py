from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    koala_id = fields.Integer(string="Koala ID", index=True)
