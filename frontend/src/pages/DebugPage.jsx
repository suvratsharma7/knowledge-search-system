import React, { useState, useEffect, useCallback, useRef, Fragment } from 'react';
import { fetchLogs } from '../api';

/**
 * Log Details Expansion Component
 */
function LogDetails({ log }) {
    return (
        <tr className="bg-gray-950 border-x border-gray-800">
            <td colSpan="6" className="px-6 py-6 transition-all duration-300 animate-in fade-in slide-in-from-top-2">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-xs">
                    <div className="space-y-4">
                        <div>
                            <span className="block text-gray-500 uppercase font-bold mb-1">Request Information</span>
                            <p className="text-gray-300"><span className="text-gray-500">Query ID:</span> {log.request_id}</p>
                            <p className="text-gray-300"><span className="text-gray-500">Timestamp:</span> {new Date(log.timestamp).toISOString()}</p>
                        </div>
                        <div>
                            <span className="block text-gray-500 uppercase font-bold mb-1">Performance</span>
                            <p className="text-gray-300"><span className="text-gray-500">Latency:</span> {(log.latency_ms || 0).toFixed(2)}ms</p>
                            <p className="text-gray-300"><span className="text-gray-500">Results:</span> {log.result_count}</p>
                        </div>
                    </div>
                    <div className="space-y-4">
                        <div>
                            <span className="block text-gray-500 uppercase font-bold mb-1">Search Parameters</span>
                            <p className="text-gray-300"><span className="text-gray-500">Top K:</span> {log.top_k}</p>
                            <p className="text-gray-300"><span className="text-gray-500">Alpha:</span> {log.alpha}</p>
                        </div>
                        {log.error && (
                            <div>
                                <span className="block text-red-500 uppercase font-bold mb-1">Error Trace</span>
                                <pre className="p-3 bg-red-950/20 border border-red-900/50 rounded text-red-200 overflow-x-auto font-mono whitespace-pre-wrap">
                                    {log.error}
                                </pre>
                            </div>
                        )}
                    </div>
                </div>
            </td>
        </tr>
    );
}

