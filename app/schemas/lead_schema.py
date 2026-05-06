from marshmallow import Schema, fields

class LeadSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    email = fields.Email(required=True)
    phone = fields.Str()
    status = fields.Str()
    score = fields.Float()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
