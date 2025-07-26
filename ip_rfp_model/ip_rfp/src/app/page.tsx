'use client'

import React, { useState, useEffect, useCallback } from 'react';

import CostCard from '@/components/CostCard';
import ExcelExport from '@/components/ExcelExport';
import PLAnalysis from '../components/PLAnalysis';


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
  <div className="flex flex-col space-y-1">
    <label className="text-sm font-semibold text-gray-700">{label}</label>
    <input
      type={type}
      value={value}
      onChange={(e) => onChange(type === "number" ? parseFloat(e.target.value) || 0 : e.target.value)}
      min={min}
      max={max}
      className="px-3 py-2 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:outline-none transition-colors"
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
    className={`flex-1 py-3 px-4 rounded-lg font-semibold transition-all duration-300 ${
      isActive
        ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg transform -translate-y-1'
        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
    }`}
  >
    {children}
  </button>
);

const AdditionalCostItem = ({ item, index, onUpdate, onRemove }: {
  item: any;
  index: number;
  onUpdate: (index: number, field: string, value: any) => void;
  onRemove: (index: number) => void;
}) => (
  <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
    <input
      type="text"
      placeholder="Item description"
      value={item.description}
      onChange={(e) => onUpdate(index, 'description', e.target.value)}
      className="flex-2 px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
    />
    <input
      type="number"
      placeholder="Amount"
      value={item.amount}
      onChange={(e) => onUpdate(index, 'amount', parseFloat(e.target.value) || 0)}
      className="flex-1 px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
    />
    <select
      value={item.frequency}
      onChange={(e) => onUpdate(index, 'frequency', e.target.value)}
      className="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
    >
      <option value="monthly">Monthly</option>
      <option value="annually">Annually</option>
      <option value="oneTime">One-time</option>
      <option value="phase1">Phase I Only</option>
      <option value="phase2">Phase II Only</option>
      <option value="phase3">Phase III Only</option>
    </select>
    <button
      onClick={() => onRemove(index)}
      className="px-3 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
    >
      Remove
    </button>
  </div>
);

