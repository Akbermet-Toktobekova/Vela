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
import { useUser } from '../context/UserContext';
import { FloatingAuroraBackground } from '../components/FloatingAuroraBackground';

type AgentRole = 'coordinator' | 'budget' | 'debt' | 'wealth';

interface ChatMessage {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  time: string;
  agentRole?: AgentRole;
  actionCard?: {
    type: 'budget_check' | 'debt_plan' | 'japan_fund';
    title: string;
    description: string;
    actionLabel: string;
  };
}

export const AdvisorScreen: React.FC = () => {
  const insets = useSafeAreaInsets();
  const { profile, totalSpent, needsSpent, wantsSpent, savingsSpent } = useUser();
  const [selectedAgent, setSelectedAgent] = useState<AgentRole>('coordinator');
  const [inputMessage, setInputMessage] = useState('');
  
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      sender: 'user',
      text: 'How is my spending looking this week? Can I afford that €180 dinner?',
      time: '9:41 AM',
    },
    {
      id: '2',
      sender: 'agent',
      agentRole: 'coordinator',
      text: `Hey ${profile.name || 'Sanatbek'}! You've logged €${totalSpent.toFixed(2)} this month. A €180 dinner would raise your Wants spending to €${(wantsSpent + 180).toFixed(2)}, leaving €${Math.max(0, (profile.monthlyLimit * 0.3) - (wantsSpent + 180)).toFixed(2)} in your 30% bucket.`,
      time: '9:41 AM',
      actionCard: {
        type: 'budget_check',
        title: 'Safe to Spend Simulation',
        description: 'Applying this dinner will keep you within your 50/30/20 target.',
        actionLabel: 'Log €180 Expense',
      },
    },
  ]);

  const quickPrompts = [
    '☕ Coffee & dining out this week?',
    '💳 How to eliminate credit card APR?',
    '📈 Optimize my 50/30/20 split',
    '🇯🇵 Japan trip savings pace',
  ];

  const handleSend = (textToSend?: string) => {
    const text = (textToSend || inputMessage).trim();
    if (!text) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: text,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputMessage('');

    // Dynamic intelligent reply based on active agent
    setTimeout(() => {
      let replyText = `I analyzed your €${profile.monthlyLimit} budget. Everything looks healthy!`;
      let actionCard: ChatMessage['actionCard'] = undefined;

      if (selectedAgent === 'budget') {
        replyText = `Your current 50/30/20 breakdown:\n• Needs: €${needsSpent.toFixed(2)}\n• Wants: €${wantsSpent.toFixed(2)}\n• Savings: €${savingsSpent.toFixed(2)}`;
      } else if (selectedAgent === 'debt') {
        replyText = `Focus on the 21.5% APR card! Directing an extra €50/mo saves €340 in interest over 12 months.`;
        actionCard = {
          type: 'debt_plan',
          title: 'Avalanche Payoff Boost',
          description: 'Allocate surplus €50 to Credit Card balance',
          actionLabel: 'Apply Avalanche Plan',
        };
      } else if (selectedAgent === 'wealth') {
        replyText = `Compounding €100/mo at 8% annual return yields €149,000+ over 30 years. Your discipline is paying off!`;
      }

      const agentMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'agent',
        agentRole: selectedAgent,
        text: replyText,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        actionCard: actionCard,
      };

      setMessages((prev) => [...prev, agentMsg]);
    }, 600);
  };

  return (
    <FloatingAuroraBackground theme="purple">
      <KeyboardAvoidingView 
        style={styles.keyboardView} 
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <View style={[styles.mainWrapper, { paddingTop: Math.max(insets.top, 14) }]}>
          {/* Header */}
          <View style={styles.header}>
            <View>
              <Text style={styles.headerTitle}>AI Financial Twin</Text>
              <Text style={styles.headerSubtitle}>Multi-Agent Intelligence</Text>
            </View>
            <View style={styles.onlineBadge}>
              <View style={styles.onlineDot} />
              <Text style={styles.onlineText}>Live</Text>
            </View>
          </View>

          {/* 4 Agent Roles Glass Switcher */}
          <View style={styles.agentTabsRow}>
            <TouchableOpacity 
              style={[styles.agentTab, selectedAgent === 'coordinator' && styles.agentTabActive]}
              onPress={() => setSelectedAgent('coordinator')}
            >
              <Ionicons name="sparkles" size={14} color={selectedAgent === 'coordinator' ? '#3D25F4' : '#FFFFFF'} />
              <Text style={[styles.agentTabText, selectedAgent === 'coordinator' && styles.agentTabTextActive]}>Coordinator</Text>
            </TouchableOpacity>

            <TouchableOpacity 
              style={[styles.agentTab, selectedAgent === 'budget' && styles.agentTabActive]}
              onPress={() => setSelectedAgent('budget')}
            >
              <Ionicons name="pie-chart" size={14} color={selectedAgent === 'budget' ? '#3D25F4' : '#FFFFFF'} />
              <Text style={[styles.agentTabText, selectedAgent === 'budget' && styles.agentTabTextActive]}>Budget</Text>
            </TouchableOpacity>

            <TouchableOpacity 
              style={[styles.agentTab, selectedAgent === 'debt' && styles.agentTabActive]}
              onPress={() => setSelectedAgent('debt')}
            >
              <Ionicons name="card" size={14} color={selectedAgent === 'debt' ? '#3D25F4' : '#FFFFFF'} />
              <Text style={[styles.agentTabText, selectedAgent === 'debt' && styles.agentTabTextActive]}>Debt</Text>
            </TouchableOpacity>

            <TouchableOpacity 
              style={[styles.agentTab, selectedAgent === 'wealth' && styles.agentTabActive]}
              onPress={() => setSelectedAgent('wealth')}
            >
              <Ionicons name="trending-up" size={14} color={selectedAgent === 'wealth' ? '#3D25F4' : '#FFFFFF'} />
              <Text style={[styles.agentTabText, selectedAgent === 'wealth' && styles.agentTabTextActive]}>Wealth</Text>
            </TouchableOpacity>
          </View>

          {/* Chat Messages */}
          <ScrollView 
            style={styles.chatScroll} 
            contentContainerStyle={styles.chatContent} 
            showsVerticalScrollIndicator={false}
          >
            {messages.map((msg) => (
              <View key={msg.id} style={[styles.messageRow, msg.sender === 'user' ? styles.userRow : styles.agentRow]}>
                {msg.sender === 'agent' && (
                  <View style={styles.agentAvatarCircle}>
                    <Ionicons name="sparkles" size={14} color="#7A22E8" />
                  </View>
                )}

                <View style={[styles.bubble, msg.sender === 'user' ? styles.userBubble : styles.agentBubble]}>
                  <Text style={[styles.bubbleText, msg.sender === 'user' ? styles.userText : styles.agentText]}>
                    {msg.text}
                  </Text>

                  {msg.actionCard && (
                    <View style={styles.actionCardEmbed}>
                      <Text style={styles.actionCardTitle}>{msg.actionCard.title}</Text>
                      <Text style={styles.actionCardDesc}>{msg.actionCard.description}</Text>
                      <TouchableOpacity style={styles.actionCardBtn} activeOpacity={0.8}>
                        <Text style={styles.actionCardBtnText}>{msg.actionCard.actionLabel}</Text>
                      </TouchableOpacity>
                    </View>
                  )}

                  <Text style={[styles.timeText, msg.sender === 'user' ? styles.userTime : styles.agentTime]}>
                    {msg.time}
                  </Text>
                </View>
              </View>
            ))}
          </ScrollView>

          {/* Quick Prompt Chips */}
          <View style={styles.chipsContainer}>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipsScroll}>
              {quickPrompts.map((prompt, idx) => (
                <TouchableOpacity 
                  key={idx} 
                  style={styles.chipPill}
                  onPress={() => handleSend(prompt)}
                  activeOpacity={0.75}
                >
                  <Text style={styles.chipText}>{prompt}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>

          {/* Input Bar */}
          <View style={styles.inputBarContainer}>
            <TouchableOpacity style={styles.attachBtn} activeOpacity={0.7}>
              <Ionicons name="add" size={22} color="#FFFFFF" />
            </TouchableOpacity>
            <TextInput
              style={styles.inputField}
              placeholder={`Ask ${selectedAgent}...`}
              placeholderTextColor="rgba(255,255,255,0.6)"
              value={inputMessage}
              onChangeText={setInputMessage}
              onSubmitEditing={() => handleSend()}
            />
            <TouchableOpacity style={styles.sendBtn} onPress={() => handleSend()} activeOpacity={0.8}>
              <Ionicons name="arrow-up" size={18} color="#2A169E" />
            </TouchableOpacity>
          </View>
        </View>
      </KeyboardAvoidingView>
    </FloatingAuroraBackground>
  );
};

const styles = StyleSheet.create({
  keyboardView: {
    flex: 1,
  },
  mainWrapper: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    marginBottom: 14,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: -0.4,
  },
  headerSubtitle: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.8)',
    marginTop: 2,
  },
  onlineBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.3)',
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
    color: '#FFFFFF',
  },
  agentTabsRow: {
    flexDirection: 'row',
    gap: 6,
    paddingHorizontal: 16,
    marginBottom: 12,
  },
  agentTab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    height: 36,
    backgroundColor: 'rgba(255,255,255,0.18)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.25)',
  },
  agentTabActive: {
    backgroundColor: '#FFFFFF',
    borderColor: '#FFFFFF',
  },
  agentTabText: {
    fontSize: 11,
    fontWeight: '600',
    color: 'rgba(255,255,255,0.9)',
  },
  agentTabTextActive: {
    color: '#2A169E',
    fontWeight: '700',
  },
  chatScroll: {
    flex: 1,
  },
  chatContent: {
    paddingHorizontal: 16,
    paddingBottom: 12,
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
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
  },
  bubble: {
    maxWidth: '82%',
    borderRadius: 18,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  userBubble: {
    backgroundColor: '#FFFFFF',
    borderBottomRightRadius: 4,
  },
  agentBubble: {
    backgroundColor: 'rgba(255, 255, 255, 0.92)',
    borderBottomLeftRadius: 4,
  },
  bubbleText: {
    fontSize: 14,
    lineHeight: 20,
  },
  userText: {
    color: '#111417',
    fontWeight: '600',
  },
  agentText: {
    color: '#111417',
  },
  timeText: {
    fontSize: 10,
    marginTop: 4,
    alignSelf: 'flex-end',
  },
  userTime: {
    color: '#72777A',
  },
  agentTime: {
    color: '#72777A',
  },
  actionCardEmbed: {
    backgroundColor: '#F4F6F9',
    borderRadius: 14,
    padding: 12,
    marginTop: 8,
    borderWidth: 1,
    borderColor: '#ECEEF2',
  },
  actionCardTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#111417',
    marginBottom: 2,
  },
  actionCardDesc: {
    fontSize: 11,
    color: '#646B73',
    marginBottom: 8,
  },
  actionCardBtn: {
    backgroundColor: '#111417',
    borderRadius: 10,
    paddingVertical: 8,
    alignItems: 'center',
  },
  actionCardBtnText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
  },
  chipsContainer: {
    marginBottom: 10,
  },
  chipsScroll: {
    paddingHorizontal: 16,
    gap: 8,
  },
  chipPill: {
    backgroundColor: 'rgba(255,255,255,0.22)',
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.3)',
  },
  chipText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  inputBarContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    backgroundColor: 'rgba(0,0,0,0.25)',
    gap: 8,
  },
  attachBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  inputField: {
    flex: 1,
    height: 42,
    backgroundColor: 'rgba(255,255,255,0.18)',
    borderRadius: 21,
    paddingHorizontal: 16,
    fontSize: 14,
    color: '#FFFFFF',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.25)',
  },
  sendBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
});
