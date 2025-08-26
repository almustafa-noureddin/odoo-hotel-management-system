from odoo import models,fields,api

class HotelRoomType(models.Model):
    _name = 'hotel.room.type'
    _description = 'hotel room type'
    _order = 'name'

    name = fields.Char(string="Room Type",required=True, index=True)
    description = fields.Char(string="Room type description")
    capacity = fields.Integer(string="Capacity",default=1)
    default_price = fields.Monetary(string="Base price", currency_field='currency_id')

    currency_id = fields.Many2one(
        'res.currency',
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )

class HotelRoomAmenity(models.Model):
    _name = 'hotel.room.amenity'
    _description = 'Room Amenity'
    _order = 'name'

    name = fields.Char(string="Amenity",required=True, index=True)
    description = fields.Text(string="Description")


class HotelRoom (models.Model):
    _name= "hotel.room"
    _description= "hotel room"
    _order = 'name'
    _check_company_auto = True  

    name =fields.Char(string="Room number or code",required=True, index=True)
    room_type_id= fields.Many2one('hotel.room.type', string="Room Type")
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Branch",
        required=True,
        index=True,
        default=lambda self: self.env.company,
        ondelete='restrict',
    )
    floor_number= fields.Integer(string="Floor Number")
    status = fields.Selection(
        string='Room Status',
        selection=[('available', 'Available'), 
            ('occupied', 'Occupied'), 
            ('dirty','Dirty'), 
            ('cleaning', 'Cleaning'),
            ('maintenance','Maintenance')]
    )
    price= fields.Monetary(string='Price', currency_field='currency_id')
    
    amenities_ids = fields.Many2many(
        string='Amenities',
        comodel_name='hotel.room.amenity',
        relation='hotel_room_amenity_rel',
        column1='room_id',
        column2='amenity_id',
    )

    currency_id = fields.Many2one(
        'res.currency',
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )

    
class HotelRoom(models.Model):
    _inherit = 'hotel.room'

    capacity = fields.Integer(string='Capacity')
    @api.onchange('room_type_id')
    def _onchange_room_type_id_autofill(self):
        """When a room type is chosen, prefill capacity & price from the type.
        Staff can still override after this onchange."""
        for rec in self:
            rt = rec.room_type_id
            if rt:
                # copy defaults from type
                if hasattr(rt, 'capacity'):
                    rec.capacity = rt.capacity or 0
                if hasattr(rt, 'default_price'):
                    rec.price = rt.default_price or 0.0

    @api.model_create_multi
    def create(self, vals_list):
        """Also enforce defaults when records are created programmatically (imports, RPC)
        (onchange only runs in the UI)."""
        RoomType = self.env['hotel.room.type'].sudo()
        for vals in vals_list:
            rt_id = vals.get('room_type_id')
            if rt_id:
                rt = RoomType.browse(rt_id)
                # Only set if the creator didn't specify a custom value
                if 'capacity' not in vals and hasattr(rt, 'capacity'):
                    vals['capacity'] = rt.capacity or 0
                if ('price' not in vals or vals.get('price') in (None, False)) and hasattr(rt, 'default_price'):
                    vals['price'] = rt.default_price or 0.0
        return super().create(vals_list)

    def write(self, vals):
        """If the room type changes later, prefill missing capacity/price from the new type."""
        res = super().write(vals)
        if 'room_type_id' in vals:
            for rec in self:
                rt = rec.room_type_id
                if not rt:
                    continue
                updates = {}
                if 'capacity' not in vals and hasattr(rt, 'capacity'):
                    updates['capacity'] = rt.capacity or 0
                if 'price' not in vals and hasattr(rt, 'default_price'):
                    updates['price'] = rt.default_price or 0.0
                if updates:
                    super(HotelRoom, rec).write(updates)
        return res
