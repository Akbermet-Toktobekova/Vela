import React, { useEffect, useRef } from 'react';
import { StyleSheet, View, Animated, Dimensions } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

export type AuroraTheme = 'mint' | 'cobalt' | 'purple' | 'teal';

interface FloatingAuroraBackgroundProps {
  children: React.ReactNode;
  theme?: AuroraTheme;
}

const THEME_COLORS = {
  mint: {
    base: ['#007F55', '#009A6B', '#0DB37A', '#10C888'] as const,
    blob1: ['rgba(52, 211, 153, 0.7)', 'rgba(16, 200, 136, 0.3)', 'transparent'] as const,
    blob2: ['rgba(110, 231, 183, 0.65)', 'rgba(5, 150, 105, 0.25)', 'transparent'] as const,
    blob3: ['rgba(0, 117, 235, 0.25)', 'rgba(0, 154, 107, 0.1)', 'transparent'] as const,
  },
  cobalt: {
    base: ['#123BB5', '#1754EE', '#2A72FF', '#5093FF'] as const,
    blob1: ['rgba(96, 165, 250, 0.75)', 'rgba(59, 130, 246, 0.35)', 'transparent'] as const,
    blob2: ['rgba(147, 197, 253, 0.65)', 'rgba(37, 99, 235, 0.25)', 'transparent'] as const,
    blob3: ['rgba(168, 85, 247, 0.3)', 'rgba(29, 78, 216, 0.15)', 'transparent'] as const,
  },
  purple: {
    base: ['#2A169E', '#3D25F4', '#5515EE', '#7A22E8'] as const,
    blob1: ['rgba(192, 132, 252, 0.7)', 'rgba(147, 51, 234, 0.35)', 'transparent'] as const,
    blob2: ['rgba(232, 121, 249, 0.65)', 'rgba(126, 34, 206, 0.25)', 'transparent'] as const,
    blob3: ['rgba(59, 130, 246, 0.35)', 'rgba(107, 33, 168, 0.15)', 'transparent'] as const,
  },
  teal: {
    base: ['#005561', '#007A87', '#0891B2', '#06B6D4'] as const,
    blob1: ['rgba(103, 232, 249, 0.7)', 'rgba(8, 145, 178, 0.35)', 'transparent'] as const,
    blob2: ['rgba(165, 243, 252, 0.65)', 'rgba(14, 116, 144, 0.25)', 'transparent'] as const,
    blob3: ['rgba(52, 211, 153, 0.3)', 'rgba(21, 94, 117, 0.15)', 'transparent'] as const,
  },
};

export const FloatingAuroraBackground: React.FC<FloatingAuroraBackgroundProps> = ({ 
  children, 
  theme = 'mint' 
}) => {
  const currentTheme = THEME_COLORS[theme] || THEME_COLORS.mint;

  // Animated float coordinates
  const floatAnim1 = useRef(new Animated.Value(0)).current;
  const floatAnim2 = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // 1. Blob 1 Motion
    Animated.loop(
      Animated.sequence([
        Animated.timing(floatAnim1, {
          toValue: 1,
          duration: 9000,
          useNativeDriver: true,
        }),
        Animated.timing(floatAnim1, {
          toValue: 0,
          duration: 9000,
          useNativeDriver: true,
        }),
      ])
    ).start();

    // 2. Blob 2 Motion
    Animated.loop(
      Animated.sequence([
        Animated.timing(floatAnim2, {
          toValue: 1,
          duration: 11000,
          useNativeDriver: true,
        }),
        Animated.timing(floatAnim2, {
          toValue: 0,
          duration: 11000,
          useNativeDriver: true,
        }),
      ])
    ).start();

    // 3. Pulse scale
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 7000,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 0,
          duration: 7000,
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, []);

  const blob1TranslateX = floatAnim1.interpolate({
    inputRange: [0, 1],
    outputRange: [-40, 60],
  });
  const blob1TranslateY = floatAnim1.interpolate({
    inputRange: [0, 1],
    outputRange: [-20, 50],
  });

  const blob2TranslateX = floatAnim2.interpolate({
    inputRange: [0, 1],
    outputRange: [50, -40],
  });
  const blob2TranslateY = floatAnim2.interpolate({
    inputRange: [0, 1],
    outputRange: [30, -30],
  });

  const blobScale = pulseAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [1, 1.2],
  });

  return (
    <View style={styles.container}>
      {/* Base Gradient Canvas */}
      <LinearGradient
        colors={currentTheme.base as any}
        start={{ x: 0.1, y: 0 }}
        end={{ x: 0.9, y: 1 }}
        style={StyleSheet.absoluteFillObject}
      />

      {/* Floating Organic Blob 1 */}
      <Animated.View
        style={[
          styles.auroraBlob,
          styles.blob1,
          {
            transform: [
              { translateX: blob1TranslateX },
              { translateY: blob1TranslateY },
              { scale: blobScale },
            ],
          },
        ]}
      >
        <LinearGradient
          colors={currentTheme.blob1 as any}
          style={styles.blobGradient}
        />
      </Animated.View>

      {/* Floating Organic Blob 2 */}
      <Animated.View
        style={[
          styles.auroraBlob,
          styles.blob2,
          {
            transform: [
              { translateX: blob2TranslateX },
              { translateY: blob2TranslateY },
            ],
          },
        ]}
      >
        <LinearGradient
          colors={currentTheme.blob2 as any}
          style={styles.blobGradient}
        />
      </Animated.View>

      {/* Ambient Blob 3 */}
      <Animated.View style={[styles.auroraBlob, styles.blob3]}>
        <LinearGradient
          colors={currentTheme.blob3 as any}
          style={styles.blobGradient}
        />
      </Animated.View>

      {/* Foreground Content */}
      <View style={styles.content}>{children}</View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    overflow: 'hidden',
  },
  auroraBlob: {
    position: 'absolute',
    borderRadius: 300,
  },
  blob1: {
    top: -60,
    left: -40,
    width: SCREEN_WIDTH * 1.1,
    height: SCREEN_WIDTH * 1.1,
  },
  blob2: {
    top: SCREEN_HEIGHT * 0.15,
    right: -80,
    width: SCREEN_WIDTH * 1.2,
    height: SCREEN_WIDTH * 1.2,
  },
  blob3: {
    top: SCREEN_HEIGHT * 0.05,
    left: SCREEN_WIDTH * 0.2,
    width: SCREEN_WIDTH * 0.9,
    height: SCREEN_WIDTH * 0.9,
  },
  blobGradient: {
    width: '100%',
    height: '100%',
    borderRadius: 300,
  },
  content: {
    flex: 1,
  },
});
