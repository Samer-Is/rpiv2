import React, { useState, useEffect, useCallback } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, LineChart, Line, Legend, AreaChart, Area } from 'recharts';
import { TrendingUp, Calendar, Activity, DollarSign, Loader2, AlertCircle, RefreshCw, MapPin, Car, Users, Clock, TrendingDown } from 'lucide-react';
import { api, SystemMetrics, WeeklyDistribution, SeasonalImpact, DemandDataPoint } from '../services/api';
import { useAppContext } from '../context/AppContext';

const Analytics = () => {
  const { branches, selectedBranch, userRole } = useAppContext();
  
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [weeklyData, setWeeklyData] = useState<WeeklyDistribution[]>([]);
  const [seasonalData, setSeasonalData] = useState<SeasonalImpact[]>([]);
  const [demandData, setDemandData] = useState<DemandDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const currentBranch = branches.find(b => b.id === selectedBranch);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // ALL DATA IS BRANCH-SPECIFIC
      const [metricsResult, weeklyResult, seasonalResult, demandResult] = await Promise.all([
        api.getSystemMetrics(selectedBranch),
        api.getWeeklyDistribution(selectedBranch),
        api.getSeasonalImpact(selectedBranch),
        api.getDemandData(selectedBranch),
      ]);
      
      setMetrics(metricsResult);
      setWeeklyData(weeklyResult);
      setSeasonalData(seasonalResult);
      setDemandData(demandResult);
    } catch (err) {
      console.error('Error loading analytics:', err);
      setError(err instanceof Error ? err.message : 'Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  }, [selectedBranch]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Calculate REAL insights from data
  const totalBookings = weeklyData.reduce((sum, d) => sum + d.bookings, 0);
  const avgBookings = weeklyData.length > 0 ? totalBookings / weeklyData.length : 0;
  
  // Find peak day from actual data
  const peakDay = weeklyData.reduce((peak, d) => 
    d.bookings > (peak?.bookings || 0) ? d : peak, weeklyData[0]);
  const peakPct = peakDay && avgBookings > 0 
    ? ((peakDay.bookings / avgBookings) - 1) * 100 
    : 0;

  // Calculate seasonal impacts from REAL data
  const normalSeason = seasonalData.find(s => s.season === 'Normal');
  const baselineVolume = normalSeason?.volume || 100;
  
  const ramadanData = seasonalData.find(s => s.season === 'Ramadan');
  const ramadanImpact = ramadanData 
    ? (ramadanData.volume - baselineVolume).toFixed(1)
    : '0';

  const hajjData = seasonalData.find(s => s.season === 'Hajj');
  const hajjImpact = hajjData
    ? (hajjData.volume - baselineVolume).toFixed(1)
    : '0';

  // Calculate demand trends from REAL data
  const recentDemand = demandData.filter(d => !d.is_forecast);
  const avgDemand = recentDemand.length > 0 
    ? recentDemand.reduce((sum, d) => sum + (d.actual_bookings || 0), 0) / recentDemand.length
    : 0;
  const latestDemand = recentDemand[recentDemand.length - 1]?.actual_bookings || 0;
  const demandTrend = avgDemand > 0 ? ((latestDemand - avgDemand) / avgDemand * 100) : 0;

  // Revenue from demand data
  const totalRevenue = recentDemand.reduce((sum, d) => sum + (d.revenue || 0), 0);
  const avgRevenue = recentDemand.length > 0 ? totalRevenue / recentDemand.length : 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-slate-600">Loading analytics data...</p>
        </div>
      </div>
    );
  }

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
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Exploratory Data Analysis (EDA)</h1>
          <p className="text-slate-500">
            <MapPin className="w-4 h-4 inline mr-1" />
            {currentBranch?.name || 'All Branches'} • {metrics?.total_contracts || 'N/A'} active rentals
          </p>
        </div>
        <button
          onClick={loadData}
          className="flex items-center px-3 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </button>
      </div>

      {/* Key Insights Cards - ALL FROM REAL DATA */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-5 text-white">
          <div className="flex items-center justify-between mb-3">
            <TrendingUp className="w-7 h-7 opacity-80" />
            <span className="text-xl font-bold">{peakPct >= 0 ? '+' : ''}{peakPct.toFixed(1)}%</span>
          </div>
          <h3 className="font-semibold">{peakDay?.day || 'Peak'} Peak</h3>
          <p className="text-xs opacity-80 mt-1">{peakDay?.bookings.toLocaleString() || 0} bookings/day</p>
        </div>
        
        <div className={`bg-gradient-to-br ${parseFloat(ramadanImpact) >= 0 ? 'from-green-500 to-green-600' : 'from-red-500 to-red-600'} rounded-xl p-5 text-white`}>
          <div className="flex items-center justify-between mb-3">
            <Calendar className="w-7 h-7 opacity-80" />
            <span className="text-xl font-bold">{parseFloat(ramadanImpact) >= 0 ? '+' : ''}{ramadanImpact}%</span>
          </div>
          <h3 className="font-semibold">Ramadan Impact</h3>
          <p className="text-xs opacity-80 mt-1">Seasonal demand adjustment</p>
        </div>
        
        <div className={`bg-gradient-to-br ${demandTrend >= 0 ? 'from-emerald-500 to-emerald-600' : 'from-amber-500 to-amber-600'} rounded-xl p-5 text-white`}>
          <div className="flex items-center justify-between mb-3">
            {demandTrend >= 0 ? <TrendingUp className="w-7 h-7 opacity-80" /> : <TrendingDown className="w-7 h-7 opacity-80" />}
            <span className="text-xl font-bold">{demandTrend >= 0 ? '+' : ''}{demandTrend.toFixed(1)}%</span>
          </div>
          <h3 className="font-semibold">Demand Trend</h3>
          <p className="text-xs opacity-80 mt-1">vs 7-day average</p>
        </div>
        
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-5 text-white">
          <div className="flex items-center justify-between mb-3">
            <DollarSign className="w-7 h-7 opacity-80" />
            <span className="text-xl font-bold">SAR {(avgRevenue / 1000).toFixed(0)}K</span>
          </div>
          <h3 className="font-semibold">Avg Daily Revenue</h3>
          <p className="text-xs opacity-80 mt-1">Last 7 days</p>
        </div>
      </div>

      {/* Demand Trend Chart - New */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
        <h3 className="text-lg font-bold text-slate-900 mb-2">Demand & Revenue Trend</h3>
        <p className="text-sm text-slate-500 mb-4">
          <MapPin className="w-3 h-3 inline mr-1" />
          {currentBranch?.name || 'All Branches'} • Last 7 days + 2-day forecast
        </p>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={demandData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis dataKey="day" axisLine={false} tickLine={false} />
              <YAxis axisLine={false} tickLine={false} />
              <Tooltip 
                contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                formatter={(value: any, name: string) => [value?.toLocaleString() || 'Pending', name]}
              />
              <Legend />
              <Area 
                type="monotone" 
                dataKey="actual_bookings" 
                name="Actual Bookings"
                stroke="#10b981" 
                fill="#10b98133"
                strokeWidth={2}
              />
              <Area 
                type="monotone" 
                dataKey="demand_forecast" 
                name="Forecast"
                stroke="#3b82f6" 
                fill="#3b82f633"
                strokeWidth={2}
                strokeDasharray="5 5"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Weekly Distribution Chart */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
          <h3 className="text-lg font-bold text-slate-900 mb-2">Weekly Demand Pattern</h3>
          <p className="text-sm text-slate-500 mb-4">
            Peak day: <span className="font-semibold text-blue-600">{peakDay?.day || 'N/A'} (+{peakPct.toFixed(1)}%)</span>
            {totalBookings > 0 && ` • Total: ${totalBookings.toLocaleString()} bookings`}
          </p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={weeklyData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="day" axisLine={false} tickLine={false} />
                <YAxis axisLine={false} tickLine={false} />
                <Tooltip 
                  cursor={{fill: '#f1f5f9'}} 
                  contentStyle={{ borderRadius: '8px', border: 'none' }}
                  formatter={(value: any) => [value?.toLocaleString() || 0, 'Bookings']}
                />
                <Bar dataKey="bookings" radius={[4, 4, 0, 0]}>
                  {weeklyData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.is_peak ? '#3b82f6' : '#cbd5e1'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Seasonal Impact Chart */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
          <h3 className="text-lg font-bold text-slate-900 mb-2">Seasonal Demand Factors</h3>
          <p className="text-sm text-slate-500 mb-4">
            Impact relative to baseline (100) • {currentBranch?.city || 'All Cities'}
          </p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={seasonalData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
                <XAxis type="number" axisLine={false} tickLine={false} domain={[0, 'auto']} />
                <YAxis dataKey="season" type="category" width={100} axisLine={false} tickLine={false} />
                <Tooltip 
                  cursor={{fill: '#f1f5f9'}} 
                  contentStyle={{ borderRadius: '8px', border: 'none' }}
                  formatter={(value: any) => [`${value}%`, 'Demand']}
                />
                <Bar dataKey="volume" radius={[0, 4, 4, 0]}>
                  {seasonalData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={
                        entry.volume < 100 ? '#ef4444' :  // Red for below baseline
                        entry.volume > 120 ? '#10b981' :  // Green for high demand
                        '#3b82f6'  // Blue for normal
                      } 
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Branch-Specific Metrics */}
      <div className="bg-slate-900 text-white p-6 rounded-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold">Branch Metrics - {currentBranch?.name || 'All Branches'}</h3>
          <span className="text-xs text-slate-400">
            <Clock className="w-3 h-3 inline mr-1" />
            Real-time from database
          </span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-center">
          <div className="p-4 bg-slate-800 rounded-lg">
            <div className="text-2xl font-bold text-blue-400">{metrics?.total_contracts || 'N/A'}</div>
            <div className="text-xs text-slate-400 uppercase mt-1">Active Rentals</div>
          </div>
          <div className="p-4 bg-slate-800 rounded-lg">
            <div className="text-2xl font-bold text-amber-400">{metrics?.avg_utilization || 'N/A'}</div>
            <div className="text-xs text-slate-400 uppercase mt-1">Utilization</div>
          </div>
          <div className="p-4 bg-slate-800 rounded-lg">
            <div className="text-2xl font-bold text-green-400">SAR {(avgRevenue / 1000).toFixed(0)}K</div>
            <div className="text-xs text-slate-400 uppercase mt-1">Avg Daily Revenue</div>
          </div>
          <div className="p-4 bg-slate-800 rounded-lg">
            <div className="text-2xl font-bold text-purple-400">{Math.round(avgDemand)}</div>
            <div className="text-xs text-slate-400 uppercase mt-1">Avg Daily Bookings</div>
          </div>
          <div className="p-4 bg-slate-800 rounded-lg">
            <div className="text-2xl font-bold text-cyan-400">{peakDay?.day || 'N/A'}</div>
            <div className="text-xs text-slate-400 uppercase mt-1">Peak Day</div>
          </div>
        </div>
      </div>

      {/* Additional Insights */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
          <h3 className="text-lg font-bold text-slate-900 mb-4">📊 Key Insights</h3>
          <div className="space-y-3 text-sm">
            <div className="flex items-start gap-3">
              <div className="w-2 h-2 rounded-full bg-blue-500 mt-2"></div>
              <div>
                <p className="font-medium text-slate-700">Peak Demand Day</p>
                <p className="text-slate-500">
                  {peakDay?.day || 'N/A'} shows {peakPct.toFixed(1)}% higher demand than average
                  ({peakDay?.bookings.toLocaleString() || 0} vs {Math.round(avgBookings).toLocaleString()} avg)
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className={`w-2 h-2 rounded-full ${demandTrend >= 0 ? 'bg-green-500' : 'bg-red-500'} mt-2`}></div>
              <div>
                <p className="font-medium text-slate-700">Recent Trend</p>
                <p className="text-slate-500">
                  Demand is {demandTrend >= 0 ? 'up' : 'down'} {Math.abs(demandTrend).toFixed(1)}% compared to 7-day average
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className={`w-2 h-2 rounded-full ${parseFloat(ramadanImpact) >= 0 ? 'bg-green-500' : 'bg-amber-500'} mt-2`}></div>
              <div>
                <p className="font-medium text-slate-700">Seasonal Factor</p>
                <p className="text-slate-500">
                  Ramadan {parseFloat(ramadanImpact) >= 0 ? 'increases' : 'decreases'} demand by {Math.abs(parseFloat(ramadanImpact)).toFixed(1)}%
                  {hajjData && ` • Hajj: ${parseFloat(hajjImpact) >= 0 ? '+' : ''}${hajjImpact}%`}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
          <h3 className="text-lg font-bold text-slate-900 mb-4">💡 Recommendations</h3>
          <div className="space-y-3 text-sm">
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-xs">1</div>
              <div>
                <p className="font-medium text-slate-700">Optimize {peakDay?.day || 'Peak'} Pricing</p>
                <p className="text-slate-500">
                  Consider {peakPct > 15 ? 'premium pricing' : 'maintaining current rates'} on peak days
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center text-green-600 font-bold text-xs">2</div>
              <div>
                <p className="font-medium text-slate-700">
                  {demandTrend >= 5 ? 'Increase Prices' : demandTrend <= -5 ? 'Consider Discounts' : 'Maintain Prices'}
                </p>
                <p className="text-slate-500">
                  Based on current {demandTrend >= 0 ? 'positive' : 'declining'} demand trend
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-purple-100 flex items-center justify-center text-purple-600 font-bold text-xs">3</div>
              <div>
                <p className="font-medium text-slate-700">Seasonal Preparation</p>
                <p className="text-slate-500">
                  {currentBranch?.city === 'Mecca' || currentBranch?.city === 'Medina' 
                    ? 'Prepare for increased Umrah/Hajj demand' 
                    : 'Monitor seasonal patterns for pricing adjustments'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Model Performance Details */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
        <h3 className="text-lg font-bold text-slate-900 mb-4">ML Model Performance</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-4">
            <h4 className="font-semibold text-slate-700">Model Specifications</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Algorithm</span>
                <span className="font-medium">XGBoost Regressor</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Version</span>
                <span className="font-medium">{metrics?.model_version || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Features</span>
                <span className="font-medium">60+ engineered</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Active Contracts</span>
                <span className="font-medium">{metrics?.total_contracts || 'N/A'}</span>
              </div>
            </div>
          </div>
          
          <div className="space-y-4">
            <h4 className="font-semibold text-slate-700">Branch Performance</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Accuracy (R²)</span>
                <span className="font-medium text-green-600">{metrics?.model_accuracy || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Utilization</span>
                <span className="font-medium">{metrics?.avg_utilization || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Daily Bookings</span>
                <span className="font-medium">{Math.round(avgDemand).toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Peak Variance</span>
                <span className="font-medium">+{peakPct.toFixed(1)}%</span>
              </div>
            </div>
          </div>
          
          <div className="space-y-4">
            <h4 className="font-semibold text-slate-700">Seasonal Factors</h4>
            <div className="space-y-2 text-sm">
              {seasonalData.slice(0, 4).map((season, idx) => (
                <div key={idx} className="flex justify-between">
                  <span className="text-slate-500">{season.season}</span>
                  <span className={`font-medium ${
                    season.volume < 100 ? 'text-red-600' : 
                    season.volume > 110 ? 'text-green-600' : ''
                  }`}>
                    {season.volume >= 100 ? '+' : ''}{(season.volume - 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Data Freshness */}
      {metrics?.data_freshness && (
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                metrics.data_freshness.available && (metrics.data_freshness.age_hours || 0) < 24 
                  ? 'bg-green-500' 
                  : metrics.data_freshness.available 
                    ? 'bg-amber-500' 
                    : 'bg-red-500'
              }`} />
              <span className="text-sm font-medium text-slate-700">
                Competitor Data: {metrics.data_freshness.status || 'Unknown'}
              </span>
            </div>
            {metrics.data_freshness.age_hours !== undefined && (
              <span className="text-xs text-slate-500">
                Last updated {metrics.data_freshness.age_hours.toFixed(1)} hours ago
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Analytics;
