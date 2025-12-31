import React from 'react';

export enum VehicleCategory {
  Economy = 'Economy',
  Compact = 'Compact',
  Standard = 'Standard',
  SUV = 'SUV',
  Luxury = 'Luxury',
  Van = 'Van',
}

export enum PricingZone {
  Riyadh = 'Riyadh',
  Jeddah = 'Jeddah',
  Dammam = 'Dammam',
  Mecca = 'Mecca',
  Medina = 'Medina',
}

export interface MetricCardProps {
  title: string;
  value: string;
  change?: string;
  isPositive?: boolean;
  icon: React.ElementType;
}

export interface CompetitorPrice {
  id: string;
  competitorName: string;
  category: VehicleCategory;
  price: number;
  lastUpdated: string;
}

export interface PricingRecommendation {
  id: string;
  category: VehicleCategory;
  currentPrice: number;
  recommendedPrice: number;
  demandMultiplier: number;
  supplyMultiplier: number;
  eventMultiplier: number;
  reason: string;
  confidence: number;
  status: 'Pending' | 'Approved' | 'Rejected';
}

export interface DailyStat {
  date: string;
  demandForecast: number;
  actualBookings: number;
  revenue: number;
}