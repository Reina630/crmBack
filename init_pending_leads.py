"""
Script pour initialiser la base de données avec des pending leads IA de test
avec leurs conversations complètes
"""
from app import app, db
from app.models.pending_lead import PendingLead
from app.models.conversation import Conversation
from app.models.user import User
from datetime import datetime, timedelta
import random
import uuid

def init_pending_leads():
    with app.app_context():
        # Vérifier s'il y a déjà des pending leads
        if PendingLead.query.count() > 0:
            print(f"⚠️  Il y a déjà {PendingLead.query.count()} pending leads dans la base de données.")
            response = input("Voulez-vous les supprimer et recommencer? (o/n): ")
            if response.lower() != 'o':
                print("❌ Opération annulée")
                return
            
            # Supprimer tous les pending leads et conversations
            Conversation.query.delete()
            PendingLead.query.delete()
            db.session.commit()
            print("✅ Pending leads et conversations existants supprimés")

        # Données de test pour les pending leads nigériens
        pending_leads_data = [
            {
                'data': {
                    'nom': 'Hassane Mahamadou',
                    'email': 'h.mahamadou@nigertech.ne',
                    'telephone': '+227 90 12 34 56',
                    'besoin': 'Solution CRM pour gérer notre base clients',
                    'company': 'Niger Tech Solutions',
                    'secteur': 'Technologie',
                    'budget_estime': '3000000',
                    'urgence': 'haute'
                },
                'score': 0.89,
                'urgency': 'haute',
                'conversation': [
                    {
                        'role': 'assistant',
                        'content': 'Bonjour ! Je suis l\'assistant virtuel d\'IMAN CRM. Comment puis-je vous aider aujourd\'hui ?'
                    },
                    {
                        'role': 'user',
                        'content': 'Bonjour, je cherche un CRM pour mon entreprise'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Excellent ! Pour mieux vous conseiller, pourriez-vous me dire quel est le nom de votre entreprise ?'
                    },
                    {
                        'role': 'user',
                        'content': 'Niger Tech Solutions'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Parfait ! Et vous êtes ? Quel est votre nom ?'
                    },
                    {
                        'role': 'user',
                        'content': 'Hassane Mahamadou, je suis le directeur commercial'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Enchanté Monsieur Mahamadou. Pourriez-vous me donner votre email professionnel ?'
                    },
                    {
                        'role': 'user',
                        'content': 'h.mahamadou@nigertech.ne'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Merci ! Et votre numéro de téléphone ?'
                    },
                    {
                        'role': 'user',
                        'content': '+227 90 12 34 56'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Parfait. Parlez-moi de vos besoins spécifiques. Que recherchez-vous dans un CRM ?'
                    },
                    {
                        'role': 'user',
                        'content': 'On a besoin de mieux organiser notre base clients. On perd beaucoup d\'opportunités faute de suivi'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Je comprends. Avez-vous une idée du budget que vous souhaitez allouer à ce projet ?'
                    },
                    {
                        'role': 'user',
                        'content': 'Autour de 3 millions FCFA'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Excellent. Et dans quel délai souhaitez-vous mettre en place cette solution ?'
                    },
                    {
                        'role': 'user',
                        'content': 'Le plus vite possible, c\'est urgent'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Merci pour toutes ces informations ! Un de nos commerciaux va vous recontacter très rapidement pour discuter de votre projet en détail.'
                    }
                ]
            },
            {
                'data': {
                    'nom': 'Aïssata Oumarou',
                    'email': 'a.oumarou@agroniger.ne',
                    'telephone': '+227 91 23 45 67',
                    'besoin': 'Logiciel de gestion commerciale pour nos produits agricoles',
                    'company': 'Agro Niger SARL',
                    'secteur': 'Agriculture',
                    'budget_estime': '5000000',
                    'urgence': 'moyenne'
                },
                'score': 0.92,
                'urgency': 'haute',
                'conversation': [
                    {
                        'role': 'assistant',
                        'content': 'Bonjour ! Je suis l\'assistant virtuel d\'IMAN CRM. Comment puis-je vous aider aujourd\'hui ?'
                    },
                    {
                        'role': 'user',
                        'content': 'Bonjour, je voudrais un logiciel pour gérer mes ventes'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Très bien ! Pour commencer, pourriez-vous me dire le nom de votre entreprise ?'
                    },
                    {
                        'role': 'user',
                        'content': 'Agro Niger SARL, on fait dans la production et distribution de produits agricoles'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Intéressant ! Et vous-même, comment vous appelez-vous ?'
                    },
                    {
                        'role': 'user',
                        'content': 'Aïssata Oumarou, directrice des ventes'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Ravie de vous connaître Madame Oumarou. Quelle est votre adresse email ?'
                    },
                    {
                        'role': 'user',
                        'content': 'a.oumarou@agroniger.ne'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Parfait. Et votre numéro de téléphone ?'
                    },
                    {
                        'role': 'user',
                        'content': '91 23 45 67'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Merci. Pourriez-vous détailler vos besoins ? Qu\'attendez-vous de cette solution ?'
                    },
                    {
                        'role': 'user',
                        'content': 'On veut suivre nos distributeurs, gérer les commandes, suivre les paiements. Actuellement tout est sur Excel et c\'est le chaos'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Je vois parfaitement. Quel budget avez-vous prévu pour ce projet ?'
                    },
                    {
                        'role': 'user',
                        'content': 'Environ 5 millions FCFA'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Merci pour toutes ces informations précieuses. Un de nos experts commerciaux va vous contacter rapidement pour vous présenter nos solutions adaptées à votre secteur.'
                    }
                ]
            },
            {
                'data': {
                    'nom': 'Ibrahim Garba',
                    'email': 'i.garba@constructionniger.ne',
                    'telephone': '+227 92 34 56 78',
                    'besoin': 'Suivi de chantiers et gestion clients',
                    'company': 'Niger Construction',
                    'secteur': 'BTP',
                    'budget_estime': '7000000',
                    'urgence': 'haute'
                },
                'score': 0.85,
                'urgency': 'haute',
                'conversation': [
                    {
                        'role': 'assistant',
                        'content': 'Bonjour ! Je suis l\'assistant virtuel d\'IMAN CRM. Comment puis-je vous aider aujourd\'hui ?'
                    },
                    {
                        'role': 'user',
                        'content': 'Salut, je cherche un outil pour mieux gérer mes chantiers'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Parfait ! Dans quel domaine travaillez-vous et quelle est votre entreprise ?'
                    },
                    {
                        'role': 'user',
                        'content': 'Niger Construction, on fait du BTP'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Excellent secteur ! Et vous êtes ?'
                    },
                    {
                        'role': 'user',
                        'content': 'Ibrahim Garba, je suis le gérant'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Enchanté Monsieur Garba. Pouvez-vous me donner votre email ?'
                    },
                    {
                        'role': 'user',
                        'content': 'i.garba@constructionniger.ne'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Merci. Et votre téléphone ?'
                    },
                    {
                        'role': 'user',
                        'content': '+227 92 34 56 78'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Super. Quels sont vos besoins précis en matière de gestion ?'
                    },
                    {
                        'role': 'user',
                        'content': 'Je veux pouvoir suivre mes chantiers, gérer mes clients et sous-traitants, et avoir une vue d\'ensemble sur les projets en cours'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Très clair. Quel budget envisagez-vous pour cette solution ?'
                    },
                    {
                        'role': 'user',
                        'content': 'Jusqu\'à 7 millions FCFA si la solution est complète'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Parfait ! C\'est noté. Un de nos consultants spécialisés dans le BTP va vous recontacter très prochainement.'
                    }
                ]
            },
            {
                'data': {
                    'nom': 'Fatoumata Souley',
                    'email': 'f.souley@pharmacieniger.ne',
                    'telephone': '+227 93 45 67 89',
                    'besoin': 'Gestion des patients et stock médicaments',
                    'company': 'Pharmacie de la Santé',
                    'secteur': 'Santé',
                    'budget_estime': '2000000',
                    'urgence': 'moyenne'
                },
                'score': 0.78,
                'urgency': 'moyenne',
                'conversation': [
                    {
                        'role': 'assistant',
                        'content': 'Bonjour ! Je suis l\'assistant virtuel d\'IMAN CRM. Comment puis-je vous aider aujourd\'hui ?'
                    },
                    {
                        'role': 'user',
                        'content': 'Bonjour, j\'ai une pharmacie et je cherche un logiciel de gestion'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Excellent ! Quel est le nom de votre pharmacie ?'
                    },
                    {
                        'role': 'user',
                        'content': 'Pharmacie de la Santé'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Très bien. Et vous-même, comment vous appelez-vous ?'
                    },
                    {
                        'role': 'user',
                        'content': 'Fatoumata Souley, je suis la pharmacienne titulaire'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Enchantée Docteur Souley. Votre email professionnel ?'
                    },
                    {
                        'role': 'user',
                        'content': 'f.souley@pharmacieniger.ne'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Merci. Et votre numéro de téléphone ?'
                    },
                    {
                        'role': 'user',
                        'content': '93 45 67 89'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Parfait. Quels sont vos besoins spécifiques ?'
                    },
                    {
                        'role': 'user',
                        'content': 'Je veux gérer mes patients réguliers, suivre les stocks de médicaments et les ventes'
                    },
                    {
                        'role': 'assistant',
                        'content': 'C\'est noté. Quel budget avez-vous prévu ?'
                    },
                    {
                        'role': 'user',
                        'content': 'Environ 2 millions FCFA'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Merci pour ces informations. Un de nos spécialistes du secteur santé va vous contacter pour vous présenter nos solutions adaptées aux pharmacies.'
                    }
                ]
            },
            {
                'data': {
                    'nom': 'Moussa Adamou',
                    'email': 'm.adamou@transniger.ne',
                    'telephone': '+227 94 56 78 90',
                    'besoin': 'Gestion flotte transport et clients',
                    'company': 'Trans Niger Express',
                    'secteur': 'Transport',
                    'budget_estime': '4000000',
                    'urgence': 'haute'
                },
                'score': 0.87,
                'urgency': 'haute',
                'conversation': [
                    {
                        'role': 'assistant',
                        'content': 'Bonjour ! Je suis l\'assistant virtuel d\'IMAN CRM. Comment puis-je vous aider aujourd\'hui ?'
                    },
                    {
                        'role': 'user',
                        'content': 'Bonjour, je gère une société de transport et j\'ai besoin d\'organiser mes activités'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Très intéressant ! Quel est le nom de votre société ?'
                    },
                    {
                        'role': 'user',
                        'content': 'Trans Niger Express'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Parfait ! Et vous êtes ?'
                    },
                    {
                        'role': 'user',
                        'content': 'Moussa Adamou, directeur général'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Ravi de vous connaître Monsieur Adamou. Votre email ?'
                    },
                    {
                        'role': 'user',
                        'content': 'm.adamou@transniger.ne'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Merci. Et votre téléphone ?'
                    },
                    {
                        'role': 'user',
                        'content': '+227 94 56 78 90'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Excellent. Quels sont vos besoins en termes de gestion ?'
                    },
                    {
                        'role': 'user',
                        'content': 'Je dois suivre ma flotte de véhicules, gérer les réservations clients, les chauffeurs et les itinéraires'
                    },
                    {
                        'role': 'assistant',
                        'content': 'Je comprends vos besoins. Quel budget envisagez-vous ?'
                    },
                    {
                        'role': 'user',
                        'content': '4 millions FCFA maximum'
                    },
                    {
                        'role': 'assistant',
                        'content': 'C\'est parfait. Merci pour toutes ces informations. Un de nos experts va vous rappeler rapidement pour discuter d\'une solution adaptée au transport.'
                    }
                ]
            }
        ]

        print(f"\n🚀 Création de {len(pending_leads_data)} pending leads avec conversations...\n")

        created_count = 0
        for lead_data in pending_leads_data:
            try:
                # Générer un conversation_id unique
                conversation_id = f"conv_{uuid.uuid4().hex[:12]}"
                
                # Créer la conversation
                conversation = Conversation(
                    conversation_id=conversation_id,
                    messages=lead_data['conversation'],
                    lead_data=lead_data['data'],
                    score=lead_data['score'],
                    status='completed',
                    started_at=datetime.utcnow() - timedelta(hours=random.randint(1, 48)),
                    completed_at=datetime.utcnow() - timedelta(minutes=random.randint(5, 120)),
                    message_count=len(lead_data['conversation']),
                    ip_address=f"41.{random.randint(100, 250)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
                )
                
                # Calculer la durée
                if conversation.started_at and conversation.completed_at:
                    conversation.duration = int((conversation.completed_at - conversation.started_at).total_seconds())
                
                db.session.add(conversation)
                db.session.flush()  # Pour obtenir l'ID
                
                # Créer le pending lead
                pending_lead = PendingLead(
                    conversation_id=conversation_id,
                    data=lead_data['data'],
                    score=lead_data['score'],
                    urgency=lead_data['urgency'],
                    status='pending',
                    created_at=conversation.completed_at
                )
                
                db.session.add(pending_lead)
                db.session.flush()
                
                # Lier la conversation au pending lead
                conversation.pending_lead_id = pending_lead.id
                
                created_count += 1
                print(f"✅ {lead_data['data']['nom']} - {lead_data['data']['company']} (Score: {lead_data['score']:.2f})")
                print(f"   📧 {lead_data['data']['email']} | 📞 {lead_data['data']['telephone']}")
                print(f"   💬 {len(lead_data['conversation'])} messages | ⏱️  {conversation.duration}s\n")
                
            except Exception as e:
                print(f"❌ Erreur lors de la création du lead {lead_data['data']['nom']}: {str(e)}")
                continue

        # Valider les changements
        db.session.commit()
        
        print(f"\n🎉 {created_count} pending leads créés avec succès!")
        print(f"📊 Score moyen: {sum(l['score'] for l in pending_leads_data) / len(pending_leads_data):.2f}")
        print(f"⚡ Urgence haute: {sum(1 for l in pending_leads_data if l['urgency'] == 'haute')}")
        print(f"📱 Total messages: {sum(len(l['conversation']) for l in pending_leads_data)}")
        
        # Créer une notification pour le DC
        dc = User.query.filter_by(role='dc').first()
        if dc:
            from app.models.notification import Notification
            notification = Notification(
                user_id=dc.id,
                type='validation',
                title='Nouveaux leads IA à valider',
                message=f'{created_count} nouveaux leads collectés par l\'agent IA sont en attente de validation',
                link='/leads-ia'
            )
            db.session.add(notification)
            db.session.commit()
            print(f"\n🔔 Notification envoyée au DC ({dc.username})")


if __name__ == '__main__':
    init_pending_leads()
