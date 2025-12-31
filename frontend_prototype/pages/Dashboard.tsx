import React, { useState, useEffect, useCallback } from 'react';
import { TrendingUp, Users, DollarSign, Activity, BrainCircuit, RefreshCw, AlertCircle, Calendar, Loader2, Database, Clock, Car } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import MetricCard from '../components/MetricCard';
import { generatePricingInsight } from '../services/geminiService';
import { api, AllPricingResponse, DemandDataPoint, SystemMetrics, CompetitorResponse } from '../services/api';
import { useAppContext } from '../context/AppContext';

interface PricingRecommendation {
  id: string;
  category: string;
  currentPrice: number;
  recommendedPrice: number;
  priceChangePct: number;
  demandMultiplier: number;
  supplyMultiplier: number;
  eventMultiplier: number;
  reason: string;
  confidence: number;
  status: 'Pending' | 'Approved' | 'Rejected';
}

interface EventFlags {
  is_holiday: boolean;
  is_school_vacation: boolean;
  is_ramadan: boolean;
  is_umrah_season: boolean;
  is_hajj: boolean;
  is_festival: boolean;
  is_sports_event: boolean;
  is_conference: boolean;
  is_weekend: boolean;
}

interface CarMatch {
  renty_model: string;
  renty_category: string;
  renty_price: number;
  best_competitor_price: number;
  price_diff: number;
  status: string;
  competitors: Array<{
    supplier: string;
    vehicle: string;
    price: number;
  }>;
}

