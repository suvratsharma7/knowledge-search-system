/**
 * API Service layer for Knowledge Search
 */

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

export const fetchLogs = async (limit = 100, severity = null, startTime = null, endTime = null) => {
    const params = new URLSearchParams({ limit });
    if (severity) params.append('severity', severity);
    if (startTime) params.append('start_time', startTime);
    if (endTime) params.append('end_time', endTime);

    const response = await fetch(`/api/logs?${params.toString()}`);
    return handleResponse(response);
};

export const submitFeedback = async (query, docId, relevance) => {
    const response = await fetch('/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, doc_id: docId, relevance }),
    });
    return handleResponse(response);
};
