/**
 * API Service for Renty Dynamic Pricing
 * Connects React frontend to Python FastAPI backend
 */

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Types matching the backend API
export interface Branch {
  id: number;
  name: string;
  city: string;
  is_airport: boolean;
}

export interface UtilizationData {
  branch_id: number;
  total_vehicles: number;
  rented_vehicles: number;
  available_vehicles: number;
  utilization_pct: number;
  source: string;
}

export interface Category {
  id: string;
  name: string;
  icon: string;
  examples: string;
  base_price: number;
}

export interface PricingRequest {
  branch_id: number;
  category: string;
  base_price: number;
  target_date?: string;
  is_holiday?: boolean;
  is_school_vacation?: boolean;
  is_ramadan?: boolean;
  is_umrah_season?: boolean;
  is_hajj?: boolean;
  is_festival?: boolean;
  is_sports_event?: boolean;
  is_conference?: boolean;
  is_weekend?: boolean;
}

export interface PricingResponse {
  category: string;
  base_price: number;
  final_price: number;
  price_change_pct: number;
  demand_multiplier: number;
  supply_multiplier: number;
  event_multiplier: number;
  final_multiplier: number;
  predicted_demand: number;
  average_demand: number;
  explanation: string;
  target_date: string;
}

export interface CompetitorData {
  competitor_name: string;
  price: number;
  vehicle?: string;
  last_updated: string;
}

export interface CompetitorResponse {
  category: string;
  avg_price: number | null;
  min_price: number | null;
  max_price: number | null;
  competitor_count: number;
  competitors: CompetitorData[];
}

export interface CategoryPricing {
  category: string;
  icon: string;
  examples: string;
  base_price: number;
  final_price: number;
  price_change_pct: number;
  demand_multiplier: number;
  supply_multiplier: number;
  event_multiplier: number;
  explanation: string;
  competitor_avg: number | null;
  competitor_count: number;
}

export interface AllPricingResponse {
  branch_id: number;
  branch_name: string;
  city: string;
  target_date: string;
  utilization: UtilizationData;
  categories: CategoryPricing[];
}

export interface SystemMetrics {
  total_contracts: string;
  model_accuracy: string;
  annual_revenue: string;
  avg_utilization: string;
  model_version: string;
  data_freshness: {
    available: boolean;
    age_hours?: number;
    status?: string;
  };
}

export interface DemandDataPoint {
  day: string;
  date: string;
  demand_forecast: number;
  actual_bookings: number;
  revenue: number;
}

export interface WeeklyDistribution {
  day: string;
  bookings: number;
  is_peak: boolean;
}

export interface SeasonalImpact {
  season: string;
  volume: number;
  color: string;
}

// API Functions
class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async fetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `API Error: ${response.status}`);
      }

      return response.json();
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error('Unable to connect to API server. Please ensure the backend is running.');
      }
      throw error;
    }
  }

  // Health check
  async healthCheck(): Promise<{ status: string; pricing_engine: boolean; timestamp: string }> {
    return this.fetch('/api/health');
  }

  // Branches
  async getBranches(): Promise<Branch[]> {
    return this.fetch('/api/branches');
  }

  async getBranch(branchId: number): Promise<Branch> {
    return this.fetch(`/api/branches/${branchId}`);
  }

  async getBranchUtilization(branchId: number, targetDate?: string): Promise<UtilizationData> {
    const params = targetDate ? `?target_date=${targetDate}` : '';
    return this.fetch(`/api/branches/${branchId}/utilization${params}`);
  }

  // Categories
  async getCategories(): Promise<Category[]> {
    return this.fetch('/api/categories');
  }

  // Pricing
  async calculatePricing(request: PricingRequest): Promise<PricingResponse> {
    return this.fetch('/api/pricing', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getAllCategoryPricing(
    branchId: number,
    options?: {
      target_date?: string;
      is_holiday?: boolean;
      is_school_vacation?: boolean;
      is_ramadan?: boolean;
      is_umrah_season?: boolean;
      is_hajj?: boolean;
      is_festival?: boolean;
      is_sports_event?: boolean;
      is_conference?: boolean;
      is_weekend?: boolean;
    }
  ): Promise<AllPricingResponse> {
    const params = new URLSearchParams();
    if (options) {
      Object.entries(options).forEach(([key, value]) => {
        if (value !== undefined && value !== false) {
          params.append(key, String(value));
        }
      });
    }
    const queryString = params.toString();
    const url = `/api/pricing/all/${branchId}${queryString ? `?${queryString}` : ''}`;
    return this.fetch(url);
  }

  // Competitors
  async getCompetitorPrices(branchId: number, category: string): Promise<CompetitorResponse> {
    return this.fetch(`/api/competitors/${branchId}/${encodeURIComponent(category)}`);
  }

  // Metrics - now branch-specific
  async getSystemMetrics(branchId?: number): Promise<SystemMetrics> {
    const params = branchId ? `?branch_id=${branchId}` : '';
    return this.fetch(`/api/metrics${params}`);
  }

  // Analytics - all now branch-specific
  async getDemandData(branchId?: number): Promise<DemandDataPoint[]> {
    const params = branchId ? `?branch_id=${branchId}` : '';
    return this.fetch(`/api/demand-data${params}`);
  }

  async getWeeklyDistribution(branchId?: number): Promise<WeeklyDistribution[]> {
    const params = branchId ? `?branch_id=${branchId}` : '';
    return this.fetch(`/api/analytics/weekly-distribution${params}`);
  }

  async getSeasonalImpact(branchId?: number): Promise<SeasonalImpact[]> {
    const params = branchId ? `?branch_id=${branchId}` : '';
    return this.fetch(`/api/analytics/seasonal-impact${params}`);
  }

  // Refresh competitor data from Booking.com API
  async refreshCompetitorData(): Promise<{
    success: boolean;
    message: string;
    categories_updated: number;
    timestamp: string;
  }> {
    return this.fetch('/api/competitors/refresh', { method: 'POST' });
  }

  // Test database connection
  async testDatabaseConnection(): Promise<{
    status: string;
    server?: string;
    database?: string;
    message?: string;
    timestamp: string;
  }> {
    return this.fetch('/api/database/test');
  }

  // Get car-by-car price matches
  async getCarMatches(branchId: number): Promise<{
    branch_id: number;
    branch_name: string;
    total_matches: number;
    models_matched: number;
    matches: Array<{
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
    }>;
  }> {
    return this.fetch(`/api/car-matches/${branchId}`);
  }

  // Generate pricing report data
  async getPricingReport(
    branchId: number,
    options?: {
      target_date?: string;
      is_holiday?: boolean;
      is_ramadan?: boolean;
      is_hajj?: boolean;
      is_weekend?: boolean;
    }
  ): Promise<{
    report_date: string;
    branch: any;
    data: any[];
  }> {
    const params = new URLSearchParams();
    if (options) {
      Object.entries(options).forEach(([key, value]) => {
        if (value !== undefined && value !== false) {
          params.append(key, String(value));
        }
      });
    }
    const queryString = params.toString();
    return this.fetch(`/api/pricing/report/${branchId}${queryString ? `?${queryString}` : ''}`);
  }
}

// Export singleton instance
export const api = new ApiService();

// Export class for testing or custom instances
export { ApiService };
