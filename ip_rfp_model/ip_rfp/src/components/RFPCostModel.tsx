'use client'

import React, { useState, useEffect, useCallback } from 'react';
import CostCard from '@/components/CostCard';
import ExcelExport from '@/components/ExcelExport';

// Constants
const HOURS_PER_MONTH = 173;

// Custom hooks
const useLocalStorage = (key: string, initialValue: any) => {
  const [storedValue, setStoredValue] = useState(initialValue);

  useEffect(() => {
    try {
      const item = window.localStorage.getItem(key);
      if (item) {
        setStoredValue(JSON.parse(item));
      }
    } catch (error) {
      console.log(error);
    }
  }, [key]);

  const setValue = (value: any) => {
    try {
      setStoredValue(value);
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.log(error);
    }
  };

  return [storedValue, setValue];
};

// Components
const InputGroup = ({ label, value, onChange, min = 0, max = 200, type = "number" }: {
  label: string;
  value: number | string;
  onChange: (value: any) => void;
  min?: number;
  max?: number;
  type?: string;
}) => (
  <div className="flex flex-col space-y-2">
    <label className="text-sm font-medium text-gray-600">{label}</label>
    <input
      type={type}
      value={value}
      onChange={(e) => onChange(type === "number" ? parseFloat(e.target.value) || 0 : e.target.value)}
      min={min}
      max={max}
      className="px-4 py-3 border border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none transition-colors text-lg font-medium"
    />
  </div>
);

