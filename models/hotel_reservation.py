from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HotelReservation(models.Model):
    _name = 'hotel.reservation'
    _description = 'Hotel Reservation'
    _order = 'check_in desc, id desc'
    _check_company_auto = True

    name = fields.Char(string="Reference", copy=False, readonly=True, default="/")
    guest_id = fields.Many2one(
        string='Guest ID',
        comodel_name='res.partner',
        required=True, 
        ondelete='restrict'
        )
    room_id = fields.Many2one(
        string="Room ID",
        comodel_name='hotel.room',
        required=True, 
        ondelete='restrict'
        )
    company_id = fields.Many2one(
        string="Branch",
        related='room_id.company_id',
        store=True,
        readonly=True
    )
    

    check_in = fields.Datetime(string="Check In",required=True, index=True)
    check_out = fields.Datetime(string="Check Out",required=True, index=True)

    booking_source = fields.Selection(
        string='Booking Source',
        selection=[('website', 'Website'),
         ('ota', 'OTA'),
         ('phone', 'Phone'),
         ('walk_in', 'Walk-in'),
         ('travel_agent', 'Travel Agent')],
        default='website',
        required=True,
        index=True
    )
    rate_type = fields.Selection(
        string='Rate Type',
        selection=[('standard', 'Standard'),
         ('seasonal', 'Seasonal'),
         ('corporate', 'Corporate')],
        default='standard',
        required=True,
        index=True
    )

    deposit_amount = fields.Monetary(string='Deposit Amount', currency_field='currency_id')
    total_amount = fields.Monetary(string='Total Amount', currency_field='currency_id')
    payment_status = fields.Selection(
        string='Payment Status',
        selection=[('unpaid', 'Unpaid'),
         ('partial', 'Partial'),
         ('paid', 'Paid')],
        default='unpaid',
        required=True,
        index=True
    )

    status = fields.Selection(
        string='Status',
        selection=[('draft', 'Draft'),
         ('confirmed', 'Confirmed'),
         ('checked_in', 'Checked In'),
         ('checked_out', 'Checked Out'),
         ('cancelled', 'Cancelled')],
        default='draft',
        required=True,
        index=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )


    # accounting links 
    invoice_ids = fields.One2many('account.move', 'hotel_reservation_id', string='Invoices')

    @api.constrains('check_in', 'check_out')
    def _check_dates(self):
        for rec in self:
            if rec.check_out and rec.check_in and rec.check_out <= rec.check_in:
                raise ValidationError("Check-out must be after check-in.")
    
    @api.model
    def create(self, vals):
        rec = super().create(vals)
        if rec.name in (False, "/"):
            rec.name = self.env['ir.sequence'].next_by_code('hotel.reservation') or '/'
        return rec

class HotelReservation(models.Model):
    _inherit = "hotel.reservation"

    def _set_room_status(self, room, status):
        if room and status in ('available', 'occupied'):
            room.status = status

    @api.model
    def create(self, vals):
        rec = super().create(vals)
        # if created already confirmed, mark occupied
        try:
            if rec.status == 'confirmed':
                self._set_room_status(rec.room_id, 'occupied')
        except Exception:
            # don't block creation on a secondary write
            pass
        return rec

    def write(self, vals):
        res = super().write(vals)
        # react only when status changes
        if 'status' in vals:
            for rec in self:
                if vals['status'] == 'confirmed':
                    self._set_room_status(rec.room_id, 'occupied')
                elif vals['status'] in ('cancelled', 'checked_out'):
                    self._set_room_status(rec.room_id, 'available')
        return res

class HotelReservationHousekeeping(models.Model):
    _inherit = 'hotel.reservation'

    def _create_cleaning_task_for_room(self, room, when=None):
        """Ensure exactly one open cleaning task exists for this room at/after checkout."""
        Task = self.env['hotel.housekeeping.task'].sudo()
        when = when or fields.Datetime.now()
        existing = Task.search([
            ('room_id', '=', room.id),
            ('status', 'in', ['pending', 'in_progress']),
            ('date_scheduled', '>=', when),
        ], limit=1)
        if existing:
            return existing
        return Task.create({
            'room_id': room.id,
            'task_type': 'cleaning',
            'status': 'pending',
            'date_scheduled': when,
        })

    def write(self, vals):
        res = super().write(vals)
        # When a reservation is checked out, mark the room dirty and queue housekeeping.
        if 'status' in vals and vals['status'] == 'checked_out':
            for rec in self:
                room = rec.room_id.sudo()
                if not room:
                    continue
                # Set room dirty 
                if room.status != 'cleaning':  # don't override if crew already started
                    room.write({'status': 'dirty'})
                # Create cleaning task scheduled at checkout time (or now)
                rec._create_cleaning_task_for_room(room, rec.check_out or fields.Datetime.now())
        return res

    @api.model
    def cron_generate_housekeeping_tasks(self):
        """Backstop: periodically ensure checked-out rooms have a cleaning task."""
        now = fields.Datetime.now()
        cutoff = now - timedelta(days=2)
        to_process = self.sudo().search([
            ('status', '=', 'checked_out'),
            ('check_out', '>=', cutoff),
            ('room_id', '!=', False),
        ])
        Task = self.env['hotel.housekeeping.task'].sudo()
        for r in to_process:
            room = r.room_id
            if not room:
                continue
            has_open = Task.search([
                ('room_id', '=', room.id),
                ('status', 'in', ['pending', 'in_progress']),
                ('date_scheduled', '>=', r.check_out or cutoff),
            ], limit=1)
            if not has_open:
                Task.create({
                    'room_id': room.id,
                    'task_type': 'cleaning',
                    'status': 'pending',
                    'date_scheduled': r.check_out or now,
                })
                # Keep/mark dirty until housekeeping starts
                if room.status != 'cleaning':
                    room.status = 'dirty'

# create the reverse FK on account.move
class AccountMove(models.Model):
    _inherit = 'account.move'
    hotel_reservation_id = fields.Many2one('hotel.reservation', ondelete='set null')
