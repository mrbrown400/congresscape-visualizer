import React, { useCallback, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { NativeStackScreenProps } from '@react-navigation/native-stack';

import { useTheme } from '@theme/ThemeProvider';
import { useUserPreferences } from '../../../context/UserPreferencesContext';
import { RootStackParamList } from '@navigation/RootNavigator';
import CivicProgressCard, { CivicProgressItem } from '@components/CivicProgressCard';

const interestGroups = [
  {
    key: 'legislative',
    title: 'Congress',
    subtitle: 'House & Senate bills, votes, and hearings',
    icon: 'business' as keyof typeof Ionicons.glyphMap,
  },
  {
    key: 'judicial',
    title: 'Courts',
    subtitle: 'Supreme Court decisions and federal rulings',
    icon: 'scale' as keyof typeof Ionicons.glyphMap,
  },
  {
    key: 'executive',
    title: 'Executive',
    subtitle: 'Executive orders and White House actions',
    icon: 'document-text' as keyof typeof Ionicons.glyphMap,
  },
  {
    key: 'budget',
    title: 'Budget',
    subtitle: 'Appropriations and spending bills',
    icon: 'cash' as keyof typeof Ionicons.glyphMap,
  },
  {
    key: 'oversight',
    title: 'Oversight',
    subtitle: 'Investigations and committee hearings',
    icon: 'eye' as keyof typeof Ionicons.glyphMap,
  },
];

type Props = NativeStackScreenProps<RootStackParamList, 'Onboarding'>;

const OnboardingScreen = ({ navigation }: Props) => {
  const { neutral, branch: branchColors } = useTheme();
  const { preferences, setInterests, completeOnboarding, hasCompletedOnboarding } = useUserPreferences();

  const [selectedInterests, setSelectedInterests] = useState<string[]>(preferences.interests);

  const toggleInterest = useCallback((key: string) => {
    setSelectedInterests(prev =>
      prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]
    );
  }, []);

  const handleContinue = useCallback(() => {
    setInterests(selectedInterests);
    completeOnboarding();
    navigation.replace('MainTabs');
  }, [selectedInterests, setInterests, completeOnboarding, navigation]);

  const handleSkip = useCallback(() => {
    completeOnboarding();
    navigation.replace('MainTabs');
  }, [completeOnboarding, navigation]);

  const isEditing = hasCompletedOnboarding;
  const setupItems: CivicProgressItem[] = [
    {
      label: 'Choose interests',
      detail: `${selectedInterests.length} topic${selectedInterests.length === 1 ? '' : 's'} selected`,
      complete: selectedInterests.length > 0,
    },
    {
      label: 'District can come next',
      detail: preferences.homeDistrict ? `${preferences.homeDistrict.state}-${preferences.homeDistrict.district}` : 'Optional in My Gov',
      complete: true,
    },
    {
      label: 'Alert controls stay optional',
      detail: 'Tune notification intensity after setup',
      complete: true,
    },
  ];

  return (
    <View style={[styles.container, { backgroundColor: neutral.background }]}>
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          {isEditing && (
            <Pressable style={styles.backButton} onPress={() => navigation.goBack()}>
              <Ionicons name="arrow-back" size={24} color={neutral.textPrimary} />
            </Pressable>
          )}
          <View style={styles.titleContainer}>
            <Text style={[styles.title, { color: neutral.textPrimary }]}>
              {isEditing ? 'Edit Your Interests' : 'Tailor Your Briefing'}
            </Text>
            <Text style={[styles.subtitle, { color: neutral.textSecondary }]}>
              {isEditing
                ? 'Update the topics you want to follow'
                : 'Follow the branches and topics you care about. We\'ll personalize your daily briefing.'}
            </Text>
          </View>
        </View>

        <CivicProgressCard
          title="Personalization setup"
          subtitle="Choose what should shape your civic feed. You can change this later."
          items={setupItems}
        />

        {/* Interest Cards */}
        <View style={styles.list}>
          {interestGroups.map(group => {
            const isSelected = selectedInterests.includes(group.key);
            const accentColor = branchColors[group.key as keyof typeof branchColors] || branchColors.agency;

            return (
              <Pressable
                key={group.key}
                style={[
                  styles.card,
                  {
                    backgroundColor: isSelected ? accentColor + '15' : neutral.card,
                    borderColor: isSelected ? accentColor : neutral.divider,
                  }
                ]}
                onPress={() => toggleInterest(group.key)}
              >
                <View style={[styles.cardIcon, { backgroundColor: accentColor + '20' }]}>
                  <Ionicons name={group.icon} size={24} color={accentColor} />
                </View>
                <View style={styles.cardContent}>
                  <Text style={[styles.cardTitle, { color: neutral.textPrimary }]}>
                    {group.title}
                  </Text>
                  <Text style={[styles.cardSubtitle, { color: neutral.textSecondary }]}>
                    {group.subtitle}
                  </Text>
                </View>
                <View style={[
                  styles.checkbox,
                  {
                    backgroundColor: isSelected ? accentColor : 'transparent',
                    borderColor: isSelected ? accentColor : neutral.textMuted,
                  }
                ]}>
                  {isSelected && (
                    <Ionicons name="checkmark" size={16} color="#FFFFFF" />
                  )}
                </View>
              </Pressable>
            );
          })}
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <Pressable
            style={[
              styles.cta,
              {
                backgroundColor: selectedInterests.length > 0 ? branchColors.agency : neutral.divider,
              }
            ]}
            onPress={handleContinue}
            disabled={selectedInterests.length === 0 && !isEditing}
          >
            <Text style={[
              styles.ctaText,
              { color: selectedInterests.length > 0 ? '#FFFFFF' : neutral.textMuted }
            ]}>
              {isEditing ? 'Save Changes' : 'Continue to Briefing'}
            </Text>
          </Pressable>

          {!isEditing && (
            <Pressable style={styles.skipButton} onPress={handleSkip}>
              <Text style={[styles.skipText, { color: neutral.textMuted }]}>
                Skip for now
              </Text>
            </Pressable>
          )}

          {selectedInterests.length > 0 && (
            <Text style={[styles.selectionCount, { color: neutral.textMuted }]}>
              {selectedInterests.length} topic{selectedInterests.length !== 1 ? 's' : ''} selected
            </Text>
          )}
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingTop: 60,
    paddingBottom: 40,
  },
  header: {
    gap: 16,
    marginBottom: 24,
  },
  backButton: {
    alignSelf: 'flex-start',
    padding: 4,
    marginBottom: 8,
  },
  titleContainer: {
    gap: 12,
  },
  title: {
    fontSize: 32,
    fontWeight: '800',
    lineHeight: 40,
  },
  subtitle: {
    fontSize: 16,
    lineHeight: 24,
  },
  list: {
    gap: 12,
  },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderRadius: 8,
    padding: 16,
    gap: 14,
  },
  cardIcon: {
    width: 42,
    height: 42,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardContent: {
    flex: 1,
    gap: 4,
  },
  cardTitle: {
    fontSize: 17,
    fontWeight: '600',
  },
  cardSubtitle: {
    fontSize: 14,
    lineHeight: 18,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 6,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  footer: {
    gap: 12,
    paddingTop: 20,
  },
  cta: {
    borderRadius: 8,
    paddingVertical: 16,
    alignItems: 'center',
  },
  ctaText: {
    fontSize: 16,
    fontWeight: '700',
  },
  skipButton: {
    alignItems: 'center',
    paddingVertical: 12,
  },
  skipText: {
    fontSize: 15,
  },
  selectionCount: {
    fontSize: 13,
    textAlign: 'center',
  },
});

export default OnboardingScreen;
