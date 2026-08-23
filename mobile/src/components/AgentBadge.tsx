import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { AgentType } from "../types";
import { colors } from "../theme/colors";

interface Props {
  agent?: AgentType;
  name?: string;
}

export const AgentBadge: React.FC<Props> = ({ agent, name }) => {
  const getBadgeStyle = () => {
    switch (agent) {
      case "budget_specialist":
        return { bg: "#065F46", text: "#34D399", label: "📊 Budget Specialist" };
      case "debt_optimizer":
        return { bg: "#7F1D1D", text: "#FCA5A5", label: "💳 Debt Optimizer" };
      case "savings_coach":
        return { bg: "#1E3A8A", text: "#93C5FD", label: "🌱 Savings Coach" };
      case "financial_educator":
        return { bg: "#581C87", text: "#D8B4FE", label: "📚 Financial Educator" };
      default:
        return { bg: "#312E81", text: "#A5B4FC", label: "🤖 Vela Coordinator" };
    }
  };

  const badge = getBadgeStyle();

  return (
    <View style={[styles.badge, { backgroundColor: badge.bg }]}>
      <Text style={[styles.badgeText, { color: badge.text }]}>
        {name || badge.label}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    alignSelf: "flex-start",
    marginBottom: 6,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: "700",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
});
