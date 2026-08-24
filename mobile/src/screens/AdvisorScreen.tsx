import React, { useState } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ScrollView, 
  TouchableOpacity, 
  TextInput, 
  KeyboardAvoidingView, 
  Platform 
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../theme/colors';
import { useUser } from '../context/UserContext';

type AgentRole = 'vela' | 'budget' | 'debt' | 'savings';

interface ChatMessage {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  time: string;
  agentRole?: AgentRole;
  interactiveCard?: {
    title: string;
    target: string;
    progress: number;
    saved: string;
  };
}

export const AdvisorScreen: React.FC = () => {
  const insets = useSafeAreaInsets();
  const { profile, totalSpent, needsSpent, wantsSpent, savingsSpent } = useUser();
  const [selectedAgent, setSelectedAgent] = useState<AgentRole>('vela');
  const [inputMessage, setInputMessage] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      sender: 'user',
      text: 'How are my expenses looking this week? Should I hold off on that new jacket?',
      time: '9:41 AM',
    },
    {
      id: '2',
      sender: 'agent',
      agentRole: 'vela',
      text: `Hello ${profile.name}! You've spent €${totalSpent.toFixed(2)} so far this month. Buying a €250 jacket would increase your Wants spending to €${(wantsSpent + 250).toFixed(2)}.`,
      time: '9:41 AM',
      interactiveCard: {
        title: 'Trip to Japan Fund',
        target: 'Target: €3,000 by Oct',
        progress: 0.65,
        saved: '€1,950 saved (65%)',
      },
    },
  ]);

  const handleSend = () => {
    if (!inputMessage.trim()) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: inputMessage.trim(),
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage('');

    // Simulated AI response
    setTimeout(() => {
      let reply = `Based on your €${profile.monthlyLimit} budget, your savings rate is on track!`;
      if (selectedAgent === 'budget') {
        reply = `Budget breakdown: Needs €${needsSpent.toFixed(2)}, Wants €${wantsSpent.toFixed(2)}, Savings €${savingsSpent.toFixed(2)}.`;
      } else if (selectedAgent === 'debt') {
        reply = `I recommend paying down your 21.5% APR credit card balance first using the Avalanche method.`;
      }

      const agentMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'agent',
        agentRole: selectedAgent,
        text: reply,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, agentMsg]);
    }, 600);
  };

  return (
    <View style={[styles.mainWrapper, { paddingTop: Math.max(insets.top, 20) }]}>
      <KeyboardAvoidingView 
        style={styles.keyboardView} 
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.screenTitle}>AI Financial Twin</Text>
            <Text style={styles.screenSubtitle}>Multi-agent Advisory</Text>
          </View>
          <View style={styles.agentStatusBadge}>
            <View style={styles.onlineDot} />
            <Text style={styles.onlineText}>Online</Text>
          </View>
        </View>

        {/* 1. Revolut Agent Selector */}
        <View style={styles.agentSelector}>
          <TouchableOpacity 
            style={[styles.agentTab, selectedAgent === 'vela' && styles.agentTabActive]}
            onPress={() => setSelectedAgent('vela')}
          >
            <Ionicons name="sparkles" size={16} color={selectedAgent === 'vela' ? '#FFFFFF' : '#72777A'} />
            <Text style={[styles.agentTabText, selectedAgent === 'vela' && styles.agentTabTextActive]}>Coordinator</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.agentTab, selectedAgent === 'budget' && styles.agentTabActive]}
            onPress={() => setSelectedAgent('budget')}
          >
            <Ionicons name="pie-chart" size={16} color={selectedAgent === 'budget' ? '#FFFFFF' : '#72777A'} />
            <Text style={[styles.agentTabText, selectedAgent === 'budget' && styles.agentTabTextActive]}>Budget</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.agentTab, selectedAgent === 'debt' && styles.agentTabActive]}
            onPress={() => setSelectedAgent('debt')}
          >
            <Ionicons name="card" size={16} color={selectedAgent === 'debt' ? '#FFFFFF' : '#72777A'} />
            <Text style={[styles.agentTabText, selectedAgent === 'debt' && styles.agentTabTextActive]}>Debt</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.agentTab, selectedAgent === 'savings' && styles.agentTabActive]}
            onPress={() => setSelectedAgent('savings')}
          >
            <Ionicons name="shield-checkmark" size={16} color={selectedAgent === 'savings' ? '#FFFFFF' : '#72777A'} />
            <Text style={[styles.agentTabText, selectedAgent === 'savings' && styles.agentTabTextActive]}>Savings</Text>
          </TouchableOpacity>
        </View>

        {/* 2. Messages List */}
        <ScrollView style={styles.chatScroll} contentContainerStyle={styles.chatContent} showsVerticalScrollIndicator={false}>
          {messages.map((msg) => (
            <View key={msg.id} style={[styles.messageRow, msg.sender === 'user' ? styles.userRow : styles.agentRow]}>
              {msg.sender === 'agent' && (
                <View style={styles.agentAvatarCircle}>
                  <Ionicons name="sparkles" size={14} color="#0075EB" />
                </View>
              )}

              <View style={[styles.bubble, msg.sender === 'user' ? styles.userBubble : styles.agentBubble]}>
                <Text style={[styles.bubbleText, msg.sender === 'user' ? styles.userText : styles.agentText]}>
                  {msg.text}
                </Text>

                {msg.interactiveCard && (
                  <View style={styles.cardEmbed}>
                    <View style={styles.cardEmbedHeader}>
                      <Ionicons name="airplane" size={16} color="#0075EB" />
                      <Text style={styles.cardEmbedTitle}>{msg.interactiveCard.title}</Text>
                    </View>
                    <Text style={styles.cardEmbedSubtitle}>{msg.interactiveCard.target}</Text>
                    <View style={styles.embedBarBg}>
                      <View style={[styles.embedBarFill, { width: `${msg.interactiveCard.progress * 100}%` }]} />
                    </View>
                    <Text style={styles.cardEmbedFooter}>{msg.interactiveCard.saved}</Text>
                  </View>
                )}

                <Text style={[styles.timeText, msg.sender === 'user' ? styles.userTime : styles.agentTime]}>
                  {msg.time}
                </Text>
              </View>
            </View>
          ))}
        </ScrollView>

        {/* 3. Input Bar */}
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            placeholder={`Ask ${selectedAgent === 'vela' ? 'Vela' : selectedAgent} anything...`}
            placeholderTextColor="#9DA2A6"
            value={inputMessage}
            onChangeText={setInputMessage}
            onSubmitEditing={handleSend}
          />
          <TouchableOpacity style={styles.sendButton} onPress={handleSend} activeOpacity={0.8}>
            <Ionicons name="arrow-up" size={20} color="#FFFFFF" />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </View>
  );
};

