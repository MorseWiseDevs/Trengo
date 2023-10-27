from random import randint

from odoo import fields, models


class TrengoLabel(models.Model):
    _name = 'trengo.label'
    _description = "Trengo Label"

    trengo_id = fields.Char(string="Trengo ID", readonly=True)
    name = fields.Char()
    object_to_create = fields.Many2one('ir.model')
    color = fields.Integer(
        string='Color Index', default=lambda self: randint(1, 11),
        help="Tag color used in both backend and website. No color means no display in kanban or front-end, to distinguish internal tags from public categorization tags")
