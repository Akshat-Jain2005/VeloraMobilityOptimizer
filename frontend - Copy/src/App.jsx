import React, {
  useCallback,
  useEffect,
  useMemo,
  useState,
  Fragment,
} from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  Rocket,
  Database,
  Settings2,
  BarChart,
  CheckCircle,
  Car,
  Users,
} from "lucide-react";
import HomePage from "./components/HomePage.jsx";
import Header from "./components/Header.jsx";
import FileUpload from "./components/FileUpload.jsx";
import ResultsSection from "./components/ResultsSection.jsx";
import { parseExcel } from "./excelParser.js";
import { getSolution, submitOptimization } from "./api.js";

const defaultStatus = "idle";

export default function App() {
  const [showHomePage, setShowHomePage] = useState(true);
  const [showResults, setShowResults] = useState(false);
  const [fileName, setFileName] = useState("");
  const [inputData, setInputData] = useState(null);
  const [parseError, setParseError] = useState("");
  const [isParsing, setIsParsing] = useState(false);

  const [status, setStatus] = useState(defaultStatus);
  const [solutionId, setSolutionId] = useState("");
  const [solution, setSolution] = useState(null);
  const [submitError, setSubmitError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isReady = useMemo(
    () => inputData?.vehicles?.length && inputData?.requests?.length,
    [inputData],
  );

  const handleFile = async (file) => {
    setParseError("");
    setIsParsing(true);
    setFileName(file.name);
    setStatus(defaultStatus);
    setSolution(null);
    setSolutionId("");
    setSubmitError("");

    try {
      const { output } = await parseExcel(file);
      if (!output.vehicles.length || !output.requests.length) {
        throw new Error("Missing required fleet or employee data structures.");
      }
      setInputData(output);
    } catch (error) {
      setParseError(error.message || "Engine failed to parse dataset.");
      setInputData(null);
    } finally {
      setIsParsing(false);
    }
  };

  const handleClear = () => {
    setFileName("");
    setInputData(null);
    setParseError("");
    setStatus(defaultStatus);
    setSolution(null);
    setSolutionId("");
    setSubmitError("");
  };

  const handleOptimize = async () => {
    if (!isReady || isSubmitting) return;
    setSubmitError("");
    setIsSubmitting(true);

    try {
      // Store employee ID mapping for later use
      const employeeIdMap = {};
      inputData.requests.forEach((r, index) => {
        if (r.employeeId) {
          employeeIdMap[index] = r.employeeId;
        }
      });

      // Transform frontend data format to C++ solver format
      const payload = {
        config: {
          allow_external_maps: false,
          maps_api_key: "",
        },
        vehicles: inputData.vehicles.map((v, index) => ({
          id: index,
          vehicle_id: v.vehicleId || `V${index + 1}`,
          capacity: v.capacity || 4,
          costPerKm: v.costPerKm || 15,
          avg_speed_kmph: v.speed || 30,
          startLoc: {
            lat: v.startLocation?.lat || 0,
            lon: v.startLocation?.lon || 0,
          },
          availabilityTime: v.availabilityTime || 0,
          type: v.type || "4w",
          vehicle_type: v.type || "4w",
          fuel_type: v.fuelType || "petrol",
          category: v.category || "normal",
        })),
        requests: inputData.requests.map((r, index) => ({
          id: index,
          employee_id: r.employeeId || `E${index + 1}`,
          priority: r.priority || 3,
          pickup: {
            lat: r.pickup?.lat || 0,
            lon: r.pickup?.lon || 0,
          },
          dropoff: {
            lat: r.dropoff?.lat || 0,
            lon: r.dropoff?.lon || 0,
          },
          earlyTime: r.earlyTime || 0,
          lateTime: r.lateTime || 90,
          load: r.load || 1,
          vehiclePreference: r.vehiclePreference || "any",
          sharingLimit: r.sharingLimit || 4,
        })),
      };

      // Add optional config if metadata exists
      if (inputData.metadata?.maxDelayByPriority) {
        payload.config.tolerances = inputData.metadata.maxDelayByPriority;
      }

      const response = await submitOptimization(payload);

      // Backend returns result immediately (not async polling)
      if (response.status === "success" && response.result) {
        // Transform result to match expected frontend format
        const output = response.result;
        const routes = output.routes || [];
        const rawSummary = output.summary || {};

        const totalMoneyCost = rawSummary.totalMoneyCost || 0;
        const totalDistance = rawSummary.totalDistance || 0;
        const totalTime = rawSummary.totalTime || 0;
        const vehiclesUsed = rawSummary.vehiclesUsed || 0;
        const unassignedCount = rawSummary.unassignedCount || 0;
        const globalCost = rawSummary.globalCost || totalMoneyCost;

        const summary = {
          totalMoneyCost,
          totalDistance,
          totalTime,
          vehiclesUsed,
          unassignedCount,
          ...rawSummary,
        };

        // Enrich routes with employee IDs
        const enrichedRoutes = routes.map((route) => ({
          ...route,
          stops: route.stops?.map((stop) => {
            let stopType = stop.type;
            if (stopType === "P") stopType = "pickup";
            else if (stopType === "D") stopType = "dropoff";

            return {
              ...stop,
              type: stopType,
              employeeId:
                stop.employeeId ||
                employeeIdMap[stop.reqId] ||
                `Req-${stop.reqId}`,
            };
          }),
        }));

        const transformed = {
          status: "completed",
          // Top-level fields for ResultsSection
          routes: enrichedRoutes,
          unassigned: output.unassigned || [],
          totalDistance,
          totalMoneyCost,
          globalCost,
          totalTime,
          vehiclesUsed,
          requestDetails: output.requestDetails || [],
          // Nested 'data' format for child components
          data: {
            routes: enrichedRoutes,
            unassigned: output.unassigned || [],
            summary: summary,
          },
          output: {
            summary: rawSummary,
            routes: routes,
          },
          _employeeIdMap: employeeIdMap,
        };

        setSolution(transformed);
        setStatus("completed");
      } else {
        // Fallback to polling if backend sends job ID
        setSolutionId(response.solutionId || response.jobId);
        setStatus(response.status || "processing");
        setSolution({
          status: response.status || "processing",
          _employeeIdMap: employeeIdMap,
        });
      }
      setShowResults(true);
    } catch (error) {
      setSubmitError(
        error.message || "Optimization request rejected by server.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const pollSolution = useCallback(async () => {
    if (!solutionId) return;
    try {
      const response = await getSolution(solutionId);

      // Transform backend response to frontend format
      if (response.status === "completed" && response.output) {
        const routes = response.output.routes || [];
        const rawSummary = response.output.summary || {};

        // Calculate summary metrics from routes if not provided
        const totalDistance =
          rawSummary.totalDistance ||
          routes.reduce((sum, route) => sum + (route.totalDist || 0), 0);

        const totalMoneyCost =
          rawSummary.totalMoneyCost ||
          routes.reduce((sum, route) => sum + (route.totalCost || 0), 0);

        const globalCost =
          rawSummary.globalCost || response.output.globalCost || totalMoneyCost;

        const vehiclesUsed = rawSummary.vehiclesUsed || routes.length;

        // Calculate total time from routes
        const totalTime =
          rawSummary.totalTime ||
          routes.reduce((sum, route) => {
            const stops = route.stops || [];
            if (stops.length === 0) return sum;
            const lastStop = stops[stops.length - 1];
            const firstStop = stops[0];
            return sum + ((lastStop.arrival || 0) - (firstStop.arrival || 0));
          }, 0);

        const unassignedCount =
          rawSummary.unassignedCount !== undefined
            ? rawSummary.unassignedCount
            : (response.output.unassigned || []).length;

        const summary = {
          globalCost,
          totalMoneyCost,
          totalDistance,
          totalTime,
          vehiclesUsed,
          unassignedCount,
          ...rawSummary,
        };

        // Add employee IDs back to stops if we have the mapping
        const employeeIdMap = solution?._employeeIdMap || {};
        const enrichedRoutes = routes.map((route) => ({
          ...route,
          stops: route.stops?.map((stop) => {
            // Normalize stop type: convert "P" to "pickup" and "D" to "dropoff"
            let stopType = stop.type;
            if (stopType === "P") stopType = "pickup";
            else if (stopType === "D") stopType = "dropoff";

            return {
              ...stop,
              type: stopType,
              employeeId:
                stop.employeeId ||
                employeeIdMap[stop.reqId] ||
                `Req-${stop.reqId}`,
            };
          }),
        }));

        const transformed = {
          ...response,
          // Top-level fields for ResultsSection
          routes: enrichedRoutes,
          unassigned: response.output.unassigned || [],
          totalDistance,
          totalMoneyCost,
          globalCost,
          totalTime,
          vehiclesUsed,
          requestDetails: response.output.requestDetails || [],
          // Nested 'data' format for child components
          data: {
            routes: enrichedRoutes,
            unassigned: response.output.unassigned || [],
            summary: summary,
          },
        };
        setSolution(transformed);
      } else {
        setSolution(response);
      }

      setStatus(response.status);
      return response.status === "completed" || response.status === "failed";
    } catch (error) {
      setSubmitError("Connectivity issue while polling status.");
      return false;
    }
  }, [solutionId, solution]);

  useEffect(() => {
    if (!solutionId) return;
    if (status === "completed" || status === "failed") return;

    const interval = setInterval(async () => {
      if (await pollSolution()) clearInterval(interval);
    }, 2000);
    return () => clearInterval(interval);
  }, [pollSolution, solutionId, status]);

  if (showHomePage) return <HomePage onStart={() => setShowHomePage(false)} />;

  if (showResults) {
    return (
      <motion.div
        className="app"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <div className="header-with-back">
          <Header />
          <button
            className="btn btn-secondary back-btn-compact"
            onClick={() => setShowResults(false)}
          >
            <ArrowLeft size={16} />
            <span>Refine Data</span>
          </button>
        </div>
        <ResultsSection solution={solution} inputData={inputData} />
      </motion.div>
    );
  }

  return (
    <div className="app">
      <Header />
      <div className="upload-workflow">
        {/* Progress Steps */}
        <div className="workflow-steps-premium">
          {[
            { id: 1, label: "Upload", icon: Database, done: !!fileName },
            { id: 2, label: "Optimize", icon: Settings2, done: !!solutionId },
            { id: 3, label: "Review", icon: BarChart, done: false },
          ].map((step, idx) => (
            <Fragment key={step.id}>
              <div
                className={`workflow-step-v2 ${step.done ? "completed" : idx === 0 || (idx === 1 && fileName) ? "active" : ""}`}
              >
                <div className="step-icon-wrapper">
                  <step.icon size={18} />
                </div>
                <span className="step-label-v2">{step.label}</span>
              </div>
              {idx < 2 && <div className="step-connector-v2" />}
            </Fragment>
          ))}
        </div>

        <div className="workflow-main">
          <FileUpload
            onFile={handleFile}
            fileName={fileName}
            isParsing={isParsing}
            onClear={handleClear}
            error={parseError}
          />
        </div>

        <AnimatePresence>
          {fileName && (
            <motion.div
              className="glass-card action-bar-premium"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
            >
              <div className="action-bar-grid">
                <div className="action-status-info">
                  <div className="status-indicator-v2">
                    <div
                      className={`status-pulse ${status === "processing" ? "active" : status === "completed" ? "success" : ""}`}
                    />
                    <span className="status-text-v2">
                      {status === "idle" && "Configuration Ready"}
                      {status === "processing" && "Optimizer Active"}
                      {status === "completed" && "Optimization Success"}
                    </span>
                  </div>
                  {isReady && (
                    <div className="dataset-chips">
                      <div className="chip">
                        <Car size={14} />{" "}
                        <span>{inputData.vehicles.length} Fleet</span>
                      </div>
                      <div className="chip">
                        <Users size={14} />{" "}
                        <span>{inputData.requests.length} Targets</span>
                      </div>
                    </div>
                  )}
                </div>

                <div className="action-buttons-group">
                  <button
                    className="btn btn-primary optimize-btn-v2"
                    onClick={handleOptimize}
                    disabled={!isReady || isSubmitting}
                  >
                    {isSubmitting ? (
                      <span className="loading-spinner">Processing...</span>
                    ) : (
                      <>
                        <Rocket size={18} />
                        <span>EXECUTE ENGINE</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
              {submitError && <p className="error-text-v2">{submitError}</p>}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <style>{`
        .upload-workflow {
          display: flex;
          flex-direction: column;
          gap: 40px;
          max-width: 800px;
          margin: 0 auto;
          width: 100%;
        }
        .workflow-steps-premium {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 12px;
          padding: 20px;
        }
        .workflow-step-v2 {
          display: flex;
          align-items: center;
          gap: 12px;
          color: var(--text-dim);
          transition: all 0.3s ease;
        }
        .workflow-step-v2.active { color: var(--primary); }
        .workflow-step-v2.completed { color: var(--accent); }
        .step-icon-wrapper {
          width: 40px;
          height: 40px;
          border-radius: 12px;
          background: var(--bg-glass);
          border: 1px solid var(--border-subtle);
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .active .step-icon-wrapper { border-color: var(--primary); background: var(--primary-glow); }
        .completed .step-icon-wrapper { border-color: var(--accent); color: var(--accent); }
        .step-label-v2 { font-family: var(--font-display); font-weight: 600; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; }
        .step-connector-v2 { width: 40px; height: 1px; background: var(--border-subtle); }
        
        .action-bar-premium {
          padding: 24px 32px;
          border-radius: var(--radius-lg);
        }
        .action-bar-grid {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 24px;
        }
        .status-indicator-v2 { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
        .status-pulse { width: 8px; height: 8px; border-radius: 50%; background: var(--text-dim); }
        .status-pulse.active { background: var(--primary); box-shadow: 0 0 10px var(--primary); animation: pulse 2s infinite; }
        .status-pulse.success { background: var(--accent); box-shadow: 0 0 10px var(--accent); }
        .status-text-v2 { font-family: var(--font-display); font-weight: 700; font-size: 0.9rem; color: var(--text-bright); }
        .dataset-chips { display: flex; gap: 8px; }
        .chip { display: flex; align-items: center; gap: 6px; padding: 4px 12px; background: var(--bg-glass); border-radius: 100px; font-size: 0.75rem; color: var(--text-dim); border: 1px solid var(--border-subtle); }
        .optimize-btn-v2 { min-width: 220px; }
        .error-text-v2 { color: #ef4444; font-size: 0.85rem; margin-top: 12px; text-align: center; }
        .header-with-back { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
        .back-btn-compact { margin-top: 12px; }
      `}</style>
    </div>
  );
}
