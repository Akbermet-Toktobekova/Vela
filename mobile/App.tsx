import React, { useState } from "react";
import { View, Text, TouchableOpacity, StyleSheet, StatusBar } from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { colors } from "./src/theme/colors";
import { ExpensesScreen } from "./src/screens/ExpensesScreen";
import { DashboardScreen } from "./src/screens/DashboardScreen";
import { ChatScreen } from "./src/screens/ChatScreen";
import { MicroLearningScreen } from "./src/screens/MicroLearningScreen";

type Tab = "expenses" | "dashboard" | "chat" | "learning";

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>("expenses");

  const renderScreen = () => {
    switch (activeTab) {
      case "expenses":
        return <ExpensesScreen />;
      case "dashboard":
        return <DashboardScreen onNavigateToChat={() => setActiveTab("chat")} />;
      case "chat":
        return <ChatScreen />;
      case "learning":
        return <MicroLearningScreen />;
    }
  };

  return (
    <SafeAreaProvider style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor={colors.background} />
      <View style={styles.screenContainer}>{renderScreen()}</View>

      {/* Bottom Navigation Bar */}
      <View style={styles.tabBar}>
        <TouchableOpacity
          style={[styles.tabItem, activeTab === "expenses" && styles.tabItemActive]}
          onPress={() => setActiveTab("expenses")}
        >
          <Text style={styles.tabIcon}>💳</Text>
          <Text style={[styles.tabLabel, activeTab === "expenses" && styles.tabLabelActive]}>
            Expenses
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tabItem, activeTab === "dashboard" && styles.tabItemActive]}
          onPress={() => setActiveTab("dashboard")}
        >
          <Text style={styles.tabIcon}>📊</Text>
          <Text style={[styles.tabLabel, activeTab === "dashboard" && styles.tabLabelActive]}>
            Overview
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tabItem, activeTab === "chat" && styles.tabItemActive]}
          onPress={() => setActiveTab("chat")}
        >
          <Text style={styles.tabIcon}>🤖</Text>
          <Text style={[styles.tabLabel, activeTab === "chat" && styles.tabLabelActive]}>
            AI Advisor
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tabItem, activeTab === "learning" && styles.tabItemActive]}
          onPress={() => setActiveTab("learning")}
        >
          <Text style={styles.tabIcon}>📚</Text>
          <Text style={[styles.tabLabel, activeTab === "learning" && styles.tabLabelActive]}>
            Daily Bite
          </Text>
        </TouchableOpacity>
      </View>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  screenContainer: {
    flex: 1,
  },
  tabBar: {
    flexDirection: "row",
    backgroundColor: colors.tabBarBg,
    borderTopWidth: 1,
    borderTopColor: colors.cardBorder,
    paddingVertical: 8,
    paddingBottom: 22,
    justifyContent: "space-around",
    alignItems: "center",
  },
  tabItem: {
    alignItems: "center",
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 8,
  },
  tabItemActive: {
    backgroundColor: "#1E293B",
  },
  tabIcon: {
    fontSize: 20,
    marginBottom: 2,
  },
  tabLabel: {
    fontSize: 11,
    fontWeight: "600",
    color: colors.textMuted,
  },
  tabLabelActive: {
    color: colors.primaryLight,
  },
});
