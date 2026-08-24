import React, { useState } from 'react';
import {
  SafeAreaView,
  ScrollView,
  View,
  Text,
  TouchableOpacity,
  TextInput,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
// @ts-ignore
import { colors } from '../theme/colors';

const AGENTS = [
  { id: 'vela', label: 'Vela', emoji: '🤖', active: true },
  { id: 'budget', label: 'Budget', emoji: '📊', active: false },
  { id: 'debt', label: 'Debt', emoji: '💳', active: false },
  { id: 'savings', label: 'Savings', emoji: '🌱', active: false },
];

const PROMPTS = [
  '📈 Save for Japan faster?',
  '☕ Coffee spending?',
  '📊 Budget analysis',
];

export const AdvisorScreen: React.FC = () => {
  const [inputText, setInputText] = useState('');

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        {/* Agent Selector */}
        <View style={styles.agentSelectorContainer}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.agentSelector}>
            {AGENTS.map((agent) => (
              <TouchableOpacity key={agent.id} style={styles.agentItem}>
                <View style={[styles.agentCircle, agent.active ? styles.agentCircleActive : styles.agentCircleInactive]}>
                  <Text style={styles.agentEmoji}>{agent.emoji}</Text>
                </View>
                <Text style={[styles.agentLabel, agent.active ? styles.agentLabelActive : styles.agentLabelInactive]}>
                  {agent.label}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        {/* Chat Area */}
        <ScrollView style={styles.chatArea} contentContainerStyle={styles.chatContent}>
          <View style={styles.timestampContainer}>
            <View style={styles.timestampPill}>
              <Text style={styles.timestampText}>Today, 9:41 AM</Text>
            </View>
          </View>

          <View style={styles.userMessageContainer}>
            <View style={styles.userBubble}>
              <Text style={styles.userMessageText}>
                How are my expenses looking this week? Should I hold off on that new jacket?
              </Text>
            </View>
          </View>

          <View style={styles.agentMessageContainer}>
            <View style={styles.agentAvatarContainer}>
              <Text style={styles.agentAvatarEmoji}>🤖</Text>
            </View>
            <View style={styles.agentBubble}>
              <Text style={styles.agentMessageText}>
                You're doing well! You're $120 under budget for dining out this week. However, buying the $250 jacket would put you slightly behind your monthly savings goal for Japan.
              </Text>
            </View>
          </View>

          {/* Embedded Card */}
          <View style={styles.cardContainer}>
            <View style={styles.cardHeader}>
              <Text style={styles.cardEmoji}>✈️</Text>
              <Text style={styles.cardTitle}>Japan Trip Fund</Text>
            </View>
            <View style={styles.progressBarBackground}>
              <View style={[styles.progressBarFill, { width: '65%' }]} />
            </View>
            <Text style={styles.progressText}>65% funded</Text>
            
            <View style={styles.cardActions}>
              <TouchableOpacity style={styles.cardButtonSecondary}>
                <Text style={styles.cardButtonTextSecondary}>Buy Jacket</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.cardButtonPrimary}>
                <Text style={styles.cardButtonTextPrimary}>Skip & Save</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Quick Prompts */}
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.promptsContainer}>
            {PROMPTS.map((prompt, index) => (
              <TouchableOpacity key={index} style={styles.promptChip}>
                <Text style={styles.promptText}>{prompt}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </ScrollView>

        {/* Input Bar */}
        <View style={styles.inputContainer}>
          <View style={styles.inputBackground}>
            <TouchableOpacity style={styles.addButton}>
              <Text style={styles.addIcon}>➕</Text>
            </TouchableOpacity>
            <TextInput
              style={styles.textInput}
              placeholder="Ask Vela anything..."
              placeholderTextColor="#45464C"
              value={inputText}
              onChangeText={setInputText}
            />
            <TouchableOpacity style={styles.sendButton}>
              <Text style={styles.sendIcon}>⬆️</Text>
            </TouchableOpacity>
          </View>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  agentSelectorContainer: {
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#C6C6CD',
    paddingVertical: 12,
  },
  agentSelector: {
    paddingHorizontal: 16,
    alignItems: 'center',
    gap: 20,
  },
  agentItem: {
    alignItems: 'center',
    marginRight: 20,
  },
  agentCircle: {
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  agentCircleActive: {
    backgroundColor: '#0058BC',
  },
  agentCircleInactive: {
    backgroundColor: '#F8F9FA',
    borderWidth: 1,
    borderColor: '#C6C6CD',
  },
  agentEmoji: {
    fontSize: 24,
  },
  agentLabel: {
    fontSize: 12,
  },
  agentLabelActive: {
    fontWeight: 'bold',
    color: '#191C1D',
  },
  agentLabelInactive: {
    color: '#45464C',
  },
  chatArea: {
    flex: 1,
  },
  chatContent: {
    padding: 16,
    paddingBottom: 24,
  },
  timestampContainer: {
    alignItems: 'center',
    marginVertical: 16,
  },
  timestampPill: {
    backgroundColor: '#F8F9FA',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  timestampText: {
    fontSize: 12,
    color: '#45464C',
    fontWeight: '500',
  },
  userMessageContainer: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginBottom: 16,
  },
  userBubble: {
    backgroundColor: '#0058BC',
    maxWidth: '80%',
    padding: 12,
    borderRadius: 16,
    borderTopRightRadius: 4,
  },
  userMessageText: {
    color: '#FFFFFF',
    fontSize: 16,
    lineHeight: 22,
  },
  agentMessageContainer: {
    flexDirection: 'row',
    marginBottom: 16,
    alignItems: 'flex-end',
  },
  agentAvatarContainer: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#F8F9FA',
    borderWidth: 1,
    borderColor: '#C6C6CD',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
  },
  agentAvatarEmoji: {
    fontSize: 14,
  },
  agentBubble: {
    backgroundColor: '#F8F9FA',
    borderWidth: 1,
    borderColor: '#C6C6CD',
    maxWidth: '80%',
    padding: 12,
    borderRadius: 16,
    borderTopLeftRadius: 4,
  },
  agentMessageText: {
    color: '#191C1D',
    fontSize: 16,
    lineHeight: 22,
  },
  cardContainer: {
    backgroundColor: '#F8F9FA',
    borderWidth: 1,
    borderColor: '#C6C6CD',
    borderRadius: 16,
    padding: 16,
    marginLeft: 36, // Align with agent message
    maxWidth: '80%',
    marginBottom: 24,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  cardEmoji: {
    fontSize: 20,
    marginRight: 8,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#191C1D',
  },
  progressBarBackground: {
    height: 8,
    backgroundColor: '#E7E8E9',
    borderRadius: 4,
    marginBottom: 8,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: '#0058BC',
    borderRadius: 4,
  },
  progressText: {
    fontSize: 12,
    color: '#45464C',
    marginBottom: 16,
  },
  cardActions: {
    flexDirection: 'row',
    gap: 8,
  },
  cardButtonSecondary: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#C6C6CD',
    backgroundColor: '#FFFFFF',
  },
  cardButtonTextSecondary: {
    color: '#45464C',
    fontWeight: '600',
    fontSize: 14,
  },
  cardButtonPrimary: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: 8,
    backgroundColor: '#0058BC',
  },
  cardButtonTextPrimary: {
    color: '#FFFFFF',
    fontWeight: '600',
    fontSize: 14,
  },
  promptsContainer: {
    flexDirection: 'row',
    marginBottom: 16,
    marginLeft: 36,
  },
  promptChip: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#0058BC',
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginRight: 8,
  },
  promptText: {
    color: '#0058BC',
    fontSize: 14,
    fontWeight: '500',
  },
  inputContainer: {
    padding: 12,
    backgroundColor: '#FFFFFF',
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: '#C6C6CD',
  },
  inputBackground: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F8F9FA',
    borderWidth: 1,
    borderColor: '#C6C6CD',
    borderRadius: 24,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  addButton: {
    padding: 4,
    marginRight: 8,
  },
  addIcon: {
    fontSize: 20,
  },
  textInput: {
    flex: 1,
    fontSize: 16,
    color: '#191C1D',
    maxHeight: 100,
    paddingTop: 0,
    paddingBottom: 0,
  },
  sendButton: {
    backgroundColor: '#0058BC',
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
  },
  sendIcon: {
    fontSize: 16,
    color: '#FFFFFF',
  },
});
