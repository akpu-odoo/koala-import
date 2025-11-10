from odoo import api, fields, models, _
from odoo.exceptions import UserError


class RBTitolo(models.Model):
    _inherit = "rb.titolo"

    reviewed_by = fields.Many2one("res.users", string="Reviewed By", readonly=True)
    reviewed_on = fields.Datetime(string="Reviewed On", readonly=True)
    review_note = fields.Text(string="Review Note", tracking=True)
    koala_reciept = fields.Boolean(
        string="Koala Reciept", compute="_compute_koala_reciept", default=False
    )

    def _compute_koala_reciept(self):
        for record in self:
            record.koala_reciept = len(record.rb_pn_line_id) > 0

    # === Actions ===

    def action_mark_reviewed(self):
        for record in self:
            if not record.rb_pn_line_id:
                UserError(_("Koala Reciept is Pending or There is Error"))

            record.write(
                {
                    "review_state": "reviewed",
                    "reviewed_by": self.env.user.id,
                    "reviewed_on": fields.Datetime.now(),
                }
            )
            record.message_post(
                body=_(
                    f"Review state set to Reviewed by User {record.reviewed_by.name} "
                    f"on {record.reviewed_on.date()}. "
                    f"Note: {record.review_note or ''}"
                )
            )

    def action_flag_to_check(self):
        for record in self:
            record.write(
                {
                    "review_state": "to_check",
                    "reviewed_by": self.env.user.id,
                    "reviewed_on": fields.Datetime.now(),
                }
            )
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
            return {"type": "ir.actions.act_window_close"}

        return {
            "type": "ir.actions.act_window",
            "name": "First Note Snapshot",
            "res_model": "rb.pn.line",
            "view_mode": "form",
            "res_id": self.rb_pn_line_id.id,
            "target": "fullscreen",
            "views": [(False, "form")],
        }

    @api.model
    def write(self, vals):
        if self.env.context.get("bypass_reviewer_restrictions"):
            return super().write(vals)

        user = self.env.user
        changed_fields = set(vals.keys())
        if user.has_group("rb_review.group_rb_titolo_reviewer"):
            allowed_fields = {"review_note", "review_state", "payment_responsibility"}
            disallowed = changed_fields - allowed_fields
            if disallowed:
                raise UserError(
                    _(
                        "You can only edit the Review Note, Review State, or Payment Responsibility. "
                        "The following fields cannot be changed: %s"
                    )
                    % ", ".join(disallowed)
                )

        # Reconciler restriction
        elif user.has_group("rb_review.group_rb_titolo_reconciler"):
            allowed_fields = {"review_note"}
            disallowed = changed_fields - allowed_fields
            if disallowed:
                raise UserError(
                    _(
                        "You can only edit the Review Note. "
                        "The following fields cannot be changed: %s"
                    )
                    % ", ".join(disallowed)
                )

        return super().write(vals)

    def action_update_title(self):
        if self.env.context.get("bypass_reviewer_restrictions"):
            return super(RBTitolo, self).action_update_title()

        if self.env.user.has_group("rb_review.group_rb_titolo_reconciler"):
            raise UserError(_("Reconciler's cannot Refresh Title."))

        return (
            super(RBTitolo, self)
            .with_context(bypass_reviewer_restrictions=True)
            .action_update_title()
        )
