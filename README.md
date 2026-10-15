<<<<<<< HEAD
"""
API du chatbot RAG pour le tarif douanier marocain.
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

app = Flask(__name__, static_folder="static")

CSV_PATH = os.environ.get("NOMENCLATURE_CSV", "./nomenclature_maroc.csv")
PERSIST_DIR = "./chroma_db_csv_new"

EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def erreur_fatale(message: str) -> None:
    """Affiche un message clair et quitte sans stack trace brute."""
    print("\n" + "=" * 60)
    print("[ERREUR AU DEMARRAGE]")
    print(message)
    print("=" * 60 + "\n")
    sys.exit(1)


# --------------------------------------------------------------------
# 1. Vérification de la clé API Gemini
# --------------------------------------------------------------------
if not os.environ.get("GEMINI_API_KEY"):
    erreur_fatale(
        "GEMINI_API_KEY n'est pas configuree.\n"
        "  1. Ajoutez GEMINI_API_KEY=votre_cle dans votre fichier .env\n"
        "  2. Obtenez une cle sur : https://aistudio.google.com/"
    )

if not os.path.isfile(CSV_PATH):
    erreur_fatale(
        f"Fichier CSV introuvable : {os.path.abspath(CSV_PATH)}\n"
        "  Lancez d'abord : python fusionner_csv.py"
    )

# --------------------------------------------------------------------
# 2. Chargement des données et de ChromaDB
# --------------------------------------------------------------------
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

print(f"Chargement du modele d'embedding ({EMBEDDING_MODEL})...")
try:
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
except Exception as e:
    erreur_fatale(f"Echec du chargement des embeddings HuggingFace :\n  {e}")

print("Chargement de la base vectorielle Chroma...")
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
    erreur_fatale(f"Echec du chargement de la base Chroma :\n  {e}")

retriever = vector_db.as_retriever(search_kwargs={"k": 5})

# --------------------------------------------------------------------
# 3. Initialisation du LLM Gemini via LangChain
# --------------------------------------------------------------------
print("Chargement du LLM Gemini...")
try:
    LLM = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=os.environ.get("GEMINI_API_KEY")
    )
except Exception as e:
    erreur_fatale(f"Echec de l'initialisation de Gemini :\n  {e}")

print("[OK] Chatbot pret.")


# --------------------------------------------------------------------
# 4. Recherche Hybride et RAG
# --------------------------------------------------------------------
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


PROMPT_TEMPLATE = """
Tu es un expert douanier marocain. Un transitaire te pose une question.

Étape 1 : Identifie la nature du produit dans la question (matière, usage, forme).
Étape 2 : Parmi les produits du contexte, trouve celui qui correspond le mieux.
Étape 3 : Si aucun produit du contexte ne correspond, dis-le clairement.
Étape 4 : Donne les 4 champs : Code SH, Désignation, Droit d'importation, Unité.

Contexte:
{context}

Question: {question}
"""


def repondre(question: str) -> dict:
    docs = recherche_hybride(question)
    context = "\n\n".join(doc.page_content for doc in docs)
    prompt = PROMPT_TEMPLATE.format(context=context or "(aucun produit trouvé)", question=question)
    response = LLM.invoke(prompt)
    return {
        "reponse": response.content,
        "nb_documents_utilises": len(docs),
    }


# --------------------------------------------------------------------
# 5. Routes Flask
# --------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory("static", "chat.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    question = (data.get("message") or "").strip()

    if not question:
        return jsonify({"erreur": "Message vide."}), 400

    try:
        resultat = repondre(question)
        return jsonify(resultat)
    except Exception as e:
        app.logger.exception("Erreur pendant la génération de la réponse")
        return jsonify({"erreur": f"Erreur serveur : {e}"}), 500


if __name__ == "__main__":
    app.run(debug=False, port=5000)
=======
# SutraChatbot
SutraChatbot est un assistant conversationnel intelligent basé sur une architecture RAG (Retrieval-Augmented Generation). Conçu pour optimiser la recherche et l'exploitation d'informations, il permet d'interroger efficacement des documents douaniers et réglementaires complexes afin de fournir des réponses précises et ciblées aux utilisateurs.
>>>>>>> ce4dce2d98dddb210a3d86d41aca9547446f8dee
