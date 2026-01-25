/**
 * Dynamic Pricing Dashboard - CHUNK 10
 * Main dashboard for viewing and approving pricing recommendations
 * 
 * Features:
 * - Branch dropdown selector
 * - Start date selector
 * - 6 category cards showing base vs recommended prices
 * - 30-day window table with scrolling
 * - Approve/skip per category
 */
import { useState, useEffect, useCallback } from 'react'
import { useAuthStore } from '../api/auth-store'
import { 
  recommendationsApi, 
  configApi,
  type Recommendation, 
  type Branch, 
  type Category,
  type RecommendationSummary
} from '../api/recommendations'

// Format currency
const formatPrice = (price: number | null | undefined): string => {
  if (price === null || price === undefined) return '--'
  return `${price.toFixed(0)} SAR`
}

// Format percentage with color
const formatPct = (pct: number | null | undefined): { text: string; className: string } => {
  if (pct === null || pct === undefined) return { text: '--', className: 'text-gray-500' }
  const sign = pct >= 0 ? '+' : ''
  const className = pct > 0 ? 'text-green-600' : pct < 0 ? 'text-red-600' : 'text-gray-600'
  return { text: `${sign}${pct.toFixed(1)}%`, className }
}

// Format date for display
const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

// Get today's date in YYYY-MM-DD format
const getTodayString = (): string => {
  return new Date().toISOString().split('T')[0]
}

// Category Card Component
interface CategoryCardProps {
  categoryId: number
  categoryName: string
  recommendations: Recommendation[]
  onApprove: (categoryId: number) => void
  onSkip: (categoryId: number) => void
  isLoading: boolean
  selectedDate: string
}

