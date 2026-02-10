import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  User,
  MapPin,
  Clock,
  Star,
  Users,
  CheckCircle,
  AlertTriangle,
  Truck,
} from "lucide-react";

export default function EmployeeResults({ solution, inputData, onEmployeeHover }) {
  if (!solution || solution.status !== "completed") return null;

  const data = solution.data;
  const routes = data.routes || [];
  const employeeTrips = {};

  // Status icon component with instant tooltip
  const StatusIcon = ({ isOnTime }) => {
    const [showTooltip, setShowTooltip] = useState(false);
    const tooltipText = isOnTime
      ? "✅ On-time (within window)"
      : "⚠️ Late/early (outside window)";

    return (
      <div
        className="status-icon-wrapper"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        {isOnTime ? (
          <CheckCircle size={18} color="var(--accent)" />
        ) : (
          <AlertTriangle size={18} color="#fbbf24" />
        )}
        {showTooltip && <div className="custom-tooltip">{tooltipText}</div>}
      </div>
    );
  };

  routes.forEach((route) => {
    (route.stops || []).forEach((stop) => {
      const empId = stop.employeeId;
      if (!empId) return;

      if (!employeeTrips[empId]) {
        employeeTrips[empId] = {
          employeeId: empId,
          vehicleId: route.vehicleIdStr || route.vehicleId,
          pickupTime: null,
          dropoffTime: null,
          pickupLat: null,
          pickupLon: null,
          dropoffLat: null,
          dropoffLon: null,
          pickupWaitTime: null,
          dropoffWaitTime: null,
        };
      }

      if (stop.type?.toLowerCase() === "pickup") {
        employeeTrips[empId].pickupTime = stop.arrivalTime;
        employeeTrips[empId].pickupLat = stop.lat;
        employeeTrips[empId].pickupLon = stop.lon;
        employeeTrips[empId].pickupWaitTime = stop.waitTime;
      } else if (stop.type?.toLowerCase() === "dropoff") {
        employeeTrips[empId].dropoffTime = stop.arrivalTime;
        employeeTrips[empId].dropoffLat = stop.lat;
        employeeTrips[empId].dropoffLon = stop.lon;
        employeeTrips[empId].dropoffWaitTime = stop.waitTime;
      }
    });
  });

  const requestMap = {};
  inputData?.requests?.forEach((req) => (requestMap[req.employeeId] = req));

  const vehicleMap = {};
  inputData?.vehicles?.forEach((veh) => (vehicleMap[veh.vehicleId] = veh));

  const employeeList = Object.values(employeeTrips).sort((a, b) =>
    a.employeeId.toString().localeCompare(b.employeeId.toString()),
  );

  const formatTime = (minutes) => {
    if (!minutes && minutes !== 0) return "-";
    const hours = Math.floor(minutes / 60);
    const mins = Math.floor(minutes % 60);
    return `${hours.toString().padStart(2, "0")}:${mins.toString().padStart(2, "0")}`;
  };

  return (
    <div className="employee-results-v2">
      <div className="grid grid-cols-3">
        {employeeList.map((emp, idx) => {
          const req = requestMap[emp.employeeId];
          const veh = vehicleMap[emp.vehicleId];
          const travelTime =
            emp.pickupTime !== null && emp.dropoffTime !== null
              ? emp.dropoffTime - emp.pickupTime
              : null;
          const isOnTime =
            emp.pickupTime >= (req?.earlyTime ?? -1) &&
            emp.pickupTime <= (req?.lateTime ?? 9999);

          return (
            <motion.div
              key={emp.employeeId}
              className="glass-card employee-card-v2"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.05 }}
              onMouseEnter={() => onEmployeeHover?.(emp.employeeId)}
              onMouseLeave={() => onEmployeeHover?.(null)}
            >
              <div className="emp-card-header">
                <div className="emp-avatar">
                  <User size={20} color="var(--primary)" />
                </div>
                <div className="emp-info-main">
                  <h4>{emp.employeeId}</h4>
                  <div className="assigned-veh">
                    <Truck size={12} />
                    <span>Vehicle {emp.vehicleId}</span>
                    {veh?.fuelType && (
                      <span className="fuel-badge">{veh.fuelType}</span>
                    )}
                    {veh?.type && veh.type !== "normal" && (
                      <span className="type-badge">{veh.type}</span>
                    )}
                  </div>
                </div>
                <StatusIcon isOnTime={isOnTime} />
              </div>

              <div className="emp-trip-details">
                <div className="trip-point">
                  <div className="point-icon">
                    <MapPin size={14} />
                  </div>
                  <div className="point-info">
                    <span className="label">Pickup</span>
                    <span className="value">{formatTime(emp.pickupTime)}</span>
                    <span className="window">
                      Window: {formatTime(req?.earlyTime)} -{" "}
                      {formatTime(req?.lateTime)}
                    </span>
                    {emp.pickupWaitTime > 0 && (
                      <span className="wait-time">
                        Wait: {emp.pickupWaitTime.toFixed(1)} min
                      </span>
                    )}
                  </div>
                </div>

                <div className="trip-point">
                  <div className="point-icon">
                    <MapPin size={14} style={{ transform: "rotate(180deg)" }} />
                  </div>
                  <div className="point-info">
                    <span className="label">Dropoff</span>
                    <span className="value">{formatTime(emp.dropoffTime)}</span>
                    {emp.dropoffWaitTime > 0 && (
                      <span className="wait-time">
                        Wait: {emp.dropoffWaitTime.toFixed(1)} min
                      </span>
                    )}
                  </div>
                </div>

                <div className="trip-point">
                  <div className="point-icon">
                    <Clock size={14} />
                  </div>
                  <div className="point-info">
                    <span className="label">Trip Duration</span>
                    <span className="value">
                      {travelTime !== null
                        ? `${travelTime.toFixed(1)} min`
                        : "-"}
                    </span>
                  </div>
                </div>
              </div>

              <div className="emp-footer-metrics">
                <div className="footer-metric">
                  <Star size={12} />
                  <span>P{req?.priority || 1}</span>
                </div>
                <div className="footer-metric">
                  <Users size={12} />
                  <span>
                    Limit: {req?.sharingLimit === 999 ? "∞" : req?.sharingLimit}
                  </span>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      <style>{`
        .point-info .wait-time { font-size: 0.7rem; color: #fbbf24; font-weight: 600; }
        .employee-results-v2 { padding: 8px; }
        .employee-card-v2 { 
          padding: 20px; 
          display: flex; 
          flex-direction: column; 
          gap: 20px; 
          cursor: pointer; 
          transition: transform 0.2s, box-shadow 0.2s;
        }
        .employee-card-v2:hover { 
          transform: translateY(-2px); 
          box-shadow: 0 8px 24px rgba(59, 130, 246, 0.2);
        }
        .emp-card-header { display: flex; align-items: center; gap: 14px; }
        .emp-avatar { width: 40px; height: 40px; border-radius: 12px; background: var(--bg-glass); display: flex; align-items: center; justify-content: center; border: 1px solid var(--border-subtle); }
        .emp-info-main { flex: 1; }
        .emp-info-main h4 { font-size: 1rem; margin-bottom: 2px; }
        .assigned-veh { display: flex; align-items: center; gap: 6px; font-size: 0.75rem; color: var(--text-dim); }
        .fuel-badge, .type-badge { padding: 2px 8px; background: rgba(59, 130, 246, 0.2); border-radius: 4px; font-size: 0.65rem; font-weight: 600; text-transform: uppercase; color: #60a5fa; }
        .type-badge { background: rgba(168, 85, 247, 0.2); color: #c084fc; }
        .status-icon-wrapper { cursor: pointer; transition: transform 0.2s; position: relative; }
        .status-icon-wrapper:hover { transform: scale(1.15); }
        .custom-tooltip { 
          position: absolute; 
          top: -35px; 
          right: 0; 
          background: rgba(17, 24, 39, 0.95); 
          color: white; 
          padding: 6px 12px; 
          border-radius: 6px; 
          font-size: 0.75rem; 
          white-space: nowrap; 
          z-index: 1000;
          border: 1px solid rgba(255, 255, 255, 0.2);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
          pointer-events: none;
        }
        .custom-tooltip::after {
          content: '';
          position: absolute;
          top: 100%;
          right: 10px;
          border: 5px solid transparent;
          border-top-color: rgba(17, 24, 39, 0.95);
        }
        .emp-trip-details { display: flex; flex-direction: column; gap: 16px; padding: 16px; background: rgba(0,0,0,0.2); border-radius: 12px; }
        .trip-point { display: flex; gap: 12px; }
        .point-icon { color: var(--primary); margin-top: 2px; }
        .point-info { display: flex; flex-direction: column; gap: 2px; }
        .point-info .label { font-size: 0.65rem; font-weight: 700; text-transform: uppercase; color: var(--text-dim); }
        .point-info .value { font-family: var(--font-display); font-size: 0.95rem; font-weight: 700; color: var(--text-bright); }
        .point-info .window { font-size: 0.7rem; color: var(--text-dim); }
        .emp-footer-metrics { display: flex; gap: 12px; }
        .footer-metric { display: flex; align-items: center; gap: 6px; font-size: 0.7rem; font-weight: 600; color: var(--text-dim); background: var(--bg-glass); padding: 4px 10px; border-radius: 6px; }
      `}</style>
    </div>
  );
}
