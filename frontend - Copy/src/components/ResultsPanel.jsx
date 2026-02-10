import React from "react";
import { motion } from "framer-motion";
import { List, Info, AlertTriangle, Cpu, Truck, UserCheck } from "lucide-react";
import RoutesTable from "./RoutesTable.jsx";

export default function ResultsPanel({ solution, inputData }) {
  if (!solution) return null;

  if (solution.status === "failed") {
    return (
      <div className="glass-card error-card">
        <AlertTriangle size={32} color="#ef4444" />
        <h3>System Interruption</h3>
        <p>The optimization engine encountered an error: {solution.error}</p>
      </div>
    );
  }

  const data = solution.data;
  if (!data) return null;

  return (
    <div className="results-panel-v2">
      <div className="glass-card summary-grid-v2">
        <div className="summary-header">
          <Cpu size={20} color="var(--primary)" />
          <h4>Engine Intelligence Summary</h4>
        </div>
        
        <div className="summary-stats-v2">
          {[
            { label: "Global Cost", value: data.summary.globalCost?.toFixed(2), icon: Info },
            { label: "Operational Cost", value: `₹${data.summary.totalMoneyCost?.toFixed(0)}`, icon: Truck },
            { label: "Distance", value: `${data.summary.totalDistance?.toFixed(1)} km`, icon: List },
            { label: "Efficiency", value: data.summary.unassignedCount === 0 ? "100%" : "Partial", icon: UserCheck }
          ].map((stat, idx) => (
            <div key={idx} className="stat-item-v2">
              <span className="stat-label">{stat.label}</span>
              <span className="stat-value">{stat.value}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="routes-table-container-v2">
        <div className="container-header">
          <Truck size={20} color="var(--primary)" />
          <h3>Vehicle Dispatch Manifest</h3>
        </div>
        <RoutesTable routes={data.routes} inputData={inputData} />
      </div>

      {data.unassignedRequests?.length > 0 && (
        <div className="glass-card warning-card">
          <div className="warning-header">
            <AlertTriangle size={20} color="#fbbf24" />
            <h3>Unassigned Logistics Targets</h3>
          </div>
          <p>The following requests could not be optimized within current constraints:</p>
          <div className="unassigned-list">
            {data.unassignedRequests.map((req, index) => (
              <span key={index} className="unassigned-chip">Target {req.employeeId || index}</span>
            ))}
          </div>
        </div>
      )}

      <style>{`
        .results-panel-v2 { display: flex; flex-direction: column; gap: 24px; }
        .summary-grid-v2 { padding: 24px; border-radius: var(--radius-lg); }
        .summary-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
        .summary-header h4 { font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-dim); }
        .summary-stats-v2 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px; }
        .stat-item-v2 { display: flex; flex-direction: column; gap: 4px; }
        .stat-label { font-size: 0.7rem; font-weight: 700; color: var(--text-dim); text-transform: uppercase; }
        .stat-value { font-family: var(--font-display); font-size: 1.2rem; font-weight: 700; color: var(--text-bright); }
        
        .routes-table-container-v2 { margin-top: 12px; }
        .container-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; padding-left: 8px; }
        .container-header h3 { font-size: 1.1rem; }
        
        .warning-card { border-color: rgba(251, 191, 36, 0.2); background: rgba(251, 191, 36, 0.05); }
        .warning-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
        .unassigned-list { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
        .unassigned-chip { padding: 4px 12px; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 100px; font-size: 0.75rem; color: #f87171; }
        
        @media (max-width: 768px) {
          .summary-stats-v2 { grid-template-columns: repeat(2, 1fr); }
        }
      `}</style>
    </div>
  );
}
