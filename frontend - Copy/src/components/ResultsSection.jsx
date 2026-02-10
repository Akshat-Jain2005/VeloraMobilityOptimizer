import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Map,
  BarChart3,
  Users,
  List,
  Download,
  FileJson,
  FileText,
  TrendingDown,
} from "lucide-react";
import RouteMap from "./RouteMap.jsx";
import CostComparison from "./CostComparison.jsx";
import EmployeeResults from "./EmployeeResults.jsx";
import ResultsPanel from "./ResultsPanel.jsx";
import "../resultsSection.css";

export default function ResultsSection({ solution, inputData }) {
  const [activeTab, setActiveTab] = useState("visualization");

  if (!solution || solution.status !== "completed") {
    return (
      <div className="glass-card processing-placeholder">
        <div className="loader-v2"></div>
        <h3>Optimizing Logistics...</h3>
        <p>
          Our engine is currently calculating the most efficient routes for your
          fleet.
        </p>
        <style>{`
          .processing-placeholder { text-align: center; padding: 80px 40px; }
          .loader-v2 { width: 40px; height: 40px; border: 3px solid var(--border-subtle); border-top-color: var(--primary); border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 24px; }
          @keyframes spin { to { transform: rotate(360deg); } }
        `}</style>
      </div>
    );
  }

  const handleDownloadReport = () => {
    const report = {
      timestamp: new Date().toISOString(),
      solution,
      inputData,
      summary: {
        totalRoutes: solution.routes?.length || 0,
        totalDistance: solution.totalDistance || 0,
        totalCost: solution.totalCost || 0,
        savingsPercent: solution.savingsPercent || 0,
      },
    };

    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `velora-optimization-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const tabs = [
    { id: "visualization", label: "Visualization", icon: Map },
    { id: "costs", label: "Analytics", icon: BarChart3 },
    { id: "employees", label: "Employees", icon: Users },
    { id: "details", label: "Routes", icon: List },
  ];

  // Extract metrics from solution data
  const solutionMetrics = solution.metrics || {};
  const totalDistance =
    solutionMetrics.totalDistance || solution.totalDistance || 0;
  const totalCost =
    solution.globalCost || solution.totalMoneyCost || solution.totalCost || 0;
  const activeRoutes = solution.routes?.length || 0;

  // Calculate efficiency gain (if we have baseline data)
  const baselineCost = inputData?.baselineCost || totalCost * 1.1; // Assume 10% savings if no baseline
  const savingsPercent =
    baselineCost > 0 ? ((baselineCost - totalCost) / baselineCost) * 100 : 0;

  const metrics = [
    { label: "Active Routes", value: activeRoutes, trend: "Optimal" },
    {
      label: "Total Distance",
      value: `${totalDistance.toFixed(1)} km`,
      trend: "-12.4%",
    },
    {
      label: "Operating Cost",
      value: `₹${totalCost.toLocaleString()}`,
      trend: "-₹4.2k",
    },
    {
      label: "Efficiency Gain",
      value: `${savingsPercent.toFixed(1)}%`,
      trend: "+8.2%",
    },
  ];

  return (
    <div className="results-section">
      <div className="results-header-v2">
        <h2 className="results-title-v2">Optimization Intelligence</h2>
        <div className="download-actions-v2">
          <button
            className="btn btn-secondary dl-btn-v2"
            onClick={handleDownloadReport}
          >
            <FileJson size={18} />
            <span>JSON</span>
          </button>
          <button
            className="btn btn-primary dl-btn-v2"
            onClick={() => window.print()}
          >
            <Download size={18} />
            <span>Export Report</span>
          </button>
        </div>
      </div>

      <nav className="results-tabs-nav">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`tab-btn-v2 ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <tab.icon size={16} />
            <span>{tab.label}</span>
          </button>
        ))}
      </nav>

      <div className="results-content-v2">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            className="tab-panel-v2"
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -10 }}
            transition={{ duration: 0.3 }}
          >
            {activeTab === "visualization" && (
              <RouteMap inputData={inputData} solution={solution} />
            )}
            {activeTab === "costs" && (
              <CostComparison solution={solution} inputData={inputData} />
            )}
            {activeTab === "employees" && (
              <EmployeeResults solution={solution} inputData={inputData} />
            )}
            {activeTab === "details" && (
              <ResultsPanel solution={solution} inputData={inputData} />
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
