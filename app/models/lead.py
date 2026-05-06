from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Lead(db.Model):
    __tablename__ = 'leads'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=False, nullable=True)
    phone = db.Column(db.String(20))
    company = db.Column(db.String(120))
    job_title = db.Column(db.String(120))
    source = db.Column(db.String(50))  # Facebook, site web, recommandation, etc.
    estimated_budget = db.Column(db.Float)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=True)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    sector = db.Column(db.String(100))  # Secteur d'activité
    company_size = db.Column(db.String(50))  # TPE, PME, Grande entreprise
    urgency = db.Column(db.String(50))  # Immédiat, 1-3 mois, 6+ mois
    notes = db.Column(db.Text)  # Notes de qualification
    status = db.Column(db.String(50), default='new')
    score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    # Relations
    assigned_to = db.relationship('User', backref='assigned_leads', foreign_keys=[assigned_to_id])
    
    def to_dict(self):
        """Convertit le lead en dictionnaire"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'company': self.company,
            'job_title': self.job_title,
            'source': self.source,
            'estimated_budget': self.estimated_budget,
            'service_id': self.service_id,
            'assigned_to_id': self.assigned_to_id,
            'assigned_to': {
                'id': self.assigned_to.id,
                'username': self.assigned_to.username,
                'role': self.assigned_to.role
            } if self.assigned_to else None,
            'sector': self.sector,
            'company_size': self.company_size,
            'urgency': self.urgency,
            'notes': self.notes,
            'status': self.status,
            'score': self.score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
