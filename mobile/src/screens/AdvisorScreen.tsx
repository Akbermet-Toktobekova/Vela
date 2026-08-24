import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, TextInput, SafeAreaView, KeyboardAvoidingView, Platform, Image } from 'react-native';
import { Ionicons, Feather, MaterialCommunityIcons } from '@expo/vector-icons';

const agents = [
  { id: 'vela', name: 'Vela', icon: 'sparkles', provider: Ionicons },
  { id: 'budget', name: 'Budget', icon: 'pie-chart', provider: Feather },
  { id: 'debt', name: 'Debt', icon: 'credit-card', provider: Feather },
  { id: 'savings', name: 'Savings', icon: 'shield-check', provider: MaterialCommunityIcons },
];

const messages = [
  { id: '1', type: 'system', text: 'Today, 10:41 AM' },
  { id: '2', type: 'received', text: 'Hi there! I noticed your grocery spending is up 15% this month. Want to review your budget?', time: '10:41 AM' },
  { id: '3', type: 'sent', text: 'Yes, let\'s look at it.', time: '10:42 AM' },
  { id: '4', type: 'received', text: 'Great. Here is a breakdown of your recent transactions.', time: '10:42 AM', hasCard: true },
];

const quickPrompts = ['Reduce bills', 'Set saving goal', 'Analyze last week'];

