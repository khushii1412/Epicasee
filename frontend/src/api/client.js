/**
 * API Client for India Epidemiology Backend
 * Handles all communication with the Flask backend
 */

const API_BASE = 'http://localhost:5001';

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;

    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            throw new Error('Unable to connect to server. Please ensure the backend is running on port 5000.');
        }
        throw error;
    }
}

/**
 * Health check endpoint
 */
export async function checkHealth() {
    return fetchAPI('/api/health');
}

/**
 * Get list of available diseases with data
 */
export async function getDiseases() {
    const data = await fetchAPI('/api/diseases');
    return data.diseases || [];
}

/**
 * Get list of states for a specific disease
 * @param {string} diseaseKey - The disease identifier (covid, dengue, malaria, idsp)
 */
export async function getStates(diseaseKey) {
    if (!diseaseKey) {
        throw new Error('disease_key is required');
    }
    const data = await fetchAPI(`/api/states?disease_key=${encodeURIComponent(diseaseKey)}`);
    return data.states || [];
}

/**
 * Get list of districts for a specific disease and state
 * @param {string} diseaseKey - The disease identifier
 * @param {string} state - The state name
 */
export async function getDistricts(diseaseKey, state) {
    if (!diseaseKey || !state) {
        throw new Error('disease_key and state are required');
    }
    const params = new URLSearchParams({
        disease_key: diseaseKey,
        state: state,
    });
    const data = await fetchAPI(`/api/districts?${params.toString()}`);
    return data.districts || [];
}

/**
 * Get epidemiological data for a disease, state, and optionally district
 * @param {string} diseaseKey - The disease identifier
 * @param {string} state - The state name
 * @param {string} [district] - Optional district name
 */
export async function getData(diseaseKey, state, district = '') {
    if (!diseaseKey || !state) {
        throw new Error('disease_key and state are required');
    }
    const params = new URLSearchParams({ disease_key: diseaseKey, state });
    if (district) params.append('district', district);
    const result = await fetchAPI(`/api/data?${params.toString()}`);
    return result.data || [];
}

export default {
    checkHealth,
    getDiseases,
    getStates,
    getDistricts,
    getData,
};
