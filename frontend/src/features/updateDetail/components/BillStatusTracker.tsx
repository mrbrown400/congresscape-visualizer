import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { useTheme } from '@theme/ThemeProvider';

const steps = [
  { key: 'intro', label: 'Intro', shortLabel: 'Intro' },
  { key: 'committee', label: 'Committee', shortLabel: 'Cmte' },
  { key: 'floor', label: 'Floor Vote', shortLabel: 'Floor' },
  { key: 'other', label: 'Other Chamber', shortLabel: 'Other' },
  { key: 'conference', label: 'Conference', shortLabel: 'Conf' },
  { key: 'president', label: 'President', shortLabel: 'Pres' },
];

type Props = {
  currentStep: number; // 0-5 index
  vertical?: boolean;
};

const BillStatusTracker = ({ currentStep, vertical = false }: Props) => {
  const { neutral, semantic, branch: branchColors } = useTheme();

  if (vertical) {
    return (
      <View style={styles.verticalContainer}>
        {steps.map((step, index) => {
          const isCompleted = index < currentStep;
          const isCurrent = index === currentStep;
          const isPending = index > currentStep;

          const dotColor = isCompleted
            ? semantic.passed
            : isCurrent
              ? branchColors.agency
              : neutral.divider;

          const lineColor = isCompleted ? semantic.passed : neutral.divider;

          return (
            <View key={step.key} style={styles.verticalStep}>
              <View style={styles.verticalIndicator}>
                <View style={[styles.verticalDot, { backgroundColor: dotColor }]}>
                  {isCompleted && (
                    <Ionicons name="checkmark" size={12} color="#FFFFFF" />
                  )}
                  {isCurrent && (
                    <View style={styles.currentDotInner} />
                  )}
                </View>
                {index < steps.length - 1 && (
                  <View style={[styles.verticalLine, { backgroundColor: lineColor }]} />
                )}
              </View>
              <View style={styles.verticalLabel}>
                <Text
                  style={[
                    styles.verticalLabelText,
                    {
                      color: isPending ? neutral.textMuted : neutral.textPrimary,
                      fontWeight: isCurrent ? '600' : '400',
                    },
                  ]}
                >
                  {step.label}
                </Text>
              </View>
            </View>
          );
        })}
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: neutral.card }]}>
      <View style={styles.trackContainer}>
        {/* Progress line */}
        <View style={[styles.trackLine, { backgroundColor: neutral.divider }]} />
        <View
          style={[
            styles.trackLineProgress,
            {
              backgroundColor: semantic.passed,
              width: `${(currentStep / (steps.length - 1)) * 100}%`,
            },
          ]}
        />

        {/* Step dots */}
        <View style={styles.dotsRow}>
          {steps.map((step, index) => {
            const isCompleted = index < currentStep;
            const isCurrent = index === currentStep;
            const isPending = index > currentStep;

            const dotColor = isCompleted
              ? semantic.passed
              : isCurrent
                ? branchColors.agency
                : neutral.divider;

            return (
              <View key={step.key} style={styles.stepContainer}>
                <View style={[styles.dot, { backgroundColor: dotColor }]}>
                  {isCompleted && (
                    <Ionicons name="checkmark" size={12} color="#FFFFFF" />
                  )}
                  {isCurrent && (
                    <View style={styles.currentDotInner} />
                  )}
                </View>
                <Text
                  style={[
                    styles.stepLabel,
                    {
                      color: isPending ? neutral.textMuted : neutral.textPrimary,
                      fontWeight: isCurrent ? '600' : '400',
                    },
                  ]}
                  numberOfLines={1}
                >
                  {step.shortLabel}
                </Text>
              </View>
            );
          })}
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: 16,
    padding: 16,
  },
  trackContainer: {
    position: 'relative',
    paddingTop: 12,
  },
  trackLine: {
    position: 'absolute',
    top: 22,
    left: 20,
    right: 20,
    height: 3,
    borderRadius: 2,
  },
  trackLineProgress: {
    position: 'absolute',
    top: 22,
    left: 20,
    height: 3,
    borderRadius: 2,
  },
  dotsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  stepContainer: {
    alignItems: 'center',
    width: 50,
  },
  dot: {
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1,
  },
  currentDotInner: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#FFFFFF',
  },
  stepLabel: {
    fontSize: 10,
    marginTop: 8,
    textAlign: 'center',
  },
  // Vertical styles
  verticalContainer: {
    gap: 0,
  },
  verticalStep: {
    flexDirection: 'row',
    gap: 16,
  },
  verticalIndicator: {
    alignItems: 'center',
    width: 24,
  },
  verticalDot: {
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  verticalLine: {
    width: 3,
    flex: 1,
    minHeight: 24,
    borderRadius: 2,
  },
  verticalLabel: {
    flex: 1,
    paddingVertical: 2,
    minHeight: 48,
  },
  verticalLabelText: {
    fontSize: 14,
  },
});

export default BillStatusTracker;
