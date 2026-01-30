import React, { useMemo } from 'react';
import { StyleSheet, Text, View, Pressable, Dimensions } from 'react-native';
import dayjs from 'dayjs';
import { GovernmentUpdate } from '@services/updatesService';

interface Props {
    year: number;
    updates: GovernmentUpdate[];
    onMonthSelect: (month: number) => void;
}

const MONTHS = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
];

const YearView = ({ year, updates, onMonthSelect }: Props) => {
    // Group updates by date string "YYYY-MM-DD"
    const activityMap = useMemo(() => {
        const map: Record<string, number> = {};
        updates.forEach(u => {
            const dateKey = dayjs(u.published_at).format('YYYY-MM-DD');
            map[dateKey] = (map[dateKey] || 0) + 1;
        });
        return map;
    }, [updates]);

    const renderMonth = (monthIndex: number) => {
        const date = dayjs().year(year).month(monthIndex).startOf('month');
        const daysInMonth = date.daysInMonth();
        const startDay = date.day(); // 0-6

        const days = [];
        for (let i = 0; i < startDay; i++) days.push(null);
        for (let i = 1; i <= daysInMonth; i++) days.push(i);

        return (
            <Pressable
                key={monthIndex}
                style={styles.monthContainer}
                onPress={() => onMonthSelect(monthIndex)}
            >
                <Text style={styles.monthTitle}>{MONTHS[monthIndex]}</Text>
                <View style={styles.monthGrid}>
                    {days.map((day, idx) => {
                        if (!day) return <View key={`empty-${idx}`} style={styles.dayPixelEmpty} />;

                        const dateKey = date.date(day).format('YYYY-MM-DD');
                        const count = activityMap[dateKey] || 0;

                        let backgroundColor = '#334155'; // default slate-700
                        if (count > 0) backgroundColor = '#93C5FD'; // light blue
                        if (count > 2) backgroundColor = '#3B82F6'; // blue
                        if (count > 5) backgroundColor = '#1D4ED8'; // dark blue

                        return (
                            <View
                                key={day}
                                style={[styles.dayPixel, { backgroundColor }]}
                            />
                        );
                    })}
                </View>
            </Pressable>
        );
    };

    return (
        <View style={styles.container}>
            <View style={styles.grid}>
                {MONTHS.map((_, index) => renderMonth(index))}
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        paddingTop: 20,
    },
    grid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        gap: 12,
    },
    monthContainer: {
        width: '30%',
        marginBottom: 16,
    },
    monthTitle: {
        color: '#94A3B8',
        fontSize: 12,
        fontWeight: '600',
        marginBottom: 4,
    },
    monthGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 1,
    },
    dayPixel: {
        width: 6,
        height: 6,
        borderRadius: 1,
    },
    dayPixelEmpty: {
        width: 6,
        height: 6,
    }
});

export default YearView;
