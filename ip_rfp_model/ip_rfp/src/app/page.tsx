'use client'

import React, { useState } from 'react';
import RFPCostModel from '../components/RFPCostModel';
import PLAnalysis from '../components/PLAnalysis';

export default function Home() {
  const [activeView, setActiveView] = useState('cost-model');

  return (
    <div className="min-h-screen">
      {/* Navigation Header */}
      <div className="bg-white shadow-sm border-b sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex space-x-1 py-4">
            <button
              onClick={() => setActiveView('cost-model')}
              className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                activeView === 'cost-model'
                  ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg transform -translate-y-1'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              🚀 RFP Cost Model
            </button>
            <button
              onClick={() => setActiveView('pl-analysis')}
              className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                activeView === 'pl-analysis'
                  ? 'bg-gradient-to-r from-green-500 to-blue-500 text-white shadow-lg transform -translate-y-1'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              📊 P&L Analysis
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="transition-all duration-300">
        {activeView === 'cost-model' && <RFPCostModel />}
        {activeView === 'pl-analysis' && <PLAnalysis />}
      </div>
    </div>
  );
}