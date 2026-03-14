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

// Use backticks and ${API_BASE} for ALL calls
export const searchDocs = async (query, topK = 10, alpha = 0.5, normalization = 'minmax') => {
    const response = await fetch(`${API_BASE}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: topK, alpha, normalization }),
    });
    return handleResponse(response);
};

export const fetchHealth = async () => {
    const response = await fetch(`${API_BASE}/health`);
    return handleResponse(response);
};

export const fetchLatency = async () => {
    const response = await fetch(`${API_BASE}/api/kpi/latency`);
    return handleResponse(response);
};

export const fetchVolume = async () => {
    const response = await fetch(`${API_BASE}/api/kpi/volume`);
    return handleResponse(response);
};

export const fetchTopQueries = async () => {
    const response = await fetch(`${API_BASE}/api/kpi/top-queries`);
    return handleResponse(response);
};

export const fetchZeroResults = async () => {
    const response = await fetch(`${API_BASE}/api/kpi/zero-results`);
    return handleResponse(response);
};

export const fetchExperiments = async () => {
    const response = await fetch(`${API_BASE}/api/eval/experiments`);
    return handleResponse(response);
};

export const fetchLogs = async (limit = 50, severity = null, start = null, end = null) => {
    const params = new URLSearchParams({ limit });
    if (severity && severity !== 'all') params.append('severity', severity);
    if (start) params.append('start', start);
    if (end) params.append('end', end);

    const response = await fetch(`${API_BASE}/api/logs?${params.toString()}`);
    return handleResponse(response);
};

export const submitFeedback = async (query, docId, relevance) => {
    const response = await fetch(`${API_BASE}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, doc_id: docId, relevance }),
    });
    return handleResponse(response);
};
