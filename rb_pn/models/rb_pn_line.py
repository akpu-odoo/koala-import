from odoo import api, fields, models, _, Command
from odoo.exceptions import ValidationError


class RBPNLine(models.Model):
    _name = 'rb.pn.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "rb.pn.line"

    # Core fileds
    company_id = fields.Many2one('res.company', string='Company', required=True, )
    move_id = fields.Many2one('account.move', string='Bank Move', required=True, index=True, ondelete='cascade')
    titolo_ids = fields.One2many('rb.titolo', 'rb_pn_line_id', string='Titles', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Partner (resolved)', readonly=True)
    date = fields.Date(string='Date', related='move_id.date', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='move_id.currency_id', store=True, readonly=True)

    _sql_constraints = [
        ('rb_pn_line_move_unique', 'unique(move_id)', 'A First Note line already exists for this bank move.'),
    ]

    @api.model
    def create_prima_mota(self, move, titolo_records):
        if not move:
            raise ValidationError(_("Missing account.move to create First Note line."))

        titolo_ids = self.env['rb.titolo'].search([('koala_titolo_id', 'in', titolo_records)]).ids
        titolo_links = [Command.link(tid) for tid in titolo_ids]

        snapshot = self.search([('move_id', '=', move.id)], limit=1)
        if snapshot:
            snapshot.sudo().write({'titolo_ids': titolo_links})
            body=_("snapshot %s updated", snapshot._get_html_link(title=f"#{snapshot.id}"))
        else:
            vals = {
                'company_id': move.company_id.id or self.env.company.id,
                'move_id': move.id,
                'titolo_ids': titolo_links,
                'partner_id': move.partner_id.id if move.partner_id else False,
            }
            snapshot = self.sudo().create(vals)
            body=_("snapshot %s created", snapshot._get_html_link(title=f"#{snapshot.id}"))
        ref_fields = self.env['rb.pn.line'].fields_get(["titolo_ids"])
        empty_values = dict.fromkeys(["titolo_ids"])
        for line in snapshot:
            if tracking_value_ids := line._mail_track(ref_fields, empty_values)[1]:
                line._message_log(
                    body=body,
                    tracking_value_ids=tracking_value_ids,
                )

    @api.model
    def delete_prima_nota(self, move_line):
        snapshot = self.search([('move_id', '=', move_line.move_id.id)], limit=1)
        if not snapshot:
            return

        reconciled_move_ids = move_line.reconciled_lines_ids.mapped('move_id.id')
        titoli_ids = self.env['rb.titolo'].search([
            ('move_id', 'in', reconciled_move_ids)
        ]).ids

        if titoli_ids:
            snapshot.sudo().write({'titolo_ids': [Command.unlink(tid) for tid in titoli_ids]})

        if not snapshot.titolo_ids:
            snapshot._message_log(
                body=_("snapshot %s deleted", snapshot._get_html_link(title=f"#{snapshot.id}")),
            )
            snapshot.unlink()
