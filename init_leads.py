"""
Script pour initialiser la base de données avec des leads de test
"""
from app import app, db
from app.models.lead import Lead
from app.models.service import Service
import random

def init_leads():
    with app.app_context():
        # Vérifier s'il y a déjà des leads
        if Lead.query.count() > 0:
            print(f"⚠️  Il y a déjà {Lead.query.count()} leads dans la base de données.")
            response = input("Voulez-vous les supprimer et recommencer? (o/n): ")
            if response.lower() != 'o':
                print("❌ Opération annulée")
                return
            
            # Supprimer tous les leads
            Lead.query.delete()
            db.session.commit()
            print("✅ Leads existants supprimés")

        # Récupérer les services disponibles
        services = Service.query.filter_by(is_active=True).all()
        if not services:
            print("❌ Aucun service actif trouvé. Exécutez d'abord init_services.py")
            return

        # Données de test pour les leads
        leads_data = [
            {
                'name': 'Amina Abdou',
                'email': 'amina.abdou@techneer.ne',
                'phone': '+227 90 123 45 67',
                'company': 'TechNeer SARL',
                'job_title': 'Directrice Marketing',
                'source': 'Site Web',
                'estimated_budget': 5000000,
                'sector': 'Technologie',
                'company_size': '50-200',
                'urgency': 'haute',
                'status': 'nouveau',
                'score': 0.85
            },
            {
                'name': 'Mahamane Issoufou',
                'email': 'm.issoufou@bankniger.ne',
                'phone': '+227 91 234 56 78',
                'company': 'Banque du Niger',
                'job_title': 'Chef de Projet Digital',
                'source': 'Référence',
                'estimated_budget': 15000000,
                'sector': 'Finance',
                'company_size': '200+',
                'urgency': 'haute',
                'status': 'nouveau',
                'score': 0.92
            },
            {
                'name': 'Hadiza Amadou',
                'email': 'h.amadou@startupneer.ne',
                'phone': '+227 92 345 67 89',
                'company': 'StartupNeer',
                'job_title': 'CEO',
                'source': 'Réseaux Sociaux',
                'estimated_budget': 2000000,
                'sector': 'E-commerce',
                'company_size': '10-50',
                'urgency': 'moyenne',
                'status': 'nouveau',
                'score': 0.68
            },
            {
                'name': 'Abdoulaye Maïga',
                'email': 'abdoulaye.maiga@retailneer.ne',
                'phone': '+227 93 456 78 90',
                'company': 'Retail Neer',
                'job_title': 'Directeur Commercial',
                'source': 'Email Marketing',
                'estimated_budget': 8000000,
                'sector': 'Commerce',
                'company_size': '50-200',
                'urgency': 'moyenne',
                'status': 'nouveau',
                'score': 0.88
            },
            {
                'name': 'Fatoumata Harouna',
                'email': 'f.harouna@educationneer.ne',
                'phone': '+227 94 567 89 01',
                'company': 'École Nigerienne',
                'job_title': 'Responsable Communication',
                'source': 'Site Web',
                'estimated_budget': 3000000,
                'sector': 'Éducation',
                'company_size': '50-200',
                'urgency': 'basse',
                'status': 'nouveau',
                'score': 0.55
            },
            {
                'name': 'Salifou Garba',
                'email': 'salifou.garba@constructionneer.ne',
                'phone': '+227 95 678 90 12',
                'company': 'BTP Niger',
                'job_title': 'Directeur Général',
                'source': 'Salon Professionnel',
                'estimated_budget': 12000000,
                'sector': 'Construction',
                'company_size': '200+',
                'urgency': 'haute',
                'status': 'nouveau',
                'score': 0.78
            },
            {
                'name': 'Ramatou Boubacar',
                'email': 'r.boubacar@consultingneer.ne',
                'phone': '+227 96 789 01 23',
                'company': 'Boubacar Consulting',
                'job_title': 'Consultante',
                'source': 'Référence',
                'estimated_budget': 4000000,
                'sector': 'Conseil',
                'company_size': '10-50',
                'urgency': 'moyenne',
                'status': 'nouveau',
                'score': 0.72
            },
            {
                'name': 'Moussa Abdallah',
                'email': 'm.abdallah@telecomneer.ne',
                'phone': '+227 97 890 12 34',
                'company': 'TelecomNeer',
                'job_title': 'Responsable Innovation',
                'source': 'LinkedIn',
                'estimated_budget': 20000000,
                'sector': 'Télécommunications',
                'company_size': '200+',
                'urgency': 'haute',
                'status': 'converti',
                'score': 0.95
            },
            {
                'name': 'Aïchatou Adamou',
                'email': 'a.adamou@agroneer.ne',
                'phone': '+227 98 901 23 45',
                'company': 'AgroNeer',
                'job_title': 'Directrice Marketing',
                'source': 'Site Web',
                'estimated_budget': 6000000,
                'sector': 'Agriculture',
                'company_size': '50-200',
                'urgency': 'moyenne',
                'status': 'nouveau',
                'score': 0.65
            },
            {
                'name': 'Oumarou Dan Mallam',
                'email': 'o.danmallam@transportneer.ne',
                'phone': '+227 99 012 34 56',
                'company': 'Transport Niger',
                'job_title': 'PDG',
                'source': 'Appel Sortant',
                'estimated_budget': 1500000,
                'sector': 'Transport',
                'company_size': '10-50',
                'urgency': 'basse',
                'status': 'nouveau',
                'score': 0.42
            },
            {
                'name': 'Zeinabou Moussa',
                'email': 'z.moussa@fashionneer.ne',
                'phone': '+227 90 123 45 68',
                'company': 'Fashion Niger',
                'job_title': 'Créatrice',
                'source': 'Réseaux Sociaux',
                'estimated_budget': 3500000,
                'sector': 'Mode',
                'company_size': '10-50',
                'urgency': 'moyenne',
                'status': 'nouveau',
                'score': 0.58
            },
            {
                'name': 'Abdoul Aziz Djibo',
                'email': 'a.djibo@hotelneer.ne',
                'phone': '+227 91 234 56 79',
                'company': 'Hôtel Sahel',
                'job_title': 'Directeur',
                'source': 'Référence',
                'estimated_budget': 10000000,
                'sector': 'Hôtellerie',
                'company_size': '50-200',
                'urgency': 'haute',
                'status': 'nouveau',
                'score': 0.81
            },
            {
                'name': 'Rakia Ibrahim',
                'email': 'r.ibrahim@pharmaneer.ne',
                'phone': '+227 92 345 67 80',
                'company': 'PharmaNeer',
                'job_title': 'Responsable Communication',
                'source': 'Email Marketing',
                'estimated_budget': 4500000,
                'sector': 'Santé',
                'company_size': '50-200',
                'urgency': 'moyenne',
                'status': 'nouveau',
                'score': 0.70
            },
            {
                'name': 'Ali Garba',
                'email': 'a.garba@assuranceneer.ne',
                'phone': '+227 93 456 78 91',
                'company': 'Assurance Niger',
                'job_title': 'Chef Marketing',
                'source': 'Site Web',
                'estimated_budget': 7000000,
                'sector': 'Assurance',
                'company_size': '200+',
                'urgency': 'haute',
                'status': 'nouveau',
                'score': 0.87
            },
            {
                'name': 'Maimouna Souley',
                'email': 'm.souley@medianeer.ne',
                'phone': '+227 94 567 89 02',
                'company': 'Media Niger',
                'job_title': 'Rédactrice en Chef',
                'source': 'LinkedIn',
                'estimated_budget': 2500000,
                'sector': 'Médias',
                'company_size': '10-50',
                'urgency': 'basse',
                'status': 'nouveau',
                'score': 0.48
            },
        ]

        # Créer les leads
        created_count = 0
        for lead_data in leads_data:
            # Assigner un service aléatoire
            service = random.choice(services)
            lead_data['service_id'] = service.id
            
            lead = Lead(**lead_data)
            db.session.add(lead)
            created_count += 1

        db.session.commit()
        
        print(f"\n✅ {created_count} leads créés avec succès!")
        
        # Afficher un résumé par statut
        print("\n📊 Résumé par statut:")
        statuses = ['nouveau', 'en_cours', 'qualifie', 'converti', 'perdu']
        for status in statuses:
            count = Lead.query.filter_by(status=status).count()
            print(f"  - {status.replace('_', ' ').title()}: {count}")

if __name__ == '__main__':
    init_leads()
