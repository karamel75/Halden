"""Les six agents Halden, dans l'ordre du parcours acheteur."""
from .collections import AgentCollections
from .contrat import AgentContrat
from .garantie import AgentGarantie
from .livraison import AgentLivraison
from .relation import AgentRelation
from .ventes import AgentVentes

AGENTS = [AgentVentes(), AgentContrat(), AgentCollections(), AgentRelation(), AgentLivraison(), AgentGarantie()]

PILOTE = (AgentCollections, AgentRelation)   # un agent (encaissements) + sa boîte de réception


def agents_actifs(db) -> list:
    """Périmètre PILOTE (par défaut) : encaissements à Dubaï. VISION : les six agents."""
    if str(db.param("perimetre", "PILOTE")).upper() == "VISION":
        return AGENTS
    return [a for a in AGENTS if isinstance(a, PILOTE)]
