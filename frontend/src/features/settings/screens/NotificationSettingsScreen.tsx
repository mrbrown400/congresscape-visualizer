import React, { useState } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { NativeStackScreenProps } from '@react-navigation/native-stack';

import { useTheme } from '@theme/ThemeProvider';
import { useUserPreferences } from '../../../context/UserPreferencesContext';
import { RootStackParamList } from '@navigation/RootNavigator';

type Props = NativeStackScreenProps<RootStackParamList, 'NotificationSettings'>;

const timeOptions = [
  '06:00', '07:00', '08:00', '09:00', '10:00', '11:00', '12:00'
];

const NotificationSettingsScreen = ({ navigation }: Props) => {
  const { neutral, branch: branchColors } = useTheme();
  const { preferences, setNotificationPreferences } = useUserPreferences();

  const [showTimePicker, setShowTimePicker] = useState(false);

  const formatTime = (time: string) => {
    const [hours] = time.split(':');
    const hour = parseInt(hours, 10);
    if (hour === 0) return '12:00 AM';
    if (hour === 12) return '12:00 PM';
    if (hour > 12) return `${hour - 12}:00 PM`;
    return `${hour}:00 AM`;
  };

  return (
    <View style={[styles.container, { backgroundColor: neutral.background }]}>
      {/* Header */}
      <View style={[styles.header, { borderBottomColor: neutral.divider }]}>
        <Pressable
          style={styles.backButton}
          onPress={() => navigation.goBack()}
          hitSlop={12}
        >
          <Ionicons name="arrow-back" size={24} color={neutral.textPrimary} />
        </Pressable>
        <Text style={[styles.headerTitle, { color: neutral.textPrimary }]}>
          Notifications
        </Text>
        <View style={styles.headerSpacer} />
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
      >
        {/* Daily Digest Section */}
        <View style={[styles.section, { backgroundColor: neutral.card }]}>
          <View style={styles.sectionHeader}>
            <Ionicons name="sunny" size={20} color={branchColors.agency} />
            <Text style={[styles.sectionTitle, { color: neutral.textPrimary }]}>
              Daily Digest
            </Text>
          </View>

          <View style={[styles.settingRow, { borderBottomColor: neutral.divider }]}>
            <View style={styles.settingInfo}>
              <Text style={[styles.settingLabel, { color: neutral.textPrimary }]}>
                Enable Daily Digest
              </Text>
              <Text style={[styles.settingDescription, { color: neutral.textMuted }]}>
                Get a morning summary of government activity
              </Text>
            </View>
            <Switch
              value={preferences.notifications.dailyDigest}
              onValueChange={(value) => setNotificationPreferences({ dailyDigest: value })}
              trackColor={{ false: neutral.divider, true: branchColors.agency + '80' }}
              thumbColor={preferences.notifications.dailyDigest ? branchColors.agency : neutral.textMuted}
            />
          </View>

          {preferences.notifications.dailyDigest && (
            <Pressable
              style={styles.settingRow}
              onPress={() => setShowTimePicker(!showTimePicker)}
            >
              <View style={styles.settingInfo}>
                <Text style={[styles.settingLabel, { color: neutral.textPrimary }]}>
                  Delivery Time
                </Text>
                <Text style={[styles.settingDescription, { color: neutral.textMuted }]}>
                  When to receive your daily briefing
                </Text>
              </View>
              <View style={styles.timeSelector}>
                <Text style={[styles.timeValue, { color: branchColors.agency }]}>
                  {formatTime(preferences.notifications.dailyDigestTime)}
                </Text>
                <Ionicons
                  name={showTimePicker ? 'chevron-up' : 'chevron-down'}
                  size={20}
                  color={branchColors.agency}
                />
              </View>
            </Pressable>
          )}

          {showTimePicker && preferences.notifications.dailyDigest && (
            <View style={[styles.timePickerContainer, { borderTopColor: neutral.divider }]}>
              {timeOptions.map(time => (
                <Pressable
                  key={time}
                  style={[
                    styles.timeOption,
                    {
                      backgroundColor: preferences.notifications.dailyDigestTime === time
                        ? branchColors.agency
                        : 'transparent',
                    }
                  ]}
                  onPress={() => {
                    setNotificationPreferences({ dailyDigestTime: time });
                    setShowTimePicker(false);
                  }}
                >
                  <Text style={[
                    styles.timeOptionText,
                    {
                      color: preferences.notifications.dailyDigestTime === time
                        ? '#FFFFFF'
                        : neutral.textPrimary,
                    }
                  ]}>
                    {formatTime(time)}
                  </Text>
                </Pressable>
              ))}
            </View>
          )}
        </View>

        {/* Breaking News Section */}
        <View style={[styles.section, { backgroundColor: neutral.card }]}>
          <View style={styles.sectionHeader}>
            <Ionicons name="alert-circle" size={20} color={branchColors.urgent} />
            <Text style={[styles.sectionTitle, { color: neutral.textPrimary }]}>
              Breaking News
            </Text>
          </View>

          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <Text style={[styles.settingLabel, { color: neutral.textPrimary }]}>
                Enable Breaking Alerts
              </Text>
              <Text style={[styles.settingDescription, { color: neutral.textMuted }]}>
                Get notified about urgent government news
              </Text>
            </View>
            <Switch
              value={preferences.notifications.breakingNews}
              onValueChange={(value) => setNotificationPreferences({ breakingNews: value })}
              trackColor={{ false: neutral.divider, true: branchColors.urgent + '80' }}
              thumbColor={preferences.notifications.breakingNews ? branchColors.urgent : neutral.textMuted}
            />
          </View>
        </View>

        {/* Tracking Updates Section */}
        <View style={[styles.section, { backgroundColor: neutral.card }]}>
          <View style={styles.sectionHeader}>
            <Ionicons name="bookmark" size={20} color={branchColors.legislative} />
            <Text style={[styles.sectionTitle, { color: neutral.textPrimary }]}>
              Tracking Updates
            </Text>
          </View>

          <View style={[styles.settingRow, { borderBottomColor: neutral.divider }]}>
            <View style={styles.settingInfo}>
              <Text style={[styles.settingLabel, { color: neutral.textPrimary }]}>
                Bill Updates
              </Text>
              <Text style={[styles.settingDescription, { color: neutral.textMuted }]}>
                Get notified when bills you follow advance
              </Text>
            </View>
            <Switch
              value={preferences.notifications.billUpdates}
              onValueChange={(value) => setNotificationPreferences({ billUpdates: value })}
              trackColor={{ false: neutral.divider, true: branchColors.legislative + '80' }}
              thumbColor={preferences.notifications.billUpdates ? branchColors.legislative : neutral.textMuted}
            />
          </View>

          <View style={[styles.settingRow, { borderBottomColor: neutral.divider }]}>
            <View style={styles.settingInfo}>
              <Text style={[styles.settingLabel, { color: neutral.textPrimary }]}>
                Representative Votes
              </Text>
              <Text style={[styles.settingDescription, { color: neutral.textMuted }]}>
                Get notified when followed representatives have sourced roll-call positions
              </Text>
            </View>
            <Switch
              value={preferences.notifications.representativeVotes}
              onValueChange={(value) => setNotificationPreferences({ representativeVotes: value })}
              trackColor={{ false: neutral.divider, true: branchColors.house + '80' }}
              thumbColor={preferences.notifications.representativeVotes ? branchColors.house : neutral.textMuted}
            />
          </View>

          <View style={[styles.settingRow, { borderBottomColor: neutral.divider }]}>
            <View style={styles.settingInfo}>
              <Text style={[styles.settingLabel, { color: neutral.textPrimary }]}>
                Hearing Reminders
              </Text>
              <Text style={[styles.settingDescription, { color: neutral.textMuted }]}>
                Get tomorrow alerts for followed committees and topics
              </Text>
            </View>
            <Switch
              value={preferences.notifications.hearingAlerts}
              onValueChange={(value) => setNotificationPreferences({ hearingAlerts: value })}
              trackColor={{ false: neutral.divider, true: branchColors.agency + '80' }}
              thumbColor={preferences.notifications.hearingAlerts ? branchColors.agency : neutral.textMuted}
            />
          </View>

          <View style={[styles.settingRow, { borderBottomColor: neutral.divider }]}>
            <View style={styles.settingInfo}>
              <Text style={[styles.settingLabel, { color: neutral.textPrimary }]}>
                New Text
              </Text>
              <Text style={[styles.settingDescription, { color: neutral.textMuted }]}>
                Get notified when followed bills publish official text
              </Text>
            </View>
            <Switch
              value={preferences.notifications.textAlerts}
              onValueChange={(value) => setNotificationPreferences({ textAlerts: value })}
              trackColor={{ false: neutral.divider, true: branchColors.senate + '80' }}
              thumbColor={preferences.notifications.textAlerts ? branchColors.senate : neutral.textMuted}
            />
          </View>

          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <Text style={[styles.settingLabel, { color: neutral.textPrimary }]}>
                Money Context
              </Text>
              <Text style={[styles.settingDescription, { color: neutral.textMuted }]}>
                Get notified only when sourced money context changes
              </Text>
            </View>
            <Switch
              value={preferences.notifications.moneyContextAlerts}
              onValueChange={(value) => setNotificationPreferences({ moneyContextAlerts: value })}
              trackColor={{ false: neutral.divider, true: branchColors.judicial + '80' }}
              thumbColor={preferences.notifications.moneyContextAlerts ? branchColors.judicial : neutral.textMuted}
            />
          </View>
        </View>

        {/* Info Section */}
        <View style={[styles.infoSection, { backgroundColor: neutral.card }]}>
          <Ionicons name="information-circle" size={20} color={neutral.textMuted} />
          <Text style={[styles.infoText, { color: neutral.textMuted }]}>
            You can manage system notification permissions in your device settings.
          </Text>
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingTop: 50,
    paddingHorizontal: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
  },
  backButton: {
    padding: 8,
    marginLeft: -8,
  },
  headerTitle: {
    flex: 1,
    fontSize: 18,
    fontWeight: '600',
    textAlign: 'center',
  },
  headerSpacer: {
    width: 40,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 100,
    gap: 16,
  },
  section: {
    borderRadius: 20,
    padding: 16,
    gap: 4,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'transparent',
  },
  settingInfo: {
    flex: 1,
    gap: 4,
    marginRight: 12,
  },
  settingLabel: {
    fontSize: 16,
    fontWeight: '500',
  },
  settingDescription: {
    fontSize: 13,
    lineHeight: 18,
  },
  timeSelector: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  timeValue: {
    fontSize: 16,
    fontWeight: '600',
  },
  timePickerContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    paddingTop: 12,
    borderTopWidth: 1,
  },
  timeOption: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
  },
  timeOptionText: {
    fontSize: 14,
    fontWeight: '500',
  },
  infoSection: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    borderRadius: 16,
    padding: 16,
    gap: 12,
  },
  infoText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 20,
  },
});

export default NotificationSettingsScreen;
