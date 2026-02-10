const express = require("express");
const cors = require("cors");
const path = require("path");
const optimizationRoutes = require("./routes/optimization");

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Serve static output files
app.use("/outputs", express.static(path.join(__dirname, "..", "outputs")));

// Root route
app.get("/", (req, res) => {
  res.json({
    message: "VELORA Backend API Server",
    frontend: "http://localhost:5173",
    endpoints: {
      health: "/api/health",
      optimize: "POST /api/optimize/json",
      results: "GET /api/results/:jobId",
    },
  });
});

// Health check
app.get("/api/health", (req, res) => {
  res.json({ status: "ok", timestamp: new Date().toISOString() });
});

// Routes
app.use("/api", optimizationRoutes);

app.listen(PORT, () => {
  console.log(`Velora Backend running on port ${PORT}`);
});

module.exports = app;
