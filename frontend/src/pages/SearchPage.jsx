import { useState, useMemo } from 'react';
import { searchDocs } from '../api';

/**
 * Score Bar Component for visualizing BM25, Vector, and Hybrid scores.
 */
function ScoreBar({ label, value, colorClass }) {
    // Normalize value for visualization (assuming it's roughly 0-1)
    const width = Math.min(Math.max(value * 100, 0), 100);

    return (
        <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-semibold text-gray-500 uppercase w-12">{label}</span>
            <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                <div
                    className={`h-full ${colorClass} transition-all duration-500 ease-out`}
                    style={{ width: `${width}%` }}
                />
            </div>
            <span className="text-[10px] font-mono text-gray-400 w-8 text-right">{value.toFixed(3)}</span>
        </div>
    );
}

/**
 * Parses **bold** markers into <b> tags.
 */
function HighlightedSnippet({ text }) {
    if (!text) return null;

    // Replace **text** with <b>text</b>
    const html = text.replace(/\*\*(.*?)\*\*/g, '<b class="text-white font-bold">$1</b>');

    return (
        <p
            className="text-gray-400 text-sm leading-relaxed"
            dangerouslySetInnerHTML={{ __html: html }}
        />
    );
}

export default function SearchPage() {
    const [query, setQuery] = useState('');
    const [topK, setTopK] = useState(10);
    const [alpha, setAlpha] = useState(0.5);
    const [normalization, setNormalization] = useState('minmax');

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [results, setResults] = useState(null);

    const handleSearch = async (e) => {
        if (e) e.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        setError(null);
        try {
            const data = await searchDocs(query, topK, alpha, normalization);
            setResults(data);
        } catch (err) {
            setError(err.message);
            setResults(null);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto py-8 px-6">
            {/* Search Controls Card */}
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl mb-8">
                <form onSubmit={handleSearch} className="space-y-6">
                    {/* Query Input */}
                    <div>
                        <label className="block text-xs font-semibold text-gray-500 uppercase mb-2">Query</label>
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="e.g. Sherlock Holmes detective"
                            className="w-full bg-gray-950 border border-gray-800 focus:border-blue-500 rounded-xl px-4 py-3 text-white placeholder-gray-600 outline-none transition-all"
                        />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {/* Top K */}
                        <div>
                            <label className="block text-xs font-semibold text-gray-500 uppercase mb-2">Top Results</label>
                            <input
                                type="number"
                                value={topK}
                                onChange={(e) => setTopK(parseInt(e.target.value, 10))}
                                min="1"
                                max="100"
                                className="w-full bg-gray-950 border border-gray-800 focus:border-blue-500 rounded-xl px-4 py-2 text-white outline-none transition-all"
                            />
                        </div>

                        {/* Alpha Slider */}
                        <div>
                            <div className="flex justify-between items-center mb-2">
                                <label className="text-xs font-semibold text-gray-500 uppercase">Alpha (BM25 Weight)</label>
                                <span className="text-xs font-mono text-blue-400">{alpha.toFixed(2)}</span>
                            </div>
                            <input
                                type="range"
                                value={alpha}
                                onChange={(e) => setAlpha(parseFloat(e.target.value))}
                                min="0"
                                max="1"
                                step="0.05"
                                className="w-full h-1.5 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                            />
                            <div className="flex justify-between mt-1">
                                <span className="text-[10px] text-gray-600">Vector</span>
                                <span className="text-[10px] text-gray-600">BM25</span>
                            </div>
                        </div>

                        {/* Normalization */}
                        <div>
                            <label className="block text-xs font-semibold text-gray-500 uppercase mb-2">Normalization</label>
                            <select
                                value={normalization}
                                onChange={(e) => setNormalization(e.target.value)}
                                className="w-full bg-gray-950 border border-gray-800 focus:border-blue-500 rounded-xl px-4 py-2 text-white outline-none transition-all appearance-none"
                            >
                                <option value="minmax">Min-Max Scale</option>
                                <option value="zscore">Z-Score (Standard)</option>
                            </select>
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={loading || !query.trim()}
                        className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 disabled:text-gray-600 text-white font-bold py-3 rounded-xl transition-all shadow-lg shadow-blue-900/20 flex items-center justify-center gap-2"
                    >
                        {loading ? (
                            <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                        ) : (
                            'Search Intelligence'
                        )}
                    </button>
                </form>
            </div>

            {/* Results Section */}
            <div className="space-y-6">
                {error && (
                    <div className="p-4 bg-red-900/20 border border-red-900/50 rounded-xl text-red-500 text-sm">
                        Error: {error}
                    </div>
                )}

                {results && (
                    <>
                        <div className="flex justify-between items-center px-2">
                            <span className="text-sm font-medium text-gray-400">
                                Found {results.results.length} results
                            </span>
                            <span className="text-xs font-mono text-gray-500">
                                Latency: {results.latency_ms.toFixed(2)}ms
                            </span>
                        </div>

                        {results.results.length === 0 ? (
                            <div className="bg-gray-900 border border-gray-800 border-dashed rounded-2xl p-12 text-center">
                                <p className="text-gray-500">No documents matched your curiosity. Try broadening your terms.</p>
                            </div>
                        ) : (
                            results.results.map((result, idx) => (
                                <div
                                    key={`${result.doc_id}-${idx}`}
                                    className="bg-gray-900 border border-gray-800 rounded-2xl p-6 hover:border-gray-700 transition-all hover:shadow-2xl hover:shadow-black/50 group"
                                >
                                    <div className="flex justify-between items-start mb-4">
                                        <h3 className="text-lg font-bold text-white group-hover:text-blue-400 transition-colors">
                                            {result.title || result.doc_id}
                                        </h3>
                                        <span className="text-[10px] font-mono bg-gray-950 px-2 py-1 rounded border border-gray-800 text-gray-500">
                                            {result.doc_id}
                                        </span>
                                    </div>

                                    <HighlightedSnippet text={result.snippet} />

                                    <div className="mt-6 pt-4 border-t border-gray-800 grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-2">
                                        <ScoreBar label="BM25" value={result.bm25_score || 0} colorClass="bg-blue-500" />
                                        <ScoreBar label="Vector" value={result.vector_score || 0} colorClass="bg-purple-500" />
                                        <div className="sm:col-span-2 mt-1">
                                            <ScoreBar label="Hybrid" value={result.score} colorClass="bg-green-500" />
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </>
                )}

                {!results && !loading && !error && (
                    <div className="py-20 text-center">
                        <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-900 rounded-2xl mb-4 text-gray-600">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                        </div>
                        <h3 className="text-white font-medium">Ready for your query</h3>
                        <p className="text-gray-500 text-sm mt-1">Enter a topic above to begin searching the digital library.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
