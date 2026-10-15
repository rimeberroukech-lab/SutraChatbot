# SutraChatbot 

SutraChatbot est un assistant conversationnel intelligent basé sur une architecture RAG (Retrieval-Augmented Generation). Conçu spécifiquement pour l'écosystème douanier, il permet d'interroger et d'exploiter efficacement les documents et nomenclatures réglementaires (notamment le tarif douanier marocain) afin de fournir des réponses précises et structurées aux transitaires et professionnels.

---

## 🏗️ Architecture et Fonctionnalités

- **Recherche Hybride Intelligente** : 
  * *Extraction par expression régulière (Regex)* : Détection automatique des codes SH à 10 chiffres dans la question pour interroger directement la base tabulaire.
  * *Recherche Sémantique Vectorielle* : Prise en charge des requêtes textuelles complexes via **ChromaDB** et les embeddings multilingues de HuggingFace.
- **Structuration Rigoureuse des Réponses** : Le modèle formate l'expertise douanière autour de 4 champs clés :
  1. Code SH
  2. Désignation
  3. Droit d'importation
  4. Unité
- **Interface Web Interactive** : Application **Flask** légère et intuitive intégrée avec une interface de chat (HTML/CSS/JS).

---

## 🛠️ Stack Technique

- **Langage** : Python
- **Framework Web** : Flask
- **Orchestration RAG & IA** : LangChain, Google Gemini (`gemini-3.1-flash`)
- **Base Vectorielle & Embeddings** : ChromaDB, HuggingFace (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`)
- **Traitement de données** : Pandas

---

## ⚙️ Guide d'Installation et d'Utilisation

### 1. Obtenir une clé API Gemini
Prendre la clé de [Google AI Studio](https://aistudio.google.com/).

### 2. Configuration de l'Environnement
Clonez le dépôt sur votre machine, puis créez un fichier nommé `.env` à la racine du projet pour y injecter vos identifiants en toute sécurité (ce secret est strictement isolé et ignoré par le versioning Git) :
```env
GEMINI_API_KEY=cle_api
