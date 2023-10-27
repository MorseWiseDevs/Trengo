import requests
from odoo.exceptions import UserError
from odoo.http import request

from odoo import http, _


class AccountContactAPI(http.Controller):

    @http.route("/inbound/message", type="http", auth="user", methods=["POST"], csrf=False)
    def inbound_message(self, **data):

        ticket_object = request.env['trengo.ticket']
        profile_obj = request.env['res.partner']

        # check if ticket exists
        ticket_id = ticket_object.sudo().search([('trengo_id', '=', int(data['ticket_id']))], limit=1)
        if ticket_id:
            # log note on existing ticket
            ticket_id.with_user(1).message_post(body=str(data['contact_name']) + ": " + str(data['message']))
        else:
            url = request.env["ir.config_parameter"].sudo().get_param("account_contact_api.trengo_api_url")
            api_key = request.env["ir.config_parameter"].sudo().get_param("account_contact_api.trengo_api_key")

            if not (url and api_key):
                raise UserError(_("Trengo API url or API key missing from system parameters"))

            endpoint = f"{url}/contacts/{data['contact_id']}"

            trengo_contact = requests.get(endpoint, headers={"Authorization": f"Bearer {api_key}"})

            trengo_profile_id = trengo_contact.json().get('profile', [[{}]])[0].get('id', False)

            # get contact
            domain = []
            if data.get('contact_identifier'):
                domain = ['|', '|', ('phone', '=', data['contact_identifier']),
                          ('mobile', '=', data['contact_identifier']), ('trengo_id', '=', trengo_profile_id)]
            elif data.get('contact_email'):
                domain = ['|', ('email', '=', data['contact_email']), ('trengo_id', '=', trengo_profile_id)]
            profile_id = profile_obj.sudo().search(
                domain, limit=1)

            if not profile_id:
                # create profile
                profile_id = profile_obj.with_user(1).sudo().create({
                    'name': data.get('contact_name', False),
                    'trengo_id': trengo_profile_id,
                    'phone': data.get('contact_identifier', False),
                    'mobile': data.get('contact_identifier', False)
                })
            else:
                if phone := data.get('contact_identifier'):
                    profile_id.write({
                        'phone': phone,
                        'mobile': phone
                    })
                if email := data.get('contact_email'):
                    profile_id.write({
                        'email': email
                    })

            # create ticket and log note
            ticket_id = ticket_object.sudo().with_user(1).create({
                'trengo_id': data.get('ticket_id', False),
                'contact_id': profile_id.id
            })
            ticket_id.with_user(1).message_post(body=str(data['contact_name']) + ": " + str(data['message']))

    @http.route("/outbound/message", type="http", auth="none", methods=["POST"], csrf=False)
    def outbound_message(self, **data):
        ticket_object = request.env['trengo.ticket']
        profile_obj = request.env['res.partner']

        # check if ticket exists
        ticket_id = ticket_object.sudo().search([('trengo_id', '=', int(data['ticket_id']))], limit=1)
        if ticket_id:
            # log note on existing ticket
            ticket_id.with_user(1).message_post(body=str(data['user_name']) + ": " + str(data['message']))
        else:

            url = request.env["ir.config_parameter"].sudo().get_param("account_contact_api.trengo_api_url")
            api_key = request.env["ir.config_parameter"].sudo().get_param("account_contact_api.trengo_api_key")

            if not (url and api_key):
                raise UserError(_("Trengo API url or API key missing from system parameters"))

            endpoint = f"{url}/contacts/{data['contact_id']}"

            trengo_contact = requests.get(endpoint, headers={"Authorization": f"Bearer {api_key}"})

            trengo_profile_id = trengo_contact.json().get('profile', [[{}]])[0].get('id', False)

            # get contact
            if data.get('contact_identifier') and data.get('contact_email'):
                domain = ['|', '|', '|', ('phone', '=', data['contact_identifier']),
                          ('mobile', '=', data['contact_identifier']),
                          ('email', '=', data['contact_email']), ('trengo_id', '=', trengo_profile_id)]
            elif data.get('contact_identifier'):
                domain = ['|', '|', ('phone', '=', data['contact_identifier']),
                          ('mobile', '=', data['contact_identifier']), ('trengo_id', '=', trengo_profile_id)]
            elif data.get('contact_email'):
                domain = ['|', ('email', '=', data['contact_email']), ('trengo_id', '=', trengo_profile_id)]
            profile_id = profile_obj.sudo().search(
                domain, limit=1)

            if not profile_id:
                # create profile
                profile_id = profile_obj.sudo().with_user(1).create({
                    'trengo_id': trengo_profile_id,
                    'name': data.get('contact_name', False),
                    'phone': data.get('contact_identifier', False),
                    'mobile': data.get('contact_identifier', False),
                    'email': data.get('contact_email', False)
                })
            else:
                if phone := data.get('contact_identifier'):
                    profile_id.write({
                        'phone': phone,
                        'mobile': phone
                    })
                if email := data.get('contact_email'):
                    profile_id.write({
                        'email': email
                    })

            # create ticket and log note
            ticket_id = ticket_object.sudo().with_user(1).create({
                'trengo_id': ['ticket_id'],
                'contact_id': profile_id.id
            })
            ticket_id.with_user(1).message_post(body=str(data['user_name']) + ": " + str(data['message']))

    @http.route("/note/added", type="http", auth="none", methods=["POST"], csrf=False)
    def note_added(self, **data):
        ticket_object = request.env['trengo.ticket']
        ticket_id = ticket_object.sudo().search([('trengo_id', '=', int(data['ticket_id']))], limit=1)
        if ticket_id:
            ticket_id.with_user(1).message_post(body=f"[INTERNAL NOTE] {data['user_name']}: {data['message']} ")

    @http.route("/label/added", type="http", auth="none", methods=["POST"], csrf=False)
    def label_added(self, **data):
        ticket_object = request.env['trengo.ticket']
        label_obj = request.env['trengo.label']

        label_id = label_obj.sudo().search([('trengo_id', '=', data['label_id'])], limit=1)
        if not label_id:
            label_id = label_obj.sudo().with_user(1).create({
                'trengo_id': data['label_id'],
                'name': data['label_name']
            })
        # check if ticket exists
        ticket_id = ticket_object.sudo().search([('trengo_id', '=', int(data['ticket_id']))], limit=1)
        if ticket_id:
            # added label to ticket
            ticket_id.label_ids |= label_id

    @http.route("/label/removed", type="http", auth="none", methods=["POST"], csrf=False)
    def label_removed(self, **data):
        ticket_object = request.env['trengo.ticket']
        label_obj = request.env['trengo.label']

        label_id = label_obj.sudo().search([('trengo_id', '=', data['label_id'])], limit=1)
        ticket_id = ticket_object.sudo().search([('trengo_id', '=', int(data['ticket_id']))], limit=1)
        if ticket_id and label_id:
            ticket_id.label_ids = [(3, label_id.id, 0)]

    @http.route("/ticket/assigned", type="http", auth="none", methods=["POST"], csrf=False)
    def ticket_assigned(self, **data):
        ticket_object = request.env['trengo.ticket']
        ticket_id = ticket_object.sudo().search([('trengo_id', '=', int(data['ticket_id']))], limit=1)
        if ticket_id and ticket_id.state != 'assigned':
            ticket_id.state = 'assigned'
            if data['assigned_to'] == 'TEAM':
                ticket_id.with_user(1).message_post(body=str("Ticket assigned to " + str(data['team_name'])))
            else:
                ticket_id.with_user(1).message_post(body=str("Ticket assigned to " + str(data['user_name'])))

    @http.route("/ticket/closed", type="http", auth="none", methods=["POST"], csrf=False)
    def ticket_closed(self, **data):
        ticket_object = request.env['trengo.ticket']
        ticket_id = ticket_object.sudo().search([('trengo_id', '=', int(data['ticket_id']))], limit=1)
        if ticket_id:
            ticket_id.state = 'closed'

    @http.route("/ticket/reopened", type="http", auth="none", methods=["POST"], csrf=False)
    def ticket_reopened(self, **data):
        ticket_object = request.env['trengo.ticket']
        ticket_id = ticket_object.sudo().search([('trengo_id', '=', int(data['ticket_id']))], limit=1)
        if ticket_id:
            ticket_id.state = 'assigned' if data['status'] == 'ASSIGNED' else 'open'

    @http.route("/spam/added", type="http", auth="none", methods=["POST"], csrf=False)
    def spam_added(self, **data):
        ticket_object = request.env['trengo.ticket']
        ticket_id = ticket_object.sudo().search([('trengo_id', '=', int(data['ticket_id']))], limit=1)
        if ticket_id:
            ticket_id.is_spam = True

    @http.route("/spam/removed", type="http", auth="none", methods=["POST"], csrf=False)
    def spam_removed(self, **data):
        ticket_object = request.env['trengo.ticket']
        ticket_id = ticket_object.sudo().search([('trengo_id', '=', int(data['ticket_id']))], limit=1)
        if ticket_id:
            ticket_id.is_spam = False
