import React, { useEffect, useRef } from 'react';
import { StyleSheet, View, Animated, Dimensions } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

interface FloatingAuroraBackgroundProps {
  children: React.ReactNode;
}

export const FloatingAuroraBackground: React.FC<FloatingAuroraBackgroundProps> = ({ children }) => {
  // Animated float coordinates for multiple ambient light spheres
  const floatAnim1 = useRef(new Animated.Value(0)).current;
  const floatAnim2 = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // 1. Slow, organic undulating motion loop for Blob 1 (Top Left / Center)
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

    // 2. Cross-diagonal organic float for Blob 2 (Top Right / Bottom)
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

    // 3. Subtle breathing scale pulse
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

  // Interpolations
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
      {/* Deep Rich Emerald Base Gradient */}
      <LinearGradient
        colors={['#007F55', '#009A6B', '#0DB37A', '#10C888']}
        start={{ x: 0.1, y: 0 }}
        end={{ x: 0.9, y: 1 }}
        style={StyleSheet.absoluteFillObject}
      />

      {/* Floating Organic Aurora Blob 1 (Bright Emerald Glow) */}
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
          colors={['rgba(52, 211, 153, 0.7)', 'rgba(16, 200, 136, 0.3)', 'transparent']}
          style={styles.blobGradient}
        />
      </Animated.View>

      {/* Floating Organic Aurora Blob 2 (Soft Mint/Cyan Glow) */}
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
          colors={['rgba(110, 231, 183, 0.65)', 'rgba(5, 150, 105, 0.25)', 'transparent']}
          style={styles.blobGradient}
        />
      </Animated.View>

      {/* Floating Organic Aurora Blob 3 (Deep Cobalt Accent Aura) */}
      <Animated.View style={[styles.auroraBlob, styles.blob3]}>
        <LinearGradient
          colors={['rgba(0, 117, 235, 0.25)', 'rgba(0, 154, 107, 0.1)', 'transparent']}
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
    backgroundColor: '#007F55',
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
