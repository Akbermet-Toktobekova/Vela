import React, { useState } from "react";
import { View, Text, TouchableOpacity, StyleSheet, StatusBar } from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { colors } from "./src/theme/colors";
import { ExpensesScreen } from "./src/screens/ExpensesScreen";
import { DashboardScreen } from "./src/screens/DashboardScreen";
import { AdvisorScreen } from "./src/screens/AdvisorScreen";
import { LearnScreen } from "./src/screens/LearnScreen";

type Tab = "expenses" | "dashboard" | "advisor" | "learn";

interface TabConfig {
  key: Tab;
  label: string;
  icon: string;
}

const tabs: TabConfig[] = [
  { key: "expenses", label: "Expenses", icon: "💳" },
  { key: "dashboard", label: "Dashboard", icon: "📊" },
  { key: "advisor", label: "Advisor", icon: "💬" },
  { key: "learn", label: "Learn", icon: "📚" },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>("expenses");

  const renderScreen = () => {
    switch (activeTab) {
      case "expenses":
        return <ExpensesScreen />;
      case "dashboard":
        return <DashboardScreen onNavigateToChat={() => setActiveTab("advisor")} />;
      case "advisor":
        return <AdvisorScreen />;
      case "learn":
        return <LearnScreen />;
    }
  };

  return (
    <SafeAreaProvider style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />
      <View style={styles.screenContainer}>{renderScreen()}</View>

      {/* Bottom Tab Bar — Apple HIG Style */}
      <View style={styles.tabBar}>
        {tabs.map((tab) => {
          const isActive = activeTab === tab.key;
          return (
            <TouchableOpacity
              key={tab.key}
              style={[styles.tabItem, isActive && styles.tabItemActive]}
              onPress={() => setActiveTab(tab.key)}
              activeOpacity={0.7}
            >
              <Text style={styles.tabIcon}>{tab.icon}</Text>
              <Text style={[styles.tabLabel, isActive && styles.tabLabelActive]}>
                {tab.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#FFFFFF",
  },
  screenContainer: {
    flex: 1,
  },
  tabBar: {
    flexDirection: "row",
    backgroundColor: "rgba(248, 249, 250, 0.95)",
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: "#C6C6CD",
    paddingVertical: 6,
    paddingBottom: 28,
    justifyContent: "space-around",
    alignItems: "center",
  },
  tabItem: {
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 999,
  },
  tabItemActive: {
    backgroundColor: "rgba(0, 88, 188, 0.1)",
  },
  tabIcon: {
    fontSize: 22,
    marginBottom: 2,
  },
  tabLabel: {
    fontSize: 10,
    fontWeight: "500",
    color: "#76777D",
    letterSpacing: 0.2,
  },
  tabLabelActive: {
    color: "#0058BC",
    fontWeight: "700",
  },
});
