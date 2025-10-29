import logging
from odoo import fields, models
from odoo.addons.rb_titoli.tools.koala_api import KoalaApiController

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    incasso_koala_id = fields.Char("Koala Incasso ID", copy=False, tracking=True)

    def unlink(self):
        """Extend unlink to also delete Koala incasso records when records are deleted."""
        # Capture Koala incasso IDs before deletion
        incasso_ids = [rec.incasso_koala_id for rec in self if rec.incasso_koala_id]

        # Run the base unlink logic first (delete in Odoo)
        res = super(AccountMoveLine, self).unlink()

        if not res:
            return res
        # After successful unlink, call Koala API for each incasso ID
        for incasso_id in incasso_ids:
            try:
                KoalaApiController(self.env)._delete_itconfiguration(
                    endpoint_key='api_incassi_id',
                    record_id=incasso_id
                )
                _logger.info("Deleted Koala incasso %s after record unlink", incasso_id)
            except Exception as e:
                _logger.error("Failed to delete Koala incasso %s: %s", incasso_id, e)

        return res

    def remove_move_reconcile(self):
        if self and self.move_id:
            self.env["rb.pn.line"].delete_prima_nota(self)
        super().remove_move_reconcile()
