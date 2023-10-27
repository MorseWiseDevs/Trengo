from odoo import fields, models, api


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

    def action_create_helpdesk_ticket(self):
        ticket = self.env['helpdesk.ticket'].create({
            'partner_id': self.contact_id.id,
            'name': self.trengo_id
        })
        self.helpdesk_ticket_id = ticket

    def action_create_lead(self):
        lead = self.env['crm.lead'].create({
            'partner_id': self.contact_id.id,
            'name': self.trengo_id
        })
        self.lead_id = lead

    def action_create_repair_order(self):
        order = self.env['repair.order'].create({
            'partner_id': self.contact_id.id,
            'product_id': 1
        })
        self.repair_ticket_id = order

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