const ScenarioTab = ({ isActive, onClick, children }: {
  isActive: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) => (
  <button
    onClick={onClick}
    className={`px-8 py-4 rounded-2xl font-semibold text-lg transition-all duration-300 min-w-[180px] ${
      isActive
        ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-xl transform scale-105'
        : 'bg-gray-100 text-gray-600 hover:bg-gray-200 hover:scale-102'
    }`}
  >
    {children}
  </button>
);

// Main Component
export default function RFPCostModel() {
  // Simple scenario-based state
  const [activeScenario, setActiveScenario] = useState('optimistic');

  const [scenarios, setScenarios] = useLocalStorage('rfp-scenarios', {
    conservative: {
      hourlyRate: 150,
      projectDuration: 8,
      teamSize: 4,
      description: '🛡️ Conservative'
    },
    optimistic: {
      hourlyRate: 175,
      projectDuration: 4,
      teamSize: 6,
      description: '🚀 Optimistic'
    },
    pessimistic: {
      hourlyRate: 125,
      projectDuration: 12,
      teamSize: 3,
      description: '⚠️ Pessimistic'
    }
  });

  const updateScenario = (scenario: string, field: string, value: any) => {
    setScenarios((prev: any) => ({
      ...prev,
      [scenario]: {
        ...prev[scenario],
        [field]: value
      }
    }));
  };

  const calculateTotalCost = (scenario: any) => {
    return scenario.hourlyRate * HOURS_PER_MONTH * scenario.projectDuration * scenario.teamSize;
  };

  const currentScenario = scenarios[activeScenario];
  const totalCost = calculateTotalCost(currentScenario);

  const exportData = () => {
    const exportObject = {
      scenarios,
      calculations: {
        conservative: calculateTotalCost(scenarios.conservative),
        optimistic: calculateTotalCost(scenarios.optimistic),
        pessimistic: calculateTotalCost(scenarios.pessimistic)
      },
      exportDate: new Date().toISOString()
    };

    const dataStr = JSON.stringify(exportObject, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    const exportFileDefaultName = `rfp-cost-model-${new Date().toISOString().split('T')[0]}.json`;

    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
            🚀 RFP Cost Model
          </h1>
          <p className="text-xl text-gray-600">Comprehensive Project Cost Analysis</p>
        </div>

        {/* Scenario Tabs */}
        <div className="flex justify-center gap-6 mb-12">
          <ScenarioTab
            isActive={activeScenario === 'conservative'}
            onClick={() => setActiveScenario('conservative')}
          >
            🛡️ Conservative
          </ScenarioTab>
          <ScenarioTab
            isActive={activeScenario === 'optimistic'}
            onClick={() => setActiveScenario('optimistic')}
          >
            🚀 Optimistic
          </ScenarioTab>
          <ScenarioTab
            isActive={activeScenario === 'pessimistic'}
            onClick={() => setActiveScenario('pessimistic')}
          >
            ⚠️ Pessimistic
          </ScenarioTab>
        </div>

        {/* Current Scenario Configuration */}
        <div className="bg-white rounded-3xl shadow-xl p-8 mb-8">
          <h3 className="text-2xl font-bold text-gray-800 mb-8 text-center">
            {currentScenario.description} Scenario
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 items-end">
            <InputGroup
              label="Hourly Rate ($)"
              value={currentScenario.hourlyRate}
              onChange={(value) => updateScenario(activeScenario, 'hourlyRate', value)}
              min={50}
              max={500}
            />
            <InputGroup
              label="Project Duration (months)"
              value={currentScenario.projectDuration}
              onChange={(value) => updateScenario(activeScenario, 'projectDuration', value)}
              min={1}
              max={24}
            />
            <InputGroup
              label="Team Size"
              value={currentScenario.teamSize}
              onChange={(value) => updateScenario(activeScenario, 'teamSize', value)}
              min={1}
              max={20}
            />
            <div className="bg-gradient-to-r from-emerald-500 to-green-500 text-white p-6 rounded-2xl text-center shadow-lg">
              <div className="text-sm opacity-90 mb-1">Total Cost</div>
              <div className="text-3xl font-bold">
                ${totalCost.toLocaleString()}
              </div>
            </div>
          </div>
        </div>

        {/* Cost Comparison Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          <div className={`bg-white rounded-3xl shadow-xl p-8 text-center transition-all duration-300 ${
            activeScenario === 'conservative' ? 'ring-4 ring-blue-500 transform scale-105' : 'hover:scale-102'
          }`}>
            <div className="text-4xl mb-4">🛡️</div>
            <h4 className="text-xl font-bold text-gray-800 mb-2">Conservative</h4>
            <div className="text-3xl font-bold text-blue-600 mb-2">
              ${calculateTotalCost(scenarios.conservative).toLocaleString()}
            </div>
            <div className="text-sm text-gray-500">
              {scenarios.conservative.teamSize} team • {scenarios.conservative.projectDuration} months
            </div>
          </div>

          <div className={`bg-white rounded-3xl shadow-xl p-8 text-center transition-all duration-300 ${
            activeScenario === 'optimistic' ? 'ring-4 ring-purple-500 transform scale-105' : 'hover:scale-102'
          }`}>
            <div className="text-4xl mb-4">🚀</div>
            <h4 className="text-xl font-bold text-gray-800 mb-2">Optimistic</h4>
            <div className="text-3xl font-bold text-purple-600 mb-2">
              ${calculateTotalCost(scenarios.optimistic).toLocaleString()}
            </div>
            <div className="text-sm text-gray-500">
              {scenarios.optimistic.teamSize} team • {scenarios.optimistic.projectDuration} months
            </div>
          </div>

          <div className={`bg-white rounded-3xl shadow-xl p-8 text-center transition-all duration-300 ${
            activeScenario === 'pessimistic' ? 'ring-4 ring-red-500 transform scale-105' : 'hover:scale-102'
          }`}>
            <div className="text-4xl mb-4">⚠️</div>
            <h4 className="text-xl font-bold text-gray-800 mb-2">Pessimistic</h4>
            <div className="text-3xl font-bold text-red-600 mb-2">
              ${calculateTotalCost(scenarios.pessimistic).toLocaleString()}
            </div>
            <div className="text-sm text-gray-500">
              {scenarios.pessimistic.teamSize} team • {scenarios.pessimistic.projectDuration} months
            </div>
          </div>
        </div>

        {/* Export Section */}
        <div className="text-center">
          <button
            onClick={exportData}
            className="px-8 py-4 bg-gradient-to-r from-emerald-500 to-green-500 text-white rounded-2xl font-semibold text-lg shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105"
          >
            📊 Export to Excel
          </button>
        </div>
      </div>
    </div>
  );
}