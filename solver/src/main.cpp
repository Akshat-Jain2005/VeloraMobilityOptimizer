// Simple solver that reads input JSON, performs a greedy constructive heuristic
// and a lightweight simulated annealing, and prints JSON output.

#include <iostream>
#include <vector>
#include <cmath>
#include <algorithm>
#include <limits>
#include <random>
#include <iomanip>
#include <fstream>
#include <string>
#include <numeric>
#include <unordered_set>

#include <nlohmann/json.hpp>

#include "map_distance.hpp"

using json = nlohmann::json;
using namespace std;

struct Location { double lat, lon; };
enum StopType { PICKUP, DROPOFF };

struct Request {
    int id;
    int priority;
    Location pickup;
    Location dropoff;
    double earlyTime;
    double lateTime;
    int load;
    string vehiclePreference;
    int sharingLimit;
};

struct Vehicle {
    int id;
    int capacity;
    double costPerKm;
    Location startLoc;
    double availabilityTime;
    string type;
};

struct Stop {
    int reqId;
    StopType type;
    Location loc;
    double arrivalTime{0};
    double departureTime{0};
};

struct Route {
    int vehicleId{-1};
    vector<Stop> stops;
    double totalDist{0};
    double totalCost{0};
};

struct Solution {
    vector<Route> routes;
    vector<int> unassignedReqs;
    double globalCost{0};
};

// Global distance provider pointer (set in main)
static MapDistance* gMapDist = nullptr;

double getDistance(const Location& a, const Location& b) {
    if (gMapDist) return gMapDist->distance(a.lat, a.lon, b.lat, b.lon);
    // fallback (shouldn't happen)
    const double R = 6371.0;
    double lat1 = a.lat * M_PI / 180.0;
    double lat2 = b.lat * M_PI / 180.0;
    double dLat = (b.lat - a.lat) * M_PI / 180.0;
    double dLon = (b.lon - a.lon) * M_PI / 180.0;
    double s = sin(dLat/2)*sin(dLat/2) + cos(lat1)*cos(lat2)*sin(dLon/2)*sin(dLon/2);
    double c = 2*asin(sqrt(s));
    return R * c;
}


// Context for tolerances and weights
struct SolutionContext {
    std::unordered_map<int, double> maxDelayMap; // priority -> max delay mins
    double wCost{0.7};
    double wTime{0.3};
} gCtx;

static int clampPriority(int p) {
    if (p < 1) return 1;
    if (p > 5) return 5;
    return p;
}

static double priorityWeight(int priority) {
    // Standard delay penalty if needed
    int p = clampPriority(priority);
    return (6 - p) * 10.0;
}


// Revised Constraints & Cost Function
bool isValidRoute(const Route& r, const Vehicle& v, const vector<Request>& reqs, bool checkDelay = true) {
    int load = 0;
    double currentTime = v.availabilityTime;
    Location currentLoc = v.startLoc;

    vector<int> activeReqs;

    for (const auto& stop : r.stops) {
        double travelTime = getDistance(currentLoc, stop.loc);
        currentTime += travelTime; // Updates arrival time at stop
        
        // Update load and active list
        if (stop.type == PICKUP) {
            load += reqs[stop.reqId].load;
            activeReqs.push_back(stop.reqId);
        } else {
            load -= reqs[stop.reqId].load;
            auto it = find(activeReqs.begin(), activeReqs.end(), stop.reqId);
            if (it != activeReqs.end()) activeReqs.erase(it);
        }

        // 1. Capacity Checks are HARD
        if (load > v.capacity) return false;
        
        // 4. Time Windows
        if (stop.type == PICKUP) {
            currentTime = max(currentTime, reqs[stop.reqId].earlyTime);
        } else {
            // Dropoff
            // HARD CONSTRAINT: Cannot exceed Max Delay (Unless checkDelay is false)
            if (checkDelay) {
                double maxDelay = 30.0; // default
                if (gCtx.maxDelayMap.count(reqs[stop.reqId].priority)) {
                    maxDelay = gCtx.maxDelayMap[reqs[stop.reqId].priority];
                }
                // If arrival > lateTime + maxDelay, route is INVALID
                if (currentTime > reqs[stop.reqId].lateTime + maxDelay) {
                    return false;
                }
            }
        }
        currentLoc = stop.loc;
    }
    return true;
}

