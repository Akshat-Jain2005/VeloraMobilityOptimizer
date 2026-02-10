const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:3001/api";

export async function submitOptimization(payload) {
  try {
    const res = await fetch(`${API_BASE}/optimize/json`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const message = await safeError(res);
      throw new Error(message || "Failed to submit optimization request");
    }

    return res.json();
  } catch (error) {
    if (
      error.message.includes("Failed to fetch") ||
      error.name === "TypeError"
    ) {
      throw new Error(
        "Cannot connect to backend server. Make sure the backend is running on http://localhost:3001",
      );
    }
    throw error;
  }
}

export async function getSolution(solutionId) {
  try {
    const res = await fetch(`${API_BASE}/results/${solutionId}`);
    if (!res.ok) {
      const message = await safeError(res);
      throw new Error(message || "Failed to fetch solution status");
    }
    return res.json();
  } catch (error) {
    if (
      error.message.includes("Failed to fetch") ||
      error.name === "TypeError"
    ) {
      throw new Error(
        "Cannot connect to backend server. Make sure the backend is running on http://localhost:3001",
      );
    }
    throw error;
  }
}

async function safeError(res) {
  try {
    const data = await res.json();
    return data?.error?.message || data?.error || data?.message;
  } catch {
    return null;
  }
}
