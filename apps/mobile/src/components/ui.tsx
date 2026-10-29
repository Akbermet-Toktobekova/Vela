import React from 'react';
import { ActivityIndicator, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { radius, space, touchTarget, type, usePalette } from '../theme';

export function Copy({children, variant = 'body', muted = false, color}: React.PropsWithChildren<{variant?: 'body' | 'title' | 'hero' | 'money' | 'small'; muted?: boolean; color?: string}>) {
  const p = usePalette();
  return <Text selectable accessibilityRole={variant === 'hero' || variant === 'title' ? 'header' : undefined} style={{color: color ?? (muted ? p.muted : p.text), fontFamily: variant === 'body' || variant === 'small' ? 'Manrope_400Regular' : 'Manrope_600SemiBold', fontSize: type[variant], lineHeight: Math.round(type[variant] * 1.32), fontVariant: ['tabular-nums']}}>{children}</Text>;
}
export function Screen({children, title, eyebrow, right}: React.PropsWithChildren<{title: string; eyebrow?: string; right?: React.ReactNode}>) {
  const p = usePalette();
  return <SafeAreaView edges={['top', 'left', 'right']} style={{flex: 1, backgroundColor: p.background}}><KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{flex: 1}}><ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={styles.page}>
    <View style={{flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: space.sm}}>
      <View style={{flex: 1, gap: 2}}>{!!eyebrow && <Copy variant="small" muted>{eyebrow}</Copy>}<Copy variant="hero">{title}</Copy></View>
      {right}
    </View>{children}
  </ScrollView></KeyboardAvoidingView></SafeAreaView>;
}
export function Card({children, soft = false}: React.PropsWithChildren<{soft?: boolean}>) {
  const p = usePalette();
  return <View style={[styles.card, {backgroundColor: soft ? p.soft : p.surface, borderColor: p.border}]}>{children}</View>;
}
export function Button({label, onPress, secondary = false, disabled = false, small = false, loading = false, destructive = false}: {label: string; onPress: () => void; secondary?: boolean; disabled?: boolean; small?: boolean; loading?: boolean; destructive?: boolean}) {
  const p = usePalette();
  return <Pressable accessibilityRole="button" accessibilityLabel={label} accessibilityState={{disabled: disabled || loading, busy: loading}} disabled={disabled || loading} onPress={onPress}
    style={({pressed}) => [styles.button, small && styles.smallButton, {backgroundColor: secondary ? p.surface : destructive ? p.negative : p.accent, borderColor: secondary ? p.border : destructive ? p.negative : p.accent, opacity: disabled || loading ? 0.5 : pressed ? 0.82 : 1}]}>
    {loading && <ActivityIndicator accessibilityLabel="Working" color={secondary ? p.text : p.accentText} />}<Text style={{textAlign: 'center', fontFamily: 'Manrope_600SemiBold', color: secondary ? p.text : p.accentText, fontSize: small ? type.small : type.body}}>{label}</Text>
  </Pressable>;
}
export function IconButton({label, children, onPress, disabled = false}: React.PropsWithChildren<{label: string; onPress: () => void; disabled?: boolean}>) {
  const p = usePalette();
  return <Pressable accessibilityRole="button" accessibilityLabel={label} accessibilityState={{disabled}} disabled={disabled} onPress={onPress} style={({pressed}) => ({minWidth: touchTarget, minHeight: touchTarget, alignItems: 'center', justifyContent: 'center', borderRadius: radius.button, backgroundColor: pressed ? p.soft : 'transparent', opacity: disabled ? 0.5 : 1})}>{children}</Pressable>;
}
export function Chip({label, active = false, onPress}: {label: string; active?: boolean; onPress: () => void}) {
  const p = usePalette();
  return <Pressable accessibilityRole="button" accessibilityState={{selected: active}} onPress={onPress} style={({pressed}) => [styles.chip, {backgroundColor: active ? p.accent : p.surface, borderColor: active ? p.accent : p.border, opacity: pressed ? 0.8 : 1}]}>
    <Text style={{fontFamily: 'Manrope_600SemiBold', fontSize: type.small, color: active ? p.accentText : p.text}}>{label}</Text>
  </Pressable>;
}
export function Field({label, value, onChangeText, numeric = false, secure = false, placeholder, helper, error}: {label: string; value: string; onChangeText: (value: string) => void; numeric?: boolean; secure?: boolean; placeholder?: string; helper?: string; error?: string}) {
  const p = usePalette();
  return <View style={{gap: 4}}><Copy variant="small" muted>{label}</Copy><TextInput accessibilityLabel={label} placeholder={placeholder} placeholderTextColor={p.muted} value={value} onChangeText={onChangeText} keyboardType={numeric ? 'decimal-pad' : 'default'} secureTextEntry={secure} autoCapitalize="none" autoCorrect={false} style={[styles.input, {color: p.text, borderColor: p.border, backgroundColor: p.surface}]} />{error ? <Text accessibilityRole="alert" style={{color: p.negative, fontSize: type.small}}>{error}</Text> : helper ? <Copy variant="small" muted>{helper}</Copy> : null}</View>;
}
export function Notice({children}: React.PropsWithChildren) {
  const p = usePalette();
  return <View accessibilityLiveRegion="polite" style={{padding: space.md, backgroundColor: p.attention, borderRadius: radius.button}}><Text style={{color: p.attentionText, fontFamily: 'Manrope_400Regular', fontSize: type.small, lineHeight: Math.round(type.small * 1.4)}}>{children}</Text></View>;
}
export function Loading() { const p = usePalette(); return <ActivityIndicator accessibilityLabel="Loading" color={p.accent} style={{padding: space.xl}} />; }
export function Row({label, value, bold = false}: {label: string; value: string; bold?: boolean}) {
  const p = usePalette();
  return <View style={{gap: space.sm, flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', paddingVertical: space.sm, borderBottomWidth: StyleSheet.hairlineWidth, borderColor: p.border}}><View style={{flexShrink: 1}}><Copy variant={bold ? 'body' : 'small'} muted={!bold}>{label}</Copy></View><Copy variant={bold ? 'title' : 'body'}>{value}</Copy></View>;
}
const styles = StyleSheet.create({
  page: {padding: space.gutter, paddingBottom: space.xxl, gap: space.md, maxWidth: 640, width: '100%', alignSelf: 'center'},
  card: {padding: space.md, borderWidth: 1, borderRadius: radius.card, gap: space.sm},
  button: {minHeight: touchTarget, paddingHorizontal: space.md, paddingVertical: 9, borderRadius: radius.button, borderWidth: 1, justifyContent: 'center'},
  smallButton: {minHeight: touchTarget, paddingHorizontal: 10, paddingVertical: 6},
  chip: {minHeight: touchTarget, justifyContent: 'center', paddingHorizontal: 11, paddingVertical: 6, borderRadius: 999, borderWidth: 1},
  input: {minHeight: touchTarget, borderWidth: 1, paddingHorizontal: space.md, paddingVertical: 8, borderRadius: radius.button, fontFamily: 'Manrope_400Regular', fontSize: type.body},
});
