from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    koala_id = fields.Integer(string="Koala ID", index=True)
    # This Payment Responsibility is not needed here as one partner may be used in different titles as different payment responsibility.
    payment_responsibility = fields.Selection(
        [
            ('customer_pays', 'Customer Pays'),
            ('collaborator_pays', 'Collaborator Pays'),
            ('unknown', 'Unknown')
        ],
        string='Payment Responsibility',
        default='unknown'
    )
