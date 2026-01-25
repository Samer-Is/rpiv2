/**
 * Recommendations API Client
 * CHUNK 10: Frontend for pricing recommendations
 */
import { api } from './client'

// Types
export interface Recommendation {
  id: number
  forecast_date: string
  horizon_day: number
  base_daily: number
  base_weekly: number
  base_monthly: number
  rec_daily: number
  rec_weekly: number
  rec_monthly: number
  premium_discount_pct: number
  utilization_signal: number | null
  forecast_signal: number | null
  competitor_signal: number | null
  weather_signal: number | null
  holiday_signal: number | null
  explanation_text: string | null
  guardrail_applied: boolean
  status: 'pending' | 'approved' | 'skipped'
}

export interface RecommendationsResponse {
  tenant_id: number
  branch_id: number
  category_id: number
  branch_name: string | null
  category_name: string | null
  run_date: string
  recommendations: Recommendation[]
}

export interface GenerateRequest {
  tenant_id?: number
  branch_id?: number
  category_id?: number
  start_date?: string
  horizon_days?: number
}

export interface GenerateResponse {
  tenant_id: number
  run_date: string
  branches_processed: number
  categories_processed: number
  recommendations_generated: number
  recommendations_saved: number
  errors: string[]
}

export interface RecommendationSummary {
  tenant_id: number
  total_recommendations: number
  pending_count: number
  approved_count: number
  skipped_count: number
  branches_with_recs: number
  categories_with_recs: number
  date_range_start: string | null
  date_range_end: string | null
  avg_adjustment_pct: number | null
}

export interface Branch {
  branch_id: number
  branch_name: string
  city: string
  is_airport: boolean
}

export interface Category {
  category_id: number
  category_name: string
}

// API Functions
export const recommendationsApi = {
  /**
   * Get recommendations for a specific branch and category
   */
  getRecommendations: async (
    branchId: number,
    categoryId: number,
    startDate?: string,
    tenantId: number = 1
  ): Promise<RecommendationsResponse> => {
    const params = new URLSearchParams({
      branch_id: branchId.toString(),
      category_id: categoryId.toString(),
      tenant_id: tenantId.toString(),
    })
    if (startDate) {
      params.append('start_date', startDate)
    }
    const response = await api.get(`/recommendations?${params}`)
    return response.data
  },

  /**
   * Get recommendations summary
   */
  getSummary: async (tenantId: number = 1): Promise<RecommendationSummary> => {
    const response = await api.get(`/recommendations/summary?tenant_id=${tenantId}`)
    return response.data
  },

  /**
   * Generate new recommendations
   */
  generate: async (request: GenerateRequest): Promise<GenerateResponse> => {
    const response = await api.post('/recommendations/generate', request)
    return response.data
  },

  /**
   * Approve a single recommendation
   */
  approve: async (recommendationId: number, userId: string, tenantId: number = 1): Promise<void> => {
    await api.post(`/recommendations/${recommendationId}/approve?tenant_id=${tenantId}`, {
      user_id: userId,
    })
  },

  /**
   * Skip a single recommendation
   */
  skip: async (recommendationId: number, userId: string, reason?: string, tenantId: number = 1): Promise<void> => {
    await api.post(`/recommendations/${recommendationId}/skip?tenant_id=${tenantId}`, {
      user_id: userId,
      reason,
    })
  },

  /**
   * Bulk approve recommendations for a date range
   */
  bulkApprove: async (
    branchId: number,
    categoryId: number,
    startDate: string,
    endDate: string,
    userId: string,
    tenantId: number = 1
  ): Promise<{ count: number }> => {
    const response = await api.post('/recommendations/bulk-approve', {
      tenant_id: tenantId,
      branch_id: branchId,
      category_id: categoryId,
      start_date: startDate,
      end_date: endDate,
      user_id: userId,
    })
    return response.data
  },

  /**
   * Get all recommendations for a specific date
   */
  getByDate: async (targetDate: string, tenantId: number = 1) => {
    const response = await api.get(`/recommendations/by-date/${targetDate}?tenant_id=${tenantId}`)
    return response.data
  },
}

// Config API for branches and categories
export const configApi = {
  /**
   * Get selected branches from config
   */
  getBranches: async (tenantId: number = 1): Promise<Branch[]> => {
    try {
      const response = await api.get(`/config/selections/branches?tenant_id=${tenantId}`)
      return response.data.map((b: any) => ({
        branch_id: b.item_id,
        branch_name: b.item_name || `Branch ${b.item_id}`,
        city: 'Saudi Arabia',
        is_airport: b.item_subtype === 'airport',
      }))
    } catch (error) {
      // Fallback to hardcoded MVP branches if config not available
      return [
        { branch_id: 122, branch_name: 'Riyadh Airport', city: 'Riyadh', is_airport: true },
        { branch_id: 15, branch_name: 'Jeddah Airport', city: 'Jeddah', is_airport: true },
        { branch_id: 26, branch_name: 'Dammam Airport', city: 'Dammam', is_airport: true },
        { branch_id: 2, branch_name: 'Riyadh City', city: 'Riyadh', is_airport: false },
        { branch_id: 34, branch_name: 'Jeddah City', city: 'Jeddah', is_airport: false },
        { branch_id: 211, branch_name: 'Riyadh - Al Quds', city: 'Riyadh', is_airport: false },
      ]
    }
  },

  /**
   * Get selected categories from config
   */
  getCategories: async (tenantId: number = 1): Promise<Category[]> => {
    try {
      const response = await api.get(`/config/selections/categories?tenant_id=${tenantId}`)
      return response.data.map((c: any) => ({
        category_id: c.item_id,
        category_name: c.item_name || `Category ${c.item_id}`,
      }))
    } catch (error) {
      // Fallback to hardcoded MVP categories if config not available
      return [
        { category_id: 1, category_name: 'Economy' },
        { category_id: 2, category_name: 'Compact' },
        { category_id: 3, category_name: 'Standard' },
        { category_id: 4, category_name: 'SUV' },
        { category_id: 5, category_name: 'Luxury' },
        { category_id: 6, category_name: 'Van' },
      ]
    }
  },
}
