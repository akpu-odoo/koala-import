from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    mode = fields.Selection(
        [("production", "Production"), ("testing", "Testing")], string="Mode"
    )
    koala_broker_api_key = fields.Char(
        string="API key:", help="API Key for Koala Broker", store=True
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        param = self.env["ir.config_parameter"].sudo()
        res.update(
            {
                "mode": param.get_param("rb_titoli.mode", default="testing"),
                "koala_broker_api_key": param.get_param(
                    "rb_titoli.koala_broker_api_key", default=""
                ),
            }
        )
        return res

    def set_values(self):
        super().set_values()
        param = self.env["ir.config_parameter"].sudo()
        param.set_param("rb_titoli.mode", self.mode or "")
        param.set_param(
            "rb_titoli.koala_broker_api_key", self.koala_broker_api_key or ""
        )
