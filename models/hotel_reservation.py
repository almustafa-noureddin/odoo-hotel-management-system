from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

class HotelReservation(models.Model):
    _name = 'hotel.reservation'
    _description = 'Hotel Reservation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'check_in desc, id desc'
    _check_company_auto = True

    name = fields.Char(string="Reference", copy=False, readonly=True, default="/", tracking=True)
    guest_id = fields.Many2one(
        string='Guest ID',
        comodel_name='res.partner',
        required=True, 
        ondelete='restrict', 
        tracking=True
        )
    room_id = fields.Many2one(
        string="Room ID",
        comodel_name='hotel.room',
        required=True, 
        ondelete='restrict', 
        tracking=True
        )
    company_id = fields.Many2one(
        string="Branch",
        related='room_id.company_id',
        store=True,
        readonly=True
    )
    

    check_in = fields.Datetime(string="Check In",required=True, index=True, tracking=True)
    check_out = fields.Datetime(string="Check Out",required=True, index=True, tracking=True)

    booking_source = fields.Selection(
        string='Booking Source',
        selection=[('website', 'Website'),
         ('ota', 'OTA'),
         ('phone', 'Phone'),
         ('walk_in', 'Walk-in'),
         ('travel_agent', 'Travel Agent')],
        default='website',
        required=True,
        index=True, 
        tracking=True
    )
    rate_type = fields.Selection(
        string='Rate Type',
        selection=[('standard', 'Standard'),
         ('seasonal', 'Seasonal'),
         ('corporate', 'Corporate')],
        default='standard',
        required=True,
        index=True, 
        tracking=True
    )

    deposit_amount = fields.Monetary(string='Deposit Amount', currency_field='currency_id', tracking=True)
    total_amount = fields.Monetary(string='Amount Per Night', currency_field='currency_id', tracking=True)
    payment_status = fields.Selection(
        string='Payment Status',
        selection=[('unpaid', 'Unpaid'),
         ('partial', 'Partial'),
         ('paid', 'Paid')],
        default='unpaid',
        required=True,
        index=True, 
        tracking=True
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
        index=True, 
        tracking=True
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

class HotelReservation(models.Model):
    _inherit = 'hotel.reservation'

    invoice_count = fields.Integer(compute='_compute_invoice_count', string='Invoice Count')

    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = self.env['account.move'].sudo().search_count([
                ('hotel_reservation_id', '=', rec.id),
                ('move_type', 'in', ['out_invoice', 'out_refund']),
            ])

    def action_view_invoices(self):
        self.ensure_one()
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        action['domain'] = [('hotel_reservation_id', '=', self.id)]
        action['context'] = {
            'default_move_type': 'out_invoice',
            'default_partner_id': self.guest_id.id,
            'default_hotel_reservation_id': self.id,
            'search_default_unpaid': 1,
        }
        return action

    def _get_sale_journal(self):
        self.ensure_one()
        journal = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', self.company_id.id),
            ('active', '=', True),
        ], limit=1)
        if not journal:
            raise UserError("No Sales Journal found for company %s." % self.company_id.display_name)
        return journal

    def _reservation_invoice_lines(self):
        """Builds invoice_line_ids triples for the reservation."""
        self.ensure_one()
        # Decide the price source. Prefer reservation.total_amount if set, else room.price.
        unit_price = self.total_amount or self.room_id.price or 0.0
        quantity = 1.0
        # nights, compute from check-in/out
        if self.check_in and self.check_out:
            nights = max(1.0, (fields.Datetime.to_datetime(self.check_out) - fields.Datetime.to_datetime(self.check_in)).days or 1.0)
            quantity = nights

        # Try to pick a product. If you have a "Room Night" product, set its external ID and use it.
        product = self.env['product.product'].search([('default_code', '=', 'ROOM_NIGHT')], limit=1) 

        # Map taxes through fiscal position
        partner = self.guest_id
        taxes = product.taxes_id if product else self.env['account.tax']
        taxes = taxes.filtered(lambda t: t.company_id == self.company_id)
        if partner.property_account_position_id and taxes:
            taxes = partner.property_account_position_id.map_tax(taxes)

        line_vals = {
            'name': product.display_name if product else (self.room_id.display_name or 'Room Charge'),
            'quantity': quantity,
            'price_unit': unit_price,
            'product_id': product.id if product else False,
            'tax_ids': [(6, 0, taxes.ids)] if taxes else False,
        }
        return [(0, 0, line_vals)]

    def action_create_invoice(self):
        self.ensure_one()
        if not self.guest_id:
            raise UserError("Reservation must have a Guest (Customer) before invoicing.")
        if self.payment_status == 'paid':
            raise UserError("This reservation is already marked Paid.")

        journal = self._get_sale_journal()
        move_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.guest_id.id,
            'invoice_date': fields.Date.context_today(self),
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.guest_id.property_payment_term_id.id or False,
            'journal_id': journal.id,
            'currency_id': self.currency_id.id,
            'invoice_line_ids': self._reservation_invoice_lines(),
            'hotel_reservation_id': self.id,  # <-- this links it back to O2M
            'invoice_user_id': self.env.user.id,
            'company_id': self.company_id.id,
        }
        move = self.env['account.move'].create(move_vals)

        # Post the invoice 
        move.action_post()

        return {
            'name': 'Customer Invoice',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': move.id,
            'target': 'current',
        }
