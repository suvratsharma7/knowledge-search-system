import { useState, useEffect, useCallback } from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { fetchLogs } from '../api';

/**
 * Metric Card for Latency
 */
function LatencyMetric({ label, value, p95Thresholds }) {
    const getColor = (val) => {
        if (!val) return 'text-gray-600';
        if (val < 300) return 'text-green-500';
        if (val < 800) return 'text-yellow-500';
        return 'text-red-500';
    };

    return (
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 flex flex-col items-center justify-center shadow-inner">
            <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">{label}</span>
            <div className={`text-4xl font-black ${getColor(value)} transition-colors duration-500`}>
                {value ? `${value.toFixed(1)}` : '--'}
                <span className="text-sm font-normal ml-1 opacity-50">ms</span>
            </div>
        </div>
    );
}

/**
 * Section Container
 */
function Section({ title, loading, children }) {
    return (
        <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden flex flex-col h-full shadow-lg">
            <div className="px-6 py-4 border-b border-gray-800 flex justify-between items-center bg-gray-900/50">
                <h3 className="text-xs font-bold text-white uppercase tracking-widest">{title}</h3>
                {loading && (
                    <div className="w-4 h-4 border-2 border-blue-600/20 border-t-blue-600 rounded-full animate-spin" />
                )}
            </div>
            <div className="p-6 flex-1 min-h-[300px]">
                {children}
            </div>
        </div>
    );
}

export default function KPIPage() {
    const [metrics, setMetrics] = useState({
        p50: 0,
        p95: 0,
        volume: [],
        topQueries: [],
        zeroResults: []
    });
    const [loading, setLoading] = useState(true);

    const processLogs = useCallback((rawLogs) => {
        // Handle both direct array and wrapped {data: []}
        const data = Array.isArray(rawLogs) ? rawLogs : (rawLogs.data || []);
        
        if (data.length === 0) return;

        // 1. Calculate Latencies
        const latencies = data.map(l => l.latency_ms || 0).sort((a, b) => a - b);
        const p50 = latencies[Math.floor(latencies.length * 0.5)];
        const p95 = latencies[Math.floor(latencies.length * 0.95)];

        // 2. Process Volume (Group by hour/minute for the chart)
        const volumeMap = {};
        data.forEach(l => {
            const time = new Date(l.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            volumeMap[time] = (volumeMap[time] || 0) + 1;
        });
        const volumeChart = Object.entries(volumeMap).map(([time, count]) => ({ hour: time, count })).reverse();

        // 3. Top Queries
        const queryMap = {};
        data.forEach(l => {
            if (l.query && l.query !== 'N/A') {
                queryMap[l.query] = (queryMap[l.query] || 0) + 1;
            }
        });
        const topQueries = Object.entries(queryMap)
            .map(([query, count]) => ({ query, count }))
            .sort((a, b) => b.count - a.count)
            .slice(0, 10);

        // 4. Zero Results
        const zeroResults = data
            .filter(l => l.result_count === 0)
            .map(l => ({ query: l.query, count: 1 }))
            .slice(0, 5);

        setMetrics({ p50, p95, volume: volumeChart, topQueries, zeroResults });
    }, []);

    const refreshData = useCallback(async () => {
        setLoading(true);
        try {
            const rawLogs = await fetchLogs(100);
            processLogs(rawLogs);
        } catch (err) {
            console.error("KPI Refresh Error:", err);
        } finally {
            setLoading(false);
        }
    }, [processLogs]);

    useEffect(() => {
        refreshData();
        const interval = setInterval(refreshData, 15000); // Faster 15s refresh
        return () => clearInterval(interval);
    }, [refreshData]);

    return (
        <div className="max-w-7xl mx-auto py-8 px-6">
            <div className="flex justify-between items-end mb-8">
                <div>
                    <h2 className="text-3xl font-bold text-white">KPI Dashboard</h2>
                    <p className="text-gray-400 mt-1">Real-time system health from recent telemetry</p>
                </div>
                <div className="text-[10px] text-gray-500 font-mono bg-gray-900 px-3 py-1 rounded-full border border-gray-800">
                    Auto-refreshing 15s
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-8">
                    <div className="grid grid-cols-2 gap-4">
                        <LatencyMetric label="p50 Latency" value={metrics.p50} />
                        <LatencyMetric label="p95 Latency" value={metrics.p95} />
                    </div>

                    <Section title="Request Activity (Recent)" loading={loading}>
                        {metrics.volume.length > 0 ? (
                            <div className="h-[250px] w-full">
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={metrics.volume}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                                        <XAxis dataKey="hour" stroke="#4b5563" fontSize={10} tickLine={false} axisLine={false} />
                                        <YAxis stroke="#4b5563" fontSize={10} tickLine={false} axisLine={false} />
                                        <Tooltip contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '8px' }} />
                                        <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={3} dot={{ fill: '#3b82f6', r: 4 }} />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        ) : (
                            <div className="flex flex-col items-center justify-center h-full text-gray-600">
                                <p className="text-sm">Waiting for search traffic...</p>
                            </div>
                        )}
                    </Section>
                </div>

                <Section title="High-Frequency Queries" loading={loading}>
                    {metrics.topQueries.length > 0 ? (
                        <div className="overflow-hidden rounded-xl border border-gray-800">
                            <table className="w-full text-left text-sm">
                                <tbody className="divide-y divide-gray-800">
                                    {metrics.topQueries.map((item, i) => (
                                        <tr key={i} className="hover:bg-gray-800/20">
                                            <td className="px-4 py-3 text-gray-300 font-medium truncate">{item.query}</td>
                                            <td className="px-4 py-3 text-right font-mono text-blue-400">{item.count}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full text-gray-600">
                            <p className="text-sm">No queries recorded yet</p>
                        </div>
                    )}
                </Section>
            </div>
        </div>
    );
}
