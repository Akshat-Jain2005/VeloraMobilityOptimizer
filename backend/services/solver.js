/**
 * Solver Service
 *
 * Spawns the compiled C++ velora_solver binary as a child process.
 * Input:  path to input .json file (from parser)
 * Output: path to output .json file (solver writes this)
 *
 * Usage: ./velora_solver input.json output.json
 */

const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

// Handle Windows .exe extension
const SOLVER_NAME =
  process.platform === "win32" ? "velora_solver.exe" : "velora_solver";
const SOLVER_BIN = path.join(__dirname, "..", "solver", SOLVER_NAME);

/**
 * Run the C++ solver on a JSON input file.
 *
 * @param {string} inputJsonPath  - Absolute path to input .json
 * @param {string} outputJsonPath - Absolute path where solver writes output .json
 * @param {number} timeoutMs      - Max time to wait (default 120s)
 * @returns {Promise<object>}     - Resolves with parsed output JSON
 */
function runSolver(inputJsonPath, outputJsonPath, timeoutMs = 120000) {
  return new Promise((resolve, reject) => {
    // Check binary exists
    if (!fs.existsSync(SOLVER_BIN)) {
      return reject(
        new Error(
          `Solver binary not found at ${SOLVER_BIN}. ` +
            `Copy your compiled velora_solver into the solver/ folder.`,
        ),
      );
    }

    console.log(
      `[Solver] Running: ${SOLVER_BIN} "${inputJsonPath}" "${outputJsonPath}"`,
    );
    const startTime = Date.now();

    const proc = spawn(SOLVER_BIN, [inputJsonPath, outputJsonPath], {
      timeout: timeoutMs,
      env: {
        ...process.env,
        CURL_CA_BUNDLE:
          process.env.CURL_CA_BUNDLE ||
          "C:\\msys64\\mingw64\\ssl\\certs\\ca-bundle.crt",
        SSL_CERT_FILE:
          process.env.SSL_CERT_FILE ||
          "C:\\msys64\\mingw64\\ssl\\certs\\ca-bundle.crt",
      },
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
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);

      if (code !== 0) {
        console.error(`[Solver] Failed (exit ${code}, ${elapsed}s): ${stderr}`);
        return reject(
          new Error(
            `Solver failed (exit ${code}): ${stderr || stdout || "Unknown error"}`,
          ),
        );
      }

      console.log(`[Solver] Completed in ${elapsed}s`);

      // Read and parse the output JSON the solver wrote
      try {
        if (!fs.existsSync(outputJsonPath)) {
          return reject(
            new Error("Solver ran but did not produce output file"),
          );
        }
        const raw = fs.readFileSync(outputJsonPath, "utf-8");
        const result = JSON.parse(raw);
        resolve(result);
      } catch (err) {
        reject(new Error(`Failed to read solver output: ${err.message}`));
      }
    });

    proc.on("error", (err) => {
      console.error(`[Solver] Spawn error: ${err.message}`);
      if (err.message.includes("EACCES")) {
        reject(
          new Error(
            `Permission denied running solver. Run: chmod +x ${SOLVER_BIN}`,
          ),
        );
      } else {
        reject(new Error(`Could not run solver: ${err.message}`));
      }
    });
  });
}

module.exports = { runSolver };
