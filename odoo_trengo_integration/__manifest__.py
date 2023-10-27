{
    "name": "Trengo Plugin",
    'summary': "This app allows you to set up webhooks in Trengo to to receive messages and update tickets in Odoo",
    'description':
        """

        This app allows you to set up webhooks in Trengo to to receive messages and update tickets in Odoo
        
        ENDPOINTS:
        
        /inbound/message : receive inbound message in Odoo
        /outbound/message : receive outbound message in Odoo
        /note/added :receive internal message in Odoo
        /label/added : add ticket label in Odoo
        /label/removed : remove ticket label in Odoo
        /ticket/assigned : move ticket to assigned in Odoo
        /ticket/closed : move ticket to closed in Odoo
        /ticket/reopened : move ticket to assigned/open in Odoo
        /spam/added : mark ticket as spam in Odoo
        /spam/removed : unmark ticket as spam in Odoo
        
        """,
    "depends": ["contacts", 'helpdesk', 'crm', 'repair'],
    "data": [
        'data/parameters.xml',
        'views/trengo_ticket_views.xml',
        'views/trengo_label_views.xml',
        'views/res_partner_views.xml',
        'security/ir.model.access.csv'
    ],
    'application': True,
}
