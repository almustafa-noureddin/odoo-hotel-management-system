from odoo import models, fields

class HotelHousekeepingTask(models.Model):
    _name = 'hotel.housekeeping.task'
    _description = 'Housekeeping Task'
    _order = 'date_scheduled, id'

    room_id = fields.Many2one(
        string='Room ID',
        comodel_name='hotel.room', 
        required=True, 
        ondelete='cascade'
        )
    assigned_to = fields.Many2one(
        string='Assigned To',
        comodel_name='res.users', 
        )
    task_type = fields.Selection(
        string='Task Type',
        selection=[('cleaning', 'Cleaning'),
         ('maintenance', 'Maintenance'),
         ('inspection', 'Inspection')],
        required=True,
        default='cleaning',
        index=True
    )
    status = fields.Selection(
        string='Status',
        selection=[('pending', 'Pending'),
         ('in_progress', 'In Progress'),
         ('done', 'Done')],
        default='pending',
        required=True,
        index=True
    )
    date_scheduled = fields.Datetime(index=True)
