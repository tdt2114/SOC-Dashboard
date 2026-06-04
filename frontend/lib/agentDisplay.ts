import type { AgentListItem, AlertListItem } from "@/lib/types";

type AgentIdentity = AgentListItem | AlertListItem["agent"];

export function getAgentDisplayName(agent: AgentIdentity) {
  if (agent.id === "000") {
    return "Wazuh Manager";
  }

  return agent.name || agent.id || "N/A";
}
