import React, { useState } from "react";
import { View, Text, TouchableOpacity, StyleSheet, StatusBar, Platform } from "react-native";
import { SafeAreaProvider, useSafeAreaInsets } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { colors } from "./src/theme/colors";
import { UserProvider } from "./src/context/UserContext";
import { ExpensesScreen } from "./src/screens/ExpensesScreen";
import { DashboardScreen } from "./src/screens/DashboardScreen";
import { AdvisorScreen } from "./src/screens/AdvisorScreen";
import { LearnScreen } from "./src/screens/LearnScreen";

type Tab = "home" | "analytics" | "advisor" | "learn";

interface TabConfig {
  key: Tab;
  label: string;
  iconActive: keyof typeof Ionicons.glyphMap;
  iconInactive: keyof typeof Ionicons.glyphMap;
}

const tabs: TabConfig[] = [
  { key: "home", label: "Home", iconActive: "wallet", iconInactive: "wallet-outline" },
  { key: "analytics", label: "Analytics", iconActive: "pie-chart", iconInactive: "pie-chart-outline" },
  { key: "advisor", label: "AI Advisor", iconActive: "sparkles", iconInactive: "sparkles-outline" },
  { key: "learn", label: "Academy", iconActive: "school", iconInactive: "school-outline" },
];

function MainNavigation() {
  const [activeTab, setActiveTab] = useState<Tab>("home");
  const insets = useSafeAreaInsets();

  const renderScreen = () => {
    switch (activeTab) {
      case "home":
        return <ExpensesScreen />;
      case "analytics":
        return <DashboardScreen onNavigateToChat={() => setActiveTab("advisor")} />;
      case "advisor":
        return <AdvisorScreen />;
      case "learn":
        return <LearnScreen />;
    }
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />
      <View style={styles.screenContainer}>{renderScreen()}</View>

      {/* Revolut 10 Minimalist Vector Tab Bar */}
      <View style={[styles.tabBar, { paddingBottom: Math.max(insets.bottom, 12) }]}>
        {tabs.map((tab) => {
          const isActive = activeTab === tab.key;
          return (
            <TouchableOpacity
              key={tab.key}
              style={styles.tabItem}
              onPress={() => setActiveTab(tab.key)}
              activeOpacity={0.7}
            >
              <View style={[styles.iconWrapper, isActive && styles.iconWrapperActive]}>
                <Ionicons
                  name={isActive ? tab.iconActive : tab.iconInactive}
                  size={22}
                  color={isActive ? "#191C1F" : "#72777A"}
                />
              </View>
              <Text style={[styles.tabLabel, isActive && styles.tabLabelActive]}>
                {tab.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <UserProvider>
        <MainNavigation />
      </UserProvider>
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
    backgroundColor: "#FFFFFF",
    borderTopWidth: 1,
    borderTopColor: "#F0F1F4",
    paddingTop: 8,
    justifyContent: "space-around",
    alignItems: "center",
    ...Platform.select({
      ios: {
        shadowColor: "#000000",
        shadowOffset: { width: 0, height: -2 },
        shadowOpacity: 0.03,
        shadowRadius: 8,
      },
      android: {
        elevation: 8,
      },
    }),
  },
  tabItem: {
    alignItems: "center",
    justifyContent: "center",
    flex: 1,
  },
  iconWrapper: {
    width: 38,
    height: 28,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 14,
  },
  iconWrapperActive: {
    backgroundColor: "#F4F5F7",
  },
  tabLabel: {
    fontSize: 10,
    fontWeight: "500",
    color: "#72777A",
    marginTop: 2,
    letterSpacing: -0.1,
  },
  tabLabelActive: {
    color: "#191C1F",
    fontWeight: "700",
  },
});
