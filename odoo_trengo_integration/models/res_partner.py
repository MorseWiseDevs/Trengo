from odoo import fields, models, api


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

    def action_open_trengo_tickets(self):
        return {
            "name": "Trengo Tickets",
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "res_model": "trengo.ticket",
            "domain": [('id', 'in', self.trengo_ticket_ids.ids)],
        }
