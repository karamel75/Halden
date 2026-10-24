"""Les six agents Halden, dans l'ordre du parcours acheteur."""
from .collections import AgentCollections
from .contrat import AgentContrat
from .garantie import AgentGarantie
from .livraison import AgentLivraison
from .relation import AgentRelation
from .ventes import AgentVentes

AGENTS = [AgentVentes(), AgentContrat(), AgentCollections(), AgentRelation(), AgentLivraison(), AgentGarantie()]
