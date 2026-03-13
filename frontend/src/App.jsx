import { lazy, Suspense, useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { fetchHealth } from './api';

// Lazy-loaded pages
const SearchPage = lazy(() => import('./pages/SearchPage'));
const KPIPage = lazy(() => import('./pages/KPIPage'));
const EvalPage = lazy(() => import('./pages/EvalPage'));
const DebugPage = lazy(() => import('./pages/DebugPage'));

/**
 * API Status Indicator Component
 */
function ApiStatus() {
    const [status, setStatus] = useState('checking'); // 'ok', 'error', 'checking'

    useEffect(() => {
        fetchHealth()
            .then(() => setStatus('ok'))
            .catch(() => setStatus('error'));
    }, []);

    return (
        <div className="flex items-center gap-2 px-3 py-1 bg-gray-900 border border-gray-800 rounded-full">
            <div className={`w-2 h-2 rounded-full ${status === 'ok' ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' :
                    status === 'error' ? 'bg-red-500 animate-pulse' :
                        'bg-yellow-500'
                }`} />
            <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">
                API: {status === 'ok' ? 'Online' : status === 'error' ? 'Offline' : 'Connecting'}
            </span>
        </div>
    );
}

/**
 * Navigation Link Component
 */
function NavbarLink({ to, children }) {
    return (
        <NavLink
            to={to}
            className={({ isActive }) =>
                `px-4 py-2 text-sm font-medium transition-all duration-200 rounded-lg ${isActive
                    ? 'text-white bg-blue-600 shadow-lg shadow-blue-900/20'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                }`
            }
        >
            {children}
        </NavLink>
    );
}

function App() {
    return (
        <BrowserRouter>
            <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">
                {/* Navigation Bar */}
                <nav className="h-16 border-b border-gray-800 bg-gray-950/80 backdrop-blur-md sticky top-0 z-50">
                    <div className="max-w-7xl mx-auto h-full px-6 flex items-center justify-between">
                        <div className="flex items-center gap-8">
                            <div className="flex items-center gap-2">
                                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center font-bold text-lg">K</div>
                                <h1 className="text-xl font-bold tracking-tight hidden sm:block">
                                    Knowledge <span className="text-blue-500">Search</span>
                                </h1>
                            </div>

                            <div className="flex items-center gap-1">
                                <NavbarLink to="/">Search</NavbarLink>
                                <NavbarLink to="/kpi">KPI Dashboard</NavbarLink>
                                <NavbarLink to="/eval">Evaluation</NavbarLink>
                                <NavbarLink to="/debug">Debug</NavbarLink>
                            </div>
                        </div>

                        <ApiStatus />
                    </div>
                </nav>

                {/* Content Area */}
                <main className="flex-1 max-w-7xl mx-auto w-full">
                    <Suspense fallback={
                        <div className="flex items-center justify-center h-64">
                            <div className="w-8 h-8 border-4 border-blue-600/20 border-t-blue-600 rounded-full animate-spin" />
                        </div>
                    }>
                        <Routes>
                            <Route path="/" element={<SearchPage />} />
                            <Route path="/kpi" element={<KPIPage />} />
                            <Route path="/eval" element={<EvalPage />} />
                            <Route path="/debug" element={<DebugPage />} />
                        </Routes>
                    </Suspense>
                </main>
            </div>
        </BrowserRouter>
    );
}

export default App;