export default function AdvisorScreen() {
  const [activeAgent, setActiveAgent] = useState('vela');
  const [inputText, setInputText] = useState('');

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.agentScroll}>
          {agents.map((agent) => {
            const Icon = agent.provider;
            const isActive = activeAgent === agent.id;
            return (
              <TouchableOpacity
                key={agent.id}
                style={[styles.agentPill, isActive && styles.agentPillActive]}
                onPress={() => setActiveAgent(agent.id)}
              >
                <Icon name={agent.icon as any} size={16} color={isActive ? '#FFFFFF' : '#8A8D93'} />
                <Text style={[styles.agentText, isActive && styles.agentTextActive]}>{agent.name}</Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </View>

      <ScrollView style={styles.chatContainer} contentContainerStyle={styles.chatContent}>
        {messages.map((msg) => {
          if (msg.type === 'system') {
            return <Text key={msg.id} style={styles.systemText}>{msg.text}</Text>;
          }
          const isSent = msg.type === 'sent';
          return (
            <View key={msg.id} style={[styles.messageWrapper, isSent ? styles.messageWrapperSent : styles.messageWrapperReceived]}>
              <View style={[styles.bubble, isSent ? styles.bubbleSent : styles.bubbleReceived]}>
                <Text style={[styles.bubbleText, isSent ? styles.bubbleTextSent : styles.bubbleTextReceived]}>{msg.text}</Text>
                {msg.hasCard && (
                  <View style={styles.interactiveCard}>
                    <View style={styles.cardHeader}>
                      <View style={styles.cardIcon}>
                        <Feather name="shopping-cart" size={16} color="#007AFF" />
                      </View>
                      <Text style={styles.cardTitle}>Groceries</Text>
                      <Text style={styles.cardAmount}>-$145.20</Text>
                    </View>
                    <TouchableOpacity style={styles.cardButton}>
                      <Text style={styles.cardButtonText}>View details</Text>
                    </TouchableOpacity>
                  </View>
                )}
              </View>
              <Text style={styles.timeText}>{msg.time}</Text>
            </View>
          );
        })}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.promptsContainer} contentContainerStyle={styles.promptsContent}>
          {quickPrompts.map((prompt, index) => (
            <TouchableOpacity key={index} style={styles.promptChip}>
              <Text style={styles.promptText}>{prompt}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </ScrollView>

      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <View style={styles.inputContainer}>
          <TouchableOpacity style={styles.attachButton}>
            <Feather name="plus" size={24} color="#8A8D93" />
          </TouchableOpacity>
          <TextInput
            style={styles.input}
            placeholder="Ask anything..."
            placeholderTextColor="#8A8D93"
            value={inputText}
            onChangeText={setInputText}
          />
          <TouchableOpacity style={[styles.sendButton, inputText.trim() ? styles.sendButtonActive : null]}>
            <Feather name="arrow-up" size={20} color="#FFFFFF" />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8F9FA' },
  header: { paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: '#EAECEF', backgroundColor: '#FFFFFF' },
  agentScroll: { paddingHorizontal: 16, gap: 12 },
  agentPill: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#F3F4F6', paddingVertical: 8, paddingHorizontal: 16, borderRadius: 20, gap: 6 },
  agentPillActive: { backgroundColor: '#191C1F' },
  agentText: { fontSize: 14, fontWeight: '600', color: '#8A8D93' },
  agentTextActive: { color: '#FFFFFF' },
  chatContainer: { flex: 1 },
  chatContent: { padding: 16, gap: 16 },
  systemText: { textAlign: 'center', fontSize: 12, color: '#8A8D93', marginVertical: 8 },
  messageWrapper: { maxWidth: '80%' },
  messageWrapperSent: { alignSelf: 'flex-end', alignItems: 'flex-end' },
  messageWrapperReceived: { alignSelf: 'flex-start', alignItems: 'flex-start' },
  bubble: { padding: 12, borderRadius: 18, marginBottom: 4 },
  bubbleSent: { backgroundColor: '#191C1F', borderBottomRightRadius: 4 },
  bubbleReceived: { backgroundColor: '#FFFFFF', borderBottomLeftRadius: 4, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 2, elevation: 1 },
  bubbleText: { fontSize: 15, lineHeight: 22 },
  bubbleTextSent: { color: '#FFFFFF' },
  bubbleTextReceived: { color: '#191C1F' },
  interactiveCard: { marginTop: 12, backgroundColor: '#F8F9FA', borderRadius: 12, padding: 12, borderWidth: 1, borderColor: '#EAECEF' },
  cardHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  cardIcon: { width: 32, height: 32, borderRadius: 16, backgroundColor: '#E5F1FF', alignItems: 'center', justifyContent: 'center', marginRight: 10 },
  cardTitle: { flex: 1, fontSize: 14, fontWeight: '600', color: '#191C1F' },
  cardAmount: { fontSize: 14, fontWeight: '600', color: '#191C1F' },
  cardButton: { backgroundColor: '#FFFFFF', paddingVertical: 8, borderRadius: 8, alignItems: 'center', borderWidth: 1, borderColor: '#EAECEF' },
  cardButtonText: { fontSize: 13, fontWeight: '600', color: '#191C1F' },
  timeText: { fontSize: 11, color: '#8A8D93', marginTop: 2, paddingHorizontal: 4 },
  promptsContainer: { marginTop: 12, marginBottom: 8 },
  promptsContent: { gap: 8, paddingRight: 32 },
  promptChip: { backgroundColor: '#FFFFFF', paddingVertical: 10, paddingHorizontal: 16, borderRadius: 20, borderWidth: 1, borderColor: '#EAECEF', shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 1, elevation: 1 },
  promptText: { fontSize: 14, fontWeight: '500', color: '#191C1F' },
  inputContainer: { flexDirection: 'row', alignItems: 'center', padding: 12, paddingBottom: Platform.OS === 'ios' ? 24 : 12, backgroundColor: '#FFFFFF', borderTopWidth: 1, borderTopColor: '#EAECEF' },
  attachButton: { padding: 8 },
  input: { flex: 1, backgroundColor: '#F3F4F6', borderRadius: 20, paddingHorizontal: 16, paddingVertical: 10, fontSize: 15, color: '#191C1F', maxHeight: 100, marginHorizontal: 8 },
  sendButton: { width: 36, height: 36, borderRadius: 18, backgroundColor: '#D1D5DB', alignItems: 'center', justifyContent: 'center' },
  sendButtonActive: { backgroundColor: '#007AFF' },
});
