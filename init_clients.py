"""
Script pour initialiser la base de données avec des clients de test
"""
from app import app, db
from app.models.client import Client
from app.models.user import User
import random

def init_clients():
    with app.app_context():
        # Vérifier s'il y a déjà des clients
        if Client.query.count() > 0:
            print(f"⚠️  Il y a déjà {Client.query.count()} clients dans la base de données.")
            response = input("Voulez-vous les supprimer et recommencer? (o/n): ")
            if response.lower() != 'o':
                print("❌ Opération annulée")
                return
            
            # Supprimer tous les clients
            Client.query.delete()
            db.session.commit()
            print("✅ Clients existants supprimés")

        # Récupérer les commerciaux disponibles
        commerciaux = User.query.filter_by(role='commercial', is_active=True).all()
        if not commerciaux:
            print("⚠️  Aucun commercial trouvé. Les clients seront créés sans responsable.")
            commerciaux = [None]

        # Données de test pour les clients
        clients_data = [
            {
                'name': 'Banque Centrale du Niger',
                'type': 'institution',
                'contact_name': 'Ibrahim Boubacar',
                'email': 'i.boubacar@bcn.ne',
                'phone': '+227 20 72 24 51',
                'address': 'Avenue de la Mairie, BP 487, Niamey',
                'sector': 'Finance',
                'company_size': 'Grande entreprise',
                'total_revenue': 45000000,
                'dossiers_count': 8
            },
            {
                'name': 'SONITEL Niger',
                'type': 'grande_entreprise',
                'contact_name': 'Aïssata Diallo',
                'email': 'a.diallo@sonitel.ne',
                'phone': '+227 20 73 31 16',
                'address': 'Rond-Point SONITEL, BP 208, Niamey',
                'sector': 'Télécommunications',
                'company_size': 'Grande entreprise',
                'total_revenue': 35000000,
                'dossiers_count': 6
            },
            {
                'name': 'SONICHAR',
                'type': 'grande_entreprise',
                'contact_name': 'Mamadou Tandja',
                'email': 'm.tandja@sonichar.ne',
                'phone': '+227 20 73 42 89',
                'address': 'Route de Tillabéri, BP 11700, Niamey',
                'sector': 'Énergie',
                'company_size': 'Grande entreprise',
                'total_revenue': 52000000,
                'dossiers_count': 10
            },
            {
                'name': 'Hôtel Gaweye',
                'type': 'pme',
                'contact_name': 'Hawa Mahamane',
                'email': 'h.mahamane@gaweye.ne',
                'phone': '+227 20 72 28 28',
                'address': 'Avenue du Président Kennedy, BP 10829, Niamey',
                'sector': 'Hôtellerie',
                'company_size': 'PME',
                'total_revenue': 8500000,
                'dossiers_count': 3
            },
            {
                'name': 'Société de Transport Rimbo',
                'type': 'pme',
                'contact_name': 'Oumarou Yazi',
                'email': 'o.yazi@rimbo.ne',
                'phone': '+227 91 85 42 36',
                'address': 'Carrefour Yantala, BP 12456, Niamey',
                'sector': 'Transport',
                'company_size': 'PME',
                'total_revenue': 12000000,
                'dossiers_count': 5
            },
            {
                'name': 'Clinique Magori',
                'type': 'pme',
                'contact_name': 'Dr. Balkissa Moussa',
                'email': 'b.moussa@magori.ne',
                'phone': '+227 20 73 55 89',
                'address': 'Plateau 2, Niamey',
                'sector': 'Santé',
                'company_size': 'PME',
                'total_revenue': 15000000,
                'dossiers_count': 4
            },
            {
                'name': 'Université Abdou Moumouni',
                'type': 'institution',
                'contact_name': 'Prof. Yahaya Djibo',
                'email': 'y.djibo@uam.ne',
                'phone': '+227 20 73 31 29',
                'address': 'Campus Universitaire, BP 237, Niamey',
                'sector': 'Éducation',
                'company_size': 'Grande entreprise',
                'total_revenue': 28000000,
                'dossiers_count': 7
            },
            {
                'name': 'SONIDEP (Dépôt Pétrolier)',
                'type': 'grande_entreprise',
                'contact_name': 'Salissou Garba',
                'email': 's.garba@sonidep.ne',
                'phone': '+227 20 73 28 47',
                'address': 'Zone Industrielle, BP 628, Niamey',
                'sector': 'Énergie',
                'company_size': 'Grande entreprise',
                'total_revenue': 40000000,
                'dossiers_count': 9
            },
            {
                'name': 'Supermarché Score Center',
                'type': 'pme',
                'contact_name': 'Mariama Souley',
                'email': 'm.souley@scorecenter.ne',
                'phone': '+227 20 73 65 42',
                'address': 'Avenue du Fleuve, Niamey',
                'sector': 'Commerce',
                'company_size': 'PME',
                'total_revenue': 6500000,
                'dossiers_count': 2
            },
            {
                'name': 'Chambre de Commerce et d\'Industrie du Niger',
                'type': 'institution',
                'contact_name': 'Adamou Seydou',
                'email': 'a.seydou@ccin.ne',
                'phone': '+227 20 73 22 10',
                'address': 'Place de la Concertation, BP 209, Niamey',
                'sector': 'Commerce',
                'company_size': 'Grande entreprise',
                'total_revenue': 18000000,
                'dossiers_count': 5
            },
            {
                'name': 'Nigelec (Société Nigérienne d\'Électricité)',
                'type': 'grande_entreprise',
                'contact_name': 'Hassane Maïdagi',
                'email': 'h.maidagi@nigelec.ne',
                'phone': '+227 20 72 24 41',
                'address': 'Boulevard du 15 Avril, BP 11202, Niamey',
                'sector': 'Énergie',
                'company_size': 'Grande entreprise',
                'total_revenue': 48000000,
                'dossiers_count': 11
            },
            {
                'name': 'Complexe Agro-Industriel Niger',
                'type': 'grande_entreprise',
                'contact_name': 'Zeinabou Hamani',
                'email': 'z.hamani@cain.ne',
                'phone': '+227 91 77 23 45',
                'address': 'Route de Dosso, BP 987, Niamey',
                'sector': 'Agriculture',
                'company_size': 'Grande entreprise',
                'total_revenue': 32000000,
                'dossiers_count': 7
            },
            {
                'name': 'Pharmacie La Santé',
                'type': 'pme',
                'contact_name': 'Dr. Ramatou Abdou',
                'email': 'r.abdou@lasante.ne',
                'phone': '+227 20 73 88 92',
                'address': 'Rue du Commerce, Niamey',
                'sector': 'Santé',
                'company_size': 'PME',
                'total_revenue': 4200000,
                'dossiers_count': 2
            },
            {
                'name': 'Imprimerie du Niger',
                'type': 'pme',
                'contact_name': 'Moussa Issoufou',
                'email': 'm.issoufou@impniger.ne',
                'phone': '+227 90 45 67 89',
                'address': 'Quartier Terminus, Niamey',
                'sector': 'Services',
                'company_size': 'PME',
                'total_revenue': 7800000,
                'dossiers_count': 3
            },
            {
                'name': 'Restaurant Salam',
                'type': 'pme',
                'contact_name': 'Fatoumata Ali',
                'email': 'f.ali@salam.ne',
                'phone': '+227 92 34 56 78',
                'address': 'Avenue de l\'Aéroport, Niamey',
                'sector': 'Restauration',
                'company_size': 'PME',
                'total_revenue': 3500000,
                'dossiers_count': 1
            }
        ]

        print(f"\n🚀 Création de {len(clients_data)} clients...\n")

        # Créer les clients
        created_count = 0
        for data in clients_data:
            try:
                # Assigner un commercial aléatoire si disponible
                responsible = random.choice(commerciaux) if commerciaux[0] is not None else None
                
                client = Client(
                    name=data['name'],
                    type=data['type'],
                    contact_name=data['contact_name'],
                    email=data['email'],
                    phone=data['phone'],
                    address=data['address'],
                    sector=data['sector'],
                    company_size=data['company_size'],
                    total_revenue=data['total_revenue'],
                    dossiers_count=data['dossiers_count'],
                    responsible_id=responsible.id if responsible else None,
                    is_active=True
                )
                
                db.session.add(client)
                created_count += 1
                
                responsible_name = responsible.username if responsible else "Non assigné"
                print(f"✅ {data['name']} ({data['type']}) - {data['sector']} - Responsable: {responsible_name}")
                
            except Exception as e:
                print(f"❌ Erreur lors de la création de {data['name']}: {str(e)}")
                continue

        # Valider les changements
        db.session.commit()
        
        print(f"\n🎉 {created_count} clients créés avec succès!")
        print(f"💰 Revenu total simulé: {sum(c['total_revenue'] for c in clients_data):,.0f} FCFA")
        print(f"📁 Total dossiers simulés: {sum(c['dossiers_count'] for c in clients_data)}")
        
        # Statistiques par type
        print("\n📊 Répartition par type:")
        for type_name in ['institution', 'grande_entreprise', 'pme']:
            count = sum(1 for c in clients_data if c['type'] == type_name)
            revenue = sum(c['total_revenue'] for c in clients_data if c['type'] == type_name)
            print(f"   - {type_name}: {count} clients ({revenue:,.0f} FCFA)")


if __name__ == '__main__':
    init_clients()
