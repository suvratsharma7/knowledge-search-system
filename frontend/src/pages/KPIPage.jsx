import { useState, useEffect, useCallback } from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import {
    fetchLatency, fetchVolume, fetchTopQueries, fetchZeroResults
} from '../api';

/**
 * Metric Card for Latency
 */
function LatencyMetric({ label, value, p95Thresholds }) {
    const getColor = (val) => {
        if (!p95Thresholds) return 'text-white';
        if (val < 500) return 'text-green-500';
        if (val < 1000) return 'text-yellow-500';
        return 'text-red-500';
    };

    return (
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 flex flex-col items-center justify-center">
            <span className="text-xs font-semibold text-gray-550 uppercase mb-2">{label}</span>
            <div className={`text-4xl font-black ${getColor(value)}`}>
                {value ? `${value.toFixed(0)}` : '--'}
                <span className="text-sm font-normal ml-1">ms</span>
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
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">{title}</h3>
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
    const [latency, setLatency] = useState(null);
    const [volume, setVolume] = useState([]);
    const [topQueries, setTopQueries] = useState([]);
    const [zeroResults, setZeroResults] = useState([]);

    const [loading, setLoading] = useState({
        latency: true,
        volume: true,
        top: true,
        zero: true
    });

    const refreshData = useCallback(async () => {
        // Latency
        fetchLatency().then(data => {
            setLatency(data);
            setLoading(prev => ({ ...prev, latency: false }));
        }).catch(() => setLoading(prev => ({ ...prev, latency: false })));

        // Volume
        fetchVolume().then(data => {
            setVolume(data);
            setLoading(prev => ({ ...prev, volume: false }));
        }).catch(() => setLoading(prev => ({ ...prev, volume: false })));

        // Top Queries
        fetchTopQueries().then(data => {
            setTopQueries(data);
            setLoading(prev => ({ ...prev, top: false }));
        }).catch(() => setLoading(prev => ({ ...prev, top: false })));

        // Zero Results
        fetchZeroResults().then(data => {
            setZeroResults(data);
            setLoading(prev => ({ ...prev, zero: false }));
        }).catch(() => setLoading(prev => ({ ...prev, zero: false })));
    }, []);

    useEffect(() => {
        refreshData();
        const interval = setInterval(refreshData, 30000); // 30s auto-refresh
        return () => clearInterval(interval);
    }, [refreshData]);

    return (
        <div className="max-w-7xl mx-auto py-8 px-6">
            <div className="flex justify-between items-end mb-8">
                <div>
                    <h2 className="text-3xl font-bold text-white">KPI Dashboard</h2>
                    <p className="text-gray-400 mt-1">Real-time system health and performance monitoring</p>
                </div>
                <div className="text-xs text-gray-500 font-mono">
                    Auto-refreshing every 30s
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Row 1: Latency and Volume */}
                <div className="space-y-8">
                    <div className="grid grid-cols-2 gap-4">
                        <LatencyMetric label="p50 Latency" value={latency?.p50_latency} />
                        <LatencyMetric
                            label="p95 Latency"
                            value={latency?.p95_latency}
                            p95Thresholds={true}
                        />
                    </div>

                    <Section title="Request Volume (Last 24h)" loading={loading.volume}>
                        {volume.length > 0 ? (
                            <div className="h-[250px] w-full">
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={volume}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                                        <XAxis
                                            dataKey="hour"
                                            stroke="#4b5563"
                                            fontSize={10}
                                            tickLine={false}
                                            axisLine={false}
                                        />
                                        <YAxis
                                            stroke="#4b5563"
                                            fontSize={10}
                                            tickLine={false}
                                            axisLine={false}
                                        />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '8px' }}
                                            itemStyle={{ color: '#60a5fa' }}
                                        />
                                        <Line
                                            type="monotone"
                                            dataKey="count"
                                            stroke="#2563eb"
                                            strokeWidth={3}
                                            dot={{ fill: '#2563eb', strokeWidth: 2, r: 4 }}
                                            activeDot={{ r: 6, strokeWidth: 0 }}
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        ) : (
                            <div className="flex flex-col items-center justify-center h-full text-gray-600">
                                <svg className="w-12 h-12 mb-2 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                                </svg>
                                <p className="text-sm">No volume data available</p>
                            </div>
                        )}
                    </Section>
                </div>

                {/* Top Queries */}
                <Section title="Top 10 High-Frequency Queries" loading={loading.top}>
                    {topQueries.length > 0 ? (
                        <div className="overflow-hidden rounded-xl border border-gray-800">
                            <table className="w-full text-left text-sm">
                                <thead>
                                    <tr className="bg-gray-800/10 border-b border-gray-800">
                                        <th className="px-4 py-3 font-semibold text-gray-500 uppercase text-[10px]">Query</th>
                                        <th className="px-4 py-3 font-semibold text-gray-500 uppercase text-[10px] text-right">Count</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-800">
                                    {topQueries.map((item, i) => (
                                        <tr key={i} className="hover:bg-gray-800/20 transition-colors">
                                            <td className="px-4 py-3 text-gray-300 font-medium truncate max-w-[200px]">{item.query}</td>
                                            <td className="px-4 py-3 text-right font-mono text-blue-400">{item.count}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full text-gray-600">
                            <p className="text-sm">No top queries recorded yet</p>
                        </div>
                    )}
                </Section>

                {/* Zero Results */}
                <Section title="Zero-Result Queries" loading={loading.zero}>
                    {zeroResults.length > 0 ? (
                        <div className="overflow-hidden rounded-xl border border-gray-800">
                            <table className="w-full text-left text-sm">
                                <thead>
                                    <tr className="bg-gray-800/10 border-b border-gray-800">
                                        <th className="px-4 py-3 font-semibold text-gray-400 uppercase text-[10px]">Query</th>
                                        <th className="px-4 py-3 font-semibold text-gray-400 uppercase text-[10px] text-right">Misses</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-800">
                                    {zeroResults.map((item, i) => (
                                        <tr key={i} className="hover:bg-red-950/20 transition-colors">
                                            <td className="px-4 py-3 text-red-100 font-medium truncate max-w-[200px]">{item.query}</td>
                                            <td className="px-4 py-3 text-right font-mono text-orange-500">{item.count}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full text-gray-600">
                            <p className="text-sm">Excellent! No zero-result queries yet.</p>
                        </div>
                    )}
                </Section>
            </div>
        </div>
    );
}
