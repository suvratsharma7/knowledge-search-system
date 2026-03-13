import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    server: {
        proxy: {
            '/search': 'http://localhost:8000',
            '/feedback': 'http://localhost:8000',
            '/health': 'http://localhost:8000',
            '/metrics': 'http://localhost:8000',
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            }
        }
    }
})
