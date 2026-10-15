"""
Module de gestion de l'historique et du nettoyage des réponses.
"""

from langchain_core.messages import HumanMessage, AIMessage


def format_history(history_list: list, max_messages: int = 6) -> list:
    """Conserve les N derniers messages et les transforme en objets LangChain."""
    formatted_history = []
    recent_history = history_list[-max_messages:] if history_list else []

    for msg in recent_history:
        role = msg.get("role")
        content = msg.get("content", "").strip()

        if role == "user" and content:
            formatted_history.append(HumanMessage(content=content))
        elif role == "assistant" and content:
            formatted_history.append(AIMessage(content=content))

    return formatted_history


def clean_response_text(raw_content) -> str:
    """Extrait le texte brut et retire les structures JSON ou préfixes."""
    if isinstance(raw_content, list) and len(raw_content) > 0:
        if isinstance(raw_content[0], dict):
            texte_clean = raw_content[0].get("text", "")
        else:
            texte_clean = str(raw_content[0])
    else:
        texte_clean = str(raw_content)

    texte_clean = texte_clean.strip()

    if texte_clean.startswith("Réponse :"):
        texte_clean = texte_clean.replace("Réponse :", "").strip()

    return texte_clean