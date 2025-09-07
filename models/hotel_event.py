from odoo import models, fields, api
from datetime import timedelta
from odoo.exceptions import UserError
class HotelEventAmenity(models.Model):
    _name = 'hotel.event.amenity'
    _description = 'Event Hall Amenity'
    _order = 'name'

    name = fields.Char(required=True, index=True)
    description = fields.Text()

class HotelEventHallType(models.Model):
    _name="hotel.event.hall.type"
    _description="Event / Banquet Hall Type"
    _order="name"

    name=fields.Char(string="Hall Type",required=True, index=True)
    capacity = fields.Integer(string="Capacity")
    price_per_hour = fields.Monetary(string="Price Per Hour", currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency',
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    

class HotelEventHall(models.Model):
    _name = 'hotel.event.hall'
    _description = 'Event / Banquet Hall'
    _order = 'name'
    _check_company_auto = True  

    name = fields.Char(string="Hall Name or Number",required=True, index=True, tracking=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Branch",
        required=True,
        index=True,
        default=lambda self: self.env.company,
        ondelete='restrict',
    )
    
    hall_type_id = fields.Many2one(
        string='Hall Type',
        comodel_name='hotel.event.hall.type',
        required=True,
        ondelete='restrict', 
        tracking=True
    )
    
    capacity = fields.Integer(string="Capacity", tracking=True)
    price_per_hour = fields.Monetary(string="Price Per Hour", currency_field='currency_id', tracking=True)
    amenities_ids = fields.Many2many(
        string="Amenities",
        comodel_name='hotel.event.amenity',
        relation='hotel_event_hall_amenity_rel',
        column1='hall_id', 
        column2='amenity_id',
    )
    currency_id = fields.Many2one(
        'res.currency',
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )

class HotelEventPackage(models.Model):
    _name = 'hotel.event.package'
    _description = 'Event Package'
    _order = 'name'

    name = fields.Char(string="Package Name", required=True, index=True)
    description = fields.Text(string="Description")
    price = fields.Monetary(string="Price", currency_field='currency_id')
    services_ids = fields.Many2many(
        string="Included Services/Items",
        comodel_name='product.product',
        relation='hotel_event_package_service_rel', 
        column1='package_id', 
        column2='product_id',
    )
    currency_id = fields.Many2one(
        'res.currency',
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )

class HotelEventBooking(models.Model):
    _name = 'hotel.event.booking'
    _description = 'Event Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'event_date desc, id desc'

    name = fields.Char(string="Reference", copy=False, readonly=True, default="/", tracking=True)

    hall_id = fields.Many2one(
        string="Hall",
        comodel_name='hotel.event.hall', 
        required=True, 
        ondelete='restrict', 
        tracking=True
        )
    company_id = fields.Many2one(
        string="Branch",
        related='hall_id.company_id',
        store=True,
        readonly=True
    )
    customer_id = fields.Many2one(
        string="Customer",
        comodel_name='res.partner', 
        required=True, 
        ondelete='restrict', 
        tracking=True
        )
    event_date = fields.Datetime(string='Event Date',required=True, index=True, tracking=True)
    duration_hours = fields.Float(string='Event Duration in Hours',required=True, tracking=True)

    package_id = fields.Many2one(
        string="Event Package",
        comodel_name='hotel.event.package', 
        ondelete='set null', 
        tracking=True
        )
    deposit_amount = fields.Monetary(string='Deposit Amount', currency_field='currency_id', tracking=True)
    total_amount = fields.Monetary(string='Total Amount', currency_field='currency_id', tracking=True)

    status = fields.Selection(
        string='Status',
        selection=[('draft', 'Draft'),
         ('confirmed', 'Confirmed'),
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
    @api.model
    def create(self, vals):
        rec = super().create(vals)
        if rec.name in (False, "/"):
            rec.name = self.env['ir.sequence'].next_by_code('hotel.reservation') or '/'
        return rec


class HotelEventBooking(models.Model):
    _inherit = "hotel.event.booking"

    @api.constrains('hall_id', 'event_date', 'duration_hours')
    def _check_overlap(self):
        """Naive time overlap: [start, end) vs others on same hall."""
        for rec in self:
            if not (rec.hall_id and rec.event_date and rec.duration_hours):
                continue
            start = rec.event_date
            end = start + timedelta(hours=rec.duration_hours)

            # quick shortlist: anything that starts before our end on the same hall
            others = self.search([
                ('id', '!=', rec.id),
                ('hall_id', '=', rec.hall_id.id),
                ('event_date', '<', end),
            ])

            for o in others:
                o_end = (o.event_date or start) + timedelta(hours=o.duration_hours or 0)
                # overlap if o.start < end AND start < o.end
                if o.event_date and (o.event_date < end and start < o_end):
                    raise models.ValidationError("Hall is already booked for that time window.")

class HotelEventHall(models.Model):
    _inherit = 'hotel.event.hall'

    @api.onchange('hall_type_id')
    def _onchange_hall_type_id_autofill(self):
        """When a hall type is chosen, prefill capacity & price from the type.
        Staff can still override after this onchange."""
        for rec in self:
            ht = rec.hall_type_id
            if ht:
                # Copy defaults from type
                if hasattr(ht, 'capacity'):
                    rec.capacity = ht.capacity or 0
                if hasattr(ht, 'price_per_hour'):
                    rec.price_per_hour = ht.price_per_hour or 0.0

    @api.model_create_multi
    def create(self, vals_list):
        """Also set defaults on programmatic create (onchange only runs in the UI)."""
        HallType = self.env['hotel.event.hall.type'].sudo()
        for vals in vals_list:
            ht_id = vals.get('hall_type_id')
            if ht_id:
                ht = HallType.browse(ht_id)
                # Only set if creator didn't specify a custom value
                if 'capacity' not in vals and hasattr(ht, 'capacity'):
                    vals['capacity'] = ht.capacity or 0
                # Set price only if not provided
                if ('price_per_hour' not in vals or not vals.get('price_per_hour')) and hasattr(ht, 'price_per_hour'):
                    vals['price_per_hour'] = ht.price_per_hour or 0.0
        return super().create(vals_list)

    def write(self, vals):
        """If the hall type changes later, prefill missing capacity/price from the new type.
        Do not overwrite fields explicitly set in this write."""
        res = super().write(vals)
        if 'hall_type_id' in vals:
            for rec in self:
                ht = rec.hall_type_id
                if not ht:
                    continue
                updates = {}
                if 'capacity' not in vals and hasattr(ht, 'capacity'):
                    updates['capacity'] = ht.capacity or 0
                if 'price_per_hour' not in vals and hasattr(ht, 'price_per_hour'):
                    updates['price_per_hour'] = ht.price_per_hour or 0.0
                if updates:
                    super(HotelEventHall, rec).write(updates)
        return res

class HotelEventBooking(models.Model):
    _inherit = 'hotel.event.booking'

    # link to account.move
    invoice_ids = fields.One2many('account.move', 'hotel_event_booking_id', string='Invoices')
    invoice_count = fields.Integer(compute='_compute_invoice_count', string='Invoices')

    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = self.env['account.move'].sudo().search_count([
                ('hotel_event_booking_id', '=', rec.id),
                ('move_type', 'in', ['out_invoice', 'out_refund']),
            ])

    def action_view_invoices(self):
        self.ensure_one()
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        action['domain'] = [('hotel_event_booking_id', '=', self.id)]
        action['context'] = {
            'default_move_type': 'out_invoice',
            'default_partner_id': self.customer_id.id,
            'default_hotel_event_booking_id': self.id,
            'default_invoice_origin': self.name,
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
            raise UserError(f"No Sales Journal found for company {self.company_id.display_name}.")
        return journal

    def _event_invoice_lines(self):
        """Build invoice lines:
        Priority: explicit total_amount > package price > hall price_per_hour * hours
        """
        self.ensure_one()
        # price logic
        if self.total_amount:
            unit_price = self.total_amount
            qty = 1.0
            label = f"Event Booking {self.name}"
        elif self.package_id and self.package_id.price:
            unit_price = self.package_id.price
            qty = 1.0
            label = f"Event Package: {self.package_id.display_name}"
        else:
            unit_price = (self.hall_id.price_per_hour or 0.0)
            qty = max(self.duration_hours or 0.0, 1.0)
            label = f"Hall {self.hall_id.display_name} — {qty:g} hour(s)"

        # optional product (helps taxes/fiscal position)
        product = self.env['product.product'].search([('default_code', '=', 'EVENT_BOOKING')], limit=1)
        partner = self.customer_id
        taxes = product.taxes_id if product else self.env['account.tax']
        taxes = taxes.filtered(lambda t: t.company_id == self.company_id)
        if partner.property_account_position_id and taxes:
            taxes = partner.property_account_position_id.map_tax(taxes)

        line_vals = {
            'name': label,
            'quantity': qty,
            'price_unit': unit_price,
            'product_id': product.id if product else False,
            'tax_ids': [(6, 0, taxes.ids)] if taxes else False,
        }
        return [(0, 0, line_vals)]

    def action_create_invoice(self):
        self.ensure_one()
        if not self.customer_id:
            raise UserError("Set a Customer before invoicing.")
        # block duplicates if a posted invoice already exists
        exists = self.env['account.move'].search_count([
            ('hotel_event_booking_id', '=', self.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
        ])
        if exists:
            raise UserError("A posted invoice already exists for this event booking.")

        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.customer_id.id,
            'invoice_date': fields.Date.context_today(self),
            'invoice_origin': self.name,
            'journal_id': self._get_sale_journal().id,
            'currency_id': self.currency_id.id,
            'company_id': self.company_id.id,
            'invoice_line_ids': self._event_invoice_lines(),
            'hotel_event_booking_id': self.id,
        })
        move.action_post()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': move.id,
        }
    
    


class AccountMove(models.Model):
    _inherit = 'account.move'
    hotel_event_booking_id = fields.Many2one('hotel.event.booking', ondelete='set null')
