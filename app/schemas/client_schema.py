from marshmallow import Schema, fields, validate

class ClientSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=120))
    type = fields.Str(required=True, validate=validate.OneOf(['entreprise', 'particulier', 'institution', 'pme', 'grande_entreprise']))
    contact_name = fields.Str(allow_none=True, validate=validate.Length(max=120))
    email = fields.Email(allow_none=True)
    phone = fields.Str(allow_none=True, validate=validate.Length(max=20))
    address = fields.Str(allow_none=True)
    responsible_id = fields.Int(allow_none=True)
    responsible_name = fields.Str(dump_only=True, allow_none=True)
    sector = fields.Str(allow_none=True, validate=validate.Length(max=100))
    company_size = fields.Str(allow_none=True, validate=validate.Length(max=50))
    total_revenue = fields.Float(dump_only=True)
    dossiers_count = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    is_active = fields.Bool()
