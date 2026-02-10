const express = require("express");
const multer = require("multer");
const path = require("path");
const { v4: uuidv4 } = require("uuid");
const optimizationController = require("../controllers/optimizationController");

const router = express.Router();

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, path.join(__dirname, "../../uploads"));
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + "-" + Math.round(Math.random() * 1e9);
    cb(null, uniqueSuffix + "-" + file.originalname);
  },
});

const upload = multer({
  storage,
  fileFilter: (req, file, cb) => {
    const allowedTypes = [
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "application/vnd.ms-excel",
    ];
    if (
      allowedTypes.includes(file.mimetype) ||
      file.originalname.endsWith(".xlsx") ||
      file.originalname.endsWith(".xls")
    ) {
      cb(null, true);
    } else {
      cb(new Error("Only Excel files (.xlsx, .xls) are allowed"));
    }
  },
});

// POST /api/optimize - Upload Excel and start optimization
router.post(
  "/optimize",
  upload.single("file"),
  optimizationController.startOptimization,
);

// POST /api/optimize/json - Direct JSON optimization (for frontend)
router.post("/optimize/json", async (req, res) => {
  try {
    const jobId = uuidv4();
    const fs = require("fs");
    const solver = require("../services/solver");

    // Save input JSON temporarily
    const inputPath = path.join(
      __dirname,
      "../../uploads",
      `${jobId}_input.json`,
    );
    const outputPath = path.join(
      __dirname,
      "../../outputs",
      `${jobId}_output.json`,
    );

    fs.writeFileSync(inputPath, JSON.stringify(req.body, null, 2));

    // Run solver
    await solver.run(inputPath, outputPath);

    // Read result
    const result = JSON.parse(fs.readFileSync(outputPath, "utf-8"));

    res.json({ jobId, status: "success", result });
  } catch (error) {
    console.error("Error in optimize/json:", error);
    res.status(500).json({ error: error.message });
  }
});

// GET /api/results/:jobId - Get result (alias for frontend compatibility)
router.get("/results/:jobId", optimizationController.getJobResult);

// GET /api/optimize/:jobId/status - Get job status
router.get("/optimize/:jobId/status", optimizationController.getJobStatus);

// GET /api/optimize/:jobId/result - Get optimization results
router.get("/optimize/:jobId/result", optimizationController.getJobResult);

// GET /api/testcases - List available test cases
router.get("/testcases", optimizationController.listTestCases);

// POST /api/testcases/:id/run - Run a specific test case
router.post("/testcases/:id/run", optimizationController.runTestCase);

module.exports = router;