const Dashboard = () => {
  // Get shared state from context
  const { branches, selectedBranch, userRole, multipliers } = useAppContext();
  
  // Local State
  const [pricingData, setPricingData] = useState<AllPricingResponse | null>(null);
  const [demandData, setDemandData] = useState<DemandDataPoint[]>([]);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [competitorData, setCompetitorData] = useState<Map<string, CompetitorResponse>>(new Map());
  const [carMatches, setCarMatches] = useState<CarMatch[]>([]);
  
  const [recommendations, setRecommendations] = useState<PricingRecommendation[]>([]);
  const [aiInsight, setAiInsight] = useState<string>('');
  const [loadingAi, setLoadingAi] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshingCompetitors, setRefreshingCompetitors] = useState(false);
  const [dbStatus, setDbStatus] = useState<{status: string; message?: string} | null>(null);
  
  const [eventFlags, setEventFlags] = useState<EventFlags>({
    is_holiday: false,
    is_school_vacation: false,
    is_ramadan: false,
    is_umrah_season: false,
    is_hajj: false,
    is_festival: false,
    is_sports_event: false,
    is_conference: false,
    is_weekend: false,
  });

  // Load initial data - ALL DATA IS BRANCH-SPECIFIC
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Load metrics and demand data in parallel - ALL BRANCH-SPECIFIC
      const [metricsData, demandDataResult] = await Promise.all([
        api.getSystemMetrics(selectedBranch),  // Branch-specific metrics
        api.getDemandData(selectedBranch),     // Branch-specific demand
      ]);
      
      setMetrics(metricsData);
      setDemandData(demandDataResult);
      
      // Load pricing for selected branch
      await loadPricingData(selectedBranch);
      
      // Test database connection
      try {
        const dbTest = await api.testDatabaseConnection();
        setDbStatus(dbTest);
      } catch {
        setDbStatus({ status: 'unknown', message: 'Could not check database' });
      }
      
    } catch (err) {
      console.error('Error loading data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [selectedBranch]);

  const loadPricingData = async (branchId: number) => {
    try {
      const pricingResult = await api.getAllCategoryPricing(branchId, eventFlags);
      setPricingData(pricingResult);
      
      // Convert to recommendations format - show ALL categories
      const recs: PricingRecommendation[] = pricingResult.categories
        .map((cat, idx) => ({
          id: String(idx + 1),
          category: cat.category,
          currentPrice: cat.base_price,
          recommendedPrice: cat.final_price,
          priceChangePct: cat.price_change_pct,
          demandMultiplier: cat.demand_multiplier,
          supplyMultiplier: cat.supply_multiplier,
          eventMultiplier: cat.event_multiplier,
          reason: cat.explanation,
          confidence: 95 - idx,
          status: 'Pending' as const,
        }));
      
      setRecommendations(recs);
      
      // Load competitor data for each category
      const compData = new Map<string, CompetitorResponse>();
      for (const cat of pricingResult.categories) {
        try {
          const comp = await api.getCompetitorPrices(branchId, cat.category);
          compData.set(cat.category, comp);
        } catch (e) {
          // Ignore individual competitor fetch errors
        }
      }
      setCompetitorData(compData);
      
      // Load car matches
      try {
        const matches = await api.getCarMatches(branchId);
        setCarMatches(matches.matches || []);
      } catch {
        setCarMatches([]);
      }
      
    } catch (err) {
      console.error('Error loading pricing data:', err);
      throw err;
    }
  };

  // Load ALL data when branch changes
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Reload pricing when events change (branch handled above)
  useEffect(() => {
    if (!loading) {
      loadPricingData(selectedBranch).catch(console.error);
    }
  }, [eventFlags]);

  const handleAction = (id: string, action: 'Approved' | 'Rejected') => {
    setRecommendations(prev => prev.map(rec => 
      rec.id === id ? { ...rec, status: action } : rec
    ));
  };

  const handleApproveAll = () => {
    setRecommendations(prev => prev.map(rec => ({ ...rec, status: 'Approved' as const })));
  };

  const fetchAiInsight = async () => {
    setLoadingAi(true);
    const insight = await generatePricingInsight(
      recommendations.map(r => ({
        id: r.id,
        category: r.category as any,
        currentPrice: r.currentPrice,
        recommendedPrice: r.recommendedPrice,
        demandMultiplier: r.demandMultiplier,
        supplyMultiplier: r.supplyMultiplier,
        eventMultiplier: r.eventMultiplier,
        reason: r.reason,
        confidence: r.confidence,
        status: r.status,
      })),
      demandData.map(d => ({
        date: d.day,
        demandForecast: d.demand_forecast,
        actualBookings: d.actual_bookings,
        revenue: d.revenue,
      }))
    );
    setAiInsight(insight);
    setLoadingAi(false);
  };

  const refreshCompetitorData = async () => {
    setRefreshingCompetitors(true);
    try {
      const result = await api.refreshCompetitorData();
      if (result.success) {
        // Reload pricing data to get fresh competitor prices
        await loadPricingData(selectedBranch);
        alert(`✅ Successfully refreshed competitor prices! ${result.categories_updated} categories updated.`);
      }
    } catch (err) {
      alert(`❌ Failed to refresh: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setRefreshingCompetitors(false);
    }
  };

  const downloadReport = async () => {
    try {
      const report = await api.getPricingReport(selectedBranch, eventFlags);
      
      // Convert to CSV
      const headers = Object.keys(report.data[0]).join(',');
      const rows = report.data.map(row => Object.values(row).join(','));
      const csv = [headers, ...rows].join('\n');
      
      // Download
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `renty_pricing_report_${pricingData?.city || 'branch'}_${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Failed to download report');
    }
  };

  const toggleEvent = (event: keyof EventFlags) => {
    setEventFlags(prev => ({ ...prev, [event]: !prev[event] }));
  };

  const currentBranch = branches.find(b => b.id === selectedBranch);
  const utilizationPct = pricingData?.utilization?.utilization_pct || 0;
  const dataFreshness = metrics?.data_freshness;

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-slate-600">Loading pricing data...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-red-800 mb-2">Connection Error</h3>
        <p className="text-red-600 mb-4">{error}</p>
        <button
          onClick={loadData}
          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
        >
          <RefreshCw className="w-4 h-4 inline mr-2" />
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:justify-between lg:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard Manager</h1>
          <p className="text-slate-500">Real-time pricing overview • <span className="font-medium">{userRole}</span> • {currentBranch?.name || 'Loading...'}</p>
        </div>
        
        <div className="flex flex-wrap items-center gap-3">
          {/* Refresh Button */}
          <button
            onClick={loadData}
            className="flex items-center px-3 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>
          
          {/* AI Insights Button */}
          <button 
            onClick={fetchAiInsight}
            disabled={loadingAi || recommendations.length === 0}
            className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
          >
            <BrainCircuit className="w-4 h-4 mr-2" />
            {loadingAi ? 'Analyzing...' : 'Ask AI Insights'}
          </button>
        </div>
      </div>

      {/* System Status Bar */}
      <div className="bg-slate-800 text-white rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-6">
          {/* Database Status */}
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4" />
            <span className="text-sm">Database:</span>
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${
              dbStatus?.status === 'connected' ? 'bg-green-500' : 
              dbStatus?.status === 'error' ? 'bg-red-500' : 'bg-yellow-500'
            }`}>
              {dbStatus?.status || 'checking...'}
            </span>
          </div>
          
          {/* Competitor Data Age */}
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4" />
            <span className="text-sm">Competitor Data:</span>
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${
              dataFreshness?.available && (dataFreshness.age_hours || 0) < 24 ? 'bg-green-500' :
              dataFreshness?.available ? 'bg-yellow-500' : 'bg-red-500'
            }`}>
              {dataFreshness?.available 
                ? `${(dataFreshness.age_hours || 0).toFixed(1)}h old` 
                : 'unavailable'}
            </span>
          </div>
          
          {/* Model Version */}
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4" />
            <span className="text-sm">Model:</span>
            <span className="px-2 py-0.5 bg-blue-500 rounded text-xs font-medium">
              {metrics?.model_version || 'ROBUST_v4'}
            </span>
          </div>
        </div>
        
        {/* Refresh Competitor Data Button */}
        <button
          onClick={refreshCompetitorData}
          disabled={refreshingCompetitors}
          className="flex items-center px-4 py-2 bg-amber-500 text-slate-900 rounded-lg hover:bg-amber-400 transition-colors disabled:opacity-50 font-medium"
        >
          {refreshingCompetitors ? (
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <RefreshCw className="w-4 h-4 mr-2" />
          )}
          {refreshingCompetitors ? 'Fetching from Booking.com...' : 'Refresh Competitor Prices'}
        </button>
      </div>

      {/* Event Toggles */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-100">
        <div className="flex items-center gap-2 mb-3">
          <Calendar className="w-4 h-4 text-slate-500" />
          <span className="text-sm font-medium text-slate-700">Active Events</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {Object.entries(eventFlags).map(([key, value]) => {
            const label = key.replace('is_', '').replace('_', ' ');
            return (
              <button
                key={key}
                onClick={() => toggleEvent(key as keyof EventFlags)}
                className={`px-3 py-1.5 text-xs font-medium rounded-full transition-colors ${
                  value
                    ? 'bg-amber-100 text-amber-800 border border-amber-200'
                    : 'bg-slate-100 text-slate-500 border border-slate-200 hover:bg-slate-200'
                }`}
              >
                {label.charAt(0).toUpperCase() + label.slice(1)}
              </button>
            );
          })}
        </div>
      </div>

      {/* AI Insight Box */}
      {aiInsight && (
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 animate-in fade-in slide-in-from-top-4">
          <div className="flex items-start">
            <BrainCircuit className="w-5 h-5 text-purple-600 mt-1 mr-3" />
            <div>
              <h4 className="font-semibold text-purple-900">Gemini AI Analysis</h4>
              <p className="text-purple-800 text-sm mt-1">{aiInsight}</p>
            </div>
          </div>
        </div>
      )}

      {/* Top Metrics - All values from REAL data */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <MetricCard 
          title="Daily Revenue" 
          value={`SAR ${demandData
            .filter(d => !d.is_forecast && d.revenue)
            .reduce((sum, d) => sum + (d.revenue || 0), 0).toLocaleString()}`}
          change={(() => {
            // Calculate real change from demand data
            const recentRevenue = demandData.filter(d => !d.is_forecast && d.revenue);
            if (recentRevenue.length >= 2) {
              const latest = recentRevenue[recentRevenue.length - 1]?.revenue || 0;
              const previous = recentRevenue[recentRevenue.length - 2]?.revenue || 1;
              const pctChange = ((latest - previous) / previous * 100);
              return `${pctChange >= 0 ? '+' : ''}${pctChange.toFixed(1)}%`;
            }
            return 'N/A';
          })()}
          isPositive={(() => {
            const recentRevenue = demandData.filter(d => !d.is_forecast && d.revenue);
            if (recentRevenue.length >= 2) {
              const latest = recentRevenue[recentRevenue.length - 1]?.revenue || 0;
              const previous = recentRevenue[recentRevenue.length - 2]?.revenue || 0;
              return latest >= previous;
            }
            return true;
          })()} 
          icon={DollarSign} 
        />
        <MetricCard 
          title="Fleet Utilization" 
          value={`${utilizationPct.toFixed(1)}%`}
          change={`${metrics?.avg_utilization || 'N/A'} avg`}
          isPositive={utilizationPct > 70} 
          icon={Activity} 
        />
        <MetricCard 
          title="Active Contracts" 
          value={pricingData?.utilization?.rented_vehicles?.toLocaleString() || '0'}
          change={`of ${pricingData?.utilization?.total_vehicles || 0} total`}
          isPositive={(pricingData?.utilization?.rented_vehicles || 0) > 0} 
          icon={Users} 
        />
      </div>

      {/* Demand Forecast Chart - Full Width */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h3 className="text-lg font-bold text-slate-900">Demand Forecast vs Actuals</h3>
            <p className="text-sm text-slate-500 mt-1">Past 5 days + Today + 2-day predictions</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
              <span className="text-xs text-slate-600">Forecast</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-emerald-500 rounded-full"></div>
              <span className="text-xs text-slate-600">Actuals</span>
            </div>
            <span className="text-sm bg-blue-100 text-blue-700 px-2 py-1 rounded ml-2">
              Model {metrics?.model_version || 'v4.0'}
            </span>
          </div>
        </div>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={demandData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis 
                dataKey="day" 
                axisLine={false} 
                tickLine={false} 
                tick={{ fill: '#64748b', fontSize: 12 }} 
              />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b' }} />
              <Tooltip 
                contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                formatter={(value: any, name: string) => {
                  if (value === null) return ['Pending', name];
                  return [value, name];
                }}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="demand_forecast" 
                name="Forecast" 
                stroke="#3b82f6" 
                strokeWidth={3} 
                dot={{ r: 5, fill: '#3b82f6' }} 
                strokeDasharray={(demandData as any[])?.some(d => d.is_forecast) ? undefined : undefined}
              />
              <Line 
                type="monotone" 
                dataKey="actual_bookings" 
                name="Actuals" 
                stroke="#10b981" 
                strokeWidth={3} 
                dot={{ r: 5, fill: '#10b981' }}
                connectNulls={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        {/* Prediction indicator */}
        <div className="mt-4 flex items-center justify-end gap-4 text-xs text-slate-500">
          <div className="flex items-center gap-1">
            <div className="w-8 h-0.5 bg-blue-500"></div>
            <span>Historical + Today</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-8 h-0.5 bg-blue-500 border-dashed border-b-2 border-blue-500"></div>
            <span>2-Day Predictions</span>
          </div>
        </div>
      </div>

      {/* Modern Pricing Cards - Dark Charcoal Theme with Amber Accents */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 rounded-2xl shadow-xl">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h3 className="text-xl font-semibold text-white">Category Pricing</h3>
            <p className="text-sm text-slate-400">{recommendations.length} categories • Real-time recommendations</p>
          </div>
        </div>
        
        {recommendations.length === 0 ? (
          <div className="text-center py-12 text-slate-500">
            <Loader2 className="w-8 h-8 mx-auto mb-3 animate-spin opacity-50" />
            <p className="text-sm">Loading pricing data...</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
            {recommendations.map((rec) => {
              // Category car images - Local images from Yelo rental fleet
              const getCategoryImage = (category: string) => {
                const images: Record<string, string> = {
                  'Economy': '/assets/cars/economy.png',
                  'Compact': '/assets/cars/compact.png',
                  'Standard': '/assets/cars/standard.png',
                  'SUV Compact': '/assets/cars/suv_compact.png',
                  'SUV Standard': '/assets/cars/suv_standard.png',
                  'SUV Large': '/assets/cars/suv_large.png',
                  'Luxury Sedan': '/assets/cars/luxury_sedan.png',
                  'Luxury SUV': '/assets/cars/luxury_suv.png',
                };
                return images[category] || images['Economy'];
              };
              
              return (
                <div 
                  key={rec.id} 
                  className={`group bg-gradient-to-b from-slate-800 to-slate-850 rounded-2xl overflow-hidden shadow-lg hover:shadow-2xl hover:shadow-amber-500/10 transition-all duration-300 border border-slate-700/50 hover:border-amber-500/30 ${
                    rec.status === 'Approved' ? 'ring-2 ring-emerald-500/50' :
                    rec.status === 'Rejected' ? 'opacity-50' : ''
                  }`}
                >
                  {/* Car Image - Larger size with dark gradient background */}
                  <div className="relative h-40 overflow-hidden bg-gradient-to-br from-slate-700/50 via-slate-800 to-slate-900 flex items-center justify-center">
                    <div className="absolute inset-0 bg-gradient-to-t from-slate-900/80 to-transparent z-10"></div>
                    <img 
                      src={getCategoryImage(rec.category)} 
                      alt={rec.category}
                      className="object-contain group-hover:scale-110 transition-transform duration-500 drop-shadow-2xl relative z-0"
                      style={{ 
                        height: '120px', 
                        width: '200px',
                        transform: rec.category === 'Luxury SUV' ? 'scale(1.3)' : 'scale(1)',
                        filter: 'drop-shadow(0 10px 20px rgba(0,0,0,0.4))'
                      }}
                    />
                    {rec.status !== 'Pending' && (
                      <div className="absolute top-3 right-3 z-20">
                        <span className={`text-xs font-bold px-3 py-1.5 rounded-full ${
                          rec.status === 'Approved' ? 'bg-emerald-500 text-white' : 'bg-slate-600 text-slate-300'
                        }`}>
                          {rec.status === 'Approved' ? '✓ Applied' : 'Skipped'}
                        </span>
                      </div>
                    )}
                    {/* Category badge on image */}
                    <div className="absolute bottom-3 left-3 z-20">
                      <span className="text-xs font-semibold text-amber-400 bg-slate-900/80 px-2 py-1 rounded-md backdrop-blur-sm">
                        {rec.category}
                      </span>
                    </div>
                  </div>
                  
                  {/* Card Content */}
                  <div className="p-4">
                    {/* Price Display - Before → After */}
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-baseline gap-1">
                        <span className="text-lg text-slate-500 line-through">{rec.currentPrice.toFixed(0)}</span>
                        <span className="text-xs text-slate-600">SAR</span>
                      </div>
                      <span className="text-slate-600 text-lg">→</span>
                      <div className="flex items-baseline gap-1">
                        <span className="text-2xl font-bold text-amber-400">{rec.recommendedPrice.toFixed(0)}</span>
                        <span className="text-sm text-amber-500/70">SAR</span>
                      </div>
                    </div>
                    
                    {/* Premium/Discount Badge */}
                    <div className="mb-4">
                      {rec.priceChangePct > 0 ? (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/20 text-rose-400 text-xs font-semibold border border-rose-500/30">
                          <span className="w-1.5 h-1.5 bg-rose-400 rounded-full animate-pulse"></span>
                          Premium <span className="font-bold">+{rec.priceChangePct.toFixed(1)}%</span>
                        </span>
                      ) : rec.priceChangePct < 0 ? (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/20 text-emerald-400 text-xs font-semibold border border-emerald-500/30">
                          <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse"></span>
                          Discount <span className="font-bold">{rec.priceChangePct.toFixed(1)}%</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-600/30 text-slate-400 text-xs font-semibold border border-slate-600/30">
                          <span className="w-1.5 h-1.5 bg-slate-400 rounded-full"></span>
                          Standard <span className="font-bold">0%</span>
                        </span>
                      )}
                    </div>
                    
                    {/* Action Buttons */}
                    {rec.status === 'Pending' && (
                      <div className="flex gap-2 pt-3 border-t border-slate-700/50">
                        <button 
                          onClick={() => handleAction(rec.id, 'Approved')}
                          className="flex-1 py-2.5 text-sm font-semibold text-slate-900 bg-gradient-to-r from-amber-400 to-amber-500 hover:from-amber-500 hover:to-amber-600 rounded-xl transition-all duration-200 shadow-lg shadow-amber-500/20"
                        >
                          ✓ Apply
                        </button>
                        <button 
                          onClick={() => handleAction(rec.id, 'Rejected')}
                          className="flex-1 py-2.5 text-sm font-semibold text-slate-300 bg-slate-700/50 hover:bg-slate-600/50 rounded-xl transition-all duration-200 border border-slate-600/50"
                        >
                          Skip
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Car-by-Car Price Comparison - Dark Theme */}
      {carMatches.length > 0 && (
        <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl overflow-hidden shadow-xl">
          <div className="p-6 border-b border-slate-700/50">
            <div className="flex items-center gap-2">
              <Car className="w-5 h-5 text-amber-400" />
              <h3 className="text-xl font-semibold text-white">Car-by-Car Price Comparison</h3>
            </div>
            <p className="text-sm text-slate-400 mt-1">
              Exact vehicle model matches between Renty and competitors • {carMatches.length} models matched
            </p>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-5 p-6">
            {carMatches.slice(0, 8).map((match, idx) => {
              // Get car image based on model name first, then fall back to category
              const getCarModelImage = (modelName: string, category: string) => {
                // Model-specific images (matching car brand/model)
                const modelImages: Record<string, string> = {
                  // Hyundai models
                  'Hyundai Elantra': '/assets/cars/models/hyundai_elantra.png',
                  'Hyundai i10': '/assets/cars/economy.png',
                  'Hyundai Grand i10': '/assets/cars/economy.png',
                  'Hyundai Accent': '/assets/cars/compact.png',
                  'Hyundai Kona': '/assets/cars/models/hyundai_kona.png',
                  'Hyundai Tucson': '/assets/cars/suv_compact.png',
                  'Hyundai Sonata': '/assets/cars/standard.png',
                  // Nissan models
                  'Nissan Sunny': '/assets/cars/models/nissan_sunny.png',
                  'Nissan Altima': '/assets/cars/standard.png',
                  'Nissan Patrol': '/assets/cars/suv_large.png',
                  'Nissan X-Trail': '/assets/cars/suv_standard.png',
                  // Toyota models
                  'Toyota Corolla': '/assets/cars/compact.png',
                  'Toyota Camry': '/assets/cars/standard.png',
                  'Toyota RAV4': '/assets/cars/models/toyota_rav4.png',
                  'Toyota Highlander': '/assets/cars/models/toyota_highlander.png',
                  'Toyota Land Cruiser': '/assets/cars/suv_large.png',
                  'Toyota Yaris': '/assets/cars/economy.png',
                  // Chevrolet models  
                  'Chevrolet Spark': '/assets/cars/models/chevrolet_spark.png',
                  'Chevrolet Malibu': '/assets/cars/standard.png',
                  'Chevrolet Tahoe': '/assets/cars/suv_large.png',
                  // BMW models
                  'BMW 5 Series': '/assets/cars/models/bmw_5_series.png',
                  'BMW 3 Series': '/assets/cars/luxury_sedan.png',
                  'BMW X5': '/assets/cars/luxury_suv.png',
                  'BMW X3': '/assets/cars/suv_standard.png',
                  // Kia models
                  'Kia Rio': '/assets/cars/models/kia_rio.png',
                  'Kia Sportage': '/assets/cars/suv_compact.png',
                  'Kia Sorento': '/assets/cars/suv_large.png',
                  // Mercedes models
                  'Mercedes E-Class': '/assets/cars/luxury_sedan.png',
                  'Mercedes GLE': '/assets/cars/luxury_suv.png',
                  // Mazda models
                  'Mazda 3': '/assets/cars/models/mazda_3.png',
                  'Mazda 6': '/assets/cars/standard.png',
                  'Mazda CX-5': '/assets/cars/suv_compact.png',
                };
                
                // Category fallback images
                const categoryImages: Record<string, string> = {
                  'Economy': '/assets/cars/economy.png',
                  'Compact': '/assets/cars/compact.png',
                  'Standard': '/assets/cars/standard.png',
                  'SUV Compact': '/assets/cars/suv_compact.png',
                  'SUV Standard': '/assets/cars/suv_standard.png',
                  'SUV Large': '/assets/cars/suv_large.png',
                  'Luxury Sedan': '/assets/cars/luxury_sedan.png',
                  'Luxury SUV': '/assets/cars/luxury_suv.png',
                };
                
                // First try exact model match
                if (modelImages[modelName]) {
                  return modelImages[modelName];
                }
                
                // Then try partial model match (check if any model key is contained in modelName)
                for (const [key, value] of Object.entries(modelImages)) {
                  if (modelName.toLowerCase().includes(key.toLowerCase()) || 
                      key.toLowerCase().includes(modelName.toLowerCase())) {
                    return value;
                  }
                }
                
                // Fall back to category image
                return categoryImages[category] || categoryImages['Economy'];
              };
              
              return (
                <div 
                  key={idx}
                  className="group bg-gradient-to-b from-slate-800 to-slate-850 rounded-2xl overflow-hidden shadow-lg hover:shadow-2xl hover:shadow-amber-500/10 transition-all duration-300 border border-slate-700/50 hover:border-amber-500/30"
                >
                  {/* Car Image - Larger size with dark gradient */}
                  <div className="relative h-32 overflow-hidden bg-gradient-to-br from-slate-700/50 via-slate-800 to-slate-900 flex items-center justify-center">
                    <div className="absolute inset-0 bg-gradient-to-t from-slate-900/80 to-transparent z-10"></div>
                    <img 
                      src={getCarModelImage(match.renty_model, match.renty_category)} 
                      alt={match.renty_model}
                      className="object-contain group-hover:scale-110 transition-transform duration-500 drop-shadow-2xl relative z-0"
                      style={{ height: '90px', width: '160px', filter: 'drop-shadow(0 10px 20px rgba(0,0,0,0.4))' }}
                    />
                    <div className={`absolute top-2 right-2 z-20 text-xs font-bold px-2.5 py-1 rounded-full ${
                      match.status === 'cheaper' 
                        ? 'bg-emerald-500 text-white' 
                        : 'bg-rose-500 text-white'
                    }`}>
                      {match.status === 'cheaper' ? '✓ Lower' : '↑ Higher'}
                    </div>
                    {/* Model badge on image */}
                    <div className="absolute bottom-2 left-2 z-20">
                      <span className="text-xs font-semibold text-amber-400 bg-slate-900/80 px-2 py-1 rounded-md backdrop-blur-sm truncate max-w-[120px] block">
                        {match.renty_model}
                      </span>
                    </div>
                  </div>
                  
                  <div className="p-4">
                    {/* Category */}
                    <div className="text-xs text-slate-500 mb-3">{match.renty_category}</div>
                    
                    {/* Price Comparison */}
                    <div className="flex justify-between items-center mb-3">
                      <div>
                        <span className="text-xs text-slate-500 block">Renty</span>
                        <span className="text-lg font-bold text-amber-400">{match.renty_price.toFixed(0)}</span>
                        <span className="text-xs text-amber-500/70 ml-1">SAR</span>
                      </div>
                      <div className="text-slate-600">vs</div>
                      <div className="text-right">
                        <span className="text-xs text-slate-500 block">Competitor</span>
                        <span className="text-lg font-bold text-slate-300">{match.best_competitor_price.toFixed(0)}</span>
                        <span className="text-xs text-slate-500 ml-1">SAR</span>
                      </div>
                    </div>
                    
                    {/* Difference Badge */}
                    <div className={`text-center py-2 rounded-xl font-bold text-sm ${
                      match.status === 'cheaper' 
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                        : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                    }`}>
                      {match.price_diff > 0 ? '+' : ''}{match.price_diff.toFixed(0)} SAR
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* All Categories Pricing Table - Dark Theme */}
      {pricingData && (
        <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl shadow-xl overflow-hidden">
          <div className="p-6 border-b border-slate-700/50">
            <h3 className="text-xl font-semibold text-white">All Category Pricing - {currentBranch?.name}</h3>
            <p className="text-sm text-slate-400 mt-1">
              Utilization: <span className="text-amber-400 font-semibold">{utilizationPct.toFixed(1)}%</span> ({pricingData.utilization.rented_vehicles}/{pricingData.utilization.total_vehicles} vehicles)
              {pricingData.utilization.source && (
                <span className="ml-2 px-2 py-0.5 bg-emerald-500/20 text-emerald-400 rounded text-xs border border-emerald-500/30">
                  Source: {pricingData.utilization.source}
                </span>
              )}
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-slate-400 uppercase bg-slate-800/50">
                <tr>
                  <th className="px-6 py-4 font-medium">Category</th>
                  <th className="px-6 py-4 font-medium">Base Price</th>
                  <th className="px-6 py-4 font-medium">Final Price</th>
                  <th className="px-6 py-4 font-medium">Change</th>
                  <th className="px-6 py-4 font-medium">Competitor Avg</th>
                  <th className="px-6 py-4 font-medium">vs Market</th>
                  <th className="px-6 py-4 font-medium">Competitors</th>
                </tr>
              </thead>
              <tbody>
                {pricingData.categories.map((cat, idx) => {
                  const compData = competitorData.get(cat.category);
                  const compAvg = cat.competitor_avg;
                  const marketDiff = compAvg ? cat.final_price - compAvg : null;
                  
                  return (
                    <tr key={cat.category} className={`border-b border-slate-700/30 hover:bg-slate-700/30 transition-colors ${idx % 2 === 0 ? 'bg-slate-800/30' : 'bg-slate-800/10'}`}>
                      <td className="px-6 py-4">
                        <div className="flex items-center">
                          <span className="text-xl mr-3">{cat.icon}</span>
                          <div>
                            <span className="font-semibold text-white">{cat.category}</span>
                            <p className="text-xs text-slate-500">{cat.examples.split(',')[0]}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-slate-400">{cat.base_price.toFixed(0)} SAR</td>
                      <td className="px-6 py-4 font-bold text-amber-400">{cat.final_price.toFixed(0)} SAR</td>
                      <td className="px-6 py-4">
                        <span className={`px-2.5 py-1 rounded-lg text-xs font-bold ${
                          cat.price_change_pct > 1 ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 
                          cat.price_change_pct < -1 ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 
                          'bg-slate-600/30 text-slate-400 border border-slate-600/30'
                        }`}>
                          {cat.price_change_pct > 0 ? '+' : ''}{cat.price_change_pct.toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-6 py-4 text-slate-400">
                        {compAvg ? `${compAvg.toFixed(0)} SAR` : '-'}
                      </td>
                      <td className="px-6 py-4">
                        {marketDiff !== null ? (
                          <span className={`px-2.5 py-1 rounded-lg text-xs font-semibold ${
                            marketDiff < 0 ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                          }`}>
                            {marketDiff > 0 ? '+' : ''}{marketDiff.toFixed(0)} SAR
                          </span>
                        ) : (
                          <span className="text-slate-600">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        {compData?.competitors?.length ? (
                          <div className="text-xs text-slate-400 max-w-[200px]">
                            {compData.competitors.slice(0, 2).map((c, i) => (
                              <div key={i} className="truncate">• {c.competitor_name}: <span className="text-slate-300">{c.price.toFixed(0)} SAR</span></div>
                            ))}
                            {compData.competitors.length > 2 && (
                              <div className="text-slate-600">+{compData.competitors.length - 2} more</div>
                            )}
                          </div>
                        ) : (
                          <span className="text-slate-600">No data</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="text-center text-sm text-slate-500 py-4">
        <p>Renty Intelligent Dynamic Pricing v2.0 • Model: {metrics?.model_version} • Accuracy: {metrics?.model_accuracy}</p>
        <p className="text-xs mt-1">Last updated: {new Date().toLocaleString()}</p>
      </div>
    </div>
  );
};

export default Dashboard;
