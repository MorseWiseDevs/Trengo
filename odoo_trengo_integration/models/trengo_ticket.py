import requests
from odoo.exceptions import UserError

from odoo import fields, models, api, _


class TrengoTicket(models.Model):
    _name = 'trengo.ticket'
    _description = "Trengo Ticket"
    _inherit = 'mail.thread'

    name = fields.Char(compute='_compute_name', store=True)
    trengo_id = fields.Char(string="Trengo ID", readonly=True)
    state = fields.Selection([('open', 'Open'), ('assigned', 'Assigned'), ('closed', 'Closed')], default='open',
                             tracking=True)
    label_ids = fields.Many2many('trengo.label', string="Labels")
    contact_id = fields.Many2one('res.partner')
    helpdesk_ticket_id = fields.Many2one('helpdesk.ticket')
    repair_ticket_id = fields.Many2one('repair.order')
    lead_id = fields.Many2one('crm.lead')
    is_create_lead_button_visible = fields.Boolean(compute='_compute_buttons_visiblity', store=True)
    is_helpdesk_button_visible = fields.Boolean(compute='_compute_buttons_visiblity', store=True)
    is_repair_button_visible = fields.Boolean(compute='_compute_buttons_visiblity', store=True)
    is_spam = fields.Boolean(tracking=True, string="Spam")

    @api.depends('contact_id.name', 'trengo_id')
    def _compute_name(self):
        for rec in self:
            if rec.contact_id.name and rec.trengo_id:
                rec.name = rec.contact_id.name + " - Ticket #" + rec.trengo_id
            else:
                rec.name = 'New'

    @api.depends('label_ids', 'label_ids.object_to_create')
    def _compute_buttons_visiblity(self):
        for rec in self:
            rec.is_create_lead_button_visible = 'crm.lead' in rec.label_ids.object_to_create.mapped('model')
            rec.is_helpdesk_button_visible = 'helpdesk.ticket' in rec.label_ids.object_to_create.mapped('model')
            rec.is_repair_button_visible = 'repair.order' in rec.label_ids.object_to_create.mapped('model')

    # add other fields as necessary

    def fetch_and_create_tickets_from_trengo(self):
        self.env['trengo.label'].fetch_and_create_labels_from_trengo()
        self.env['res.partner'].fetch_and_create_profiles_from_trengo()
        url = self.env["ir.config_parameter"].sudo().get_param("account_contact_api.trengo_api_url")
        api_key = self.env["ir.config_parameter"].sudo().get_param("account_contact_api.trengo_api_key")

        if not (url and api_key):
            raise UserError(_("Trengo API url or API key missing from system parameters"))

        endpoint = f"{url}/tickets?status=CLOSED"

        trengo_tickets = requests.get(endpoint, headers={"Authorization": f"Bearer {api_key}"})

        for ticket in trengo_tickets.json()['data']:
            if ticket['labels']:
                existing_ticket = self.search([('trengo_id', '=', ticket['id'])], limit=1)
                profiles = ticket.get('contact', {}).get('profile', {})
                profile_id = False
                for profile in profiles:
                    profile_id = profile.get('id')
                label_ids = []
                contact_id = False
                if profile_id:
                    contact_id = self.env['res.partner'].search([('trengo_id', '=', profile_id)]).id
                for label in ticket['labels']:
                    label_ids.append(label['id'])
                label_ids = list(set(label_ids))
                if not existing_ticket:
                    self.create({
                        'trengo_id': str(ticket['id']),
                        'label_ids': self.env['trengo.label'].search([('trengo_id', 'in', label_ids)]).ids,
                        'contact_id': contact_id
                    })
                else:
                    existing_ticket.write({
                        'trengo_id': str(ticket['id']),
                        'label_ids': self.env['trengo.label'].search([('trengo_id', 'in', label_ids)]).ids,
                        'contact_id': contact_id
                    })

    def action_create_helpdesk_ticket(self):
        a = self.env['helpdesk.ticket'].create({
            'partner_id': self.contact_id.id,
            'name': self.trengo_id
        })
        self.helpdesk_ticket_id = a

    def action_create_lead(self):
        a = self.env['crm.lead'].create({
            'partner_id': self.contact_id.id,
            'name': self.trengo_id
        })
        self.lead_id = a

    def action_create_repair_order(self):
        a = self.env['repair.order'].create({
            'partner_id': self.contact_id.id,
            'product_id': 1
        })
        self.repair_ticket_id = a

    def action_view_help_desk_ticket(self):
        return {
            "name": "Helpdesk",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "helpdesk.ticket",
            "res_id": self.helpdesk_ticket_id.id,
        }

    def action_view_lead(self):
        return {
            "name": "Lead",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "crm.lead",
            "res_id": self.lead_id.id,
        }

    def action_view_repair_ticket(self):
        return {
            "name": "Repair",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "repair.order",
            "res_id": self.repair_ticket_id.id,
        }