double calculateRouteCost(Route& r, const Vehicle& v, const vector<Request>& reqs, bool allowLate) {
    double totalDist = 0;
    double totalTravelTime = 0; // simple sum of travel times
    double penaltyCost = 0;

    double currentTime = v.availabilityTime;
    Location currentLoc = v.startLoc;
    
    int load = 0; 
    vector<int> activeReqs;

    r.totalDist = 0;
    
    double routeStartTime = currentTime;

    for (auto& stop : r.stops) {
        double dist = getDistance(currentLoc, stop.loc);
        double travel = dist; // Assume 1km = 1min implies speed 60km/h? 
                              // Text says dist in km. Speed is unknown. 
                              // Metadata implies haversine (km).
                              // If using map API, we'd get time.
                              // Assuming avg speed 30km/h for city? 2 min per km?
                              // Or just use distance as proxy for time if no speed given.
                              // WhatsApp: "allow_external_maps only for dist/time... otherwise haversine"
                              // If haversine, we usually assume 1 unit dist = 1 unit cost.
                              // Let's assume Time = Dist for now unless speed provided.
                              
        r.totalDist += dist;
        currentTime += travel;
        
        // Update load for checking sharing constraints
        if (stop.type == PICKUP) {
            load += reqs[stop.reqId].load;
            activeReqs.push_back(stop.reqId);
            currentTime = max(currentTime, reqs[stop.reqId].earlyTime);
        } else {
            load -= reqs[stop.reqId].load;
            auto it = find(activeReqs.begin(), activeReqs.end(), stop.reqId);
            if (it != activeReqs.end()) activeReqs.erase(it);
        }
    
        stop.arrivalTime = currentTime;
        currentLoc = stop.loc;
        
        // Sharing Limit Penalty
        for (int activeId : activeReqs) {
            if (load > reqs[activeId].sharingLimit) {
                penaltyCost += 5000.0; // Significant penalty per violation per stop
            }
        }
        
        // Vehicle Preference Penalty
        if (stop.type == PICKUP) {
            const auto& req = reqs[stop.reqId];
            if (req.vehiclePreference != "any" && !v.type.empty() && v.type != "any" && req.vehiclePreference != v.type) {
                penaltyCost += 5000.0;
            }
        }

        if (stop.type == DROPOFF) {
            // Lateness penalty (soft window violation)
            double lateness = max(0.0, currentTime - reqs[stop.reqId].lateTime);
            if (lateness > 0.0) {
                 penaltyCost += lateness * priorityWeight(reqs[stop.reqId].priority);
                 
                 // Check Max Delay violation for Forced Assignments
                 double maxDelay = 30.0;
                 if (gCtx.maxDelayMap.count(reqs[stop.reqId].priority)) {
                    maxDelay = gCtx.maxDelayMap[reqs[stop.reqId].priority];
                 }
                 if (lateness > maxDelay) {
                     // MASSIVE PENALTY to flag this as a "Forced but Infeasible" assignment
                     penaltyCost += 1000000.0 + (lateness - maxDelay) * 1000.0;
                 }
            }
        }
    }
    
    // Objective Function: 
    // Cost = (TotalDist * CostPerKm * 0.7) + (TotalDist * 0.3) + Penalties
    // Assuming Time Approx = Dist (1 min/km? 30km/h = 0.5km/min -> 2 min/km. Let's use 1.0)
    
    double moneyCost = r.totalDist * v.costPerKm;
    double timeCost = r.totalDist; // Proxy if no speed given
    
    // Note: Weights are 0.7 for cost, 0.3 for time
    r.totalCost = (moneyCost * gCtx.wCost) + (timeCost * gCtx.wTime) + penaltyCost;
    return r.totalCost;
}

