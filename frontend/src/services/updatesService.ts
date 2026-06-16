import axios from 'axios';
import Constants from 'expo-constants';

// Fallback to localhost if not configured (e.g. in development)
const API_BASE_URL =
    process.env.EXPO_PUBLIC_API_BASE_URL ||
    Constants.expoConfig?.extra?.apiBaseUrl ||
    'http://localhost:8000/api/v1';

export interface GovernmentUpdate {
    id: number;
    external_id: string;
    source: string;
    branch: 'legislative' | 'executive' | 'judicial';
    headline: string;
    summary?: string;
    full_text?: string;
    published_at: string;
    url?: string;
    tags: string[];
    metadata?: Record<string, any>;
}

export interface FeedResponse {
    items: GovernmentUpdate[];
    total: number;
}

export const fetchUpdates = async (
    startDate?: string,
    endDate?: string,
    limit: number = 100
): Promise<GovernmentUpdate[]> => {
    try {
        const params: Record<string, any> = { limit };
        if (startDate) params.start_date = startDate;
        if (endDate) params.end_date = endDate;

        const response = await axios.get<FeedResponse>(`${API_BASE_URL}/feed/`, { params });
        return response.data.items;
    } catch (error) {
        console.error('Error fetching updates:', error);
        return [];
    }
};
