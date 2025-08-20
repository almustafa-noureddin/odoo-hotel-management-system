from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    preferences = fields.Text(string="preferences")
    vip_status = fields.Boolean(string="VIP",default=False)
    nationality = fields.Many2one(
        string="Nationality",
        comodel_name= 'res.country'
        )

    



