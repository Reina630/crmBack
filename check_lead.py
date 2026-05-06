"""
Script pour vérifier l'affectation d'un lead
"""
from app import app, db
from app.models.lead import Lead
from app.models.user import User

def check_lead():
    with app.app_context():
        # Récupérer le dernier lead créé
        lead = Lead.query.order_by(Lead.created_at.desc()).first()
        
        if lead:
            print(f"\n📋 Dernier lead créé:")
            print(f"  - ID: {lead.id}")
            print(f"  - Nom: {lead.name}")
            print(f"  - Email: {lead.email}")
            print(f"  - assigned_to_id: {lead.assigned_to_id}")
            
            if lead.assigned_to:
                print(f"  - Assigné à: {lead.assigned_to.username} (ID: {lead.assigned_to.id})")
            else:
                print(f"  - Non assigné")
            
            print(f"\n  Dict: {lead.to_dict()}")
        else:
            print("❌ Aucun lead trouvé")

if __name__ == '__main__':
    check_lead()
