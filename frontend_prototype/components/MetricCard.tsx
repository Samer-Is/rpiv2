import React from 'react';
import { MetricCardProps } from '../types';

const MetricCard: React.FC<MetricCardProps> = ({ title, value, change, isPositive, icon: Icon }) => {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start">
        <div>
          <p className="text-sm font-medium text-slate-500">{title}</p>
          <h3 className="text-2xl font-bold text-slate-900 mt-2">{value}</h3>
        </div>
        <div className={`p-2 rounded-lg ${isPositive === undefined ? 'bg-slate-100' : isPositive ? 'bg-green-50' : 'bg-red-50'}`}>
          <Icon className={`w-6 h-6 ${isPositive === undefined ? 'text-slate-600' : isPositive ? 'text-green-600' : 'text-red-600'}`} />
        </div>
      </div>
      {change && (
        <div className="mt-4 flex items-center">
          <span className={`text-sm font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
            {change}
          </span>
          <span className="text-sm text-slate-400 ml-2">vs last month</span>
        </div>
      )}
    </div>
  );
};

export default MetricCard;
