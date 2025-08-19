# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HotelReservation(models.Model):
    _name = 'hotel.reservation'
    _description = 'Hotel Reservation'
    _order = 'check_in desc, id desc'

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
    branch_id = fields.Many2one(
        string="Branch ID",
        related='room_id.branch_id', 
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

    deposit_amount = fields.Monetary(string='Deposit Amount')
    total_amount = fields.Monetary(string='Total Amount')
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

    # accounting links 
    invoice_ids = fields.One2many('account.move', 'hotel_reservation_id', string='Invoices')

    @api.constrains('check_in', 'check_out')
    def _check_dates(self):
        for rec in self:
            if rec.check_out and rec.check_in and rec.check_out <= rec.check_in:
                raise ValidationError("Check-out must be after check-in.")


# create the reverse FK on account.move
class AccountMove(models.Model):
    _inherit = 'account.move'
    hotel_reservation_id = fields.Many2one('hotel.reservation', ondelete='set null')
