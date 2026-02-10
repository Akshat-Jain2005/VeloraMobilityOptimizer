/**
 * VELORA MOBILITY OPTIMIZER - Backend API Server
 *
 * Endpoints:
 *   POST /api/optimize          Upload Excel → Run pipeline → Return JSON result
 *   POST /api/optimize/json     Upload raw JSON → Run solver directly → Return JSON result
 *   GET  /api/results/:jobId    Fetch a previously computed result
 *   GET  /api/health            Health check
 *
 * Pipeline: Excel → Python parser → JSON → C++ solver → JSON output
 */

require("dotenv").config();
const express = require("express");
const cors = require("cors");
const path = require("path");
const fs = require("fs");

const optimizeRoutes = require("./routes/optimize");

const app = express();
const PORT = process.env.PORT || 3001;

// ---------------------------------------------------------------------------
// Middleware
// ---------------------------------------------------------------------------

// CORS — allow any origin for now. Lock this down before production.
app.use(cors());

// Parse JSON bodies (for the /optimize/json endpoint)
app.use(express.json({ limit: "10mb" }));

// Serve output files so frontend can fetch result JSONs directly if needed
app.use("/outputs", express.static(path.join(__dirname, "outputs")));

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

// Root route - redirect to frontend or show info
app.get("/", (req, res) => {
  res.json({
    message: "VELORA Backend API Server",
    frontend: "http://localhost:5176",
    health: "/api/health",
    docs: "See /api/health for available endpoints",
  });
});

// Health check - must be before app.use("/api", ...) to take precedence
app.get("/api/health", (req, res) => {
  const solverName =
    process.platform === "win32" ? "velora_solver.exe" : "velora_solver";
  const solverPath = path.join(__dirname, "solver", solverName);
  const parserPath = path.join(__dirname, "parser", "excel_to_json.py");

  res.json({
    status: "ok",
    timestamp: new Date().toISOString(),
    solver: fs.existsSync(solverPath) ? "found" : "MISSING",
    parser: fs.existsSync(parserPath) ? "found" : "MISSING",
    mapsApiKey: process.env.MAPS_API_KEY
      ? "configured"
      : "not set (using Haversine)",
  });
});

app.use("/api", optimizeRoutes);

// ---------------------------------------------------------------------------
// Error handling
// ---------------------------------------------------------------------------

// 404 for unknown routes
app.use((req, res) => {
  res.status(404).json({ error: "Route not found" });
});

// Global error handler
app.use((err, req, res, next) => {
  console.error("[ERROR]", err.message);
  res
    .status(500)
    .json({ error: "Internal server error", details: err.message });
});

// ---------------------------------------------------------------------------
// Startup
// ---------------------------------------------------------------------------

app.listen(PORT, () => {
  console.log("=".repeat(50));
  console.log("  VELORA MOBILITY OPTIMIZER — Backend API");
  console.log("=".repeat(50));
  console.log(`  Server:  http://localhost:${PORT}`);
  console.log(`  Health:  http://localhost:${PORT}/api/health`);
  console.log(`  API:     POST http://localhost:${PORT}/api/optimize`);
  console.log("=".repeat(50));

  // Startup checks
  const solverName =
    process.platform === "win32" ? "velora_solver.exe" : "velora_solver";
  const solverPath = path.join(__dirname, "solver", solverName);
  const parserPath = path.join(__dirname, "parser", "excel_to_json.py");

  if (!fs.existsSync(solverPath)) {
    console.warn("\n  ⚠  WARNING: solver/" + solverName + " not found!");
    console.warn("     Copy your compiled binary into the solver/ folder.\n");
  }
  if (!fs.existsSync(parserPath)) {
    console.warn("\n  ⚠  WARNING: parser/excel_to_json.py not found!");
    console.warn("     Copy your parser script into the parser/ folder.\n");
  }
});
