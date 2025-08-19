from odoo import models, fields

class ResBranch(models.Model):
    _name = 'res.branch'
    _description = 'Hotel Branch'
    _order = 'name'

    name = fields.Char(string="Branch name",required=True, index=True)
    location = fields.Char(string="Physical address or city")
    #google_maps_link = fields.Char(string="Google Maps URL")
    manager_id = fields.Many2one(
        string="Branch Manager",
        comodel_name='res.users'
        )
    active = fields.Boolean(string="Is The Branch Active",default=True)
    
