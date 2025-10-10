from datetime import datetime, timedelta
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.addons.rb_titoli.controllers.main import KoalaApiController

koala_service = KoalaApiController()
_logger = logging.getLogger(__name__)


class RBTitolo(models.Model):
    _name = 'rb.titolo'
    _description = "RB Titolo"

    koala_titolo_id = fields.Integer(string="Koala Title ID", index=True)
    numero = fields.Char(string='Numero')
    cliente = fields.Char(string='Cliente')
    fornitore = fields.Char(string='Fornitore')
    tipo = fields.Char(string='Tipo')
    compagnia = fields.Char(string='Compagnia')
    data = fields.Datetime(string='Data')
    operazione = fields.Char(string='Operazione')
    data_inizio = fields.Date(string='Data Inizio')
    data_fine = fields.Date(string='Data Fine')
    frazionamento = fields.Char(string='Frazionamento')
    premio = fields.Float(string='Premio')
    competenze = fields.Float(string='Competenze')
    saldato = fields.Boolean(string='Saldato')
    versato = fields.Boolean(string='Versato')

    # Additional fields
    idquietanza = fields.Integer(string='ID Quietanza')
    stato = fields.Char(string='Stato')
    imponibile = fields.Float(string='Imponibile')
    importo_agenzia = fields.Float(string='Importo Agenzia')
    importo_gestore = fields.Float(string='Importo Gestore')
    perc_agenzia = fields.Float(string='Perc Agenzia')
    perc_gestore = fields.Float(string='Perc Gestore')
    perc_gestore_competenze = fields.Float(string='Perc Gestore Competenze')
    importo_gestore_competenze = fields.Float(string='Importo Gestore Competenze')
    tot_competenze = fields.Float(string='Totale Competenze')
    autentica_comp = fields.Float(string='Autentica Comp')
    motivazione = fields.Text(string='Motivazione')
    quota_associativa = fields.Float(string='Quota Associativa')
    tipo_pagamento_coll = fields.Char(string='Tipo Pagamento Collaboratore')
    anticipato_collaboratore = fields.Boolean(string='Anticipato Collaboratore')
    note = fields.Text(string='Note')
    imposte = fields.Float(string='Imposte')
    ssn = fields.Float(string='SSN')
    diritti_emissione = fields.Float(string='Diritti Emissione')
    premio_lordo = fields.Float(string='Premio Lordo')
    anticipo_spese = fields.Float(string='Anticipo Spese')
    perc_ritenuta = fields.Float(string='Perc Ritenuta')
    premio_totale = fields.Float(string='Premio Totale')
    perc_collaboratore = fields.Float(string='Perc Collaboratore')
    autentica = fields.Float(string='Autentica')
    costo_autentica = fields.Float(string='Costo Autentica')
    accessori = fields.Float(string='Accessori')
    spese = fields.Float(string='Spese')
    nascondi_foglio_cassa = fields.Boolean(string='Nascondi Foglio Cassa')
    usa_castelletto = fields.Boolean(string='Usa Castelletto')
    idrca = fields.Integer(string='ID RCA')
    idvita = fields.Integer(string='ID Vita')
    simpli = fields.Char(string='Simpli')
    data_inserimento = fields.Datetime(string='Data Inserimento')
    ultimo_incasso_nome = fields.Char(string='Ultimo Incasso Nome')
    ultimo_incasso_data = fields.Date(string='Ultimo Incasso Data')
    ultimo_incasso_intestato_compagnia = fields.Boolean(string='Ultimo Incasso Intestato Compagnia')
    incassato = fields.Float(string='Incassato')
    saldato_old = fields.Boolean(string='Saldato Old')
    codice_operazione = fields.Char(string='Codice Operazione')
    data_comunicazione = fields.Datetime(string='Data Comunicazione')
    prodotto = fields.Char(string='Prodotto')
    costo_gps = fields.Float(string='Costo GPS')
    prima_emissione = fields.Boolean(string='Prima Emissione')
    rinnovo = fields.Boolean(string='Rinnovo')
    val_ritenuta = fields.Float(string='Valore Ritenuta')
    importo_versato = fields.Float(string='Importo Versato')
    non_usare_garanzie = fields.Boolean(string='Non Usare Garanzie')
    importo_da_versare = fields.Float(string='Importo Da Versare')
    non_altera_polizza = fields.Boolean(string='Non Altera Polizza')
    tot_credito_provv_fornitore = fields.Float(string='Totale Credito Provv. Fornitore')
    ultimo_incasso_conto = fields.Char(string='Ultimo Incasso Conto')
    competenze_surplus = fields.Float(string='Competenze Surplus')
    val_ritenuta_fornitore = fields.Float(string='Valore Ritenuta Fornitore')

    partner_cliente_id = fields.Many2one('res.partner', string='Client')
    partner_collaboratore_id = fields.Many2one('res.partner', string='Collaborator')
    move_id = fields.Many2one('account.move', string='Account Move')

    _sql_constraints = [
        ('koala_titolo_unique', 'unique(koala_titolo_id)', 'Koala Titolo ID must be unique!')
    ]

    @api.model
    def upsert_partner(self, name, koala_id=None, payment_responsibility='unknown'):
        """Get or create res.partner with optional Koala ID and payment responsibility"""
        partner = self.env['res.partner'].search([('koala_id', '=', koala_id)], limit=1) if koala_id else None
        if not partner:
            partner = self.env['res.partner'].create({
                'name': name,
                'koala_id': koala_id,
                'payment_responsibility': payment_responsibility
            })
        else:
            # update koala_id and responsibility if needed
            if partner.payment_responsibility != payment_responsibility:
                partner.write({'payment_responsibility': payment_responsibility})
        return partner

    @api.model
    def process_title(self, koala_titolo_records):
        """
        Main function to process Titles
        Steps:
        1. Fetch detail from /api/Titoli/{id} → idrca/idvita
        2. Fetch policy /api/Polizze/... → idcliente/idgestore
        3. Upsert partners
        4. Create or update Titles and related Account Moves
        """
        create_data = []
        two_months_ago = datetime.today() - timedelta(days=60)
        for koala_titolo in koala_titolo_records:
            koala_titolo_id = koala_titolo.get('id')

            # 1 Fetch title detail
            try:
                title_detail = koala_service._get_itconfiguration(endpoint_key='api_titoli_id', record_id=koala_titolo_id)
                if not title_detail:
                    raise UserError(f"Title {koala_titolo_id} not found in Koala API")
                if title_detail.get('dataInserimento') and title_detail.get('dataInserimento') <= two_months_ago:
                    continue

                # Extract policy references
                idrca = title_detail.get('idrca')
                idvita = title_detail.get('idvita')
                policy_data = {}
                if idrca:
                    policy_data = koala_service._get_itconfiguration(endpoint_key='api_rca_idrca', record_id=idrca)
                elif idvita:
                    # policy_data = koala_service._get_itconfiguration(endpoint_key='api_vita_idvita', record_id=idvita)
                    # demo data for test
                    policy_data = {
                        "id": 1,
                        "idcliente": 1023,
                        "idgestore": 7,
                        "dbOrigineNome": "Via Roma",
                    }
                else:
                    raise UserError(f"Title {koala_titolo_id} has no policy reference")

                if not policy_data:
                    _logger.warning("Skipping title %s due to missing policy data", koala_titolo_id)
                    continue

            except Exception as e:
                _logger.exception("Error processing title %s: %s", koala_titolo_id, e)
                continue

            # 2 Upsert partners
            client = self.upsert_partner(
                name=policy_data.get('dbOrigineNome', 'Unknown Client'),
                koala_id=policy_data.get('idcliente'),
                payment_responsibility='customer_pays'
            )
            collaborator = self.upsert_partner(
                name=policy_data.get('dbOrigineNome', 'Unknown Collaborator'),
                koala_id=policy_data.get('idgestore'),
                payment_responsibility='collaborator_pays'
            )

            # 3 Prepare rb.titolo values
            rb_vals = self.prepare_values(koala_titolo | title_detail)
            rb_vals['partner_cliente_id'] = client.id
            rb_vals['partner_collaboratore_id'] = collaborator.id
            move_vals = self.create_account_move(rb_vals, client, collaborator)

            # 4 Create/ Update Titles and Account move
            rb_record = self.search([('koala_titolo_id', '=', koala_titolo_id)], limit=1)
            if rb_record:
                rb_record.move_id.write(move_vals)
                rb_record.write(rb_vals)
                _logger.info('------------> update records :- %s <-------------', rb_record.id)
            else:
                rb_vals['koala_titolo_id'] = koala_titolo_id
                move_record = self.env['account.move'].create(move_vals)
                rb_vals['move_id'] = move_record.id
                create_data.append(rb_vals)
        self.create_koala_titles(create_data)

    @api.model
    def create_koala_titles(self, create_data):
        """Create records for the title"""
        if create_data:
            create_result = self.create(create_data)
            _logger.info("------------> Created %d rb_titolo records <-------------", len(create_result))

    @api.model
    def create_account_move(self, rb_record, client_partner, collaborator_partner):
        """
        Create account.move of type 'entry' for the title
        """
        # Partner selection logic
        payment_responsibility = client_partner.payment_responsibility
        if payment_responsibility == 'customer_pays' or payment_responsibility == 'unknown':
            partner_to_use = client_partner
        else:
            partner_to_use = collaborator_partner

        journal = self.env['account.journal'].search([('rb_titolo','=', True)], limit=1)
        if not journal:
            raise UserError("Journal 'RB Titles' not found")

        move_vals = {
            'move_type': 'entry',
            'journal_id': journal.id,
            'date': rb_record.get('data'),
            'ref': rb_record.get('numero'),
            'line_ids': [
                # Partner line
                (0, 0, {
                    'account_id': self.env['account.account'].search([('account_type','=','asset_receivable')], limit=1).id,
                    'partner_id': partner_to_use.id,
                    'name': rb_record.get('numero'),
                    'debit': rb_record.get('tot_competenze', 0.0),
                }),
                # Counterpart line
                (0, 0, {
                    'account_id': self.env['account.account'].search([('account_type','=','income_other')], limit=1).id,
                    'partner_id': partner_to_use.id,
                    'name': rb_record.get('numero'),
                    'credit': rb_record.get('tot_competenze', 0.0),
                }),
            ]
        }
        return move_vals

    @api.model
    def _cron_koala_get_titles(self):
        try:
            records = koala_service._get_itconfiguration(endpoint_key='api_titoli')
            if records:
                self.process_title(records)
        except Exception as e:
            _logger.warning("Failed to fetch Koala titles: %s", e)

    def prepare_values(self, vals):
        return {
            'numero': vals.get('numero'),
            'cliente': vals.get('cliente'),
            'fornitore': vals.get('fornitore'),
            'tipo': vals.get('tipo'),
            'compagnia': vals.get('compagnia'),
            'data': self._parse_datetime(vals.get('data')),
            'operazione': vals.get('stato') or vals.get('operazione'),
            'data_inizio': vals.get('dataInizio'),
            'data_fine': vals.get('dataFine'),
            'frazionamento': vals.get('frazionamento'),
            'premio': vals.get('premio'),
            'premio_lordo': vals.get('premioLordo'),
            'premio_totale': vals.get('premioTotale'),
            'competenze': vals.get('competenze'),
            'tot_competenze': vals.get('totCompetenze'),
            'saldato': vals.get('saldato', False),
            'versato': vals.get('versato', False),
            'idquietanza': vals.get('idquietanza'),
            'imponibile': vals.get('imponibile'),
            'importo_agenzia': vals.get('importoAgenzia'),
            'importo_gestore': vals.get('importoGestore'),
            'perc_agenzia': vals.get('percAgenzia'),
            'perc_gestore': vals.get('percGestore'),
            'perc_gestore_competenze': vals.get('percGestoreCompetenze'),
            'importo_gestore_competenze': vals.get('importoGestoreCompetenze'),
            'autentica_comp': vals.get('autenticaComp'),
            'motivazione': vals.get('motivazione'),
            'quota_associativa': vals.get('quotaAssociativa'),
            'tipo_pagamento_coll': vals.get('tipoPagamentoColl'),
            'anticipato_collaboratore': vals.get('anticipatoCollaboratore', False),
            'note': vals.get('note'),
            'imposte': vals.get('imposte'),
            'ssn': vals.get('ssn'),
            'diritti_emissione': vals.get('dirittiEmissione'),
            'nascondi_foglio_cassa': vals.get('nascondiFoglioCassa', False),
            'usa_castelletto': vals.get('usaCastelletto', False),
            'idrca': vals.get('idrca'),
            'idvita': vals.get('idvita'),
            'simpli': vals.get('simpli'),
            'data_inserimento': self._parse_datetime(vals.get('dataInserimento')),
            'ultimo_incasso_nome': vals.get('ultimoIncassoNome'),
            'ultimo_incasso_data': vals.get('ultimoIncassoData'),
            'ultimo_incasso_intestato_compagnia': vals.get('ultimoIncassoIntestatoCompagnia', False),
            'incassato': vals.get('incassato'),
            'saldato_old': vals.get('saldatoOld', False),
            'codice_operazione': vals.get('codiceOperazione'),
            'data_comunicazione': self._parse_datetime(vals.get('dataComunicazione')),
            'prodotto': vals.get('prodotto'),
            'costo_gps': vals.get('costoGps'),
            'prima_emissione': vals.get('primaEmissione', False),
            'rinnovo': vals.get('rinnovo', False),
            'val_ritenuta': vals.get('valRitenuta'),
            'importo_versato': vals.get('importoVersato'),
            'non_usare_garanzie': vals.get('nonUsareGaranzie', False),
            'importo_da_versare': vals.get('importoDaVersare'),
            'non_altera_polizza': vals.get('nonAlteraPolizza', False),
            'tot_credito_provv_fornitore': vals.get('totCreditoProvvFornitore'),
            'ultimo_incasso_conto': vals.get('ultimoIncassoConto'),
            'competenze_surplus': vals.get('competenzeSurplus'),
            'val_ritenuta_fornitore': vals.get('valRitenutaFornitore'),
        }

    def action_update_title(self, koala_titolo_id):
        """Update record on button click"""
        if koala_titolo_id:
            koala_titolo = [{'id': koala_titolo_id}]
            self.process_title(koala_titolo)

    def _parse_datetime(self, value):
        """Update datetime format"""
        try:
            return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S') if value else None
        except Exception:
            return None
