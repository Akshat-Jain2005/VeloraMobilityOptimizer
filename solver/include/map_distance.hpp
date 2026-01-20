#pragma once
#include <string>

class MapDistance {
public:
    MapDistance(bool allowExternal = false, const std::string &apiKey = "") : allowExternal_(allowExternal), apiKey_(apiKey) {}
    // Returns distance in kilometers
    double distance(double lat1, double lon1, double lat2, double lon2) const;
private:
    bool allowExternal_;
    std::string apiKey_;
    double haversine(double lat1, double lon1, double lat2, double lon2) const;
};