double getSolutionCost(Solution& sol, const vector<Vehicle>& vehicles, const vector<Request>& reqs, bool allowLate) {
    double total = 0;
    for (auto &rt : sol.routes) total += calculateRouteCost(rt, vehicles[rt.vehicleId], reqs, allowLate);
    total += sol.unassignedReqs.size() * 10000.0;
    sol.globalCost = total;
    return total;
}

struct InsertResult {
    bool feasible{false};
    double newCost{0};
    Route newRoute;
};

static InsertResult bestInsertion(const Route& route, int reqId, const Vehicle& v, const vector<Request>& reqs, bool checkDelay) {
    InsertResult best;
    best.newCost = numeric_limits<double>::max();
    int n = static_cast<int>(route.stops.size());
    for (int p = 0; p <= n; ++p) {
        for (int d = p + 1; d <= n + 1; ++d) {
            Route trial = route;
            Stop pu{reqId, PICKUP, reqs[reqId].pickup};
            Stop dof{reqId, DROPOFF, reqs[reqId].dropoff};
            trial.stops.insert(trial.stops.begin() + p, pu);
            trial.stops.insert(trial.stops.begin() + d, dof);
            
            if (!isValidRoute(trial, v, reqs, checkDelay)) continue;
            
            double cost = calculateRouteCost(trial, v, reqs, true);
            if (cost < best.newCost) {
                best.feasible = true;
                best.newCost = cost;
                best.newRoute = std::move(trial);
            }
        }
    }
    return best;
}

static void removeRequestFromRoute(Route& r, int reqId) {
    r.stops.erase(remove_if(r.stops.begin(), r.stops.end(), [&](const Stop& s){ return s.reqId == reqId; }), r.stops.end());
}

static vector<int> uniqueReqsInRoute(const Route& r) {
    unordered_set<int> seen;
    vector<int> out;
    for (const auto& s : r.stops) {
        if (seen.insert(s.reqId).second) out.push_back(s.reqId);
    }
    return out;
}

Solution constructInitialSolution(const vector<Request>& reqs, const vector<Vehicle>& vehicles, bool allowLate, mt19937& gen) {
    Solution sol;
    sol.routes.resize(vehicles.size());
    for (size_t i=0;i<vehicles.size();++i) sol.routes[i].vehicleId = i;
    vector<int> idx(reqs.size()); iota(idx.begin(), idx.end(), 0);
    sort(idx.begin(), idx.end(), [&](int a,int b){
        if (reqs[a].priority!=reqs[b].priority) return reqs[a].priority < reqs[b].priority;
        return reqs[a].lateTime < reqs[b].lateTime;
    });
    // Small randomization within same priority bucket
    for (size_t i = 0; i < idx.size();) {
        size_t j = i + 1;
        while (j < idx.size() && reqs[idx[j]].priority == reqs[idx[i]].priority) ++j;
        shuffle(idx.begin() + i, idx.begin() + j, gen);
        i = j;
    }

    for (int rId : idx) {
        double bestIncrease = numeric_limits<double>::max();
        int bestV = -1;
        Route bestRoute;
        
        // 1. Try Normal Insertion (Strict Delay Check)
        for (int v=0; v<vehicles.size(); ++v) {
            auto ins = bestInsertion(sol.routes[v], rId, vehicles[v], reqs, true);
            if (!ins.feasible) continue;
            double oldC = sol.routes[v].totalCost;
            double inc = ins.newCost - oldC;
            if (inc < bestIncrease) {
                bestIncrease = inc;
                bestV = v;
                bestRoute = std::move(ins.newRoute);
            }
        }
        
        // 2. If Failed, Try Forced Insertion (Relax Delay Check) - "Employee must go"
        if (bestV < 0) {
             for (int v=0; v<vehicles.size(); ++v) {
                // Pass checkDelay = false
                auto ins = bestInsertion(sol.routes[v], rId, vehicles[v], reqs, false);
                if (!ins.feasible) continue; // Might still fail on Capacity
                double oldC = sol.routes[v].totalCost;
                double inc = ins.newCost - oldC;
                if (inc < bestIncrease) {
                    bestIncrease = inc;
                    bestV = v;
                    bestRoute = std::move(ins.newRoute);
                }
            }
        }

        if (bestV>=0) {
            sol.routes[bestV] = std::move(bestRoute);
            calculateRouteCost(sol.routes[bestV], vehicles[bestV], reqs, allowLate);
        } else {
            sol.unassignedReqs.push_back(rId);
        }
    }
    getSolutionCost(sol, vehicles, reqs, allowLate);
    return sol;
}

