from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    koala_id = fields.Integer(string="Koala ID", index=True)
    payment_responsibility = fields.Selection(
        [
            ('customer_pays', 'Customer Pays'),
            ('collaborator_pays', 'Collaborator Pays'),
            ('unknown', 'Unknown')
        ],
        string='Payment Responsibility',
        default='unknown'
    )
