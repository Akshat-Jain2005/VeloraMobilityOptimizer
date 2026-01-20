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
};

struct Vehicle {
    int id;
    int capacity;
    double costPerKm;
    Location startLoc;
    double availabilityTime;
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

bool isValidRoute(const Route& r, const Vehicle& v, const vector<Request>& reqs) {
    int load = 0;
    double currentTime = v.availabilityTime;
    Location currentLoc = v.startLoc;
    for (const auto& stop : r.stops) {
        double travelTime = getDistance(currentLoc, stop.loc);
        currentTime += travelTime;
        if (stop.type == PICKUP) load += reqs[stop.reqId].load;
        else load -= reqs[stop.reqId].load;
        if (load > v.capacity) return false;
        if (stop.type == PICKUP) currentTime = max(currentTime, reqs[stop.reqId].earlyTime);
        else if (currentTime > reqs[stop.reqId].lateTime) return false;
        currentLoc = stop.loc;
    }
    return true;
}

double calculateRouteCost(Route& r, const Vehicle& v, const vector<Request>& reqs) {
    double distCost = 0;
    double penaltyCost = 0;
    double currentTime = v.availabilityTime;
    Location currentLoc = v.startLoc;
    r.totalDist = 0;
    for (auto& stop : r.stops) {
        double dist = getDistance(currentLoc, stop.loc);
        r.totalDist += dist;
        currentTime += dist;
        if (stop.type == PICKUP) currentTime = max(currentTime, reqs[stop.reqId].earlyTime);
        stop.arrivalTime = currentTime;
        currentLoc = stop.loc;
        if (stop.type == DROPOFF) {
            double lateness = max(0.0, currentTime - reqs[stop.reqId].lateTime);
            double priorityWeight = (4.0 - reqs[stop.reqId].priority) * 10.0;
            penaltyCost += lateness * priorityWeight;
        }
    }
    distCost = r.totalDist * v.costPerKm;
    r.totalCost = distCost + penaltyCost;
    return r.totalCost;
}

double getSolutionCost(Solution& sol, const vector<Vehicle>& vehicles, const vector<Request>& reqs) {
    double total = 0;
    for (auto &rt : sol.routes) total += calculateRouteCost(rt, vehicles[rt.vehicleId], reqs);
    total += sol.unassignedReqs.size() * 10000.0;
    sol.globalCost = total;
    return total;
}

Solution constructInitialSolution(const vector<Request>& reqs, const vector<Vehicle>& vehicles) {
    Solution sol;
    sol.routes.resize(vehicles.size());
    for (size_t i=0;i<vehicles.size();++i) sol.routes[i].vehicleId = i;
    vector<int> idx(reqs.size()); iota(idx.begin(), idx.end(), 0);
    sort(idx.begin(), idx.end(), [&](int a,int b){ if (reqs[a].priority!=reqs[b].priority) return reqs[a].priority < reqs[b].priority; return reqs[a].lateTime < reqs[b].lateTime; });
    for (int rId : idx) {
        double bestIncrease = numeric_limits<double>::max();
        int bestV = -1;
        for (int v=0; v<vehicles.size(); ++v) {
            Route trial = sol.routes[v];
            Stop pu{rId, PICKUP, reqs[rId].pickup};
            Stop dof{rId, DROPOFF, reqs[rId].dropoff};
            trial.stops.push_back(pu); trial.stops.push_back(dof);
            if (!isValidRoute(trial, vehicles[v], reqs)) continue;
            double oldC = sol.routes[v].totalCost;
            double newC = calculateRouteCost(trial, vehicles[v], reqs);
            double inc = newC - oldC;
            if (inc < bestIncrease) { bestIncrease = inc; bestV = v; }
        }
        if (bestV>=0) { Stop pu{rId,PICKUP,reqs[rId].pickup}; Stop dof{rId,DROPOFF,reqs[rId].dropoff}; sol.routes[bestV].stops.push_back(pu); sol.routes[bestV].stops.push_back(dof); calculateRouteCost(sol.routes[bestV], vehicles[bestV], reqs); }
        else sol.unassignedReqs.push_back(rId);
    }
    getSolutionCost(sol, vehicles, reqs);
    return sol;
}

Solution simulatedAnnealing(Solution currentSol, const vector<Request>& reqs, const vector<Vehicle>& vehicles) {
    Solution bestSol = currentSol;
    double currentCost = currentSol.globalCost;
    double bestCost = currentCost;
    double temp = 1000.0, cooling=0.995;
    random_device rd; mt19937 gen(rd());
    for (int iter=0; iter<2000; ++iter) {
        Solution neigh = currentSol;
        vector<int> nonEmpty;
        for (int i=0;i<neigh.routes.size();++i) if (!neigh.routes[i].stops.empty()) nonEmpty.push_back(i);
        if (nonEmpty.empty()) break;
        uniform_int_distribution<> rdist(0, nonEmpty.size()-1);
        int svid = nonEmpty[rdist(gen)];
        if (neigh.routes[svid].stops.empty()) continue;
        uniform_int_distribution<> sstop(0, neigh.routes[svid].stops.size()-1);
        int stopIdx = sstop(gen); int reqToMove = neigh.routes[svid].stops[stopIdx].reqId;
        auto &sStops = neigh.routes[svid].stops;
        sStops.erase(remove_if(sStops.begin(), sStops.end(), [&](const Stop& s){ return s.reqId==reqToMove; }), sStops.end());
        uniform_int_distribution<> tv(0, vehicles.size()-1);
        int tvId = tv(gen);
        Stop pu{reqToMove,PICKUP,reqs[reqToMove].pickup}; Stop dof{reqToMove,DROPOFF,reqs[reqToMove].dropoff};
        neigh.routes[tvId].stops.push_back(pu); neigh.routes[tvId].stops.push_back(dof);
        if (!isValidRoute(neigh.routes[tvId], vehicles[tvId], reqs)) continue;
        calculateRouteCost(neigh.routes[svid], vehicles[svid], reqs);
        calculateRouteCost(neigh.routes[tvId], vehicles[tvId], reqs);
        double neighCost = getSolutionCost(neigh, vehicles, reqs);
        double delta = neighCost - currentCost;
        bool accept = false;
        if (delta < 0) accept = true; else { uniform_real_distribution<> p(0,1); if (p(gen) < exp(-delta/temp)) accept = true; }
        if (accept) { currentSol = neigh; currentCost = neighCost; if (currentCost < bestCost) { bestSol = currentSol; bestCost = currentCost; } }
        temp *= cooling;
    }
    return bestSol;
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
    }
    
