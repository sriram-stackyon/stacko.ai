"""LangGraph pipeline wiring for the claims workflow."""

from langgraph.graph import END, START, StateGraph

from app.agents.nodes.adjudication import adjudication_node
from app.agents.nodes.communication import communication_node
from app.agents.nodes.damage_assessment import damage_assessment_node
from app.agents.nodes.fraud_detection import fraud_detection_node
from app.agents.nodes.intake import intake_node
from app.agents.nodes.policy_verification import policy_verification_node
from app.agents.state import ClaimsState


graph = StateGraph(ClaimsState)

graph.add_node("intake", intake_node)
graph.add_node("policy_verification", policy_verification_node)
graph.add_node("damage_assessment", damage_assessment_node)
graph.add_node("fraud_detection", fraud_detection_node)
graph.add_node("adjudication", adjudication_node)
graph.add_node("communication", communication_node)

graph.add_edge(START, "intake")
graph.add_edge("intake", "policy_verification")
graph.add_edge("policy_verification", "damage_assessment")
graph.add_edge("damage_assessment", "fraud_detection")
graph.add_edge("fraud_detection", "adjudication")
graph.add_edge("adjudication", "communication")
graph.add_edge("communication", END)

pipeline = graph.compile()
