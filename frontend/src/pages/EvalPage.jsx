import { useState, useEffect, useMemo } from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
    ScatterChart, Scatter, ZAxis
} from 'recharts';
import { fetchExperiments } from '../api';

/**
 * Empty State for Evaluation Page
 */
function EmptyEval() {
    return (
        <div className="bg-gray-900 border border-gray-800 border-dashed rounded-2xl p-12 text-center max-w-2xl mx-auto">
            <div className="w-16 h-16 bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-6 text-gray-500">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
            </div>
            <h3 className="text-xl font-bold text-white mb-2">No Experiments Yet</h3>
            <p className="text-gray-400 mb-8">
                Run the evaluation harness CLI to populate this dashboard with data and track your search performance improvements.
            </p>
            <div className="bg-gray-950 p-4 rounded-lg border border-gray-800 text-left">
                <p className="text-xs font-mono text-blue-400 mb-2"># Run this command in the backend directory:</p>
                <code className="text-sm font-mono text-gray-300">python -m app.eval --alpha 0.5</code>
            </div>
        </div>
    );
}

export default function EvalPage() {
    const [experiments, setExperiments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchExperiments()
            .then(data => {
                // Sort by timestamp descending
                const sorted = data.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
                setExperiments(sorted);
                setLoading(false);
            })
            .catch(err => {
                setError(err.message);
                setLoading(false);
            });
    }, []);

    const bestNdcg = useMemo(() => {
        if (experiments.length === 0) return 0;
        return Math.max(...experiments.map(e => e.ndcg_10));
    }, [experiments]);

    const trendData = useMemo(() => {
        return [...experiments].reverse().map((e, idx) => ({
            ...e,
            index: idx + 1,
            shortTime: new Date(e.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }));
    }, [experiments]);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="w-8 h-8 border-4 border-blue-600/20 border-t-blue-600 rounded-full animate-spin" />
            </div>
        );
    }

    if (experiments.length === 0) {
        return (
            <div className="py-20 px-6">
                <EmptyEval />
            </div>
        );
    }

    return (
        <div className="max-w-7xl mx-auto py-8 px-6">
            <div className="mb-10">
                <h2 className="text-3xl font-bold text-white">Evaluation Results</h2>
                <p className="text-gray-400 mt-1">Quantitative benchmarking and parameter sensitivity analysis</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
                {/* Metric Trends */}
                <div className="lg:col-span-2 bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-lg h-[400px]">
                    <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-6">Performance Trends</h3>
                    <ResponsiveContainer width="100%" height="85%">
                        <LineChart data={trendData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                            <XAxis dataKey="index" stroke="#4b5563" fontSize={10} tickLine={false} axisLine={false} />
                            <YAxis domain={[0, 1]} stroke="#4b5563" fontSize={10} tickLine={false} axisLine={false} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '8px' }}
                                itemStyle={{ fontSize: '12px' }}
                            />
                            <Legend verticalAlign="top" height={36} />
                            <Line type="monotone" dataKey="ndcg_10" name="nDCG@10" stroke="#3b82f6" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                            <Line type="monotone" dataKey="recall_10" name="Recall@10" stroke="#a855f7" strokeWidth={2} dot={{ r: 4 }} />
                            <Line type="monotone" dataKey="mrr_10" name="MRR@10" stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>

                {/* Alpha Impact */}
                <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-lg h-[400px]">
                    <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-6">Alpha Sensitivity (nDCG)</h3>
                    <ResponsiveContainer width="100%" height="85%">
                        <ScatterChart>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                            <XAxis type="number" dataKey="alpha" name="Alpha" domain={[0, 1]} stroke="#4b5563" fontSize={10} />
                            <YAxis type="number" dataKey="ndcg_10" name="nDCG" domain={[0, 1]} stroke="#4b5563" fontSize={10} />
                            <ZAxis range={[100, 100]} />
                            <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '8px' }} />
                            <Scatter name="Experiments" data={experiments} fill="#3b82f6" />
                        </ScatterChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Experiment Registry Table */}
            <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden shadow-xl">
                <div className="px-6 py-4 border-b border-gray-800 bg-gray-900/50">
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider">Experiment Registry</h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead>
                            <tr className="bg-gray-800/10 border-b border-gray-800">
                                <th className="px-6 py-4 font-semibold text-gray-500 uppercase text-[10px]">Timestamp</th>
                                <th className="px-6 py-4 font-semibold text-gray-500 uppercase text-[10px]">Alpha</th>
                                <th className="px-6 py-4 font-semibold text-gray-500 uppercase text-[10px]">Norm</th>
                                <th className="px-6 py-4 font-semibold text-gray-500 uppercase text-[10px]">nDCG@10</th>
                                <th className="px-6 py-4 font-semibold text-gray-500 uppercase text-[10px]">Recall@10</th>
                                <th className="px-6 py-4 font-semibold text-gray-500 uppercase text-[10px]">MRR@10</th>
                                <th className="px-6 py-4 font-semibold text-gray-500 uppercase text-[10px]">Commit</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-800">
                            {experiments.map((exp, idx) => {
                                const isBest = exp.ndcg_10 === bestNdcg;
                                return (
                                    <tr key={idx} className={`transition-colors hover:bg-gray-800/20 ${isBest ? 'bg-green-950/20' : ''}`}>
                                        <td className="px-6 py-4 text-gray-400 whitespace-nowrap">
                                            {new Date(exp.timestamp).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                                        </td>
                                        <td className="px-6 py-4 text-white font-medium">{exp.alpha.toFixed(2)}</td>
                                        <td className="px-6 py-4">
                                            <span className="bg-gray-800 px-2 py-0.5 rounded text-[10px] text-gray-300 font-mono">
                                                {exp.normalization}
                                            </span>
                                        </td>
                                        <td className={`px-6 py-4 font-mono font-bold ${isBest ? 'text-green-500' : 'text-blue-400'}`}>
                                            {exp.ndcg_10.toFixed(4)}
                                        </td>
                                        <td className="px-6 py-4 font-mono text-purple-400">{exp.recall_10.toFixed(4)}</td>
                                        <td className="px-6 py-4 font-mono text-emerald-400">{exp.mrr_10.toFixed(4)}</td>
                                        <td className="px-6 py-4">
                                            <span className="text-gray-600 font-mono text-[10px]">
                                                {exp.commit_hash?.slice(0, 7) || 'unknown'}
                                            </span>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