export default function DebugPage() {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [expandedRow, setExpandedRow] = useState(null);

    // Filters State
    const [severity, setSeverity] = useState('all');
    const [startTime, setStartTime] = useState('');
    const [endTime, setEndTime] = useState('');
    const [limit, setLimit] = useState(50);
    const [autoRefresh, setAutoRefresh] = useState(false);

    const timerRef = useRef(null);

    const loadLogs = useCallback(async () => {
    setLoading(true);
    try {
        const response = await fetchLogs(
            limit,
            severity === 'all' ? null : severity,
            startTime ? new Date(startTime).toISOString() : null,
            endTime ? new Date(endTime).toISOString() : null
        );
        
        // FIX: Extract the array from the "data" property
        const logsArray = response.data || response || [];
        setLogs(logsArray);
        
        setError(null);
    } catch (err) {
        setError(err.message);
    } finally {
        setLoading(false);
    }
}, [limit, severity, startTime, endTime]);

    useEffect(() => {
        loadLogs();
    }, [loadLogs]);

    useEffect(() => {
        if (autoRefresh) {
            timerRef.current = setInterval(loadLogs, 10000);
        } else {
            if (timerRef.current) clearInterval(timerRef.current);
        }
        return () => {
            if (timerRef.current) clearInterval(timerRef.current);
        };
    }, [autoRefresh, loadLogs]);

    const toggleExpand = (id) => {
        setExpandedRow(expandedRow === id ? null : id);
    };

    return (
        <div className="max-w-7xl mx-auto py-8 px-6">
            <div className="flex justify-between items-end mb-8">
                <div>
                    <h2 className="text-3xl font-bold text-white">Debug Log Viewer</h2>
                    <p className="text-gray-400 mt-1">Structured telemetry and error diagnostics</p>
                </div>
                <div className="flex items-center gap-4">
                    <label className="flex items-center gap-2 cursor-pointer group">
                        <span className="text-xs font-semibold text-gray-500 group-hover:text-gray-300 transition-colors uppercase tracking-widest">Auto-Refresh (10s)</span>
                        <div
                            className={`relative w-10 h-5 px-1 flex items-center rounded-full transition-all duration-300 ${autoRefresh ? 'bg-blue-600' : 'bg-gray-800'}`}
                            onClick={() => setAutoRefresh(!autoRefresh)}
                        >
                            <div className={`w-3.5 h-3.5 bg-white rounded-full transition-all duration-300 shadow-sm ${autoRefresh ? 'translate-x-5' : 'translate-x-0'}`} />
                        </div>
                    </label>
                    <button
                        onClick={loadLogs}
                        disabled={loading}
                        className="px-4 py-2 bg-gray-900 border border-gray-800 rounded-lg text-xs font-bold uppercase tracking-widest text-gray-400 hover:text-white hover:border-gray-700 transition-all active:scale-95 flex items-center gap-2 disabled:opacity-50"
                    >
                        <svg className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        {loading ? 'Updating...' : 'Refresh'}
                    </button>
                </div>
            </div>

            {/* Filters Card */}
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-lg mb-8">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-end">
                    <div>
                        <label className="block text-xs font-semibold text-gray-500 uppercase mb-2">Severity</label>
                        <select
                            value={severity}
                            onChange={(e) => setSeverity(e.target.value)}
                            className="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-2 text-white outline-none focus:border-blue-500 text-sm"
                        >
                            <option value="all">All Logs</option>
                            <option value="info">Info only</option>
                            <option value="error">Errors only</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-xs font-semibold text-gray-500 uppercase mb-2">Start Time</label>
                        <input
                            type="datetime-local"
                            value={startTime}
                            onChange={(e) => setStartTime(e.target.value)}
                            className="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-2 text-white outline-none focus:border-blue-500 text-sm"
                        />
                    </div>

                    <div>
                        <label className="block text-xs font-semibold text-gray-500 uppercase mb-2">End Time</label>
                        <input
                            type="datetime-local"
                            value={endTime}
                            onChange={(e) => setEndTime(e.target.value)}
                            className="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-2 text-white outline-none focus:border-blue-500 text-sm"
                        />
                    </div>

                    <div>
                        <label className="block text-xs font-semibold text-gray-500 uppercase mb-2">Result Limit</label>
                        <input
                            type="number"
                            value={limit}
                            onChange={(e) => setLimit(parseInt(e.target.value, 10))}
                            min="1"
                            max="500"
                            className="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-2 text-white outline-none focus:border-blue-500 text-sm"
                        />
                    </div>
                </div>
            </div>

            {/* Logs Table */}
            <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden shadow-xl">
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead>
                            <tr className="bg-gray-800/10 border-b border-gray-800">
                                <th className="px-6 py-4 font-semibold text-gray-500 uppercase text-[10px]">Timestamp</th>
                                <th className="px-6 py-4 font-semibold text-gray-500 uppercase text-[10px]">Request ID</th>
                                <th className="px-6 py-4 font-semibold text-gray-500 uppercase text-[10px]">Query</th>
                                <th className="px-6 py-4 font-semibold text-gray-500 uppercase text-[10px] text-right">Latency</th>
                                <th className="px-6 py-4 font-semibold text-gray-500 uppercase text-[10px] text-right">Count</th>
                                <th className="px-6 py-4 font-semibold text-gray-500 uppercase text-[10px]">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-800">
                            {logs.length === 0 && !loading ? (
                                <tr>
                                    <td colSpan="6" className="px-6 py-12 text-center text-gray-600">
                                        No logs found matching your criteria.
                                    </td>
                                </tr>
                            ) : (
                                logs.map((log) => {
                                    const isError = Boolean(log.error);
                                    const isExpanded = expandedRow === log.request_id;

                                    return (
                                        <Fragment key={log.request_id}>
                                            <tr
                                                className={`cursor-pointer transition-colors ${isError ? 'bg-red-950/10 hover:bg-red-950/20' :
                                                    isExpanded ? 'bg-gray-800/40' : 'hover:bg-gray-800/20'
                                                    }`}
                                                onClick={() => toggleExpand(log.request_id)}
                                            >
                                                <td className="px-6 py-4 text-gray-500 font-mono text-[10px] whitespace-nowrap">
                                                    {new Date(log.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                                </td>
                                                <td className="px-6 py-4 font-mono text-gray-400 text-[10px]">
                                                    {log.request_id ? `${log.request_id.slice(0, 8)}...` : 'N/A'}
                                                </td>
                                                <td className="px-6 py-4 text-gray-200 truncate max-w-[200px]">{log.query || 'N/A'}</td>
                                                <td className="px-6 py-4 text-right font-mono text-xs text-blue-400">{(log.latency_ms || 0).toFixed(1)}ms</td>
                                                <td className="px-6 py-4 text-right font-mono text-xs text-purple-400">{log.result_count || 0}</td>
                                                <td className="px-6 py-4">
                                                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-widest border ${isError ? 'bg-red-900/20 text-red-400 border-red-900/50' : 'bg-green-900/20 text-green-400 border-green-900/50'
                                                        }`}>
                                                        {isError ? 'Error' : 'Success'}
                                                    </span>
                                                </td>
                                            </tr>
                                            {isExpanded && <LogDetails log={log} />}
                                        </Fragment>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {error && (
                <div className="mt-6 p-4 bg-red-900/20 border border-red-900/50 rounded-xl text-red-500 text-sm flex items-center gap-3">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {error}
                </div>
            )}
        </div>
    );
}