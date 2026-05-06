from marshmallow import Schema, fields
from .lead_schema import LeadSchema

class ProspectSchema(Schema):
    id = fields.Int(dump_only=True)
    lead_id = fields.Int(required=True)
    qualified_at = fields.DateTime(dump_only=True)
    notes = fields.Str()
    lead = fields.Nested(LeadSchema, dump_only=True)
