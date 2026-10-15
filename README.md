# SutraChatbot

SutraChatbot est un assistant conversationnel intelligent basé sur une architecture RAG (Retrieval-Augmented Generation). Il permet d'interroger efficacement les documents douaniers et réglementaires marocains pour fournir des réponses précises et ciblées.

---

## 🚀 Fonctionnalités principales
* **Recherche hybride intelligente** : Extraction directe par code SH (10 chiffres) ou recherche sémantique vectorielle via ChromaDB.
* **Expertise douanière** : Réponses structurées intégrant le Code SH, la Désignation, le Droit d'importation et l'Unité.
* **Interface Web** : API Flask connectée à une interface de chat interactive.

## 🛠️ Technologies utilisées
* **Backend** : Python, Flask
* **IA & NLP** : LangChain, HuggingFace Embeddings, Google Gemini (`gemini-2.5-flash`)
* **Base vectorielle** : ChromaDB
* **Manipulation de données** : Pandas

---

## ⚙️ Installation et Guide d'utilisation

### 1. Cloner le projet et préparer l'environnement
Clonez le dépôt sur votre machine et créez un fichier `.env` à la racine contenant votre clé API :
```env
GEMINI_API_KEY=votre_cle_api_ici
