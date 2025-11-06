from datetime import datetime, timedelta
import logging

from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError
from odoo.addons.rb_titoli.tools.koala_api import KoalaApiController

_logger = logging.getLogger(__name__)


class RBTitolo(models.Model):
    _name = "rb.titolo"
    _description = "RB Titolo"

    koala_titolo_id = fields.Integer(string="Koala Title ID", index=True)
    numero = fields.Char(string="Numero")
    cliente = fields.Char(string="Cliente")
    fornitore = fields.Char(string="Fornitore")
    tipo = fields.Char(string="Tipo")
    compagnia = fields.Char(string="Compagnia")
    data = fields.Datetime(string="Data")
    operazione = fields.Char(string="Operazione")
    data_inizio = fields.Date(string="Data Inizio")
    data_fine = fields.Date(string="Data Fine")
    frazionamento = fields.Char(string="Frazionamento")
    premio = fields.Float(string="Premio")
    competenze = fields.Float(string="Competenze")
    saldato = fields.Boolean(string="Saldato")
    versato = fields.Boolean(string="Versato")

    # Additional fields
    idquietanza = fields.Integer(string="ID Quietanza")
    stato = fields.Char(string="Stato")
    imponibile = fields.Float(string="Imponibile")
    importo_agenzia = fields.Float(string="Importo Agenzia")
    importo_gestore = fields.Float(string="Importo Gestore")
    perc_agenzia = fields.Float(string="Perc Agenzia")
    perc_gestore = fields.Float(string="Perc Gestore")
    perc_gestore_competenze = fields.Float(string="Perc Gestore Competenze")
    importo_gestore_competenze = fields.Float(string="Importo Gestore Competenze")
    tot_competenze = fields.Float(string="Totale Competenze")
    autentica_comp = fields.Float(string="Autentica Comp")
    motivazione = fields.Text(string="Motivazione")
    quota_associativa = fields.Float(string="Quota Associativa")
    tipo_pagamento_coll = fields.Char(string="Tipo Pagamento Collaboratore")
    anticipato_collaboratore = fields.Boolean(string="Anticipato Collaboratore")
    note = fields.Text(string="Note")
    imposte = fields.Float(string="Imposte")
    ssn = fields.Float(string="SSN")
    diritti_emissione = fields.Float(string="Diritti Emissione")
    premio_lordo = fields.Float(string="Premio Lordo")
    anticipo_spese = fields.Float(string="Anticipo Spese")
    perc_ritenuta = fields.Float(string="Perc Ritenuta")
    premio_totale = fields.Float(string="Premio Totale")
    perc_collaboratore = fields.Float(string="Perc Collaboratore")
    autentica = fields.Float(string="Autentica")
    costo_autentica = fields.Float(string="Costo Autentica")
    accessori = fields.Float(string="Accessori")
    spese = fields.Float(string="Spese")
    nascondi_foglio_cassa = fields.Boolean(string="Nascondi Foglio Cassa")
    usa_castelletto = fields.Boolean(string="Usa Castelletto")
    idrca = fields.Integer(string="ID RCA")
    idvita = fields.Integer(string="ID Vita")
    simpli = fields.Char(string="Simpli")
    data_inserimento = fields.Datetime(string="Data Inserimento")
    ultimo_incasso_nome = fields.Char(string="Ultimo Incasso Nome")
    ultimo_incasso_data = fields.Date(string="Ultimo Incasso Data")
    ultimo_incasso_intestato_compagnia = fields.Boolean(
        string="Ultimo Incasso Intestato Compagnia"
    )
    incassato = fields.Float(string="Incassato")
    saldato_old = fields.Boolean(string="Saldato Old")
    codice_operazione = fields.Char(string="Codice Operazione")
    data_comunicazione = fields.Datetime(string="Data Comunicazione")
    prodotto = fields.Char(string="Prodotto")
    costo_gps = fields.Float(string="Costo GPS")
    prima_emissione = fields.Boolean(string="Prima Emissione")
    rinnovo = fields.Boolean(string="Rinnovo")
    val_ritenuta = fields.Float(string="Valore Ritenuta")
    importo_versato = fields.Float(string="Importo Versato")
    non_usare_garanzie = fields.Boolean(string="Non Usare Garanzie")
    importo_da_versare = fields.Float(string="Importo Da Versare")
    non_altera_polizza = fields.Boolean(string="Non Altera Polizza")
    tot_credito_provv_fornitore = fields.Float(string="Totale Credito Provv. Fornitore")
    ultimo_incasso_conto = fields.Char(string="Ultimo Incasso Conto")
    competenze_surplus = fields.Float(string="Competenze Surplus")
    val_ritenuta_fornitore = fields.Float(string="Valore Ritenuta Fornitore")

    partner_cliente_id = fields.Many2one("res.partner", string="Client")
    partner_collaboratore_id = fields.Many2one("res.partner", string="Collaborator")
    move_id = fields.Many2one("account.move", string="Account Move")

    payment_responsibility = fields.Selection(
        [
            ("customer_pays", "Customer Pays"),
            ("collaborator_pays", "Collaborator Pays"),
            ("unknown", "Unknown"),
        ],
        string="Payment Responsibility",
        default="unknown",
    )

    _sql_constraints = [
        (
            "koala_titolo_unique",
            "unique(koala_titolo_id)",
            "Koala Titolo ID must be unique!",
        )
    ]

    """When Resolving the Partner if payment resposibility changes for the title( Who is handling the payment ) we need to update the partner"""
    @api.depends("payment_responsibility")
    def update_payment_responsibility(self):
        for record in self:
            if record.payment_responsibility == "collaborator_pays":
                if not record.partner_collaboratore_id:
                    partner = record.get_partner_information()
                    if not partner:
                        record.payment_responsibility = record._origin.payment_responsibility
                        continue
                    record.partner_collaboratore_id = partner
                partner_id = record.partner_collaboratore_id
            else:
                if not record.partner_cliente_id:
                    partner = record.get_partner_information(is_idvita=False)
                    if not partner:
                        record.payment_responsibility = record._origin.payment_responsibility
                        continue
                    record.partner_cliente_id = partner
                partner_id = record.partner_cliente_id

            record.move_id.line_ids.write({"partner_id": partner_id.id})

    @api.model
    def get_partner_information(self, is_idvita=True):
        record_id = self.idvita if is_idvita else self.idrca
        endpoint = "api_vita_idvita" if is_idvita else "api_rca_idrca"
        if not record_id:
            raise UserError(_("Not found partner for this responsibility"))

        try:
            policy_data = KoalaApiController(self.env)._get_itconfiguration(
                endpoint_key=endpoint, record_id=record_id,
            )
            person_id = policy_data.get("idgestore") if is_idvita else policy_data.get("idcliente")

            # API throw 401 unauthorized error: 401 Unauthorized error.
            client_data = KoalaApiController(self.env)._get_itconfiguration(
                endpoint_key='api_client', record_id=person_id,
            )

        except Exception as e:
            _logger.exception("Error processing title %s: %s", self.koala_titolo_id, e)
            return None

        return  self.upsert_partner(
            name=f"{client_data.get('nome', '')} {client_data.get('cognome', '')}".strip(),
            koala_id=person_id,
        )

    @api.model
    def upsert_partner(self, name, koala_id=None):
        """Get or create res.partner with optional Koala ID and payment responsibility"""
        partner = (
            self.env["res.partner"].search([("koala_id", "=", koala_id)], limit=1)
            if koala_id else None
        )
        if not partner:
            partner = self.env["res.partner"].create(
                {
                    "name": name,
                    "koala_id": koala_id,
                }
            )
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
            koala_titolo_id = koala_titolo.get("id")
            try:
                # 1) Title details
                title_detail = KoalaApiController(self.env)._get_itconfiguration(
                    endpoint_key="api_titoli_id", record_id=koala_titolo_id
                )
                if not title_detail:
                    raise UserError(_(f"Title {koala_titolo_id} not found in Koala API"))
                if title_detail.get("dataInserimento") and title_detail.get("dataInserimento") <= two_months_ago:
                    continue

                # 2) Policy details
                idrca = title_detail.get("idrca")
                idvita = title_detail.get("idvita")
                is_collaborator = False

                if idrca:
                    policy_data = KoalaApiController(self.env)._get_itconfiguration(
                        endpoint_key="api_rca_idrca", record_id=idrca
                    )
                elif idvita:
                    policy_data = KoalaApiController(self.env)._get_itconfiguration(
                        endpoint_key="api_vita_idvita", record_id=idvita
                    )
                    is_collaborator = True
                else:
                    raise UserError(_(f"Title {koala_titolo_id} has no policy reference"))

                if not policy_data:
                    _logger.warning("Skipping title %s due to missing policy data", koala_titolo_id)
                    continue

                # Fetch the person data depending on collaborator vs client
                person_id = policy_data.get('idgestore') if is_collaborator else policy_data.get('idcliente')

                client_data = {}
                # API throw 401 unauthorized error: 401 Unauthorized error.
                if person_id:
                    client_data = KoalaApiController(self.env)._get_itconfiguration(endpoint_key='api_client', record_id=person_id)

                # Merge person details (name parts etc.) into policy_data for convenience
                if client_data:
                    policy_data = {**policy_data, **client_data}

            except Exception as e:
                _logger.exception("Error processing title %s: %s", koala_titolo_id, e)
                continue

            # 3) Prepare titolo values and partners
            rb_vals = self.prepare_values(koala_titolo | title_detail)
            full_name = f"{policy_data.get('nome', '')} {policy_data.get('cognome', '')}".strip()

            if is_collaborator:
                partner = self.upsert_partner(
                    name=full_name,
                    koala_id=policy_data.get('idgestore'),
                )
                rb_vals["partner_collaboratore_id"] = partner.id
                rb_vals["payment_responsibility"] = "collaborator_pays"
            else:
                partner = self.upsert_partner(
                    name=full_name,
                    koala_id=policy_data.get('idcliente'),
                )
                rb_vals["partner_cliente_id"] = partner.id
                rb_vals["payment_responsibility"] = "customer_pays"

            # 4) Upsert titolo and account move
            rb_record = self.search([("koala_titolo_id", "=", koala_titolo_id)], limit=1)
            move_vals = self.create_account_move(rb_vals, partner, rb_record)
            if rb_record:
                if rb_record.move_id.state != 'draft':
                    continue
                if rb_record.move_id:
                    rb_record.move_id.write(move_vals)
                else:
                    new_move = self.env["account.move"].create(move_vals)
                    rb_vals["move_id"] = new_move.id
                rb_record.write(rb_vals)
                _logger.info("------------> update records :- %s <-------------", rb_record.id)
            else:
                rb_vals["koala_titolo_id"] = koala_titolo_id
                move_record = self.env["account.move"].create(move_vals)
                rb_vals["move_id"] = move_record.id
                create_data.append(rb_vals)

        self.create_koala_titles(create_data)

    @api.model
    def create_koala_titles(self, create_data):
        """Create records for the title"""
        if create_data:
            create_result = self.create(create_data)
            _logger.info(
                "------------> Created %d rb_titolo records <-------------",
                len(create_result),
            )

    @api.model
    def create_account_move(self, rb_vals, partner, rb_record=None):
        """
        Create or update account.move of type 'entry' for the title.
        If rb_record is passed and has a move_id, update the existing move.
        """
        journal = self.env["account.journal"].search(
            [("rb_titolo", "=", True)], limit=1
        )
        if not journal:
            raise UserError(_("Journal 'RB Titles' not found"))

        account = self.env["account.account"].search(
            [("code", "=", "999999")], limit=1
        )
        if not account:
            raise UserError(_("Account with code '999999' not found."))

        move_vals = {
            "move_type": "entry",
            "journal_id": journal.id,
            "date": rb_vals.get("data"),
            "ref": rb_vals.get("numero"),
        }

        # Build line_ids depending on whether we are updating or creating
        line_vals = []

        if rb_record and rb_record.move_id:
            move = rb_record.move_id
            if move.line_ids.filtered(lambda l: l.full_reconcile_id):
                return move_vals
            # Partner line
            partner_line = move.line_ids.filtered(
                lambda l: l.account_id == partner.property_account_receivable_id
            )
            if partner_line:
                line_vals.append(Command.update(partner_line.id, {
                    "debit": rb_vals.get("tot_competenze", 0.0),
                    "name": rb_vals.get("numero"),
                    "partner_id": partner.id,
                }))
            else:
                line_vals.append(Command.create({
                    "account_id": partner.property_account_receivable_id.id,
                    "partner_id": partner.id,
                    "name": rb_vals.get("numero"),
                    "debit": rb_vals.get("tot_competenze", 0.0),
                }))

            # Counterpart line
            counterpart_line = move.line_ids.filtered(lambda l: l.account_id == account)
            if counterpart_line:
                line_vals.append(Command.update(counterpart_line.id, {
                    "credit": rb_vals.get("tot_competenze", 0.0),
                    "name": rb_vals.get("numero"),
                    "partner_id": partner.id,
                }))
            else:
                line_vals.append(Command.create({
                    "account_id": account.id,
                    "partner_id": partner.id,
                    "name": rb_vals.get("numero"),
                    "credit": rb_vals.get("tot_competenze", 0.0),
                }))
        else:
            # Create new lines
            line_vals = [
                Command.create({
                    "account_id": partner.property_account_receivable_id.id,
                    "partner_id": partner.id,
                    "name": rb_vals.get("numero"),
                    "debit": rb_vals.get("tot_competenze", 0.0),
                }),
                Command.create({
                    "account_id": account.id,
                    "partner_id": partner.id,
                    "name": rb_vals.get("numero"),
                    "credit": rb_vals.get("tot_competenze", 0.0),
                }),
            ]

        move_vals["line_ids"] = line_vals
        return move_vals

    @api.model
    def _cron_koala_get_titles(self):
        try:
            records = KoalaApiController(self.env)._get_itconfiguration(endpoint_key="api_titoli")
            if records:
                self.process_title(records)
        except Exception as e:
            _logger.warning("Failed to fetch Koala titles: %s", e)

    def prepare_values(self, vals):
        return {
            "numero": vals.get("numero"),
            "cliente": vals.get("cliente"),
            "fornitore": vals.get("fornitore"),
            "tipo": vals.get("tipo"),
            "compagnia": vals.get("compagnia"),
            "data": self._parse_datetime(vals.get("data")),
            "operazione": vals.get("stato") or vals.get("operazione"),
            "data_inizio": vals.get("dataInizio"),
            "data_fine": vals.get("dataFine"),
            "frazionamento": vals.get("frazionamento"),
            "premio": vals.get("premio"),
            "premio_lordo": vals.get("premioLordo"),
            "premio_totale": vals.get("premioTotale"),
            "competenze": vals.get("competenze"),
            "tot_competenze": vals.get("totCompetenze"),
            "saldato": vals.get("saldato", False),
            "versato": vals.get("versato", False),
            "idquietanza": vals.get("idquietanza"),
            "imponibile": vals.get("imponibile"),
            "importo_agenzia": vals.get("importoAgenzia"),
            "importo_gestore": vals.get("importoGestore"),
            "perc_agenzia": vals.get("percAgenzia"),
            "perc_gestore": vals.get("percGestore"),
            "perc_gestore_competenze": vals.get("percGestoreCompetenze"),
            "importo_gestore_competenze": vals.get("importoGestoreCompetenze"),
            "autentica_comp": vals.get("autenticaComp"),
            "motivazione": vals.get("motivazione"),
            "quota_associativa": vals.get("quotaAssociativa"),
            "tipo_pagamento_coll": vals.get("tipoPagamentoColl"),
            "anticipato_collaboratore": vals.get("anticipatoCollaboratore", False),
            "note": vals.get("note"),
            "imposte": vals.get("imposte"),
            "ssn": vals.get("ssn"),
            "diritti_emissione": vals.get("dirittiEmissione"),
            "nascondi_foglio_cassa": vals.get("nascondiFoglioCassa", False),
            "usa_castelletto": vals.get("usaCastelletto", False),
            "idrca": vals.get("idrca"),
            "idvita": vals.get("idvita"),
            "simpli": vals.get("simpli"),
            "data_inserimento": self._parse_datetime(vals.get("dataInserimento")),
            "ultimo_incasso_nome": vals.get("ultimoIncassoNome"),
            "ultimo_incasso_data": vals.get("ultimoIncassoData"),
            "ultimo_incasso_intestato_compagnia": vals.get(
                "ultimoIncassoIntestatoCompagnia", False
            ),
            "incassato": vals.get("incassato"),
            "saldato_old": vals.get("saldatoOld", False),
            "codice_operazione": vals.get("codiceOperazione"),
            "data_comunicazione": self._parse_datetime(vals.get("dataComunicazione")),
            "prodotto": vals.get("prodotto"),
            "costo_gps": vals.get("costoGps"),
            "prima_emissione": vals.get("primaEmissione", False),
            "rinnovo": vals.get("rinnovo", False),
            "val_ritenuta": vals.get("valRitenuta"),
            "importo_versato": vals.get("importoVersato"),
            "non_usare_garanzie": vals.get("nonUsareGaranzie", False),
            "importo_da_versare": vals.get("importoDaVersare"),
            "non_altera_polizza": vals.get("nonAlteraPolizza", False),
            "tot_credito_provv_fornitore": vals.get("totCreditoProvvFornitore"),
            "ultimo_incasso_conto": vals.get("ultimoIncassoConto"),
            "competenze_surplus": vals.get("competenzeSurplus"),
            "val_ritenuta_fornitore": vals.get("valRitenutaFornitore"),
        }

    def action_update_title(self):
        """Update record on button click"""
        for record in self:
            if record.koala_titolo_id:
                koala_titolo = [{"id": record.koala_titolo_id}]
                self.process_title(koala_titolo)

    def _parse_datetime(self, value):
        """Update datetime format"""
        try:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S") if value else None
        except Exception:
            return None
