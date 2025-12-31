import React, { useState, useEffect } from 'react';
import { api, SystemMetrics } from '../services/api';
import { Loader2, CheckCircle, ExternalLink, Code, Server, Database, Cpu } from 'lucide-react';

const Documentation = () => {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [apiStatus, setApiStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  useEffect(() => {
    const checkApi = async () => {
      try {
        await api.healthCheck();
        setApiStatus('online');
        const metricsData = await api.getSystemMetrics();
        setMetrics(metricsData);
      } catch {
        setApiStatus('offline');
      }
    };
    checkApi();
  }, []);

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="border-b border-slate-200 pb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">System Documentation</h1>
            <p className="text-slate-500 mt-2">Version 2.0 - Production Ready</p>
          </div>
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium ${
            apiStatus === 'online' ? 'bg-green-100 text-green-700' :
            apiStatus === 'offline' ? 'bg-red-100 text-red-700' :
            'bg-slate-100 text-slate-600'
          }`}>
            {apiStatus === 'checking' ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : apiStatus === 'online' ? (
              <CheckCircle className="w-4 h-4" />
            ) : (
              <span className="w-2 h-2 rounded-full bg-red-500" />
            )}
            API {apiStatus === 'checking' ? 'Checking...' : apiStatus === 'online' ? 'Connected' : 'Offline'}
          </div>
        </div>
      </div>

      {/* System Overview */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold text-slate-800">System Overview</h2>
        <p className="text-slate-600 leading-relaxed">
          The Renty Intelligent Dynamic Pricing System is an AI-powered solution for car rental operations.
          It utilizes an <strong>XGBoost ML model with {metrics?.model_accuracy || '95.35%'} demand prediction accuracy</strong>. 
          The system analyzes over <strong>{metrics?.total_contracts || '2.48 million'}</strong> rental contracts 
          spanning 2.88 years to provide real-time pricing recommendations based on demand, supply, and events.
        </p>
      </section>

      {/* Architecture Diagram */}
      <section className="bg-slate-900 text-white p-6 rounded-xl">
        <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
          <Server className="w-5 h-5" />
          System Architecture
        </h2>
        <div className="font-mono text-sm space-y-2 text-slate-300">
          <pre className="overflow-x-auto">{`
┌─────────────────────────────────────────────────────────────────┐
│                     RENTY DYNAMIC PRICING v2.0                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    REST API    ┌────────────────────────┐   │
│  │    React     │ ◄────────────► │   FastAPI Backend      │   │
│  │   Frontend   │   /api/*       │                        │   │
│  │  (Vite+TS)   │                │  ┌──────────────────┐  │   │
│  └──────────────┘                │  │  Pricing Engine  │  │   │
│                                  │  │    (XGBoost)     │  │   │
│  ┌──────────────┐                │  └──────────────────┘  │   │
│  │  Streamlit   │ ───────────────│                        │   │
│  │  Dashboard   │   (legacy)     │  ┌──────────────────┐  │   │
│  └──────────────┘                │  │ Pricing Rules    │  │   │
│                                  │  │ (Multipliers)    │  │   │
│                                  │  └──────────────────┘  │   │
│                                  └────────────────────────┘   │
│                                             │                  │
│                              ┌──────────────┴──────────────┐  │
│                              │                             │  │
│                    ┌─────────▼─────────┐   ┌───────────────▼─┐│
│                    │   SQL Server DB   │   │ Competitor APIs ││
│                    │  (VehicleHistory, │   │ (Booking.com,   ││
│                    │   Contracts, etc) │   │  Kayak)         ││
│                    └───────────────────┘   └─────────────────┘│
│                                                                │
└─────────────────────────────────────────────────────────────────┘
          `}</pre>
        </div>
      </section>

      {/* Pricing Rules Engine */}
      <section className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
          <Cpu className="w-5 h-5 text-blue-600" />
          Pricing Rules Engine
        </h2>
        <p className="text-sm text-slate-600 mb-4">
          Final Price = Base Price × Demand Multiplier × Supply Multiplier × Event Multiplier
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
            <span className="text-sm font-semibold block text-slate-700">Demand Multiplier</span>
            <span className="text-blue-600 font-mono text-lg">0.85x - 1.20x</span>
            <p className="text-xs text-slate-500 mt-1">Based on ML predicted vs historical demand</p>
          </div>
          <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
            <span className="text-sm font-semibold block text-slate-700">Supply Multiplier</span>
            <span className="text-blue-600 font-mono text-lg">0.90x - 1.15x</span>
            <p className="text-xs text-slate-500 mt-1">Based on fleet availability percentage</p>
          </div>
          <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
            <span className="text-sm font-semibold block text-slate-700">Event Multiplier</span>
            <span className="text-blue-600 font-mono text-lg">1.00x - 1.60x</span>
            <p className="text-xs text-slate-500 mt-1">Holidays, Ramadan, festivals, sports events</p>
          </div>
          <div className="p-4 bg-green-50 rounded-lg border border-green-100">
            <span className="text-sm font-semibold block text-green-700">Hajj Premium (Mecca)</span>
            <span className="text-green-600 font-mono text-lg">+45%</span>
            <p className="text-xs text-green-600 mt-1">Maximum premium during Hajj in Mecca</p>
          </div>
        </div>
        <div className="mt-4 p-3 bg-amber-50 border border-amber-100 rounded-lg">
          <p className="text-sm text-amber-800">
            <strong>Price Boundaries:</strong> Final multiplier is capped between 0.80x (max 20% discount) 
            and 2.50x (max 150% premium) to ensure reasonable pricing.
          </p>
        </div>
      </section>

      {/* API Endpoints */}
      <section className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
          <Code className="w-5 h-5 text-purple-600" />
          API Endpoints
        </h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg font-mono text-sm">
            <span className="text-slate-700">GET /api/branches</span>
            <span className="text-slate-500">List all branches</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg font-mono text-sm">
            <span className="text-slate-700">GET /api/pricing/all/:branchId</span>
            <span className="text-slate-500">Get all category pricing</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg font-mono text-sm">
            <span className="text-slate-700">POST /api/pricing</span>
            <span className="text-slate-500">Calculate specific price</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg font-mono text-sm">
            <span className="text-slate-700">GET /api/competitors/:branchId/:category</span>
            <span className="text-slate-500">Get competitor prices</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg font-mono text-sm">
            <span className="text-slate-700">GET /api/metrics</span>
            <span className="text-slate-500">System metrics</span>
          </div>
        </div>
        <a 
          href="http://localhost:8000/docs" 
          target="_blank" 
          rel="noopener noreferrer"
          className="mt-4 inline-flex items-center text-sm text-blue-600 hover:text-blue-700"
        >
          View Full API Documentation <ExternalLink className="w-4 h-4 ml-1" />
        </a>
      </section>

      {/* Data Sources */}
      <section className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
          <Database className="w-5 h-5 text-amber-600" />
          Data Sources
        </h2>
        <div className="space-y-4">
          <div className="p-4 border border-slate-100 rounded-lg">
            <h4 className="font-semibold text-slate-700">Internal Database (SQL Server)</h4>
            <ul className="mt-2 text-sm text-slate-600 space-y-1">
              <li>• <code className="bg-slate-100 px-1 rounded">Fleet.VehicleHistory</code> - Real-time utilization</li>
              <li>• <code className="bg-slate-100 px-1 rounded">Rental.Contract</code> - Historical contracts (2.48M+)</li>
              <li>• <code className="bg-slate-100 px-1 rounded">Rental.RentalRates</code> - Pricing history</li>
            </ul>
          </div>
          <div className="p-4 border border-slate-100 rounded-lg">
            <h4 className="font-semibold text-slate-700">External APIs</h4>
            <ul className="mt-2 text-sm text-slate-600 space-y-1">
              <li>• Booking.com Car Rental API - Competitor pricing</li>
              <li>• Kayak Search API - Additional competitor data</li>
            </ul>
          </div>
          <div className="p-4 border border-slate-100 rounded-lg">
            <h4 className="font-semibold text-slate-700">External Features</h4>
            <ul className="mt-2 text-sm text-slate-600 space-y-1">
              <li>• KSA Public Holidays (2023-2025)</li>
              <li>• Ramadan & Hajj periods</li>
              <li>• School vacations</li>
              <li>• Major events (F1, Riyadh Season, etc.)</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Future Roadmap */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold text-slate-800">Future Roadmap</h2>
        <div className="space-y-4">
          <div className="flex border-l-4 border-blue-500 pl-4">
            <div className="flex-shrink-0 w-24 font-bold text-slate-500">Q1-Q2 2026</div>
            <div>
              <h3 className="font-semibold text-slate-900">Phase 1</h3>
              <p className="text-slate-600 text-sm">7-day forecast horizon (currently 1-2 days), automated competitor price tracking.</p>
            </div>
          </div>
          <div className="flex border-l-4 border-purple-500 pl-4">
            <div className="flex-shrink-0 w-24 font-bold text-slate-500">Q3-Q4 2026</div>
            <div>
              <h3 className="font-semibold text-slate-900">Phase 2</h3>
              <p className="text-slate-600 text-sm">Weather impact integration, Customer segmentation & personalized pricing.</p>
            </div>
          </div>
          <div className="flex border-l-4 border-green-500 pl-4">
            <div className="flex-shrink-0 w-24 font-bold text-slate-500">2027+</div>
            <div>
              <h3 className="font-semibold text-slate-900">Phase 3</h3>
              <p className="text-slate-600 text-sm">AI-powered reinforcement learning, Multi-location fleet optimization.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Quick Start */}
      <section className="bg-slate-900 text-white p-6 rounded-xl">
        <h2 className="text-lg font-bold mb-4">Quick Start</h2>
        <div className="space-y-4 font-mono text-sm">
          <div>
            <p className="text-slate-400 mb-1"># Start the API server</p>
            <code className="text-green-400">python api_server.py</code>
          </div>
          <div>
            <p className="text-slate-400 mb-1"># Start the React frontend</p>
            <code className="text-green-400">cd frontend_prototype && npm run dev</code>
          </div>
          <div>
            <p className="text-slate-400 mb-1"># Or start the Streamlit dashboard</p>
            <code className="text-green-400">streamlit run dashboard_manager.py</code>
          </div>
        </div>
      </section>

      {/* Footer */}
      <div className="text-center text-sm text-slate-500 pb-8">
        <p>Renty Intelligent Dynamic Pricing System v2.0</p>
        <p>Model: {metrics?.model_version || 'ROBUST_v4'} | Accuracy: {metrics?.model_accuracy || '95.35%'}</p>
      </div>
    </div>
  );
};

export default Documentation;
