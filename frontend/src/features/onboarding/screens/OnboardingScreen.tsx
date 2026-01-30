import React from 'react';
import { LinearGradient } from 'expo-linear-gradient';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';

import { useTheme } from '@theme/ThemeProvider';
import { RootStackParamList } from '@navigation/RootNavigator';

const interestGroups = [
  { key: 'legislative', title: 'Congress (House & Senate)' },
  { key: 'judicial', title: 'Supreme Court & Courts' },
  { key: 'executive', title: 'Executive Orders & Agencies' },
  { key: 'budget', title: 'Budget & Appropriations' },
  { key: 'oversight', title: 'Oversight & Investigations' }
];

type Props = NativeStackScreenProps<RootStackParamList, 'Onboarding'>;

const OnboardingScreen = ({ navigation }: Props) => {
  const { neutral } = useTheme();

  const handleContinue = () => {
    // TODO: Persist selection and mark onboarding as complete
    navigation.replace('Main');
  };

  return (
    <LinearGradient colors={['#0F172A', '#020617']} style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Tailor Your Daily Briefing</Text>
        <Text style={styles.subtitle}>
          Follow the branches, agencies, and topics you care about. We will personalize your daily briefing with timely
          highlights and urgent alerts.
        </Text>
      </View>

      <View style={styles.list}>
        {interestGroups.map(group => (
          <Pressable key={group.key} style={[styles.card, { backgroundColor: neutral.card }]}> 
            <Text style={styles.cardTitle}>{group.title}</Text>
            <Text style={styles.cardSubtitle}>Tap to follow</Text>
          </Pressable>
        ))}
      </View>

      <Pressable style={styles.cta} onPress={handleContinue} accessibilityRole="button">
        <Text style={styles.ctaText}>Continue to Briefing</Text>
      </Pressable>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 24,
    paddingVertical: 48,
    justifyContent: 'space-between'
  },
  header: {
    gap: 16
  },
  title: {
    fontSize: 32,
    fontWeight: '800',
    color: '#F8FAFC'
  },
  subtitle: {
    fontSize: 16,
    color: '#CBD5F5'
  },
  list: {
    gap: 16
  },
  card: {
    borderRadius: 20,
    padding: 20
  },
  cardTitle: {
    color: '#F8FAFC',
    fontSize: 18,
    fontWeight: '600'
  },
  cardSubtitle: {
    color: '#C7D2FE',
    marginTop: 4
  },
  cta: {
    backgroundColor: '#F59E0B',
    borderRadius: 999,
    paddingVertical: 16,
    alignItems: 'center'
  },
  ctaText: {
    color: '#0B1D3A',
    fontSize: 16,
    fontWeight: '700'
  }
});

export default OnboardingScreen;
