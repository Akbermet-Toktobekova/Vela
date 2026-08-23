import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  SafeAreaView,
} from "react-native";
import { ChatMessage } from "../types";
import { colors } from "../theme/colors";
import { AgentBadge } from "../components/AgentBadge";
import { api } from "../services/api";

const INITIAL_MESSAGES: ChatMessage[] = [
  {
    id: "1",
    role: "assistant",
    agent: "coordinator",
    agentName: "Vela Coordinator",
    content: "👋 Hello! I am **Vela**, your Personal Multi-Agent Financial Advisor.\n\nI continuously coordinate between your **Budget Specialist**, **Debt Optimizer**, and **Savings Coach** to help you achieve financial independence. How can we help you today?",
    actionItems: [
      "Ask: 'Analyze my current budget balance'",
      "Ask: 'What is my fastest debt payoff plan?'",
      "Ask: 'How can I reach my savings goals faster?'",
    ],
    timestamp: "Just now",
  },
];

const SUGGESTIONS = [
  "📊 Optimize my budget",
  "💳 Best debt strategy",
  "🌱 Project savings growth",
  "💡 Cut discretionary costs",
];

export const ChatScreen: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>(INITIAL_MESSAGES);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async (textToSend?: string) => {
    const messageText = textToSend || input;
    if (!messageText.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: messageText.trim(),
      timestamp: "Just now",
    };

    const newHistory = [...messages, userMessage];
    setMessages(newHistory);
    setInput("");
    setLoading(true);

    try {
      const response = await api.sendChatMessage(messageText, newHistory);
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.content || "I have analyzed your situation.",
        agent: response.agent || "coordinator",
        agentName: response.agentName || "Vela Advisor",
        actionItems: response.actionItems || [],
        metrics: response.metrics,
        timestamp: "Just now",
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch {
      // Handled in api client
    } finally {
      setLoading(false);
    }
  };

  const renderMessageItem = ({ item }: { item: ChatMessage }) => {
    const isUser = item.role === "user";

    return (
      <View
        style={[
          styles.messageContainer,
          isUser ? styles.userContainer : styles.assistantContainer,
        ]}
      >
        {!isUser && <AgentBadge agent={item.agent} name={item.agentName} />}
        <View
          style={[
            styles.bubble,
            isUser ? styles.userBubble : styles.assistantBubble,
          ]}
        >
          <Text style={[styles.messageText, isUser && styles.userMessageText]}>
            {item.content}
          </Text>

          {item.actionItems && item.actionItems.length > 0 && (
            <View style={styles.actionItemsContainer}>
              <Text style={styles.actionItemsHeader}>🎯 Recommended Actions:</Text>
              {item.actionItems.map((action, idx) => (
                <View key={idx} style={styles.actionRow}>
                  <Text style={styles.actionBullet}>•</Text>
                  <Text style={styles.actionText}>{action}</Text>
                </View>
              ))}
            </View>
          )}
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        style={styles.container}
        keyboardVerticalOffset={80}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Vela Multi-Agent Advisor</Text>
          <Text style={styles.headerSubtitle}>
            Coordinating Budget, Debt & Savings Specialists
          </Text>
        </View>

        {/* Message Feed */}
        <FlatList
          data={messages}
          keyExtractor={(item) => item.id}
          renderItem={renderMessageItem}
          contentContainerStyle={styles.messageList}
          showsVerticalScrollIndicator={false}
        />

        {/* Quick Suggestion Pills */}
        <View style={styles.suggestionsContainer}>
          <FlatList
            horizontal
            data={SUGGESTIONS}
            keyExtractor={(item) => item}
            showsHorizontalScrollIndicator={false}
            renderItem={({ item }) => (
              <TouchableOpacity
                style={styles.suggestionPill}
                onPress={() => sendMessage(item)}
                disabled={loading}
              >
                <Text style={styles.suggestionText}>{item}</Text>
              </TouchableOpacity>
            )}
          />
        </View>

        {/* Input Bar */}
        <View style={styles.inputBar}>
          <TextInput
            style={styles.textInput}
            value={input}
            onChangeText={setInput}
            placeholder="Ask about your budget, debts, or goals..."
            placeholderTextColor={colors.textMuted}
            editable={!loading}
          />
          <TouchableOpacity
            style={[styles.sendButton, loading && styles.sendButtonDisabled]}
            onPress={() => sendMessage()}
            disabled={loading || !input.trim()}
          >
            {loading ? (
              <ActivityIndicator color="#FFFFFF" size="small" />
            ) : (
              <Text style={styles.sendButtonText}>Send</Text>
            )}
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
    backgroundColor: colors.cardBackground,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  headerSubtitle: {
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: 2,
  },
  messageList: {
    padding: 16,
    paddingBottom: 20,
  },
  messageContainer: {
    marginBottom: 16,
    maxWidth: "88%",
  },
  userContainer: {
    alignSelf: "flex-end",
  },
  assistantContainer: {
    alignSelf: "flex-start",
  },
  bubble: {
    padding: 14,
    borderRadius: 16,
  },
  userBubble: {
    backgroundColor: colors.userBubble,
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    backgroundColor: colors.agentBubble,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    borderBottomLeftRadius: 4,
  },
  messageText: {
    fontSize: 14,
    lineHeight: 21,
    color: colors.textPrimary,
  },
  userMessageText: {
    color: "#FFFFFF",
  },
  actionItemsContainer: {
    marginTop: 12,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: colors.cardBorder,
  },
  actionItemsHeader: {
    fontSize: 12,
    fontWeight: "700",
    color: colors.accent,
    marginBottom: 6,
  },
  actionRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    marginBottom: 4,
  },
  actionBullet: {
    color: colors.accent,
    marginRight: 6,
    fontSize: 14,
  },
  actionText: {
    fontSize: 13,
    color: colors.textSecondary,
    flex: 1,
    lineHeight: 18,
  },
  suggestionsContainer: {
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  suggestionPill: {
    backgroundColor: colors.cardBackground,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 20,
    marginHorizontal: 4,
  },
  suggestionText: {
    color: colors.primaryLight,
    fontSize: 13,
    fontWeight: "600",
  },
  inputBar: {
    flexDirection: "row",
    padding: 12,
    borderTopWidth: 1,
    borderTopColor: colors.cardBorder,
    backgroundColor: colors.cardBackground,
    alignItems: "center",
  },
  textInput: {
    flex: 1,
    backgroundColor: colors.background,
    color: colors.textPrimary,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    fontSize: 14,
  },
  sendButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: 18,
    paddingVertical: 10,
    borderRadius: 24,
    marginLeft: 8,
  },
  sendButtonDisabled: {
    opacity: 0.6,
  },
  sendButtonText: {
    color: "#FFFFFF",
    fontWeight: "700",
    fontSize: 14,
  },
});
