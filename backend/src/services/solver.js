const { runProcess } = require('../utils/processRunner');
const path = require('path');

const SOLVER_PATH = path.join(__dirname, '../../../build/solver/velora_solver');
const TIMEOUT_MS = 2 * 60 * 1000; // 2 minutes

async function run(inputPath, outputPath) {
  console.log(`Running solver: ${inputPath} -> ${outputPath}`);

  const result = await runProcess(SOLVER_PATH, [inputPath, outputPath], {
    timeout: TIMEOUT_MS,
    cwd: path.join(__dirname, '../../..')
  });

  if (result.exitCode !== 0) {
    throw new Error(`Solver failed with exit code ${result.exitCode}: ${result.stderr}`);
  }

  console.log('Solver completed successfully');
  return result;
}

module.exports = { run };