    MapDistance mapDist(allowExternal, mapsKey);
    gMapDist = &mapDist;

    // Parse requests
    vector<Request> requests;
    for (auto &jr : j["requests"]) {
        Request r;
        r.id = jr.value("id", -1);
        r.priority = jr.value("priority", 3);
        r.earlyTime = jr.value("earlyTime", 0.0);
        r.lateTime = jr.value("lateTime", 1e6);
        r.load = jr.value("load", 1);
        r.pickup.lat = jr["pickup"].value("lat", 0.0);
        r.pickup.lon = jr["pickup"].value("lon", 0.0);
        r.dropoff.lat = jr["dropoff"].value("lat", 0.0);
        r.dropoff.lon = jr["dropoff"].value("lon", 0.0);
        requests.push_back(r);
    }

    vector<Vehicle> vehicles;
    for (auto &jv : j["vehicles"]) {
        Vehicle v; v.id = jv.value("id", 0); v.capacity = jv.value("capacity", 4); v.costPerKm = jv.value("costPerKm", 1.0);
        v.startLoc.lat = jv["startLoc"].value("lat", 0.0); v.startLoc.lon = jv["startLoc"].value("lon", 0.0);
        v.availabilityTime = jv.value("availabilityTime", 0.0);
        vehicles.push_back(v);
    }

    cout << "Running greedy constructive heuristic...\n";
    Solution init = constructInitialSolution(requests, vehicles);
    cout << "Initial cost: "<< init.globalCost <<"\n";
    cout << "Running simulated annealing...\n";
    Solution finalSol = simulatedAnnealing(init, requests, vehicles);
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