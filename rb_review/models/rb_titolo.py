from odoo import fields, models, _


class RBTitolo(models.Model):
    _inherit = 'rb.titolo'

    reviewed_by = fields.Many2one('res.users', string="Reviewed By", readonly=True)
    reviewed_on = fields.Datetime(string="Reviewed On", readonly=True)
    review_note = fields.Text(string="Review Note")

    # === Actions ===

    def action_mark_reviewed(self):
        for record in self:
            record.write({
                'review_state': 'reviewed',
                'reviewed_by': self.env.user.id,
                'reviewed_on': fields.Datetime.now(),
            })
            record.message_post(
                body=_(
                    f"Review state set to Reviewed by User {record.reviewed_by.name} "
                    f"on {record.reviewed_on.date()}. "
                    f"Note: {record.review_note or ''}"
                )
            )

    def action_flag_to_check(self):
        for record in self:
            record.write({
                'review_state': 'to_check',
                'reviewed_by': self.env.user.id,
                'reviewed_on': fields.Datetime.now(),
            })
            record.message_post(
                body=_(
                    f"Review state set to To Check by User {record.reviewed_by.name} "
                    f"on {record.reviewed_on.date()}. "
                    f"Note: {record.review_note or ''}"
                )
            )

    def action_open_first_note_snapshot(self):
        """Open popup showing the First Note snapshot (rb.pn.line)"""
        self.ensure_one()
        if not self.rb_pn_line_id:
            return {'type': 'ir.actions.act_window_close'}

        return {
            'type': 'ir.actions.act_window',
            'name': 'First Note Snapshot',
            'res_model': 'rb.pn.line',
            'view_mode': 'form',
            'res_id': self.rb_pn_line_id.id,
            'target': 'fullscreen',
            'views': [(False, 'form')],
        }