// Main Component
export default function RFPCostModel() {
  // State management
  const [rates, setRates] = useLocalStorage('rfp-rates', {
    manager: 165,
    developer: 160,
    dba: 155,
    junior: 150,
    mobile: 150
  });

  const [phases, setPhases] = useLocalStorage('rfp-phases', {
    phase1: {
      manager: 60, developer: 75, dba: 50, junior: 65, mobile: 80, duration: 8
    },
    phase2: {
      manager: 50, developer: 60, dba: 70, junior: 55, mobile: 40, duration: 10
    },
    phase3: {
      manager: 40, developer: 45, dba: 60, junior: 50, mobile: 20, duration: 6
    }
  });

  const [additionalCosts, setAdditionalCosts] = useLocalStorage('rfp-additional', [
    { description: 'Software Licenses', amount: 5000, frequency: 'annually' }
  ]);

  const [activeScenario, setActiveScenario] = useState('custom');
  const [calculations, setCalculations] = useState<any>({});

  // Scenario presets
  const scenarios: any = {
    conservative: {
      phase1: { manager: 50, developer: 50, dba: 50, junior: 50, mobile: 60 },
      phase2: { manager: 50, developer: 50, dba: 50, junior: 50, mobile: 30 },
      phase3: { manager: 50, developer: 50, dba: 50, junior: 50, mobile: 20 }
    },
    moderate: {
      phase1: { manager: 62.5, developer: 65, dba: 60, junior: 62.5, mobile: 70 },
      phase2: { manager: 62.5, developer: 62.5, dba: 65, junior: 62.5, mobile: 40 },
      phase3: { manager: 62.5, developer: 62.5, dba: 65, junior: 62.5, mobile: 25 }
    },
    aggressive: {
      phase1: { manager: 75, developer: 75, dba: 70, junior: 75, mobile: 80 },
      phase2: { manager: 75, developer: 75, dba: 75, junior: 75, mobile: 50 },
      phase3: { manager: 75, developer: 75, dba: 75, junior: 75, mobile: 30 }
    }
  };

  // Calculations
  const calculateCosts = useCallback(() => {
    const phaseNames = ['phase1', 'phase2', 'phase3'];
    let totalCost = 0;
    let totalHours = 0;
    let permStaffCost = 0;
    let contractorCost = 0;
    const phaseBreakdown: any[] = [];

    phaseNames.forEach((phaseName, index) => {
      const phase = phases[phaseName];
      const phaseCosts: any = {};
      let phaseTotal = 0;
      let phaseHours = 0;

      Object.keys(rates).forEach(role => {
        const monthlyHours = HOURS_PER_MONTH * (phase[role] / 100);
        const roleHours = monthlyHours * phase.duration;
        const roleCost = roleHours * rates[role];

        phaseCosts[role] = roleCost;
        phaseTotal += roleCost;
        phaseHours += roleHours;

        if (role === 'mobile') {
          contractorCost += roleCost;
        } else {
          permStaffCost += roleCost;
        }
      });

      totalCost += phaseTotal;
      totalHours += phaseHours;

      phaseBreakdown.push({
        name: `Phase ${index + 1}`,
        duration: phase.duration,
        costs: phaseCosts,
        total: phaseTotal,
        hours: phaseHours
      });
    });

    // Calculate additional costs
    let additionalTotal = 0;
    additionalCosts.forEach((item: any) => {
      let itemTotal = 0;
      switch(item.frequency) {
        case 'monthly':
          itemTotal = item.amount * 24;
          break;
        case 'annually':
          itemTotal = item.amount * 2;
          break;
        case 'oneTime':
        case 'phase1':
        case 'phase2':
        case 'phase3':
          itemTotal = item.amount;
          break;
      }
      additionalTotal += itemTotal;
    });

    const totalDuration = Object.values(phases).reduce((sum: number, phase: any) => sum + phase.duration, 0);

    setCalculations({
      totalCost,
      totalHours,
      permStaffCost,
      contractorCost,
      additionalTotal,
      grandTotal: totalCost + additionalTotal,
      avgMonthly: totalCost / totalDuration,
      phaseBreakdown,
      totalDuration
    });
  }, [rates, phases, additionalCosts]);

  // Effects
  useEffect(() => {
    calculateCosts();
  }, [calculateCosts]);

  // Event handlers
  const updateRate = (role: string, value: number) => {
    setRates((prev: any) => ({ ...prev, [role]: value }));
  };

  const updatePhase = (phaseName: string, field: string, value: number) => {
    setPhases((prev: any) => ({
      ...prev,
      [phaseName]: { ...prev[phaseName], [field]: value }
    }));
  };

  const applyScenario = (scenarioName: string) => {
    setActiveScenario(scenarioName);
    if (scenarios[scenarioName]) {
      const newPhases = { ...phases };
      Object.keys(scenarios[scenarioName]).forEach(phaseName => {
        Object.keys(scenarios[scenarioName][phaseName]).forEach(role => {
          newPhases[phaseName][role] = scenarios[scenarioName][phaseName][role];
        });
      });
      setPhases(newPhases);
    }
  };

  const addAdditionalCost = () => {
    setAdditionalCosts((prev: any[]) => [
      ...prev,
      { description: '', amount: 0, frequency: 'monthly' }
    ]);
  };

  const updateAdditionalCost = (index: number, field: string, value: any) => {
    setAdditionalCosts((prev: any[]) => prev.map((item, i) =>
      i === index ? { ...item, [field]: value } : item
    ));
  };

  const removeAdditionalCost = (index: number) => {
    setAdditionalCosts((prev: any[]) => prev.filter((_, i) => i !== index));
  };

  const exportData = () => {
    const exportObject = {
      rates,
      phases,
      additionalCosts,
      calculations,
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2">
            🚀 RFP Project Cost Model
          </h1>
          <p className="text-gray-600">Next.js Implementation - Professional Cost Estimation Tool</p>
          <div className="flex justify-center gap-4 mt-4">
  <button
    onClick={exportData}
    className="px-6 py-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-lg hover:shadow-lg transition-all"
  >
    📊 Export JSON
  </button>
  <ExcelExport
    rates={rates}
    phases={phases}
    additionalCosts={additionalCosts}
    calculations={calculations}
    scenarios={scenarios}
  />
</div>
        </div>

        {/* Team Rates Configuration */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Team Hourly Rates</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <InputGroup
              label="Manager ($/hour)"
              value={rates.manager}
              onChange={(value) => updateRate('manager', value)}
            />
            <InputGroup
              label="C#/JS Developer ($/hour)"
              value={rates.developer}
              onChange={(value) => updateRate('developer', value)}
            />
            <InputGroup
              label="Database Admin ($/hour)"
              value={rates.dba}
              onChange={(value) => updateRate('dba', value)}
            />
            <InputGroup
              label="Junior DBA/Tester ($/hour)"
              value={rates.junior}
              onChange={(value) => updateRate('junior', value)}
            />
            <InputGroup
              label="Mobile Developer ($/hour)"
              value={rates.mobile}
              onChange={(value) => updateRate('mobile', value)}
            />
          </div>
        </div>

        {/* Scenario Selection */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Utilization Scenarios</h3>
          <div className="flex space-x-2 mb-6">
            <ScenarioTab
              isActive={activeScenario === 'conservative'}
              onClick={() => applyScenario('conservative')}
            >
              Conservative (50%)
            </ScenarioTab>
            <ScenarioTab
              isActive={activeScenario === 'moderate'}
              onClick={() => applyScenario('moderate')}
            >
              Moderate (62.5%)
            </ScenarioTab>
            <ScenarioTab
              isActive={activeScenario === 'aggressive'}
              onClick={() => applyScenario('aggressive')}
            >
              Aggressive (75%)
            </ScenarioTab>
            <ScenarioTab
              isActive={activeScenario === 'custom'}
              onClick={() => setActiveScenario('custom')}
            >
              Custom
            </ScenarioTab>
          </div>

          {/* Phase Configuration */}
          {['phase1', 'phase2', 'phase3'].map((phaseName, index) => (
            <div key={phaseName} className="mb-6 p-4 bg-gray-50 rounded-lg">
              <h4 className="font-semibold text-gray-700 mb-3">Phase {index + 1} - Utilization (%)</h4>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <InputGroup
                  label="Manager"
                  value={phases[phaseName].manager}
                  onChange={(value) => updatePhase(phaseName, 'manager', value)}
                  max={100}
                />
                <InputGroup
                  label="Developer"
                  value={phases[phaseName].developer}
                  onChange={(value) => updatePhase(phaseName, 'developer', value)}
                  max={100}
                />
                <InputGroup
                  label="DBA"
                  value={phases[phaseName].dba}
                  onChange={(value) => updatePhase(phaseName, 'dba', value)}
                  max={100}
                />
                <InputGroup
                  label="Junior"
                  value={phases[phaseName].junior}
                  onChange={(value) => updatePhase(phaseName, 'junior', value)}
                  max={100}
                />
                <InputGroup
                  label="Mobile Dev"
                  value={phases[phaseName].mobile}
                  onChange={(value) => updatePhase(phaseName, 'mobile', value)}
                  max={100}
                />
                <InputGroup
                  label="Duration (months)"
                  value={phases[phaseName].duration}
                  onChange={(value) => updatePhase(phaseName, 'duration', value)}
                  max={24}
                />
              </div>
            </div>
          ))}
        </div>

        {/* Cost Summary */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">📊 Project Cost Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <CostCard
              title="Total Project Cost"
              value={`$${calculations.totalCost?.toLocaleString() || 0}`}
              gradient="from-blue-500 to-purple-600"
            />
            <CostCard
              title="Total Hours"
              value={calculations.totalHours?.toLocaleString() || 0}
              gradient="from-green-500 to-blue-500"
            />
            <CostCard
              title="Avg Monthly Cost"
              value={`$${Math.round(calculations.avgMonthly)?.toLocaleString() || 0}`}
              gradient="from-purple-500 to-pink-500"
            />
            <CostCard
              title="Permanent Staff"
              value={`$${calculations.permStaffCost?.toLocaleString() || 0}`}
              gradient="from-indigo-500 to-blue-500"
            />
            <CostCard
              title="Contractor"
              value={`$${calculations.contractorCost?.toLocaleString() || 0}`}
              gradient="from-orange-500 to-red-500"
            />
          </div>
        </div>

        {/* Detailed Breakdown */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Detailed Cost Breakdown</h3>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-gradient-to-r from-blue-500 to-purple-600 text-white">
                  <th className="p-3 text-left">Phase</th>
                  <th className="p-3 text-left">Duration</th>
                  <th className="p-3 text-left">Manager</th>
                  <th className="p-3 text-left">Developer</th>
                  <th className="p-3 text-left">DBA</th>
                  <th className="p-3 text-left">Junior</th>
                  <th className="p-3 text-left">Mobile Dev</th>
                  <th className="p-3 text-left">Phase Total</th>
                </tr>
              </thead>
              <tbody>
                {calculations.phaseBreakdown?.map((phase: any, index: number) => (
                  <tr key={index} className={index % 2 === 0 ? 'bg-gray-50' : 'bg-white'}>
                    <td className="p-3 font-semibold">{phase.name}</td>
                    <td className="p-3">{phase.duration} months</td>
                    <td className="p-3">${phase.costs.manager?.toLocaleString()}</td>
                    <td className="p-3">${phase.costs.developer?.toLocaleString()}</td>
                    <td className="p-3">${phase.costs.dba?.toLocaleString()}</td>
                    <td className="p-3">${phase.costs.junior?.toLocaleString()}</td>
                    <td className="p-3">${phase.costs.mobile?.toLocaleString()}</td>
                    <td className="p-3 font-bold">${phase.total?.toLocaleString()}</td>
                  </tr>
                ))}
                <tr className="bg-gradient-to-r from-blue-500 to-purple-600 text-white font-bold">
                  <td className="p-3">TOTALS</td>
                  <td className="p-3">{calculations.totalDuration} months</td>
                  <td className="p-3">-</td>
                  <td className="p-3">-</td>
                  <td className="p-3">-</td>
                  <td className="p-3">-</td>
                  <td className="p-3">-</td>
                  <td className="p-3">${calculations.totalCost?.toLocaleString()}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Additional Costs */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">➕ Additional Costs & Revenue Streams</h3>
          <div className="space-y-3 mb-4">
            {additionalCosts.map((item: any, index: number) => (
              <AdditionalCostItem
                key={index}
                item={item}
                index={index}
                onUpdate={updateAdditionalCost}
                onRemove={removeAdditionalCost}
              />
            ))}
          </div>
          <div className="flex justify-between items-center">
            <button
              onClick={addAdditionalCost}
              className="px-4 py-2 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-lg hover:shadow-lg transition-all"
            >
              Add Item
            </button>
            <div className="text-right">
              <div className="text-lg font-semibold">
                Additional Costs: <span className="text-blue-600">${calculations.additionalTotal?.toLocaleString() || 0}</span>
              </div>
              <div className="text-2xl font-bold text-purple-600">
                Grand Total: <span>${calculations.grandTotal?.toLocaleString() || 0}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}