from datetime import datetime, timezone
import logging

from odoo import models
from odoo.addons.rb_titoli.tools.koala_api import KoalaApiController

_logger = logging.getLogger(__name__)


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    def _set_move_line_to_statement_line_move(self, lines_to_set, lines_to_add):
        super()._set_move_line_to_statement_line_move(lines_to_set, lines_to_add)

        move_line_ids = self.move_id.line_ids - lines_to_set
        titoli_ids = {}

        for move_line in move_line_ids:
            reconciled_move_ids = move_line.reconciled_lines_ids.mapped('move_id.id')
            titoli_records = self.env['rb.titolo'].search([('move_id', 'in', reconciled_move_ids)])
            for titoli in titoli_records:
                titoli_ids[titoli.koala_titolo_id] = move_line.id

        if not titoli_ids:
            return

        # idConto and idTipoPagamento has not consider in document.
        payload = {
            "idConto": 84,
            "idTipoPagamento": 51,
            "data": datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z'),
            "idTitoli": list(titoli_ids.keys()),
        }

        try:
            koala_invoices = KoalaApiController(self.env)._post_itconfiguration('api_incassi', payload)
        except Exception as e:
            _logger.error("Failed to post Koala incassi: %s", e)
            return

        if not koala_invoices:
            _logger.warning("Not found invoice")
            return

        for invoice in koala_invoices:
            id_titolo = invoice.get('idTitolo')
            line_id = titoli_ids.get(id_titolo)
            if line_id and invoice.get('idIncasso'):
                self.env['account.move.line'].browse(line_id).write({
                    'incasso_koala_id': invoice['idIncasso']
                })
