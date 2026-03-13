import { useState } from 'react'

function App() {
    return (
        <div className="min-h-screen bg-gray-950 p-8">
            <header className="max-w-6xl mx-auto flex justify-between items-center mb-12">
                <div>
                    <h1 className="text-4xl font-bold text-white tracking-tight">
                        Knowledge <span className="text-blue-500">Search</span>
                    </h1>
                    <p className="text-gray-400 mt-2">Enterprise-grade semantic discovery engine</p>
                </div>
            </header>

            <main className="max-w-6xl mx-auto">
                <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 text-center">
                    <h2 className="text-2xl font-semibold text-white mb-4">Frontend Dashboard Initialized</h2>
                    <p className="text-gray-400 max-w-lg mx-auto">
                        The frontend boilerplate has been set up with Vite, React, and Tailwind CSS.
                        The API layer is ready to communicate with your FastAPI backend.
                    </p>
                    <div className="mt-8 flex justify-center gap-4">
                        <div className="px-4 py-2 bg-blue-600 rounded-lg text-white font-medium hover:bg-blue-500 transition-colors">
                            Ready for Components
                        </div>
                        <div className="px-4 py-2 bg-gray-800 rounded-lg text-gray-300 font-medium border border-gray-700">
                            Backend Proxy Connected
                        </div>
                    </div>
                </div>
            </main>
        </div>
    )
}

export default App
