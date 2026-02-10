/**
 * Optimization Routes
 * 
 * POST /api/optimize       — Upload Excel → Parser → Solver → JSON result
 * POST /api/optimize/json  — Upload raw JSON → Solver directly → JSON result
 * GET  /api/results/:jobId — Fetch a previously computed result by job ID
 */

const express = require('express');
const router = express.Router();
const path = require('path');
const fs = require('fs');
const { v4: uuidv4 } = require('uuid');

const upload = require('../middleware/upload');
const { parseExcelToJson } = require('../services/parser');
const { runSolver } = require('../services/solver');

const OUTPUTS_DIR = path.join(__dirname, '..', 'outputs');
const UPLOADS_DIR = path.join(__dirname, '..', 'uploads');

// ──────────────────────────────────────────────────────────────────────────
// POST /api/optimize — Full pipeline (Excel → JSON → Solver → Result)
// ──────────────────────────────────────────────────────────────────────────

router.post('/optimize', upload.single('file'), async (req, res) => {
  const jobId = uuidv4();
  const startTime = Date.now();

  // Paths for this job's files
  const inputJsonPath = path.join(UPLOADS_DIR, `${jobId}_input.json`);
  const outputJsonPath = path.join(OUTPUTS_DIR, `${jobId}_output.json`);

  try {
    // 1. Validate upload
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded. Send an Excel file with key "file".' });
    }
    const excelPath = req.file.path;
    console.log(`\n[Job ${jobId}] Started — file: ${req.file.originalname}`);

    // 2. Parse Excel → JSON
    console.log(`[Job ${jobId}] Step 1/2: Parsing Excel to JSON...`);
    await parseExcelToJson(excelPath, inputJsonPath);

    // 3. Run C++ solver
    console.log(`[Job ${jobId}] Step 2/2: Running solver...`);
    const result = await runSolver(inputJsonPath, outputJsonPath);

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    console.log(`[Job ${jobId}] Done in ${elapsed}s`);

    // 4. Return result
    res.json({
      jobId,
      status: 'success',
      elapsedSeconds: parseFloat(elapsed),
      result
    });

    // 5. Cleanup uploaded Excel (keep JSON outputs for /results/:jobId)
    cleanup(excelPath);

  } catch (err) {
    console.error(`[Job ${jobId}] FAILED:`, err.message);
    res.status(500).json({
      jobId,
      status: 'error',
      error: err.message
    });

    // Cleanup on failure too
    cleanup(req.file?.path);
    cleanup(inputJsonPath);
  }
});

// ──────────────────────────────────────────────────────────────────────────
// POST /api/optimize/json — Direct JSON input (skip parser)
// ──────────────────────────────────────────────────────────────────────────
// Useful for: testing, frontend sending pre-built JSON, re-running with tweaks

router.post('/optimize/json', async (req, res) => {
  const jobId = uuidv4();
  const startTime = Date.now();

  const inputJsonPath = path.join(UPLOADS_DIR, `${jobId}_input.json`);
  const outputJsonPath = path.join(OUTPUTS_DIR, `${jobId}_output.json`);

  try {
    // 1. Validate body
    const inputData = req.body;
    if (!inputData || !inputData.requests || !inputData.vehicles) {
      return res.status(400).json({
        error: 'Invalid JSON. Must contain "requests" and "vehicles" arrays.'
      });
    }

    console.log(`\n[Job ${jobId}] Started — direct JSON input`);

    // 2. Write input JSON to file (solver reads from file)
    fs.writeFileSync(inputJsonPath, JSON.stringify(inputData, null, 2));

    // 3. Run solver
    console.log(`[Job ${jobId}] Running solver...`);
    const result = await runSolver(inputJsonPath, outputJsonPath);

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    console.log(`[Job ${jobId}] Done in ${elapsed}s`);

    res.json({
      jobId,
      status: 'success',
      elapsedSeconds: parseFloat(elapsed),
      result
    });

  } catch (err) {
    console.error(`[Job ${jobId}] FAILED:`, err.message);
    res.status(500).json({
      jobId,
      status: 'error',
      error: err.message
    });

    cleanup(inputJsonPath);
  }
});

// ──────────────────────────────────────────────────────────────────────────
// GET /api/results/:jobId — Retrieve a past result
// ──────────────────────────────────────────────────────────────────────────

router.get('/results/:jobId', (req, res) => {
  const { jobId } = req.params;

  // Basic validation to prevent path traversal
  if (!/^[a-f0-9-]{36}$/.test(jobId)) {
    return res.status(400).json({ error: 'Invalid job ID format' });
  }

  const outputPath = path.join(OUTPUTS_DIR, `${jobId}_output.json`);

  if (!fs.existsSync(outputPath)) {
    return res.status(404).json({ error: 'Result not found. It may have been cleaned up.' });
  }

  try {
    const raw = fs.readFileSync(outputPath, 'utf-8');
    const result = JSON.parse(raw);
    res.json({ jobId, status: 'success', result });
  } catch (err) {
    res.status(500).json({ error: 'Failed to read result file' });
  }
});

// ──────────────────────────────────────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────────────────────────────────────

function cleanup(filePath) {
  if (filePath && fs.existsSync(filePath)) {
    try {
      fs.unlinkSync(filePath);
    } catch (e) {
      // not critical
    }
  }
}

module.exports = router;
