"""Unit tests use explicit doubles, never credentials from the developer's .env."""
import os

# Loaded before application imports. python-dotenv preserves these empty values.
# This changes this pytest process only; it never edits the user's .env file.
for name in ['APP_ACCESS_TOKEN', 'OPENAI_API_KEY', 'FIREBASE_PROJECT_ID',
             'FIREBASE_SERVICE_ACCOUNT_JSON', 'GOOGLE_APPLICATION_CREDENTIALS',
             'FIRESTORE_EMULATOR_HOST']:
    os.environ[name] = ''
os.environ['APP_ENV'] = 'development'
