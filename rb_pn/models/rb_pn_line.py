from odoo import fields, models, _


class RBPNLine(models.Model):
    _name = 'rb.pn.line'
    _description = "rb.pn.line"

    # Core links
    company_id = fields.Many2one('res.company', string='Company', required=True, index=True)
    move_id = fields.Many2one('account.move', string='Bank Move', required=True, index=True, ondelete='cascade')
    titolo_ids = fields.Many2many('rb.titolo', string='Titles', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner (resolved)', readonly=True)
    client_partner_id = fields.Many2one('res.partner', string='Client', readonly=True)
    collaborator_partner_id = fields.Many2one('res.partner', string='Collaborator', readonly=True)

    # Snapshot fields (summary of the move / titles) - stored at creation time
    date = fields.Date(string='Date', related='move_id.date', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='move_id.currency_id', store=True, readonly=True)
    total_allocated = fields.Monetary(string='Total Allocated', currency_field='currency_id', readonly=True)
    number_of_titles = fields.Integer(string='Number of Titles', readonly=True)
    titres_snapshot = fields.Text(string='Titles Snapshot (JSON)', readonly=True)
    note = fields.Text(string='Notes', readonly=True)

    # Audit
    create_uid = fields.Many2one('res.users', string='Created by', readonly=True)
    create_date = fields.Datetime(string='Creation Date', readonly=True)

    _sql_constraints = [
        ('rb_pn_line_move_unique', 'unique(move_id)', 'A First Note line already exists for this bank move.'),
    ]