const styles = StyleSheet.create({
  mainWrapper: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  keyboardView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    marginBottom: 14,
    paddingTop: 4,
  },
  screenTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: '#191C1F',
    letterSpacing: -0.5,
  },
  screenSubtitle: {
    fontSize: 12,
    color: '#72777A',
  },
  agentStatusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#E8F8EE',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
  },
  onlineDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#00C853',
  },
  onlineText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#00C853',
  },
  agentSelector: {
    flexDirection: 'row',
    gap: 6,
    paddingHorizontal: 20,
    marginBottom: 14,
  },
  agentTab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    height: 36,
    backgroundColor: '#F4F5F7',
    borderRadius: 12,
  },
  agentTabActive: {
    backgroundColor: '#191C1F',
  },
  agentTabText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#72777A',
  },
  agentTabTextActive: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  chatScroll: {
    flex: 1,
  },
  chatContent: {
    paddingHorizontal: 20,
    paddingBottom: 16,
  },
  messageRow: {
    flexDirection: 'row',
    marginBottom: 12,
    gap: 8,
  },
  userRow: {
    justifyContent: 'flex-end',
  },
  agentRow: {
    justifyContent: 'flex-start',
  },
  agentAvatarCircle: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#E5F2FF',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 4,
  },
  bubble: {
    maxWidth: '82%',
    borderRadius: 18,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  userBubble: {
    backgroundColor: '#0075EB',
    borderBottomRightRadius: 4,
  },
  agentBubble: {
    backgroundColor: '#F4F5F7',
    borderBottomLeftRadius: 4,
  },
  bubbleText: {
    fontSize: 14,
    lineHeight: 20,
  },
  userText: {
    color: '#FFFFFF',
    fontWeight: '500',
  },
  agentText: {
    color: '#191C1F',
  },
  timeText: {
    fontSize: 10,
    marginTop: 4,
    alignSelf: 'flex-end',
  },
  userTime: {
    color: 'rgba(255,255,255,0.7)',
  },
  agentTime: {
    color: '#9DA2A6',
  },
  cardEmbed: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 12,
    marginTop: 8,
    marginBottom: 4,
    borderWidth: 1,
    borderColor: '#EBECEF',
  },
  cardEmbedHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 2,
  },
  cardEmbedTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#191C1F',
  },
  cardEmbedSubtitle: {
    fontSize: 11,
    color: '#72777A',
    marginBottom: 8,
  },
  embedBarBg: {
    height: 4,
    backgroundColor: '#F4F5F7',
    borderRadius: 2,
    marginBottom: 6,
  },
  embedBarFill: {
    height: '100%',
    backgroundColor: '#0075EB',
    borderRadius: 2,
  },
  cardEmbedFooter: {
    fontSize: 11,
    fontWeight: '600',
    color: '#0075EB',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 10,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#F0F1F4',
    gap: 8,
  },
  input: {
    flex: 1,
    height: 44,
    backgroundColor: '#F4F5F7',
    borderRadius: 22,
    paddingHorizontal: 16,
    fontSize: 14,
    color: '#191C1F',
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#191C1F',
    alignItems: 'center',
    justifyContent: 'center',
  },
});
