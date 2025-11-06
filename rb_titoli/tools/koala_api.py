import logging
import requests

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
TIMEOUT = 20
ENDPOINT = {
    "testing": {
        "api_titoli": "https://ext.softwarebroker.it/api/Titoli?stati=Coperta&stati=Stornata&stati=Franchigia&stati=Giacenza&stati=Sospesa",
        "api_titoli_id": "https://ext.softwarebroker.it/api/Titoli",
        "api_rca_idrca": "https://ext.softwarebroker.it/api/Polizze/Rca",
        "api_vita_idvita": "https://ext.softwarebroker.it/api/Polizze/Vita",
        "api_client": "https://ext.softwarebroker.it/api/Clienti",
        "api_incassi": "https://ext.softwarebroker.it/api/Incassi",
        "api_incassi_id": "https://ext.softwarebroker.it/api/Incassi",
        "api_gestori_id": "https://ext.softwarebroker.it/api/Gestori",
    },
    "production": {
        "api_titoli": "https://ext.softwarebroker.it/api/Titoli?stati=Coperta&stati=Stornata&stati=Franchigia&stati=Giacenza&stati=Sospesa",
        "api_titoli_id": "https://ext.softwarebroker.it/api/Titoli",
        "api_rca_idrca": "https://ext.softwarebroker.it/api/Polizze/Rca",
        "api_vita_idvita": "https://ext.softwarebroker.it/api/Polizze/Vita",
        "api_client": "https://ext.softwarebroker.it/api/Clienti",
        "api_incassi": "https://ext.softwarebroker.it/api/Incassi",
        "api_incassi_id": "https://ext.softwarebroker.it/api/Incassi",
        "api_gestori_id": "https://ext.softwarebroker.it/api/Gestori",
    },
}

class KoalaApiController:
    def __init__(self, env):
        self.env = env

    def _get_api_key(self):
        """Fetch API key from system parameters"""
        api_key = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("rb_titoli.koala_broker_api_key")
        )
        if not api_key:
            _logger.warning("API Key not found in system configuration.")
        return api_key

    def _get_mode(self):
        mode = (
            self.env["ir.config_parameter"].sudo().get_param("rb_titoli.mode")
            or "testing"
        )
        if mode not in ENDPOINT:
            raise UserError(f"Invalid mode '{mode}' configured.")
        return mode

    def _get_headers(self, content_type="text/plain"):
        api_key = self._get_api_key()
        if not api_key:
            raise UserError("Missing API Key configuration.")
        headers = {"accept": "text/plain", "X-Api-Key": api_key}
        if content_type == "application/json":
            headers["Content-Type"] = "application/json"
        return headers

    """ GET method: call from anywhere by endpoint key """

    def _get_itconfiguration(self, endpoint_key, record_id=None, params=None):
        """
        Generic GET request to Koala API
        :param endpoint_key: key from ENDPOINT dict (e.g. 'api_titoli')
        :param record_id: optional ID to fetch a specific record
        :param params: optional query parameters as dict
        :return: response data (JSON or text)
        """

        mode = self._get_mode()
        url = ENDPOINT[mode].get(endpoint_key)
        if not url:
            raise UserError(f"Endpoint '{endpoint_key}' not defined for mode '{mode}'.")

        if record_id:
            url = f"{url}/{record_id}"

        headers = self._get_headers()

        try:
            response = requests.get(
                url, headers=headers, params=params, timeout=TIMEOUT
            )
            response.raise_for_status()

            try:
                return response.json()
            except ValueError:
                return response.text

        except requests.RequestException as e:
            _logger.error("GET request failed for %s: %s", url, e)
            raise UserError(f"GET request failed: {str(e)}")

    """ POST method: call from anywhere by endpoint key """

    def _post_itconfiguration(self, endpoint_key, payload=None, record_id=None):
        """
        Generic POST request to Koala API
        :param endpoint_key: key from ENDPOINT dict (e.g. 'api_titoli')
        :param payload: dict to send in body
        :param record_id: optional ID to append to the endpoint
        :return: response data (JSON or text)
        """
        mode = self._get_mode()
        url = ENDPOINT[mode].get(endpoint_key)
        if not url:
            raise UserError(f"Endpoint '{endpoint_key}' not defined for mode '{mode}'.")

        if record_id:
            url = f"{url}/{record_id}"

        headers = self._get_headers(content_type="application/json")

        try:
            response = requests.post(
                url, headers=headers, json=payload or {}, timeout=TIMEOUT
            )
            response.raise_for_status()

            try:
                return response.json()
            except ValueError:
                return response.text

        except requests.RequestException as e:
            _logger.error("POST request failed for %s: %s", url, e)
            raise UserError(f"POST request failed: {str(e)}")

    def _delete_itconfiguration(self, endpoint_key, record_id):
        """
        Generic DELETE request to Koala API
        :param endpoint_key: key from ENDPOINT dict (e.g. 'api_titoli')
        :param record_id: ID of the record to delete
        :return: dict with response data and HTTP status
        """
        mode = self._get_mode()
        url = ENDPOINT[mode].get(endpoint_key)
        if not url:
            raise UserError(f"Endpoint '{endpoint_key}' not defined for mode '{mode}'.")

        full_url = f"{url}/{record_id}"
        headers = self._get_headers()

        try:
            response = requests.delete(full_url, headers=headers, timeout=TIMEOUT)
            response.raise_for_status()

            try:
                response_data = response.json()
            except ValueError:
                response_data = {"message": f"Record {record_id} deleted successfully."}

            return {"data": response_data, "status": response.status_code}

        except requests.exceptions.RequestException as e:
            try:
                error_data = e.response.json()
                error_message = error_data.get("message", str(e))
            except Exception:
                error_message = str(e)

            _logger.error("DELETE request failed for %s: %s", full_url, error_message)
            raise UserError(f"DELETE request failed: {error_message}")
