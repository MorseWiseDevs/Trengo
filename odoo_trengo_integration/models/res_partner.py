import requests
from odoo.exceptions import UserError

from odoo import fields, models, _, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    trengo_id = fields.Char(string="Trengo ID", readonly=True)
    instagram_username = fields.Char("Instagram")
    facebook_username = fields.Char("Facebook")
    telegram_username = fields.Char("Telegram")
    twitter_username = fields.Char('Twitter')
    trengo_ticket_ids = fields.One2many('trengo.ticket', 'contact_id')
    trengo_tickets_count = fields.Integer(compute='_compute_trengo_tickets_count', store=True)

    @api.depends('trengo_ticket_ids')
    def _compute_trengo_tickets_count(self):
        for rec in self:
            rec.trengo_tickets_count = len(rec.trengo_ticket_ids)

    def fetch_and_create_profiles_from_trengo(self):
        url = self.env["ir.config_parameter"].sudo().get_param("account_contact_api.trengo_api_url")
        api_key = self.env["ir.config_parameter"].sudo().get_param("account_contact_api.trengo_api_key")

        if not (url and api_key):
            raise UserError(_("Trengo API url or API key missing from system parameters"))

        endpoint = f"{url}/profiles"

        trengo_profiles = requests.get(endpoint, headers={"Authorization": f"Bearer {api_key}"})

        for profile in trengo_profiles.json()['data']:
            phone = False
            email = False
            for contact in profile['contacts']:
                if contact.get('phone'):
                    phone = contact['phone']
                if contact.get('email'):
                    email = contact['email']
            if phone and email:
                domain = ['|', '|', '|', '|', '|', '|', '|', ('trengo_id', '=', profile['id']), ('phone', '=', phone),
                          ('mobile', '=', phone), ('email', '=', email),
                          ('twitter_username', '=', email), ('facebook_username', '=', email),
                          ('telegram_username', '=', email), ('twitter_username', '=', email)]
            elif phone:
                domain = ['|', '|', ('trengo_id', '=', profile['id']), ('phone', '=', phone), ('mobile', '=', phone)]
            elif email:
                domain = ['|', ('trengo_id', '=', profile['id']), ('email', '=', email)]
            else:
                domain = [('trengo_id', '=', profile['id'])]
            partner = self.search(
                domain, limit=1)
            if partner:
                partner.write({
                    'trengo_id': profile['id'],
                    'name': profile['name'],
                    'phone': phone,
                    'mobile': phone,
                    'email': email,
                })
            else:
                self.create({
                    'name': profile['name'],
                    'phone': phone,
                    'mobile': phone,
                    'email': email,
                    'trengo_id': profile['id'],
                })

    def action_open_trengo_tickets(self):
        return {
            "name": "Trengo Tickets",
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "res_model": "trengo.ticket",
            "domain": [('id', 'in', self.trengo_ticket_ids.ids)],
        }
