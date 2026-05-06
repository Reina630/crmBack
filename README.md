# BackendAgent

Assistant commercial intelligent pour la gestion des leads.

## Stack
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- PostgreSQL
- Flasgger (Swagger UI)

## Démarrage rapide

1. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
2. Configurer PostgreSQL et les variables d’environnement (`.env`)
3. Initialiser la base de données :
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```
4. Lancer le serveur :
   ```bash
   flask run
   ```

La documentation Swagger sera disponible sur `/apidocs`.
