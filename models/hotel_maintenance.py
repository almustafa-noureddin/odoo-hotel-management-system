from odoo import models, fields, api
from datetime import timedelta

class HotelMaintenanceTask(models.Model):
    _name = 'hotel.maintenance.task'
    _description = 'Room Maintenance Task'
    _order = 'priority desc, date_scheduled asc, id desc'

    name = fields.Char(string='Title', required=True, default='Maintenance Task')
    room_id = fields.Many2one('hotel.room', string='Room', required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Branch', related='room_id.company_id', store=True, readonly=True)
    task_type = fields.Selection([
        ('inspection', 'Inspection'),
        ('repair', 'Repair'),
    ], string='Type', required=True, default='inspection')
    source = fields.Selection([
        ('inspection', 'Scheduled Inspection'),
        ('housekeeping', 'Housekeeping Report'),
        ('manual', 'Manual'),
    ], string='Source', required=True, default='manual')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='pending', tracking=True)
    date_reported = fields.Datetime(string='Reported On', default=fields.Datetime.now)
    date_scheduled = fields.Datetime(string='Scheduled For')
    duration_hours = fields.Float(string='Expected Duration (hours)', default=1.0)
    assigned_user_id = fields.Many2one('res.users', string='Assigned To')
    priority = fields.Selection([('0','Low'),('1','Normal'),('2','High'),('3','Urgent')], default='1')
    description = fields.Text()
    housekeeping_task_id = fields.Many2one('hotel.housekeeping.task', string='From Housekeeping Task', ondelete='set null')

    def name_get(self):
        res = []
        for rec in self:
            base = rec.name or 'Maintenance'
            label = f"{base} - {rec.room_id.display_name}" if rec.room_id else base
            res.append((rec.id, label))
        return res

    # Room status sync for maintenance lifecycle
    def write(self, vals):
        res = super().write(vals)
        if 'status' in vals:
            for t in self:
                room = t.room_id.sudo()
                if not room:
                    continue
                if vals['status'] == 'in_progress':
                    room.write({'status': 'maintenance'})
                elif vals['status'] == 'done':
                    HK = self.env['hotel.housekeeping.task'].sudo()
                    has_open_hk = HK.search_count([('room_id','=',room.id), ('status','in',['pending','in_progress'])]) > 0
                    if not has_open_hk and room.status == 'maintenance':
                        room.write({'status': 'available'})
        return res

    # Cron: periodic inspections every 30 days
    @api.model
    def cron_generate_periodic_inspections(self, days=30):
        Room = self.env['hotel.room'].sudo()
        Task = self.sudo()
        now = fields.Datetime.now()
        cutoff = now - timedelta(days=days)
        rooms = Room.search([])
        for room in rooms:
            has_open = Task.search_count([
                ('room_id','=',room.id),
                ('task_type','=','inspection'),
                ('status','in',['pending','in_progress'])
            ]) > 0
            if has_open:
                continue
            last = Task.search([('room_id','=',room.id), ('task_type','=','inspection')],
                               order='date_scheduled desc, date_reported desc', limit=1)
            last_when = (last.date_scheduled or last.date_reported) if last else None
            if not last_when or last_when <= cutoff:
                Task.create({
                    'name': 'Periodic Inspection',
                    'room_id': room.id,
                    'task_type': 'inspection',
                    'source': 'inspection',
                    'status': 'pending',
                    'date_scheduled': now + timedelta(days=1),
                    'duration_hours': 1.0,
                })
