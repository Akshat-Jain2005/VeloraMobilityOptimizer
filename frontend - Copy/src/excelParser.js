import * as XLSX from "xlsx";

const toNumber = (value, fallback = 0) => {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }
  const num = Number(value);
  return Number.isFinite(num) ? num : fallback;
};

const toString = (value, fallback = "") => {
  if (value === null || value === undefined) {
    return fallback;
  }
  const text = String(value).trim();
  return text || fallback;
};

const timeToMinutes = (value) => {
  if (value instanceof Date) {
    return value.getHours() * 60 + value.getMinutes();
  }

  if (typeof value === "number") {
    if (value > 0 && value < 1) {
      return Math.round(value * 24 * 60);
    }
    return value;
  }

  if (typeof value === "string") {
    const match = value.match(/^(\d{1,2}):(\d{2})/);
    if (match) {
      return Number(match[1]) * 60 + Number(match[2]);
    }
  }

  return 0;
};

const getSharingLimit = (value) => {
  const text = toString(value, "").toLowerCase();
  if (text.includes("single")) return 1;
  if (text.includes("double")) return 2;
  if (text.includes("triple")) return 3;
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : 4;
};

const getVehicleType = (value) => {
  const text = toString(value, "any").toLowerCase();
  return text || "any";
};

const getRows = (workbook, name) => {
  const sheet = workbook.Sheets[name];
  if (!sheet) {
    return [];
  }
  return XLSX.utils.sheet_to_json(sheet, { defval: null });
};

export async function parseExcel(file) {
  const buffer = await file.arrayBuffer();
  const workbook = XLSX.read(buffer, { type: "array" });

  const vehiclesRows = getRows(workbook, "vehicles");
  const employeesRows = getRows(workbook, "employees");
  const requestsRows = getRows(workbook, "requests");
  const metadataRows = getRows(workbook, "metadata");
  const baselineRows = getRows(workbook, "baseline");

  const vehicles = vehiclesRows.map((row, index) => {
    const vehicleType = getVehicleType(
      row.vehicle_type ?? row.type ?? row.Type ?? "any",
    );

    return {
      vehicleId: toString(row.vehicle_id ?? row.vehicleId ?? `V${index}`),
      capacity: toNumber(row.capacity, 4),
      costPerKm: toNumber(row.cost_per_km ?? row.costPerKm, 1),
      startLocation: {
        lat: toNumber(row.current_lat ?? row.startLat ?? row.start_lat, 0),
        lon: toNumber(row.current_lng ?? row.startLon ?? row.start_lon, 0),
      },
      availabilityTime: timeToMinutes(
        row.available_from ?? row.availabilityTime ?? row.availableFrom,
      ),
      speed: toNumber(row.avg_speed_kmph ?? row.speed ?? row.avgSpeedKmph, 30),
      type: vehicleType,
      category: toString(row.category ?? ""),
      fuelType: toString(row.fuel_type ?? row.fuelType ?? ""),
    };
  });

  const requestsSource = employeesRows.length ? employeesRows : requestsRows;
  const requests = requestsSource.map((row, index) => {
    const pickupLat = row.pickup_lat ?? row.pickupLat ?? row.pickup_latitude;
    const pickupLon = row.pickup_lng ?? row.pickupLon ?? row.pickup_longitude;
    const dropLat = row.drop_lat ?? row.dropoffLat ?? row.drop_latitude;
    const dropLon = row.drop_lng ?? row.dropoffLon ?? row.drop_longitude;

    return {
      employeeId: toString(row.employee_id ?? row.employeeId ?? `E${index}`),
      priority: toNumber(row.priority, 3),
      pickup: {
        lat: toNumber(pickupLat, 0),
        lon: toNumber(pickupLon, 0),
      },
      dropoff: {
        lat: toNumber(dropLat, 0),
        lon: toNumber(dropLon, 0),
      },
      earlyTime: timeToMinutes(
        row.earliest_pickup ?? row.earlyTime ?? row.earliestPickup,
      ),
      lateTime: timeToMinutes(
        row.latest_drop ?? row.lateTime ?? row.latestDrop,
      ),
      load: toNumber(row.load ?? row.Load, 1),
      vehiclePreference: getVehicleType(
        row.vehicle_preference ??
          row.vehiclePreference ??
          row.vehiclePreference,
      ),
      sharingLimit: getSharingLimit(
        row.sharing_preference ??
          row.sharingPreference ??
          row.sharingPreference,
      ),
    };
  });

  const metadata = {};
  const maxDelayByPriority = { 1: 5, 2: 10, 3: 15, 4: 20, 5: 30 };

  metadataRows.forEach((row) => {
    const key = toString(row.key ?? row.Key, "");
    const value = row.value ?? row.Value;
    if (!key) return;
    metadata[key] = value;
  });

  for (let i = 1; i <= 5; i += 1) {
    const key = `priority_${i}_max_delay_min`;
    if (metadata[key] !== undefined && metadata[key] !== null) {
      maxDelayByPriority[i] = toNumber(metadata[key], maxDelayByPriority[i]);
    }
  }

  const output = {
    vehicles,
    requests,
    metadata: { maxDelayByPriority },
  };

  if (baselineRows.length) {
    output.baseline = baselineRows;
  }

  return {
    output,
    raw: {
      vehiclesRows: vehiclesRows.length,
      requestsRows: requestsRows.length,
      employeesRows: employeesRows.length,
      metadataRows: metadataRows.length,
      baselineRows: baselineRows.length,
      sheetNames: workbook.SheetNames,
    },
  };
}
