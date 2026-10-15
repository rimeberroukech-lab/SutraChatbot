"""
API Flask du chatbot RAG pour le tarif douanier marocain.
"""

from dotenv import load_dotenv
load_dotenv()

import os
import re
import sys

import pandas as pd
from flask import Flask, jsonify, request, send_from_directory
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Import du module local history_manager
from history_manager import clean_response_text, format_history

app = Flask(__name__, static_folder="static")

CSV_PATH = os.environ.get("NOMENCLATURE_CSV", "./nomenclature_maroc.csv")
PERSIST_DIR = "./chroma_db_csv_new"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def erreur_fatale(message: str) -> None:
    print("\n" + "=" * 60)
    print("[ERREUR AU DEMARRAGE]")
    print(message)
    print("=" * 60 + "\n")
    sys.exit(1)


# 1. Vérifications initiales
if not os.environ.get("GEMINI_API_KEY"):
    erreur_fatale("GEMINI_API_KEY non configurée dans le fichier .env")

if not os.path.isfile(CSV_PATH):
    erreur_fatale(f"Fichier CSV introuvable : {os.path.abspath(CSV_PATH)}")


# 2. Chargement des données et modèles
print("Chargement du CSV...")
try:
    df = pd.read_csv(
        CSV_PATH,
        sep=r"\|\|\|",
        engine="python",
        encoding="utf-8",
        dtype={"code_sh_10": str},
    )
    df["code_sh_10"] = df["code_sh_10"].astype(str).str.strip()
except Exception as e:
    erreur_fatale(f"Impossible de lire le CSV ({CSV_PATH}) :\n  {e}")

print(f"Chargement du modèle d'embedding ({EMBEDDING_MODEL})...")
try:
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
except Exception as e:
    erreur_fatale(f"Échec des embeddings HuggingFace : {e}")

print("Chargement de la base vectorielle ChromaDB...")
try:
    if os.path.exists(PERSIST_DIR) and os.listdir(PERSIST_DIR):
        vector_db = Chroma(
            persist_directory=PERSIST_DIR, embedding_function=embeddings
        )
    else:
        documents = [
            Document(page_content="\n".join(f"{col}: {row[col]}" for col in df.columns))
            for _, row in df.iterrows()
        ]
        vector_db = Chroma.from_documents(
            documents=documents, embedding=embeddings, persist_directory=PERSIST_DIR
        )
except Exception as e:
    erreur_fatale(f"Échec de la base Chroma : {e}")

retriever = vector_db.as_retriever(search_kwargs={"k": 8})

# Initialisation du LLM Gemini
print("Chargement du LLM Gemini...")
try:
    LLM = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        temperature=0,
        google_api_key=os.environ.get("GEMINI_API_KEY")
    )
except Exception as e:
    erreur_fatale(f"Échec de l'initialisation de Gemini : {e}")


# 3. Logique RAG et Prompt
def recherche_hybride(question: str):
    match = re.search(r"\b(\d{10})\b", question)
    if match:
        code = match.group(1)
        ligne = df[df["code_sh_10"] == code]
        if not ligne.empty:
            contenu = "\n".join(f"{col}: {ligne.iloc[0][col]}" for col in df.columns)
            return [Document(page_content=contenu)]
        return []

    docs = retriever.invoke(question)
    seen = set()
    docs_uniques = []
    for doc in docs:
        if doc.page_content not in seen:
            seen.add(doc.page_content)
            docs_uniques.append(doc)
    return docs_uniques

def extraire_code_sh_depuis_docs(docs: list) -> list:
    """Extrait la liste des codes SH à 10 chiffres présents dans les documents récupérés par le RAG.

    :param docs: Liste de Documents LangChain
    :return: Liste de dictionnaires contenant le code_sh et le contenu
    """
    resultats = []
    for doc in docs:
        # Recherche du motif d'un code SH à 10 chiffres
        match = re.search(r"code_sh_10:\s*(\d{10})", doc.page_content)
        if match:
            resultats.append(
                {"code_sh": match.group(1), "details": doc.page_content}
            )
    return resultats


