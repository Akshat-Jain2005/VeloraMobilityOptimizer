const express = require('express');
const multer = require('multer');
const path = require('path');
const optimizationController = require('../controllers/optimizationController');

const router = express.Router();

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, path.join(__dirname, '../../uploads'));
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, uniqueSuffix + '-' + file.originalname);
  }
});

const upload = multer({
  storage,
  fileFilter: (req, file, cb) => {
    const allowedTypes = [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel'
    ];
    if (allowedTypes.includes(file.mimetype) || file.originalname.endsWith('.xlsx') || file.originalname.endsWith('.xls')) {
      cb(null, true);
    } else {
      cb(new Error('Only Excel files (.xlsx, .xls) are allowed'));
    }
  }
});

// POST /api/optimize - Upload Excel and start optimization
router.post('/optimize', upload.single('file'), optimizationController.startOptimization);

// GET /api/optimize/:jobId/status - Get job status
router.get('/optimize/:jobId/status', optimizationController.getJobStatus);

// GET /api/optimize/:jobId/result - Get optimization results
router.get('/optimize/:jobId/result', optimizationController.getJobResult);

// GET /api/testcases - List available test cases
router.get('/testcases', optimizationController.listTestCases);

// POST /api/testcases/:id/run - Run a specific test case
router.post('/testcases/:id/run', optimizationController.runTestCase);

module.exports = router;
