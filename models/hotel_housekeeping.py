from odoo import models, fields,api
from datetime import timedelta
class HotelHousekeepingTask(models.Model):
    _name = 'hotel.housekeeping.task'
    _description = 'Housekeeping Task'
    _inherit = ['mail.thread', 'mail.activity.mixin'] 
    _order = 'date_scheduled, id'

    room_id = fields.Many2one(
        string='Room ID',
        comodel_name='hotel.room', 
        required=True, 
        ondelete='cascade', 
        tracking=True
        )
    company_id = fields.Many2one(
        'res.company', 
        string='Branch',
        related='room_id.company_id', 
        store=True, 
        readonly=True
    )
    assigned_to = fields.Many2one(
        string='Assigned To',
        comodel_name='res.users', 
        tracking=True
        )
    task_type = fields.Selection(
        string='Task Type',
        selection=[('cleaning', 'Cleaning'),
         ('maintenance', 'Maintenance'),
         ('inspection', 'Inspection')],
        required=True,
        default='cleaning',
        index=True, 
        tracking=True
    )
    status = fields.Selection(
        string='Status',
        selection=[('pending', 'Pending'),
         ('in_progress', 'In Progress'),
         ('done', 'Done')],
        default='pending',
        required=True,
        index=True, 
        tracking=True
    )
    date_scheduled = fields.Datetime(string='Date Scheduled',index=True, tracking=True)
class HotelHousekeepingTaskProgress(models.Model):
    _inherit = 'hotel.housekeeping.task'

    def write(self, vals):
        res = super().write(vals)
        if 'status' in vals:
            for t in self:
                room = t.room_id.sudo()
                if not room:
                    continue
                if vals['status'] == 'in_progress':
                    # Crew is in, mark room as cleaning
                    room.write({'status': 'cleaning'})
                elif vals['status'] == 'done':
                    # All set — flip to available
                    room.write({'status': 'available'})
        return res