static Solution getNeighbor(const Solution& current, const vector<Request>& reqs, const vector<Vehicle>& vehicles, bool allowLate, mt19937& gen) {
    Solution neighbor = current; // Deep copy
    
    // 1. Pick a route that has requests
    vector<int> activeRoutes;
    for(size_t i=0; i<neighbor.routes.size(); ++i) {
        if(!neighbor.routes[i].stops.empty()) activeRoutes.push_back(i);
    }
    if(activeRoutes.empty()) return current;

    uniform_int_distribution<> dRoute(0, (int)activeRoutes.size()-1);
    int sourceV = activeRoutes[dRoute(gen)];
    
    // 2. Pick a request in that route
    vector<int> rIds = uniqueReqsInRoute(neighbor.routes[sourceV]);
    if(rIds.empty()) return current;
    uniform_int_distribution<> dReq(0, (int)rIds.size()-1);
    int reqId = rIds[dReq(gen)];

    // 3. Remove from source
    removeRequestFromRoute(neighbor.routes[sourceV], reqId);
    // If strict validity fails here, we continue anyway (maybe it was already invalid)
    calculateRouteCost(neighbor.routes[sourceV], vehicles[sourceV], reqs, allowLate); 

    // 4. Insert into random target route (could be same)
    uniform_int_distribution<> dTarget(0, (int)vehicles.size()-1);
    int targetV = dTarget(gen);

    // Try normal insertion first
    auto res = bestInsertion(neighbor.routes[targetV], reqId, vehicles[targetV], reqs, true);
    
    if (!res.feasible) {
        // Try forced insertion if strict fails
        res = bestInsertion(neighbor.routes[targetV], reqId, vehicles[targetV], reqs, false);
    }

    if (!res.feasible) {
        // If still infeasible, invalid move
        return current; 
    }

    neighbor.routes[targetV] = std::move(res.newRoute);
    calculateRouteCost(neighbor.routes[targetV], vehicles[targetV], reqs, allowLate);

    // Update global cost
    getSolutionCost(neighbor, vehicles, reqs, allowLate);
    
    return neighbor;
}

static Solution improveSolution(const Solution& initSol, const vector<Request>& reqs, const vector<Vehicle>& vehicles, bool allowLate) {
    mt19937 gen(12345);
    Solution current = initSol;
    Solution best = initSol;
    
    double T = 200.0;
    double alpha = 0.99;
    double minT = 0.1;
    int maxIter = 5000; 

    for (int i = 0; i < maxIter && T > minT; ++i) {
        Solution next = getNeighbor(current, reqs, vehicles, allowLate, gen);
        
        // If move failed (returned current), skip
        if (abs(next.globalCost - current.globalCost) < 1e-6) {
           continue;
        }

        double delta = next.globalCost - current.globalCost;
        
        bool accept = false;
        if (delta < 0) {
            accept = true;
        } else {
            uniform_real_distribution<> prob(0.0, 1.0);
            if (prob(gen) < exp(-delta / T)) {
                accept = true;
            }
        }

        if (accept) {
            current = std::move(next);
            if (current.globalCost < best.globalCost) {
                best = current;
            }
        }
        T *= alpha;
    }
    return best;
}

