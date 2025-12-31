import { VehicleCategory, PricingRecommendation, CompetitorPrice, DailyStat } from './types';

// Based on "95.63% accurate demand prediction" and "Thursday Peak +16.7%"
export const DEMAND_DATA: DailyStat[] = [
  { date: 'Mon', demandForecast: 120, actualBookings: 118, revenue: 45000 },
  { date: 'Tue', demandForecast: 115, actualBookings: 112, revenue: 42000 },
  { date: 'Wed', demandForecast: 125, actualBookings: 128, revenue: 48000 },
  { date: 'Thu', demandForecast: 145, actualBookings: 142, revenue: 58000 }, // Peak
  { date: 'Fri', demandForecast: 140, actualBookings: 135, revenue: 56000 },
  { date: 'Sat', demandForecast: 130, actualBookings: 129, revenue: 51000 },
  { date: 'Sun', demandForecast: 110, actualBookings: 108, revenue: 41000 },
];

export const MOCK_RECOMMENDATIONS: PricingRecommendation[] = [
  {
    id: '1',
    category: VehicleCategory.Economy,
    currentPrice: 120,
    recommendedPrice: 135,
    demandMultiplier: 1.1,
    supplyMultiplier: 0.95,
    eventMultiplier: 1.0,
    reason: 'High weekday demand forecast',
    confidence: 96,
    status: 'Pending',
  },
  {
    id: '2',
    category: VehicleCategory.SUV,
    currentPrice: 350,
    recommendedPrice: 385,
    demandMultiplier: 1.05,
    supplyMultiplier: 1.0,
    eventMultiplier: 1.0,
    reason: 'Thursday Peak adjustment',
    confidence: 94,
    status: 'Pending',
  },
  {
    id: '3',
    category: VehicleCategory.Luxury,
    currentPrice: 800,
    recommendedPrice: 750,
    demandMultiplier: 0.85,
    supplyMultiplier: 1.1,
    eventMultiplier: 1.0,
    reason: 'Excess supply in current branch',
    confidence: 92,
    status: 'Pending',
  },
];

export const COMPETITOR_DATA: CompetitorPrice[] = [
  { id: 'c1', competitorName: 'Yallo', category: VehicleCategory.Economy, price: 130, lastUpdated: '2h ago' },
  { id: 'c2', competitorName: 'Sixto', category: VehicleCategory.Economy, price: 140, lastUpdated: '1h ago' },
  { id: 'c3', competitorName: 'Budgeto', category: VehicleCategory.Economy, price: 125, lastUpdated: '4h ago' },
  { id: 'c4', competitorName: 'Yallo', category: VehicleCategory.SUV, price: 390, lastUpdated: '2h ago' },
  { id: 'c5', competitorName: 'Sixto', category: VehicleCategory.SUV, price: 410, lastUpdated: '1h ago' },
];

export const SYSTEM_METRICS = {
  totalContracts: '2,483,704',
  accuracy: '95.63%',
  revenue: '739.2M',
  utilization: '78.4%',
  ramadanImpact: '-20.8%',
  thursdayPeak: '+16.7%',
};
