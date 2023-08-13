from random import randint

import requests
from odoo.exceptions import UserError

from odoo import fields, models, _


class TrengoLabel(models.Model):
    _name = 'trengo.label'
    _description = "Trengo Label"

    trengo_id = fields.Char(string="Trengo ID", readonly=True)
    name = fields.Char()
    object_to_create = fields.Many2one('ir.model')
    color = fields.Integer(
        string='Color Index', default=lambda self: randint(1, 11),
        help="Tag color used in both backend and website. No color means no display in kanban or front-end, to distinguish internal tags from public categorization tags")

    def fetch_and_create_labels_from_trengo(self):
        url = self.env["ir.config_parameter"].sudo().get_param("account_contact_api.trengo_api_url")
        api_key = self.env["ir.config_parameter"].sudo().get_param("account_contact_api.trengo_api_key")

        if not (url and api_key):
            raise UserError(_("Trengo API url or API key missing from system parameters"))

        endpoint = f"{url}/labels"

        trengo_labels = requests.get(endpoint, headers={"Authorization": f"Bearer {api_key}"})

        for label in trengo_labels.json()['data']:
            existing_label = self.search([('trengo_id', '=', label['id'])], limit=1)
            if not existing_label:
                self.create({
                    'trengo_id': str(label['id']),
                    'name': str(label['slug']),
                })
            else:
                existing_label.write({
                    'name': str(label['slug']),
                })
