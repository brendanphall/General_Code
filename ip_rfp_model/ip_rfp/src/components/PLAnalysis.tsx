import React, { useState, useEffect, useCallback } from 'react';
import * as XLSX from 'xlsx';

interface PLData {
  revenue: {
    internalLicensesPhase1: { quantity: number; rate: number };
    externalLicensesPhase2: { quantity: number; rate: number };
    implementationServicesPhase1: { quantity: number; rate: number };
    implementationServicesPhase2: { quantity: number; rate: number };
    training: { quantity: number; rate: number };
    annualMaintenance: { quantity: number; rate: number };
  };
  cogs: {
    externalUsersPhase1: { quantity: number; rate: number };
    externalUsersPhase2: { quantity: number; rate: number };
    cloudInfrastructure: { quantity: number; rate: number };
    implementationTools: number;
    existingStaffPhase1: number;
    frontEndDeveloper: number;
    mobileDeveloper: number;
    benefitsRate: number;
    equipmentTools: number;
  };
  opex: {
    salesMarketing: number;
    generalAdmin: number;
    researchDev: number;
  };
}

const PLAnalysis = () => {
  const [plData, setPlData] = useState<PLData>({
    revenue: {
      internalLicensesPhase1: { quantity: 100, rate: 400 },
      externalLicensesPhase2: { quantity: 15100, rate: 210 },
      implementationServicesPhase1: { quantity: 220, rate: 3000 },
      implementationServicesPhase2: { quantity: 220, rate: 5000 },
      training: { quantity: 2, rate: 10000 },
      annualMaintenance: { quantity: 12, rate: 10000 }
    },
    cogs: {
      externalUsersPhase1: { quantity: 100, rate: 210 },
      externalUsersPhase2: { quantity: 15100, rate: 55 },
      cloudInfrastructure: { quantity: 12, rate: 2500 },
      implementationTools: 5000,
      existingStaffPhase1: 360000,
      frontEndDeveloper: 100000,
      mobileDeveloper: 100000,
      benefitsRate: 0.30,
      equipmentTools: 20000
    },
    opex: {
      salesMarketing: 10000,
      generalAdmin: 10000,
      researchDev: 10000
    }
  });

  const [calculations, setCalculations] = useState<any>({});

  const calculatePL = useCallback(() => {
    const { revenue, cogs, opex } = plData;

    // Revenue Calculations
    const revenuePhase1 = {
      internalLicenses: revenue.internalLicensesPhase1.quantity * revenue.internalLicensesPhase1.rate,
      implementationServices: revenue.implementationServicesPhase1.quantity * revenue.implementationServicesPhase1.rate,
      training: revenue.training.quantity * revenue.training.rate / 2, // Split over 2 phases
      annualMaintenance: revenue.annualMaintenance.quantity * revenue.annualMaintenance.rate
    };

    const revenuePhase2 = {
      externalLicenses: revenue.externalLicensesPhase2.quantity * revenue.externalLicensesPhase2.rate,
      implementationServices: revenue.implementationServicesPhase2.quantity * revenue.implementationServicesPhase2.rate,
      training: revenue.training.quantity * revenue.training.rate / 2, // Split over 2 phases
      annualMaintenance: revenue.annualMaintenance.quantity * revenue.annualMaintenance.rate
    };

    const totalRevenuePhase1 = Object.values(revenuePhase1).reduce((sum, val) => sum + val, 0);
    const totalRevenuePhase2 = Object.values(revenuePhase2).reduce((sum, val) => sum + val, 0);
    const totalRevenue = totalRevenuePhase1 + totalRevenuePhase2;

    // COGS Calculations
    const cogsPhase1 = {
      externalUsers: cogs.externalUsersPhase1.quantity * cogs.externalUsersPhase1.rate,
      cloudInfrastructure: cogs.cloudInfrastructure.quantity * cogs.cloudInfrastructure.rate,
      implementationTools: cogs.implementationTools,
      existingStaff: cogs.existingStaffPhase1,
      newHires: 0,
      benefits: 0,
      equipment: 0
    };

    const cogsPhase2 = {
      externalUsers: cogs.externalUsersPhase2.quantity * cogs.externalUsersPhase2.rate,
      cloudInfrastructure: cogs.cloudInfrastructure.quantity * cogs.cloudInfrastructure.rate,
      implementationTools: cogs.implementationTools,
      existingStaff: cogs.existingStaffPhase1,
      newHires: cogs.frontEndDeveloper + cogs.mobileDeveloper,
      benefits: (cogs.frontEndDeveloper + cogs.mobileDeveloper) * cogs.benefitsRate,
      equipment: cogs.equipmentTools
    };

    const totalCogsPhase1 = Object.values(cogsPhase1).reduce((sum, val) => sum + val, 0);
    const totalCogsPhase2 = Object.values(cogsPhase2).reduce((sum, val) => sum + val, 0);
    const totalCogs = totalCogsPhase1 + totalCogsPhase2;

    // Gross Profit
    const grossProfitPhase1 = totalRevenuePhase1 - totalCogsPhase1;
    const grossProfitPhase2 = totalRevenuePhase2 - totalCogsPhase2;
    const totalGrossProfit = grossProfitPhase1 + grossProfitPhase2;

    const grossMarginPhase1 = totalRevenuePhase1 > 0 ? (grossProfitPhase1 / totalRevenuePhase1) * 100 : 0;
    const grossMarginPhase2 = totalRevenuePhase2 > 0 ? (grossProfitPhase2 / totalRevenuePhase2) * 100 : 0;
    const totalGrossMargin = totalRevenue > 0 ? (totalGrossProfit / totalRevenue) * 100 : 0;

    // Operating Expenses
    const totalOpexPhase1 = opex.salesMarketing + opex.generalAdmin + opex.researchDev;
    const totalOpexPhase2 = opex.salesMarketing + opex.generalAdmin + opex.researchDev;
    const totalOpex = totalOpexPhase1 + totalOpexPhase2;

    // Net Operating Income
    const netIncomePhase1 = grossProfitPhase1 - totalOpexPhase1;
    const netIncomePhase2 = grossProfitPhase2 - totalOpexPhase2;
    const totalNetIncome = netIncomePhase1 + netIncomePhase2;

    const netMarginPhase1 = totalRevenuePhase1 > 0 ? (netIncomePhase1 / totalRevenuePhase1) * 100 : 0;
    const netMarginPhase2 = totalRevenuePhase2 > 0 ? (netIncomePhase2 / totalRevenuePhase2) * 100 : 0;
    const totalNetMargin = totalRevenue > 0 ? (totalNetIncome / totalRevenue) * 100 : 0;

    setCalculations({
      revenue: {
        phase1: revenuePhase1,
        phase2: revenuePhase2,
        totalPhase1: totalRevenuePhase1,
        totalPhase2: totalRevenuePhase2,
        total: totalRevenue
      },
      cogs: {
        phase1: cogsPhase1,
        phase2: cogsPhase2,
        totalPhase1: totalCogsPhase1,
        totalPhase2: totalCogsPhase2,
        total: totalCogs
      },
      grossProfit: {
        phase1: grossProfitPhase1,
        phase2: grossProfitPhase2,
        total: totalGrossProfit
      },
      grossMargin: {
        phase1: grossMarginPhase1,
        phase2: grossMarginPhase2,
        total: totalGrossMargin
      },
      opex: {
        phase1: totalOpexPhase1,
        phase2: totalOpexPhase2,
        total: totalOpex
      },
      netIncome: {
        phase1: netIncomePhase1,
        phase2: netIncomePhase2,
        total: totalNetIncome
      },
      netMargin: {
        phase1: netMarginPhase1,
        phase2: netMarginPhase2,
        total: totalNetMargin
      }
    });
  }, [plData]);

  useEffect(() => {
    calculatePL();
  }, [calculatePL]);

  const updateRevenue = (field: string, subfield: string, value: number) => {
    setPlData(prev => ({
      ...prev,
      revenue: {
        ...prev.revenue,
        [field]: {
          ...prev.revenue[field as keyof typeof prev.revenue],
          [subfield]: value
        }
      }
    }));
  };

  const updateCogs = (field: string, value: number | { quantity?: number; rate?: number }) => {
    setPlData(prev => ({
      ...prev,
      cogs: {
        ...prev.cogs,
        [field]: typeof value === 'object' ? { ...prev.cogs[field as keyof typeof prev.cogs], ...value } : value
      }
    }));
  };

  const updateOpex = (field: string, value: number) => {
    setPlData(prev => ({
      ...prev,
      opex: {
        ...prev.opex,
        [field]: value
      }
    }));
  };

  const exportPLToExcel = () => {
    const workbook = XLSX.utils.book_new();

    // Main P&L Sheet
    const plSheetData = [
      ['2 Year P&L Analysis - Fiber of the Future'],
      ['Generated:', new Date().toLocaleDateString()],
      [''],
      ['', 'Phase I', 'Phase II', 'Total'],
      [''],
      ['REVENUE'],
      ['Internal User Licenses - Phase I', calculations.revenue?.phase1?.internalLicenses || 0, 0, calculations.revenue?.phase1?.internalLicenses || 0],
      ['External User Licenses - Phase II', 0, calculations.revenue?.phase2?.externalLicenses || 0, calculations.revenue?.phase2?.externalLicenses || 0],
      ['Implementation Services Phase I', calculations.revenue?.phase1?.implementationServices || 0, 0, calculations.revenue?.phase1?.implementationServices || 0],
      ['Implementation Services Phase II', 0, calculations.revenue?.phase2?.implementationServices || 0, calculations.revenue?.phase2?.implementationServices || 0],
      ['Training (2 sessions)', calculations.revenue?.phase1?.training || 0, calculations.revenue?.phase2?.training || 0, (calculations.revenue?.phase1?.training || 0) + (calculations.revenue?.phase2?.training || 0)],
      ['Annual Maintenance', calculations.revenue?.phase1?.annualMaintenance || 0, calculations.revenue?.phase2?.annualMaintenance || 0, (calculations.revenue?.phase1?.annualMaintenance || 0) + (calculations.revenue?.phase2?.annualMaintenance || 0)],
      ['Total Revenue:', calculations.revenue?.totalPhase1 || 0, calculations.revenue?.totalPhase2 || 0, calculations.revenue?.total || 0],
      [''],
      ['COST OF GOODS SOLD (COGS)'],
      ['External Users Phase I', calculations.cogs?.phase1?.externalUsers || 0, 0, calculations.cogs?.phase1?.externalUsers || 0],
      ['External Users Phase II', 0, calculations.cogs?.phase2?.externalUsers || 0, calculations.cogs?.phase2?.externalUsers || 0],
      ['Cloud Infrastructure (AWS)', calculations.cogs?.phase1?.cloudInfrastructure || 0, calculations.cogs?.phase2?.cloudInfrastructure || 0, (calculations.cogs?.phase1?.cloudInfrastructure || 0) + (calculations.cogs?.phase2?.cloudInfrastructure || 0)],
      ['Implementation Tools', calculations.cogs?.phase1?.implementationTools || 0, calculations.cogs?.phase2?.implementationTools || 0, (calculations.cogs?.phase1?.implementationTools || 0) + (calculations.cogs?.phase2?.implementationTools || 0)],
      ['Existing Staff (Phase I)', calculations.cogs?.phase1?.existingStaff || 0, calculations.cogs?.phase2?.existingStaff || 0, (calculations.cogs?.phase1?.existingStaff || 0) + (calculations.cogs?.phase2?.existingStaff || 0)],
      ['New Hires (Phase II)', calculations.cogs?.phase1?.newHires || 0, calculations.cogs?.phase2?.newHires || 0, (calculations.cogs?.phase1?.newHires || 0) + (calculations.cogs?.phase2?.newHires || 0)],
      ['Benefits (30%)', calculations.cogs?.phase1?.benefits || 0, calculations.cogs?.phase2?.benefits || 0, (calculations.cogs?.phase1?.benefits || 0) + (calculations.cogs?.phase2?.benefits || 0)],
      ['Equipment & Tools', calculations.cogs?.phase1?.equipment || 0, calculations.cogs?.phase2?.equipment || 0, (calculations.cogs?.phase1?.equipment || 0) + (calculations.cogs?.phase2?.equipment || 0)],
      ['Total COGS:', calculations.cogs?.totalPhase1 || 0, calculations.cogs?.totalPhase2 || 0, calculations.cogs?.total || 0],
      [''],
      ['GROSS PROFIT:', calculations.grossProfit?.phase1 || 0, calculations.grossProfit?.phase2 || 0, calculations.grossProfit?.total || 0],
      [`Gross Margin:`, `${(calculations.grossMargin?.phase1 || 0).toFixed(1)}%`, `${(calculations.grossMargin?.phase2 || 0).toFixed(1)}%`, `${(calculations.grossMargin?.total || 0).toFixed(1)}%`],
      [''],
      ['OPERATING EXPENSES'],
      ['Sales & Marketing', calculations.opex?.phase1 / 3 || 0, calculations.opex?.phase2 / 3 || 0, (calculations.opex?.phase1 / 3 || 0) + (calculations.opex?.phase2 / 3 || 0)],
      ['General & Administrative', calculations.opex?.phase1 / 3 || 0, calculations.opex?.phase2 / 3 || 0, (calculations.opex?.phase1 / 3 || 0) + (calculations.opex?.phase2 / 3 || 0)],
      ['Research & Development', calculations.opex?.phase1 / 3 || 0, calculations.opex?.phase2 / 3 || 0, (calculations.opex?.phase1 / 3 || 0) + (calculations.opex?.phase2 / 3 || 0)],
      ['Total Operating Expenses:', calculations.opex?.phase1 || 0, calculations.opex?.phase2 || 0, calculations.opex?.total || 0],
      [''],
      ['NET OPERATING INCOME:', calculations.netIncome?.phase1 || 0, calculations.netIncome?.phase2 || 0, calculations.netIncome?.total || 0],
      [`Net Margin:`, `${(calculations.netMargin?.phase1 || 0).toFixed(1)}%`, `${(calculations.netMargin?.phase2 || 0).toFixed(1)}%`, `${(calculations.netMargin?.total || 0).toFixed(1)}%`]
    ];

    const plSheet = XLSX.utils.aoa_to_sheet(plSheetData);
    plSheet['!cols'] = [{ width: 35 }, { width: 15 }, { width: 15 }, { width: 15 }];
    XLSX.utils.book_append_sheet(workbook, plSheet, 'P&L Analysis');

    XLSX.writeFile(workbook, `PL-Analysis-${new Date().toISOString().split('T')[0]}.xlsx`);
  };

  const InputGroup = ({ label, value, onChange, prefix = '' }: {
    label: string;
    value: number;
    onChange: (value: number) => void;
    prefix?: string;
  }) => (
    <div className="flex flex-col">
      <label className="text-xs font-medium text-gray-600 mb-1">{label}</label>
      <div className="relative">
        {prefix && <span className="absolute left-3 top-2 text-gray-500">{prefix}</span>}
        <input
          type="number"
          value={value}
          onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
          className={`w-full px-3 py-2 border border-gray-200 rounded focus:border-blue-500 focus:outline-none text-sm ${prefix ? 'pl-8' : ''}`}
        />
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-blue-50 to-purple-50 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent mb-2">
            📊 2-Year P&L Analysis
          </h1>
          <p className="text-gray-600">Fiber of the Future - Financial Model</p>
          <div className="flex justify-center mt-4">
            <button
              onClick={exportPLToExcel}
              className="px-6 py-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-lg hover:shadow-lg transition-all"
            >
              📊 Export P&L to Excel
            </button>
          </div>
        </div>

        {/* Revenue Inputs */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">💰 Revenue Assumptions</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="space-y-3">
              <h4 className="font-medium text-gray-700">Internal Licenses Phase I</h4>
              <InputGroup
                label="Quantity"
                value={plData.revenue.internalLicensesPhase1.quantity}
                onChange={(value) => updateRevenue('internalLicensesPhase1', 'quantity', value)}
              />
              <InputGroup
                label="Rate per License"
                value={plData.revenue.internalLicensesPhase1.rate}
                onChange={(value) => updateRevenue('internalLicensesPhase1', 'rate', value)}
                prefix="$"
              />
            </div>

            <div className="space-y-3">
              <h4 className="font-medium text-gray-700">External Licenses Phase II</h4>
              <InputGroup
                label="Quantity"
                value={plData.revenue.externalLicensesPhase2.quantity}
                onChange={(value) => updateRevenue('externalLicensesPhase2', 'quantity', value)}
              />
              <InputGroup
                label="Rate per License"
                value={plData.revenue.externalLicensesPhase2.rate}
                onChange={(value) => updateRevenue('externalLicensesPhase2', 'rate', value)}
                prefix="$"
              />
            </div>

            <div className="space-y-3">
              <h4 className="font-medium text-gray-700">Implementation Services Phase I</h4>
              <InputGroup
                label="Hours"
                value={plData.revenue.implementationServicesPhase1.quantity}
                onChange={(value) => updateRevenue('implementationServicesPhase1', 'quantity', value)}
              />
              <InputGroup
                label="Rate per Hour"
                value={plData.revenue.implementationServicesPhase1.rate}
                onChange={(value) => updateRevenue('implementationServicesPhase1', 'rate', value)}
                prefix="$"
              />
            </div>

            <div className="space-y-3">
              <h4 className="font-medium text-gray-700">Implementation Services Phase II</h4>
              <InputGroup
                label="Hours"
                value={plData.revenue.implementationServicesPhase2.quantity}
                onChange={(value) => updateRevenue('implementationServicesPhase2', 'quantity', value)}
              />
              <InputGroup
                label="Rate per Hour"
                value={plData.revenue.implementationServicesPhase2.rate}
                onChange={(value) => updateRevenue('implementationServicesPhase2', 'rate', value)}
                prefix="$"
              />
            </div>

            <div className="space-y-3">
              <h4 className="font-medium text-gray-700">Training Sessions</h4>
              <InputGroup
                label="Number of Sessions"
                value={plData.revenue.training.quantity}
                onChange={(value) => updateRevenue('training', 'quantity', value)}
              />
              <InputGroup
                label="Rate per Session"
                value={plData.revenue.training.rate}
                onChange={(value) => updateRevenue('training', 'rate', value)}
                prefix="$"
              />
            </div>

            <div className="space-y-3">
              <h4 className="font-medium text-gray-700">Annual Maintenance</h4>
              <InputGroup
                label="Months"
                value={plData.revenue.annualMaintenance.quantity}
                onChange={(value) => updateRevenue('annualMaintenance', 'quantity', value)}
              />
              <InputGroup
                label="Rate per Month"
                value={plData.revenue.annualMaintenance.rate}
                onChange={(value) => updateRevenue('annualMaintenance', 'rate', value)}
                prefix="$"
              />
            </div>
          </div>
        </div>

        {/* COGS Inputs */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">📦 Cost of Goods Sold (COGS)</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <InputGroup
              label="Existing Staff Phase I"
              value={plData.cogs.existingStaffPhase1}
              onChange={(value) => updateCogs('existingStaffPhase1', value)}
              prefix="$"
            />
            <InputGroup
              label="Front-End Developer"
              value={plData.cogs.frontEndDeveloper}
              onChange={(value) => updateCogs('frontEndDeveloper', value)}
              prefix="$"
            />
            <InputGroup
              label="Mobile Developer"
              value={plData.cogs.mobileDeveloper}
              onChange={(value) => updateCogs('mobileDeveloper', value)}
              prefix="$"
            />
            <InputGroup
              label="Benefits Rate (%)"
              value={plData.cogs.benefitsRate * 100}
              onChange={(value) => updateCogs('benefitsRate', value / 100)}
            />
            <InputGroup
              label="Cloud Infrastructure (Monthly)"
              value={plData.cogs.cloudInfrastructure.rate}
              onChange={(value) => updateCogs('cloudInfrastructure', { rate: value })}
              prefix="$"
            />
            <InputGroup
              label="Implementation Tools"
              value={plData.cogs.implementationTools}
              onChange={(value) => updateCogs('implementationTools', value)}
              prefix="$"
            />
            <InputGroup
              label="Equipment & Tools"
              value={plData.cogs.equipmentTools}
              onChange={(value) => updateCogs('equipmentTools', value)}
              prefix="$"
            />
          </div>
        </div>

        {/* Operating Expenses */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">🏢 Operating Expenses</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <InputGroup
              label="Sales & Marketing"
              value={plData.opex.salesMarketing}
              onChange={(value) => updateOpex('salesMarketing', value)}
              prefix="$"
            />
            <InputGroup
              label="General & Administrative"
              value={plData.opex.generalAdmin}
              onChange={(value) => updateOpex('generalAdmin', value)}
              prefix="$"
            />
            <InputGroup
              label="Research & Development"
              value={plData.opex.researchDev}
              onChange={(value) => updateOpex('researchDev', value)}
              prefix="$"
            />
          </div>
        </div>

        {/* P&L Summary */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">📈 P&L Summary</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gradient-to-r from-green-500 to-blue-500 text-white">
                  <th className="p-3 text-left">Item</th>
                  <th className="p-3 text-right">Phase I</th>
                  <th className="p-3 text-right">Phase II</th>
                  <th className="p-3 text-right">Total</th>
                </tr>
              </thead>
              <tbody>
                <tr className="bg-green-50">
                  <td className="p-3 font-semibold">Total Revenue</td>
                  <td className="p-3 text-right font-medium">${calculations.revenue?.totalPhase1?.toLocaleString() || 0}</td>
                  <td className="p-3 text-right font-medium">${calculations.revenue?.totalPhase2?.toLocaleString() || 0}</td>
                  <td className="p-3 text-right font-bold">${calculations.revenue?.total?.toLocaleString() || 0}</td>
                </tr>
                <tr className="bg-red-50">
                  <td className="p-3 font-semibold">Total COGS</td>
                  <td className="p-3 text-right font-medium">${calculations.cogs?.totalPhase1?.toLocaleString() || 0}</td>
                  <td className="p-3 text-right font-medium">${calculations.cogs?.totalPhase2?.toLocaleString() || 0}</td>
                  <td className="p-3 text-right font-bold">${calculations.cogs?.total?.toLocaleString() || 0}</td>
                </tr>
                <tr className="bg-blue-50">
                  <td className="p-3 font-semibold">Gross Profit</td>
                  <td className="p-3 text-right font-medium">${calculations.grossProfit?.phase1?.toLocaleString() || 0}</td>
                  <td className="p-3 text-right font-medium">${calculations.grossProfit?.phase2?.toLocaleString() || 0}</td>
                  <td className="p-3 text-right font-bold">${calculations.grossProfit?.total?.toLocaleString() || 0}</td>
                </tr>
                <tr className="bg-blue-100">
                  <td className="p-3 font-semibold">Gross Margin</td>
                  <td className="p-3 text-right font-medium">{calculations.grossMargin?.phase1?.toFixed(1) || 0}%</td>
                  <td className="p-3 text-right font-medium">{calculations.grossMargin?.phase2?.toFixed(1) || 0}%</td>
                  <td className="p-3 text-right font-bold">{calculations.grossMargin?.total?.toFixed(1) || 0}%</td>
                </tr>
                <tr className="bg-yellow-50">
                  <td className="p-3 font-semibold">Operating Expenses</td>
                  <td className="p-3 text-right font-medium">${calculations.opex?.phase1?.toLocaleString() || 0}</td>
                  <td className="p-3 text-right font-medium">${calculations.opex?.phase2?.toLocaleString() || 0}</td>
                  <td className="p-3 text-right font-bold">${calculations.opex?.total?.toLocaleString() || 0}</td>
                </tr>
                <tr className="bg-gradient-to-r from-purple-500 to-pink-500 text-white">
                  <td className="p-3 font-bold">Net Operating Income</td>
                  <td className="p-3 text-right font-bold">${calculations.netIncome?.phase1?.toLocaleString() || 0}</td>
                  <td className="p-3 text-right font-bold">${calculations.netIncome?.phase2?.toLocaleString() || 0}</td>
                  <td className="p-3 text-right font-bold">${calculations.netIncome?.total?.toLocaleString() || 0}</td>
                </tr>
                <tr className="bg-gradient-to-r from-purple-600 to-pink-600 text-white">
                  <td className="p-3 font-bold">Net Margin</td>
                  <td className="p-3 text-right font-bold">{calculations.netMargin?.phase1?.toFixed(1) || 0}%</td>
                  <td className="p-3 text-right font-bold">{calculations.netMargin?.phase2?.toFixed(1) || 0}%</td>
                  <td className="p-3 text-right font-bold">{calculations.netMargin?.total?.toFixed(1) || 0}%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Key Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          <div className="bg-gradient-to-r from-green-500 to-emerald-500 text-white p-6 rounded-xl shadow-lg">
            <div className="text-3xl font-bold">${calculations.revenue?.total?.toLocaleString() || 0}</div>
            <div className="text-sm opacity-90">Total Revenue</div>
            <div className="text-xs opacity-75 mt-1">2-Year Period</div>
          </div>

          <div className="bg-gradient-to-r from-blue-500 to-cyan-500 text-white p-6 rounded-xl shadow-lg">
            <div className="text-3xl font-bold">${calculations.grossProfit?.total?.toLocaleString() || 0}</div>
            <div className="text-sm opacity-90">Gross Profit</div>
            <div className="text-xs opacity-75 mt-1">{calculations.grossMargin?.total?.toFixed(1) || 0}% Margin</div>
          </div>

          <div className="bg-gradient-to-r from-purple-500 to-pink-500 text-white p-6 rounded-xl shadow-lg">
            <div className="text-3xl font-bold">${calculations.netIncome?.total?.toLocaleString() || 0}</div>
            <div className="text-sm opacity-90">Net Income</div>
            <div className="text-xs opacity-75 mt-1">{calculations.netMargin?.total?.toFixed(1) || 0}% Margin</div>
          </div>

          <div className="bg-gradient-to-r from-orange-500 to-red-500 text-white p-6 rounded-xl shadow-lg">
            <div className="text-3xl font-bold">${calculations.cogs?.total?.toLocaleString() || 0}</div>
            <div className="text-sm opacity-90">Total COGS</div>
            <div className="text-xs opacity-75 mt-1">2-Year Period</div>
          </div>
        </div>

        {/* Revenue Breakdown Chart */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">📊 Revenue Breakdown by Phase</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-gray-700 mb-3">Phase I Revenue</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Internal Licenses:</span>
                  <span className="font-medium">${calculations.revenue?.phase1?.internalLicenses?.toLocaleString() || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Implementation Services:</span>
                  <span className="font-medium">${calculations.revenue?.phase1?.implementationServices?.toLocaleString() || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Training:</span>
                  <span className="font-medium">${calculations.revenue?.phase1?.training?.toLocaleString() || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Maintenance:</span>
                  <span className="font-medium">${calculations.revenue?.phase1?.annualMaintenance?.toLocaleString() || 0}</span>
                </div>
                <div className="border-t pt-2 flex justify-between font-bold">
                  <span>Phase I Total:</span>
                  <span>${calculations.revenue?.totalPhase1?.toLocaleString() || 0}</span>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-medium text-gray-700 mb-3">Phase II Revenue</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">External Licenses:</span>
                  <span className="font-medium">${calculations.revenue?.phase2?.externalLicenses?.toLocaleString() || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Implementation Services:</span>
                  <span className="font-medium">${calculations.revenue?.phase2?.implementationServices?.toLocaleString() || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Training:</span>
                  <span className="font-medium">${calculations.revenue?.phase2?.training?.toLocaleString() || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Maintenance:</span>
                  <span className="font-medium">${calculations.revenue?.phase2?.annualMaintenance?.toLocaleString() || 0}</span>
                </div>
                <div className="border-t pt-2 flex justify-between font-bold">
                  <span>Phase II Total:</span>
                  <span>${calculations.revenue?.totalPhase2?.toLocaleString() || 0}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Financial Ratios */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">📈 Financial Ratios & Analysis</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-700 mb-3">Profitability Ratios</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Gross Margin:</span>
                  <span className="font-medium">{calculations.grossMargin?.total?.toFixed(1) || 0}%</span>
                </div>
                <div className="flex justify-between">
                  <span>Net Margin:</span>
                  <span className="font-medium">{calculations.netMargin?.total?.toFixed(1) || 0}%</span>
                </div>
                <div className="flex justify-between">
                  <span>COGS as % of Revenue:</span>
                  <span className="font-medium">{calculations.revenue?.total > 0 ? ((calculations.cogs?.total / calculations.revenue?.total) * 100).toFixed(1) : 0}%</span>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-700 mb-3">Growth Metrics</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Phase I to II Revenue Growth:</span>
                  <span className="font-medium">
                    {calculations.revenue?.totalPhase1 > 0
                      ? `${(((calculations.revenue?.totalPhase2 - calculations.revenue?.totalPhase1) / calculations.revenue?.totalPhase1) * 100).toFixed(1)}%`
                      : 'N/A'
                    }
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Monthly Average Revenue:</span>
                  <span className="font-medium">${((calculations.revenue?.total || 0) / 24).toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>Break-even Point:</span>
                  <span className="font-medium">
                    {calculations.netIncome?.phase1 > 0 ? 'Phase I' : calculations.netIncome?.phase2 > 0 ? 'Phase II' : 'Not Achieved'}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-700 mb-3">Cost Structure</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Staffing as % of Revenue:</span>
                  <span className="font-medium">
                    {calculations.revenue?.total > 0
                      ? (((calculations.cogs?.phase1?.existingStaff + calculations.cogs?.phase2?.existingStaff + calculations.cogs?.phase2?.newHires + calculations.cogs?.phase2?.benefits) / calculations.revenue?.total) * 100).toFixed(1)
                      : 0}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Infrastructure Costs:</span>
                  <span className="font-medium">${((calculations.cogs?.phase1?.cloudInfrastructure + calculations.cogs?.phase2?.cloudInfrastructure) || 0).toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>OpEx as % of Revenue:</span>
                  <span className="font-medium">
                    {calculations.revenue?.total > 0 ? ((calculations.opex?.total / calculations.revenue?.total) * 100).toFixed(1) : 0}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PLAnalysis;