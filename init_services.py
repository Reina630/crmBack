"""
Script pour initialiser les services par défaut d'IMAN Agence
"""

from app import app
from app.models.service import Service, db

def init_services():
    """Crée les services par défaut s'ils n'existent pas déjà"""
    with app.app_context():
        # Services hiérarchiques d'IMAN Agence
        service_categories = [
            # 1. COMMUNICATION CLASSIQUE
            {
                'name': 'Communication Classique',
                'category': 'communication_classique',
                'description': 'Services de communication traditionnelle et impression',
                'parent_id': None,
                'children': [
                    {
                        'name': 'Art Graphique et Audiovisuel',
                        'description': 'Logotype, Charte graphique, Carte de visite, Affiche/flyers, Magazine/Plaquette, Dépliant/Brochure/Catalogue, Illustration 3D et 2D, Charte digitale, Production vidéo',
                        'price_range': '300 000-3 000 000 XOF'
                    },
                    {
                        'name': 'Publicité par l\'Objet',
                        'description': 'Tee-shirt/Casquette, Stylo/porte-clé/pin\'s, Macaron, clé USB, Eventail, Calendrier/agenda, Edition de catalogues, livres d\'or, rapports, dossiers de presse',
                        'price_range': '50 000-1 200 000 XOF'
                    },
                    {
                        'name': 'Impression Numérique',
                        'description': 'Impression sur vinyle simple ou perforé, bâche simple ou perforée, papier réfléchissant, magnétique, film transparent, Découpe numérique, Défonce numérique',
                        'price_range': '30 000-900 000 XOF'
                    },
                    {
                        'name': 'Marketing Direct',
                        'description': 'Etudes de marché, Evènementiel, Lancement de produits, Animations commerciales',
                        'price_range': '600 000-4 800 000 XOF'
                    },
                    {
                        'name': 'Affichage Urbain',
                        'description': 'Panneaux classiques, modernes et dynamiques, Affichages Terrasses/Mur/Toit, Affichages entrées de territoires, zones commerciales, administratives, Affichage digital',
                        'price_range': '1 200 000-9 000 000 XOF'
                    },
                    {
                        'name': 'Régie Médias',
                        'description': 'Définition des axes publicitaires, Compositions des scripts, Réalisations des scénarios, Planning média, Conseil Média, Espaces publicitaires',
                        'price_range': '900 000-6 000 000 XOF'
                    },
                    {
                        'name': 'Régie Hors Médias',
                        'description': 'Signalétiques, Branding locaux et manifestations',
                        'price_range': '480 000-3 000 000 XOF'
                    }
                ]
            },
            
            # 2. COMMUNICATION DIGITALE
            {
                'name': 'Communication Digitale',
                'category': 'communication_digitale',
                'description': 'Services de communication numérique et web',
                'parent_id': None,
                'children': [
                    {
                        'name': 'Community Management',
                        'description': 'Gestion des réseaux sociaux, création de contenu, animation de communautés',
                        'price_range': '480 000-1 800 000 XOF'
                    },
                    {
                        'name': 'Live Streaming et Session Hybride',
                        'description': 'Diffusion en direct, événements hybrides, production audiovisuelle en temps réel',
                        'price_range': '600 000-3 000 000 XOF'
                    },
                    {
                        'name': 'Création et Gestion de Sites Web',
                        'description': 'Développement de sites vitrine, e-commerce, applications web, maintenance et hébergement',
                        'price_range': '1 200 000-15 000 000 XOF'
                    }
                ]
            },
            
            # 3. SOLUTIONS NUMÉRIQUES
            {
                'name': 'Solutions Numériques',
                'category': 'solutions_numeriques',
                'description': 'Technologies et solutions informatiques avancées',
                'parent_id': None,
                'children': [
                    {
                        'name': 'Vidéo Surveillance',
                        'description': 'Installation et maintenance de systèmes de vidéosurveillance, monitoring et sécurité',
                        'price_range': '1 800 000-12 000 000 XOF'
                    },
                    {
                        'name': 'Téléphonie IP',
                        'description': 'Systèmes de communication VoIP, central téléphonique IP, solutions de téléconférence',
                        'price_range': '1 200 000-9 000 000 XOF'
                    },
                    {
                        'name': 'Développement d\'Applications',
                        'description': 'Applications mobiles et web sur mesure, logiciels métiers, solutions digitales personnalisées',
                        'price_range': '3 000 000-30 000 000 XOF'
                    },
                    {
                        'name': 'Cybersécurité',
                        'description': 'Audit sécurité, protection des données, formation cyber, solutions antivirus et firewall',
                        'price_range': '1 200 000-7 200 000 XOF'
                    }
                ]
            }
        ]
        
        services_created = 0
        
        # Créer les catégories principales et leurs sous-services
        for category_data in service_categories:
            # Créer la catégorie principale
            existing_category = Service.query.filter_by(name=category_data['name']).first()
            
            if not existing_category:
                category = Service(
                    name=category_data['name'],
                    description=category_data['description'],
                    category=category_data['category'],
                    parent_id=None,
                    is_active=True
                )
                db.session.add(category)
                db.session.flush()  # Pour obtenir l'ID
                services_created += 1
                
                # Créer les sous-services
                for child_data in category_data['children']:
                    existing_child = Service.query.filter_by(name=child_data['name']).first()
                    
                    if not existing_child:
                        child_service = Service(
                            name=child_data['name'],
                            description=child_data['description'],
                            price_range=child_data['price_range'],
                            category=category_data['category'],
                            parent_id=category.id,
                            is_active=True
                        )
                        db.session.add(child_service)
                        services_created += 1
        
        if services_created > 0:
            db.session.commit()
            print(f"✅ {services_created} service(s) créé(s) avec succès!")
            
            # Afficher tous les services
            print("\n📋 Services disponibles:")
            services = Service.query.all()
            for service in services:
                status = "🟢 Actif" if service.is_active else "🔴 Inactif"
                print(f"  • {service.id}: {service.name} - {service.price_range} {status}")
        else:
            print("ℹ️  Tous les services existent déjà")

if __name__ == '__main__':
    init_services()