int main(int argc, char** argv) {
    string inputPath = (argc>1? argv[1] : "input.json");
    string outputPath = (argc>2? argv[2] : "solution.json");
    // Read input JSON
    ifstream in(inputPath);
    if (!in.is_open()) { cerr<<"Failed to open "<<inputPath<<"\n"; return 1; }
    json j; in >> j; in.close();

    // Config
    bool allowExternal = false; string mapsKey;
    if (j.contains("config")) { 
        allowExternal = j["config"].value("allow_external_maps", false); 
        mapsKey = j["config"].value("maps_api_key", ""); 
        
        // Load Weights
        if (j["config"].contains("weights")) {
            gCtx.wCost = j["config"]["weights"].value("cost", 0.7);
            gCtx.wTime = j["config"]["weights"].value("time", 0.3);
        }
        
        // Load Tolerances
        if (j["config"].contains("tolerances")) {
            auto& tols = j["config"]["tolerances"];
            for (auto it = tols.begin(); it != tols.end(); ++it) {
                try {
                    int p = stoi(it.key());
                    double val = it.value();
                    gCtx.maxDelayMap[p] = val;
                } catch(...) {}
            }
        }
    }
    // Always allow late (soft constraint) but use stricter penalties/checks inside
    bool allowLate = true; 
    
    MapDistance mapDist(allowExternal, mapsKey);
    gMapDist = &mapDist;

    // Parse requests
    vector<Request> requests;
    for (auto &jr : j["requests"]) {
        Request r;
        r.id = jr.value("id", -1);
        r.priority = clampPriority(jr.value("priority", 3));
        r.earlyTime = jr.value("earlyTime", 0.0);
        r.lateTime = jr.value("lateTime", 1e6);
        r.load = jr.value("load", 1);
        r.pickup.lat = jr["pickup"].value("lat", 0.0);
        r.pickup.lon = jr["pickup"].value("lon", 0.0);
        r.dropoff.lat = jr["dropoff"].value("lat", 0.0);
        r.dropoff.lon = jr["dropoff"].value("lon", 0.0);
        r.vehiclePreference = jr.value("vehiclePreference", "any");
        r.sharingLimit = jr.value("sharingLimit", 100);
        requests.push_back(r);
    }

    vector<Vehicle> vehicles;
    for (auto &jv : j["vehicles"]) {
        Vehicle v; v.id = jv.value("id", 0); v.capacity = jv.value("capacity", 4); v.costPerKm = jv.value("costPerKm", 1.0);
        v.startLoc.lat = jv["startLoc"].value("lat", 0.0); v.startLoc.lon = jv["startLoc"].value("lon", 0.0);
        v.availabilityTime = jv.value("availabilityTime", 0.0);
        v.type = jv.value("type", "any");
        vehicles.push_back(v);
    }

    cout << "Running greedy constructive heuristic...\n";
    random_device rd; mt19937 gen(rd());
    Solution bestInit;
    double bestInitCost = numeric_limits<double>::max();
    for (int seed = 0; seed < 5; ++seed) {
        Solution init = constructInitialSolution(requests, vehicles, allowLate, gen);
        if (init.globalCost < bestInitCost) {
            bestInit = std::move(init);
            bestInitCost = bestInit.globalCost;
        }
    }
    cout << "Initial cost: "<< bestInit.globalCost <<"\n";
    cout << "Running local search improvements...\n";
    Solution finalSol = improveSolution(bestInit, requests, vehicles, allowLate);
    cout << "Final cost: "<< finalSol.globalCost <<"\n";

    // Serialize to JSON
    json out;
    out["globalCost"] = finalSol.globalCost;
    out["unassigned"] = finalSol.unassignedReqs;
    out["routes"] = json::array();
    for (auto &rt : finalSol.routes) {
        json jr; jr["vehicleId"] = rt.vehicleId; jr["totalDist"] = rt.totalDist; jr["totalCost"] = rt.totalCost; jr["stops"] = json::array();
        for (auto &s : rt.stops) {
            jr["stops"].push_back({{"reqId", s.reqId}, {"type", s.type==PICKUP?"P":"D"}, {"lat", s.loc.lat}, {"lon", s.loc.lon}, {"arrival", s.arrivalTime}});
        }
        out["routes"].push_back(jr);
    }
    ofstream fo(outputPath); fo<<setw(2)<<out<<"\n"; fo.close();
    cout<<"Solution written to "<<outputPath<<"\n";
    return 0;
}