function CategoryCard({ 
  categoryId, 
  categoryName, 
  recommendations, 
  onApprove, 
  onSkip,
  isLoading,
  selectedDate
}: CategoryCardProps) {
  // Get recommendation for selected date
  const rec = recommendations.find(r => r.forecast_date === selectedDate)
  
  const pctDisplay = formatPct(rec?.premium_discount_pct)
  const isPending = rec?.status === 'pending'
  const isApproved = rec?.status === 'approved'
  const isSkipped = rec?.status === 'skipped'

  return (
    <div className={`bg-white rounded-lg shadow-md p-5 border-l-4 ${
      isApproved ? 'border-green-500' : isSkipped ? 'border-gray-400' : 'border-blue-500'
    }`}>
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-lg font-semibold text-gray-800">{categoryName}</h3>
        {rec && (
          <span className={`px-2 py-1 rounded text-xs font-medium ${
            isApproved ? 'bg-green-100 text-green-700' : 
            isSkipped ? 'bg-gray-100 text-gray-600' : 
            'bg-blue-100 text-blue-700'
          }`}>
            {rec.status.toUpperCase()}
          </span>
        )}
      </div>

      {rec ? (
        <>
          <div className="grid grid-cols-2 gap-4 mb-4">
            {/* Base Prices */}
            <div>
              <h4 className="text-xs font-medium text-gray-500 uppercase mb-2">
                Base Prices
              </h4>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Daily:</span>
                  <span className="font-medium">{formatPrice(rec.base_daily)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Weekly:</span>
                  <span className="font-medium">{formatPrice(rec.base_weekly)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Monthly:</span>
                  <span className="font-medium">{formatPrice(rec.base_monthly)}</span>
                </div>
              </div>
            </div>
            {/* Recommended Prices */}
            <div>
              <h4 className="text-xs font-medium text-gray-500 uppercase mb-2">
                Recommended
              </h4>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Daily:</span>
                  <span className={`font-medium ${pctDisplay.className}`}>
                    {formatPrice(rec.rec_daily)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Weekly:</span>
                  <span className={`font-medium ${pctDisplay.className}`}>
                    {formatPrice(rec.rec_weekly)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Monthly:</span>
                  <span className={`font-medium ${pctDisplay.className}`}>
                    {formatPrice(rec.rec_monthly)}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Adjustment Badge */}
          <div className="mb-3 flex items-center gap-2">
            <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${
              rec.premium_discount_pct > 0 ? 'bg-green-100 text-green-700' :
              rec.premium_discount_pct < 0 ? 'bg-red-100 text-red-700' :
              'bg-gray-100 text-gray-600'
            }`}>
              {pctDisplay.text}
            </span>
            {rec.guardrail_applied && (
              <span className="text-xs text-orange-600" title="Guardrail was applied">
                ⚠️ Clamped
              </span>
            )}
          </div>

          {/* Explanation */}
          {rec.explanation_text && (
            <p className="text-xs text-gray-500 mb-3 italic">
              {rec.explanation_text}
            </p>
          )}

          {/* Actions */}
          <div className="flex gap-2">
            <button
              onClick={() => onApprove(categoryId)}
              disabled={!isPending || isLoading}
              className={`flex-1 py-2 rounded font-medium text-sm transition ${
                isPending && !isLoading
                  ? 'bg-green-600 text-white hover:bg-green-700'
                  : 'bg-gray-100 text-gray-400 cursor-not-allowed'
              }`}
            >
              {isLoading ? '...' : isApproved ? '✓ Approved' : 'Approve'}
            </button>
            <button
              onClick={() => onSkip(categoryId)}
              disabled={!isPending || isLoading}
              className={`flex-1 py-2 rounded font-medium text-sm transition ${
                isPending && !isLoading
                  ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  : 'bg-gray-100 text-gray-400 cursor-not-allowed'
              }`}
            >
              {isSkipped ? '✓ Skipped' : 'Skip'}
            </button>
          </div>
        </>
      ) : (
        <div className="text-center py-8 text-gray-400">
          No recommendation for this date
        </div>
      )}
    </div>
  )
}

// 30-Day Window Table Component
interface ForecastTableProps {
  recommendations: Recommendation[]
  categoryName: string
  onApproveDate: (recId: number) => void
  onSkipDate: (recId: number) => void
}

function ForecastTable({ recommendations, categoryName, onApproveDate, onSkipDate }: ForecastTableProps) {
  if (recommendations.length === 0) {
    return (
      <div className="text-center py-8 text-gray-400">
        No forecast data available
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
            <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Base Daily</th>
            <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Rec Daily</th>
            <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Adj %</th>
            <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
            <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {recommendations.map((rec) => {
            const pct = formatPct(rec.premium_discount_pct)
            const isPending = rec.status === 'pending'
            
            return (
              <tr key={rec.id} className={`hover:bg-gray-50 ${
                rec.status === 'approved' ? 'bg-green-50' : 
                rec.status === 'skipped' ? 'bg-gray-50' : ''
              }`}>
                <td className="px-3 py-2 whitespace-nowrap">
                  <div className="font-medium">{formatDate(rec.forecast_date)}</div>
                  <div className="text-xs text-gray-400">Day {rec.horizon_day}</div>
                </td>
                <td className="px-3 py-2 text-right font-mono">
                  {formatPrice(rec.base_daily)}
                </td>
                <td className={`px-3 py-2 text-right font-mono font-medium ${pct.className}`}>
                  {formatPrice(rec.rec_daily)}
                </td>
                <td className={`px-3 py-2 text-right font-medium ${pct.className}`}>
                  {pct.text}
                  {rec.guardrail_applied && <span className="ml-1" title="Guardrail applied">⚠️</span>}
                </td>
                <td className="px-3 py-2 text-center">
                  <span className={`px-2 py-1 rounded text-xs ${
                    rec.status === 'approved' ? 'bg-green-100 text-green-700' :
                    rec.status === 'skipped' ? 'bg-gray-100 text-gray-600' :
                    'bg-blue-100 text-blue-700'
                  }`}>
                    {rec.status}
                  </span>
                </td>
                <td className="px-3 py-2 text-center">
                  {isPending ? (
                    <div className="flex gap-1 justify-center">
                      <button
                        onClick={() => onApproveDate(rec.id)}
                        className="px-2 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700"
                      >
                        ✓
                      </button>
                      <button
                        onClick={() => onSkipDate(rec.id)}
                        className="px-2 py-1 bg-gray-200 text-gray-600 text-xs rounded hover:bg-gray-300"
                      >
                        ✗
                      </button>
                    </div>
                  ) : (
                    <span className="text-gray-400">--</span>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

// Main Dashboard Component
export default function DashboardPage() {
  const { username, tenantId, logout } = useAuthStore()
  
  // State
  const [branches, setBranches] = useState<Branch[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [selectedBranch, setSelectedBranch] = useState<number | null>(null)
  const [selectedDate, setSelectedDate] = useState<string>(getTodayString())
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null)
  const [recommendationsByCategory, setRecommendationsByCategory] = useState<Record<number, Recommendation[]>>({})
  const [summary, setSummary] = useState<RecommendationSummary | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load branches and categories on mount
  useEffect(() => {
    const loadConfig = async () => {
      try {
        const [branchesData, categoriesData] = await Promise.all([
          configApi.getBranches(tenantId || 1),
          configApi.getCategories(tenantId || 1),
        ])
        setBranches(branchesData)
        setCategories(categoriesData)
        
        // Auto-select first branch
        if (branchesData.length > 0) {
          setSelectedBranch(branchesData[0].branch_id)
        }
      } catch (err) {
        console.error('Failed to load config:', err)
        setError('Failed to load configuration')
      }
    }
    loadConfig()
  }, [tenantId])

  // Load summary
  useEffect(() => {
    const loadSummary = async () => {
      try {
        const data = await recommendationsApi.getSummary(tenantId || 1)
        setSummary(data)
      } catch (err) {
        console.error('Failed to load summary:', err)
      }
    }
    loadSummary()
  }, [tenantId])

  // Load recommendations when branch changes
  const loadRecommendations = useCallback(async () => {
    if (!selectedBranch) return

    setIsLoading(true)
    setError(null)
    
    try {
      const results: Record<number, Recommendation[]> = {}
      
      // Load for all categories in parallel
      await Promise.all(
        categories.map(async (cat) => {
          try {
            const data = await recommendationsApi.getRecommendations(
              selectedBranch,
              cat.category_id,
              selectedDate,
              tenantId || 1
            )
            results[cat.category_id] = data.recommendations
          } catch (err) {
            console.error(`Failed to load for category ${cat.category_id}:`, err)
            results[cat.category_id] = []
          }
        })
      )
      
      setRecommendationsByCategory(results)
    } catch (err) {
      setError('Failed to load recommendations')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }, [selectedBranch, selectedDate, categories, tenantId])

  useEffect(() => {
    if (selectedBranch && categories.length > 0) {
      loadRecommendations()
    }
  }, [selectedBranch, selectedDate, categories, loadRecommendations])

  // Generate recommendations
  const handleGenerate = async () => {
    setIsGenerating(true)
    setError(null)
    
    try {
      const result = await recommendationsApi.generate({
        tenant_id: tenantId || 1,
        start_date: selectedDate,
        horizon_days: 30,
      })
      
      alert(`Generated ${result.recommendations_generated} recommendations for ${result.branches_processed} branches`)
      
      // Reload
      await loadRecommendations()
      const newSummary = await recommendationsApi.getSummary(tenantId || 1)
      setSummary(newSummary)
    } catch (err) {
      setError('Failed to generate recommendations')
      console.error(err)
    } finally {
      setIsGenerating(false)
    }
  }

  // Approve category (all 30 days)
  const handleApproveCategory = async (categoryId: number) => {
    if (!selectedBranch || !username) return
    
    setIsLoading(true)
    try {
      const recs = recommendationsByCategory[categoryId] || []
      if (recs.length === 0) return
      
      const startDate = recs[0].forecast_date
      const endDate = recs[recs.length - 1].forecast_date
      
      await recommendationsApi.bulkApprove(
        selectedBranch,
        categoryId,
        startDate,
        endDate,
        username,
        tenantId || 1
      )
      
      // Reload recommendations
      await loadRecommendations()
    } catch (err) {
      setError('Failed to approve recommendations')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  // Skip category (just mark first pending as skipped)
  const handleSkipCategory = async (categoryId: number) => {
    if (!selectedBranch || !username) return
    
    setIsLoading(true)
    try {
      const recs = recommendationsByCategory[categoryId] || []
      const pending = recs.find(r => r.status === 'pending')
      
      if (pending) {
        await recommendationsApi.skip(pending.id, username, 'Skipped from dashboard', tenantId || 1)
        await loadRecommendations()
      }
    } catch (err) {
      setError('Failed to skip recommendation')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  // Approve single date
  const handleApproveDate = async (recId: number) => {
    if (!username) return
    
    try {
      await recommendationsApi.approve(recId, username, tenantId || 1)
      await loadRecommendations()
    } catch (err) {
      setError('Failed to approve')
      console.error(err)
    }
  }

  // Skip single date
  const handleSkipDate = async (recId: number) => {
    if (!username) return
    
    try {
      await recommendationsApi.skip(recId, username, undefined, tenantId || 1)
      await loadRecommendations()
    } catch (err) {
      setError('Failed to skip')
      console.error(err)
    }
  }

  const selectedBranchName = branches.find(b => b.branch_id === selectedBranch)?.branch_name || ''

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-xl font-bold text-gray-800">
              Renty Dynamic Pricing
            </h1>
            <p className="text-sm text-gray-500">Pricing Recommendations Dashboard</p>
          </div>
          <div className="flex items-center gap-4">
            {summary && (
              <div className="text-sm text-gray-500 hidden md:block">
                <span className="font-medium text-green-600">{summary.approved_count}</span> approved |{' '}
                <span className="font-medium text-blue-600">{summary.pending_count}</span> pending
              </div>
            )}
            <span className="text-sm text-gray-600">
              {username}
            </span>
            <button
              onClick={logout}
              className="text-sm text-red-600 hover:text-red-700"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Controls Bar */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex flex-wrap gap-4 items-end">
            {/* Branch Selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Branch
              </label>
              <select
                value={selectedBranch || ''}
                onChange={(e) => setSelectedBranch(Number(e.target.value))}
                className="px-3 py-2 border border-gray-300 rounded-md min-w-[220px] focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Select Branch...</option>
                {branches.map((branch) => (
                  <option key={branch.branch_id} value={branch.branch_id}>
                    {branch.branch_name} {branch.is_airport ? '✈️' : '🏢'}
                  </option>
                ))}
              </select>
            </div>

            {/* Date Selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Start Date
              </label>
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Generate Button */}
            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className={`px-4 py-2 rounded-md font-medium text-white transition ${
                isGenerating
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {isGenerating ? 'Generating...' : '🔄 Generate Recommendations'}
            </button>

            {/* Loading Indicator */}
            {isLoading && (
              <div className="flex items-center text-gray-500">
                <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Loading...
              </div>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div className="mt-3 p-3 bg-red-50 text-red-700 rounded-md text-sm">
              {error}
            </div>
          )}
        </div>

        {/* Category Cards Grid */}
        {selectedBranch ? (
          <>
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-gray-700">
                {selectedBranchName} — {formatDate(selectedDate)}
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mb-8">
              {categories.map((cat) => (
                <CategoryCard
                  key={cat.category_id}
                  categoryId={cat.category_id}
                  categoryName={cat.category_name}
                  recommendations={recommendationsByCategory[cat.category_id] || []}
                  onApprove={handleApproveCategory}
                  onSkip={handleSkipCategory}
                  isLoading={isLoading}
                  selectedDate={selectedDate}
                />
              ))}
            </div>

            {/* 30-Day Forecast Window */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-4 border-b flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-800">
                  30-Day Forecast Window
                </h3>
                <select
                  value={selectedCategory || ''}
                  onChange={(e) => setSelectedCategory(Number(e.target.value) || null)}
                  className="px-3 py-1 border border-gray-300 rounded text-sm"
                >
                  <option value="">Select Category...</option>
                  {categories.map((cat) => (
                    <option key={cat.category_id} value={cat.category_id}>
                      {cat.category_name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="p-4 max-h-[500px] overflow-y-auto">
                {selectedCategory ? (
                  <ForecastTable
                    recommendations={recommendationsByCategory[selectedCategory] || []}
                    categoryName={categories.find(c => c.category_id === selectedCategory)?.category_name || ''}
                    onApproveDate={handleApproveDate}
                    onSkipDate={handleSkipDate}
                  />
                ) : (
                  <div className="text-center py-8 text-gray-400">
                    Select a category to view the 30-day forecast
                  </div>
                )}
              </div>
            </div>
          </>
        ) : (
          <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
            <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            <h3 className="text-lg font-medium mb-2">Select a Branch</h3>
            <p>Choose a branch from the dropdown above to view pricing recommendations</p>
          </div>
        )}
      </main>
    </div>
  )
}
