/**
 * Parser Service
 *
 * Spawns the Python excel_to_json.py script as a child process.
 * Input:  path to .xlsx file
 * Output: path to generated .json file
 *
 * The Python script reads the Excel, produces a standardized JSON
 * that the C++ solver understands.
 */

const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

const PARSER_SCRIPT = path.join(__dirname, "..", "parser", "excel_to_json.py");

// Try to find Python in common locations
function findPythonExecutable() {
  if (process.env.PYTHON_BIN) return process.env.PYTHON_BIN;

  // Try venv first
  const venvPython = path.join(
    __dirname,
    "..",
    "..",
    ".venv",
    "Scripts",
    "python.exe",
  );
  if (fs.existsSync(venvPython)) return venvPython;

  // Fallback to common Python commands
  return process.platform === "win32" ? "python" : "python3";
}

const PYTHON_BIN = findPythonExecutable();

/**
 * Convert an Excel file to solver-compatible JSON.
 *
 * @param {string} excelPath  - Absolute path to uploaded .xlsx file
 * @param {string} jsonPath   - Absolute path where output .json should be written
 * @param {number} timeoutMs  - Max time to wait (default 30s)
 * @returns {Promise<string>} - Resolves with jsonPath on success
 */
function parseExcelToJson(excelPath, jsonPath, timeoutMs = 30000) {
  return new Promise((resolve, reject) => {
    console.log(
      `[Parser] Running: ${PYTHON_BIN} ${PARSER_SCRIPT} "${excelPath}" "${jsonPath}"`,
    );

    const proc = spawn(PYTHON_BIN, [PARSER_SCRIPT, excelPath, jsonPath], {
      // Pass env so the parser can read MAPS_API_KEY from environment
      env: { ...process.env },
      timeout: timeoutMs,
    });

    let stdout = "";
    let stderr = "";

    proc.stdout.on("data", (data) => {
      stdout += data.toString();
    });

    proc.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    proc.on("close", (code) => {
      if (code === 0) {
        console.log(`[Parser] Success: ${stdout.trim()}`);
        resolve(jsonPath);
      } else {
        console.error(`[Parser] Failed (exit ${code}): ${stderr}`);
        reject(
          new Error(
            `Parser failed (exit ${code}): ${stderr || "Unknown error"}`,
          ),
        );
      }
    });

    proc.on("error", (err) => {
      console.error(`[Parser] Spawn error: ${err.message}`);
      reject(new Error(`Could not run Python parser: ${err.message}`));
    });
  });
}

module.exports = { parseExcelToJson };