# Adaptation de la fonction repondre()
def repondre(question: str, history_list: list = None) -> dict:
    docs = recherche_hybride(question)
    context = "\n\n".join(doc.page_content for doc in docs)

    formatted_history = format_history(history_list or [])

    chain = PROMPT_TEMPLATE | LLM
    response = chain.invoke(
        {
            "context": context or "(aucun produit trouvé)",
            "history": formatted_history,
            "question": question,
        }
    )

    texte_clean = clean_response_text(response.content)

    # Extraction optionnelle des codes SH pour enrichir la réponse JSON
    codes_extraits = extraire_code_sh_depuis_docs(docs)

    return {
        "reponse": texte_clean,
        "nb_documents_utilises": len(docs),
        "codes_sh_trouves": [
            item["code_sh"] for item in codes_extraits
        ],  # Liste des codes 10 chiffres
    }
    
PROMPT_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Vous êtes un assistant douanier marocain expert. Répondez à la question de manière extrêmement concise, en suivant STRICTEMENT la consigne ci-dessous, sans introduction ni bavardage.

Contexte douanier :
{context}

Consignes de réponse :
1. Si l'utilisateur demande le code SH, la position douanière ou la nomenclature d'un produit, donnez le code SH à 10 chiffres correspondant, accompagné du libellé exact et du droit d'importation (DI).
2. Format de réponse attendu :
   - Code SH (10 chiffres) : [Code]
   - Libellé : [Description du produit]
   - Droit d'importation : [X %]

Si aucun produit correspondant n'est trouvé dans le contexte, répondez simplement : "Aucun produit correspondant trouvé dans la nomenclature douanière." """,
        ),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ]
)
def extraire_code_sh_depuis_docs(docs: list) -> list:
    """Extrait la liste des codes SH à 10 chiffres présents dans les documents récupérés par le RAG.

    :param docs: Liste de Documents LangChain
    :return: Liste de dictionnaires contenant le code_sh et le contenu
    """
    resultats = []
    for doc in docs:
        # Recherche du motif d'un code SH à 10 chiffres
        match = re.search(r"code_sh_10:\s*(\d{10})", doc.page_content)
        if match:
            resultats.append(
                {"code_sh": match.group(1), "details": doc.page_content}
            )
    return resultats


# Adaptation de la fonction repondre()
def repondre(question: str, history_list: list = None) -> dict:
    docs = recherche_hybride(question)
    context = "\n\n".join(doc.page_content for doc in docs)

    formatted_history = format_history(history_list or [])

    chain = PROMPT_TEMPLATE | LLM
    response = chain.invoke(
        {
            "context": context or "(aucun produit trouvé)",
            "history": formatted_history,
            "question": question,
        }
    )

    texte_clean = clean_response_text(response.content)

    # Extraction optionnelle des codes SH pour enrichir la réponse JSON
    codes_extraits = extraire_code_sh_depuis_docs(docs)

    return {
        "reponse": texte_clean,
        "nb_documents_utilises": len(docs),
        "codes_sh_trouves": [
            item["code_sh"] for item in codes_extraits
        ],  # Liste des codes 10 chiffres
    }

def repondre(question: str, history_list: list = None) -> dict:
    docs = recherche_hybride(question)
    context = "\n\n".join(doc.page_content for doc in docs)

    formatted_history = format_history(history_list or [])

    chain = PROMPT_TEMPLATE | LLM
    response = chain.invoke(
        {
            "context": context or "(aucun produit trouvé)",
            "history": formatted_history,
            "question": question,
        }
    )

    texte_clean = clean_response_text(response.content)

    return {
        "reponse": texte_clean,
        "nb_documents_utilises": len(docs),
    }


# 4. Routes de l'application
@app.route("/")
def index():
    return send_from_directory("static", "chat.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    question = (data.get("message") or "").strip()
    history = data.get("history") or []

    if not question:
        return jsonify({"erreur": "Message vide."}), 400

    try:
        resultat = repondre(question, history)
        return jsonify(resultat)
    except Exception as e:
        app.logger.exception("Erreur pendant la génération de la réponse")
        return jsonify({"erreur": f"Erreur serveur : {e}"}), 500


if __name__ == "__main__":
    app.run(debug=False, port=5000)
