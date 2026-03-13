/**
 * API Service layer for Knowledge Search
 */
const API_BASE = 'http://localhost:8000';

const handleResponse = async (response) => {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `API error: ${response.status}`);
    }
    return response.json();
};

export const searchDocs = async (query, topK = 10, alpha = 0.5, normalization = 'minmax') => {
    const response = await fetch('/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: topK, alpha, normalization }),
    });
    return handleResponse(response);
};

export const fetchHealth = async () => {
    const response = await fetch('/health');
    return handleResponse(response);
};

export const fetchLatency = async () => {
    const response = await fetch('/api/kpi/latency');
    return handleResponse(response);
};

export const fetchVolume = async () => {
    const response = await fetch('/api/kpi/volume');
    return handleResponse(response);
};

export const fetchTopQueries = async () => {
    const response = await fetch('/api/kpi/top-queries');
    return handleResponse(response);
};

export const fetchZeroResults = async () => {
    const response = await fetch('/api/kpi/zero-results');
    return handleResponse(response);
};

export const fetchExperiments = async () => {
    const response = await fetch('/api/eval/experiments');
    return handleResponse(response);
};

export const fetchLogs = async (limit = 50, severity = null, start = null, end = null) => {
    try {
        const params = new URLSearchParams({ limit });
        if (severity && severity !== 'all') params.append('severity', severity);
        if (start) params.append('start', start);
        if (end) params.append('end', end);

        const response = await fetch(`${API_BASE}/api/logs?${params.toString()}`);
        if (!response.ok) throw new Error('Failed to fetch logs');
        
        return await response.json();
    } catch (error) {
        // This is what is catching the "API_BASE is not defined" error
        throw new Error(error.message);
    }
};

export const submitFeedback = async (query, docId, relevance) => {
    const response = await fetch('/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, doc_id: docId, relevance }),
    });
    return handleResponse(response);
};
