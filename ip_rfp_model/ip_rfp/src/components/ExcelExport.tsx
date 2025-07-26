import React, { useState } from 'react';
import * as XLSX from 'xlsx';

interface ExcelExportProps {
  rates: any;
  phases: any;
  additionalCosts: any;
  calculations: any;
  scenarios: any;
}

interface ExportOptions {
  includeRates: boolean;
  includePhaseDetails: boolean;
  includeCostBreakdown: boolean;
  includeAdditionalCosts: boolean;
  includeScenarios: boolean;
  includeSummaryCharts: boolean;
  includeExecutiveSummary: boolean;
  selectedScenarios: string[];
  customFileName: string;
  includeFormulas: boolean;
  addFormatting: boolean;
}

export default function ExcelExport({
  rates,
  phases,
  additionalCosts,
  calculations,
  scenarios
}: ExcelExportProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    includeRates: true,
    includePhaseDetails: true,
    includeCostBreakdown: true,
    includeAdditionalCosts: true,
    includeScenarios: false,
    includeSummaryCharts: true,
    includeExecutiveSummary: true,
    selectedScenarios: ['conservative', 'moderate', 'aggressive'],
    customFileName: `RFP-Cost-Model-${new Date().toISOString().split('T')[0]}`,
    includeFormulas: true,
    addFormatting: true
  });

  const updateOption = (key: keyof ExportOptions, value: any) => {
    setExportOptions(prev => ({ ...prev, [key]: value }));
  };

  const toggleScenario = (scenario: string) => {
    setExportOptions(prev => ({
      ...prev,
      selectedScenarios: prev.selectedScenarios.includes(scenario)
        ? prev.selectedScenarios.filter(s => s !== scenario)
        : [...prev.selectedScenarios, scenario]
    }));
  };

  const generateExcelData = () => {
    const workbook = XLSX.utils.book_new();

    // Executive Summary Sheet
    if (exportOptions.includeExecutiveSummary) {
      const summaryData = [
        ['RFP PROJECT COST MODEL - EXECUTIVE SUMMARY'],
        ['Generated:', new Date().toLocaleDateString()],
        [''],
        ['KEY METRICS'],
        ['Total Project Cost:', `$${calculations.totalCost?.toLocaleString() || 0}`],
        ['Total Project Hours:', calculations.totalHours?.toLocaleString() || 0],
        ['Project Duration:', `${calculations.totalDuration || 0} months`],
        ['Average Monthly Cost:', `$${Math.round(calculations.avgMonthly || 0).toLocaleString()}`],
        [''],
        ['COST BREAKDOWN'],
        ['Permanent Staff Cost:', `$${calculations.permStaffCost?.toLocaleString() || 0}`],
        ['Contractor Cost:', `$${calculations.contractorCost?.toLocaleString() || 0}`],
        ['Additional Costs:', `$${calculations.additionalTotal?.toLocaleString() || 0}`],
        [''],
        ['GRAND TOTAL:', `$${calculations.grandTotal?.toLocaleString() || 0}`]
      ];

      const summarySheet = XLSX.utils.aoa_to_sheet(summaryData);

      // Add formatting if enabled
      if (exportOptions.addFormatting) {
        summarySheet['!cols'] = [{ width: 25 }, { width: 20 }];
        // Style header
        if (summarySheet['A1']) {
          summarySheet['A1'].s = {
            font: { bold: true, size: 14 },
            alignment: { horizontal: 'center' }
          };
        }
      }

      XLSX.utils.book_append_sheet(workbook, summarySheet, 'Executive Summary');
    }

    // Team Rates Sheet
    if (exportOptions.includeRates) {
      const ratesData = [
        ['TEAM HOURLY RATES'],
        ['Role', 'Rate ($/hour)'],
        ['Manager', rates.manager],
        ['C#/JS Developer', rates.developer],
        ['Database Administrator', rates.dba],
        ['Junior DBA/Tester', rates.junior],
        ['Mobile Developer (Contractor)', rates.mobile]
      ];

      const ratesSheet = XLSX.utils.aoa_to_sheet(ratesData);
      if (exportOptions.addFormatting) {
        ratesSheet['!cols'] = [{ width: 25 }, { width: 15 }];
      }
      XLSX.utils.book_append_sheet(workbook, ratesSheet, 'Team Rates');
    }

    // Phase Details Sheet
    if (exportOptions.includePhaseDetails) {
      const phaseData = [
        ['PHASE UTILIZATION DETAILS'],
        ['Phase', 'Duration (months)', 'Manager (%)', 'Developer (%)', 'DBA (%)', 'Junior (%)', 'Mobile (%)'],
      ];

      ['phase1', 'phase2', 'phase3'].forEach((phaseName, index) => {
        const phase = phases[phaseName];
        phaseData.push([
          `Phase ${index + 1}`,
          phase.duration,
          phase.manager,
          phase.developer,
          phase.dba,
          phase.junior,
          phase.mobile
        ]);
      });

      const phaseSheet = XLSX.utils.aoa_to_sheet(phaseData);
      if (exportOptions.addFormatting) {
        phaseSheet['!cols'] = Array(7).fill({ width: 15 });
      }
      XLSX.utils.book_append_sheet(workbook, phaseSheet, 'Phase Details');
    }

    // Cost Breakdown Sheet
    if (exportOptions.includeCostBreakdown) {
      const breakdownData = [
        ['DETAILED COST BREAKDOWN'],
        ['Phase', 'Duration', 'Manager Cost', 'Developer Cost', 'DBA Cost', 'Junior Cost', 'Mobile Cost', 'Phase Total']
      ];

      calculations.phaseBreakdown?.forEach((phase: any) => {
        breakdownData.push([
          phase.name,
          `${phase.duration} months`,
          phase.costs.manager,
          phase.costs.developer,
          phase.costs.dba,
          phase.costs.junior,
          phase.costs.mobile,
          exportOptions.includeFormulas ?
            `=C${breakdownData.length + 1}+D${breakdownData.length + 1}+E${breakdownData.length + 1}+F${breakdownData.length + 1}+G${breakdownData.length + 1}+H${breakdownData.length + 1}` :
            phase.total
        ]);
      });

      // Add totals row
      const totalRow = ['TOTALS', `${calculations.totalDuration} months`];
      const costColumns = ['manager', 'developer', 'dba', 'junior', 'mobile'];
      costColumns.forEach(role => {
        const total = calculations.phaseBreakdown?.reduce((sum: number, phase: any) => sum + (phase.costs[role] || 0), 0);
        totalRow.push(total);
      });
      totalRow.push(exportOptions.includeFormulas ?
        `=SUM(H3:H${breakdownData.length})` :
        calculations.totalCost
      );
      breakdownData.push(totalRow);

      const breakdownSheet = XLSX.utils.aoa_to_sheet(breakdownData);
      if (exportOptions.addFormatting) {
        breakdownSheet['!cols'] = Array(8).fill({ width: 15 });
      }
      XLSX.utils.book_append_sheet(workbook, breakdownSheet, 'Cost Breakdown');
    }

    // Additional Costs Sheet
    if (exportOptions.includeAdditionalCosts && additionalCosts.length > 0) {
      const additionalData = [
        ['ADDITIONAL COSTS & REVENUE STREAMS'],
        ['Item', 'Amount', 'Frequency', 'Total (24 months)']
      ];

      additionalCosts.forEach((item: any) => {
        let totalAmount = 0;
        switch(item.frequency) {
          case 'monthly': totalAmount = item.amount * 24; break;
          case 'annually': totalAmount = item.amount * 2; break;
          default: totalAmount = item.amount; break;
        }
        additionalData.push([item.description, item.amount, item.frequency, totalAmount]);
      });

      // Add total row
      const additionalTotal = additionalCosts.reduce((sum: number, item: any) => {
        let itemTotal = 0;
        switch(item.frequency) {
          case 'monthly': itemTotal = item.amount * 24; break;
          case 'annually': itemTotal = item.amount * 2; break;
          default: itemTotal = item.amount; break;
        }
        return sum + itemTotal;
      }, 0);

      additionalData.push(['TOTAL ADDITIONAL COSTS', '', '', additionalTotal]);

      const additionalSheet = XLSX.utils.aoa_to_sheet(additionalData);
      if (exportOptions.addFormatting) {
        additionalSheet['!cols'] = [{ width: 30 }, { width: 15 }, { width: 15 }, { width: 20 }];
      }
      XLSX.utils.book_append_sheet(workbook, additionalSheet, 'Additional Costs');
    }

    // Scenario Comparison Sheet
    if (exportOptions.includeScenarios && exportOptions.selectedScenarios.length > 0) {
      const scenarioData = [
        ['SCENARIO COMPARISON'],
        ['Metric', ...exportOptions.selectedScenarios.map(s => s.charAt(0).toUpperCase() + s.slice(1))]
      ];

      // Calculate costs for each scenario
      exportOptions.selectedScenarios.forEach(scenarioName => {
        if (scenarios[scenarioName]) {
          let scenarioTotal = 0;
          const phaseNames = ['phase1', 'phase2', 'phase3'];

          phaseNames.forEach(phaseName => {
            const phase = { ...phases[phaseName] };
            // Apply scenario utilization
            Object.keys(scenarios[scenarioName][phaseName]).forEach(role => {
              phase[role] = scenarios[scenarioName][phaseName][role];
            });

            // Calculate phase cost
            Object.keys(rates).forEach(role => {
              const monthlyHours = 173 * (phase[role] / 100);
              const roleHours = monthlyHours * phase.duration;
              const roleCost = roleHours * rates[role];
              scenarioTotal += roleCost;
            });
          });

          // Add scenario data
          const scenarioIndex = exportOptions.selectedScenarios.indexOf(scenarioName);
          if (scenarioData[2]) {
            scenarioData[2][scenarioIndex + 1] = scenarioTotal;
          } else {
            const row = new Array(exportOptions.selectedScenarios.length + 1);
            row[0] = 'Total Cost';
            row[scenarioIndex + 1] = scenarioTotal;
            scenarioData.push(row);
          }
        }
      });

      if (scenarioData.length <= 2) {
        scenarioData.push(['Total Cost', ...exportOptions.selectedScenarios.map(() => 'N/A')]);
      }

      const scenarioSheet = XLSX.utils.aoa_to_sheet(scenarioData);
      if (exportOptions.addFormatting) {
        scenarioSheet['!cols'] = [{ width: 20 }, ...exportOptions.selectedScenarios.map(() => ({ width: 15 }))];
      }
      XLSX.utils.book_append_sheet(workbook, scenarioSheet, 'Scenario Comparison');
    }

    return workbook;
  };

  const exportToExcel = () => {
    try {
      const workbook = generateExcelData();
      XLSX.writeFile(workbook, `${exportOptions.customFileName}.xlsx`);
      setIsModalOpen(false);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed. Please try again.');
    }
  };

  return (
    <>
      <button
        onClick={() => setIsModalOpen(true)}
        className="px-6 py-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-lg hover:shadow-lg transition-all flex items-center gap-2"
      >
        📊 Export to Excel
      </button>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-800">Excel Export Options</h2>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ×
              </button>
            </div>

            <div className="space-y-6">
              {/* File Name */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  File Name
                </label>
                <input
                  type="text"
                  value={exportOptions.customFileName}
                  onChange={(e) => updateOption('customFileName', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                  placeholder="Enter file name (without .xlsx)"
                />
              </div>

              {/* Content Selection */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-3">Include in Export</h3>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { key: 'includeExecutiveSummary', label: 'Executive Summary' },
                    { key: 'includeRates', label: 'Team Hourly Rates' },
                    { key: 'includePhaseDetails', label: 'Phase Utilization Details' },
                    { key: 'includeCostBreakdown', label: 'Detailed Cost Breakdown' },
                    { key: 'includeAdditionalCosts', label: 'Additional Costs' },
                    { key: 'includeScenarios', label: 'Scenario Comparison' }
                  ].map(option => (
                    <label key={option.key} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={exportOptions[option.key as keyof ExportOptions] as boolean}
                        onChange={(e) => updateOption(option.key as keyof ExportOptions, e.target.checked)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700">{option.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Scenario Selection */}
              {exportOptions.includeScenarios && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-3">Select Scenarios</h3>
                  <div className="grid grid-cols-3 gap-3">
                    {['conservative', 'moderate', 'aggressive'].map(scenario => (
                      <label key={scenario} className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={exportOptions.selectedScenarios.includes(scenario)}
                          onChange={() => toggleScenario(scenario)}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-700 capitalize">{scenario}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {/* Advanced Options */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-3">Advanced Options</h3>
                <div className="space-y-2">
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={exportOptions.includeFormulas}
                      onChange={(e) => updateOption('includeFormulas', e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">Include Excel formulas (for dynamic calculations)</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={exportOptions.addFormatting}
                      onChange={(e) => updateOption('addFormatting', e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">Add formatting (column widths, styling)</span>
                  </label>
                </div>
              </div>

              {/* Export Preview */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-800 mb-2">Export Preview</h4>
                <div className="text-sm text-gray-600">
                  <p><strong>File:</strong> {exportOptions.customFileName}.xlsx</p>
                  <p><strong>Sheets:</strong> {
                    [
                      exportOptions.includeExecutiveSummary && 'Executive Summary',
                      exportOptions.includeRates && 'Team Rates',
                      exportOptions.includePhaseDetails && 'Phase Details',
                      exportOptions.includeCostBreakdown && 'Cost Breakdown',
                      exportOptions.includeAdditionalCosts && 'Additional Costs',
                      exportOptions.includeScenarios && 'Scenario Comparison'
                    ].filter(Boolean).join(', ')
                  }</p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end space-x-3 pt-4 border-t">
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={exportToExcel}
                  className="px-6 py-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-lg hover:shadow-lg transition-all"
                >
                  Export Excel File
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}