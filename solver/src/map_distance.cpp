#include "map_distance.hpp"
#include <cmath>
#include <iostream>
#ifdef USE_CURL
#include <curl/curl.h>
#include <nlohmann/json.hpp>
#endif

static double toRad(double deg) { return deg * M_PI / 180.0; }

double MapDistance::haversine(double lat1, double lon1, double lat2, double lon2) const {
    const double R = 6371.0; // km
    double dLat = toRad(lat2 - lat1);
    double dLon = toRad(lon2 - lon1);
    double a = sin(dLat/2)*sin(dLat/2) + cos(toRad(lat1))*cos(toRad(lat2))*sin(dLon/2)*sin(dLon/2);
    double c = 2 * asin(std::min(1.0, sqrt(a)));
    return R * c;
}

#ifdef USE_CURL
static size_t curlWrite(void* ptr, size_t size, size_t nmemb, void* userdata) {
    std::string* s = static_cast<std::string*>(userdata);
    s->append(static_cast<char*>(ptr), size * nmemb);
    return size * nmemb;
}
#endif

double MapDistance::distance(double lat1, double lon1, double lat2, double lon2) const {
    // Fail-fast mechanism: If API is unstable, switch to Haversine globally
    static bool globalDisableExternal = false;
    
    // CASE 1: External Maps Not Allowed -> Use Pure Haversine (Air Distance)
    if (!allowExternal_) {
        return haversine(lat1, lon1, lat2, lon2);
    }

    // CASE 2: External Maps Allowed
    // If disabled due to previous error or empty key, use Estimated Road Distance (1.4x Air)
    if (globalDisableExternal) {
        return haversine(lat1, lon1, lat2, lon2) * 1.4;
    }
    
    if (apiKey_.empty()) {
        static bool warned = false;
        if (!warned) {
             std::cerr << "[Warning] Maps API Key is empty. Switching to Haversine * 1.4x globally.\n";
             warned = true;
        }
        globalDisableExternal = true;
        return haversine(lat1, lon1, lat2, lon2) * 1.4;
    }

#ifdef USE_CURL
        try {
            CURL* curl = curl_easy_init();
            if (!curl) return haversine(lat1, lon1, lat2, lon2) * 1.4;
            
            std::string url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins=" +
                std::to_string(lat1) + "," + std::to_string(lon1) + "&destinations=" + std::to_string(lat2) + "," + std::to_string(lon2) + "&key=" + apiKey_;
            std::string response;
            curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
            curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, curlWrite);
            curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
            
            // Timeout settings (Added per user request to handle lag)
            curl_easy_setopt(curl, CURLOPT_TIMEOUT_MS, 100L); // 100ms max - AGGRESSIVE FAILFAST
            curl_easy_setopt(curl, CURLOPT_CONNECTTIMEOUT_MS, 100L); // 100ms connect
            
            CURLcode res = curl_easy_perform(curl);
            curl_easy_cleanup(curl);
            
            if (res != CURLE_OK) {
                // If ANY failure occurs, immediately disable external maps globally.
                // This prevents "lag" completely after the first hiccup.
                globalDisableExternal = true;
                std::cerr << "[Warning] External Map API failed (" << curl_easy_strerror(res) << "). Switching to Haversine * 1.4x globally.\n";
                return haversine(lat1, lon1, lat2, lon2) * 1.4;
            }
            
            auto doc = nlohmann::json::parse(response);
            if (doc.contains("rows") && doc["rows"].size() && doc["rows"][0].contains("elements")) {
                auto elem = doc["rows"][0]["elements"][0];
                if (elem.contains("distance") && elem["distance"].contains("value")) {
                    double meters = elem["distance"]["value"].get<double>();
                    return meters / 1000.0;
                }
            }
        } catch (...) {
            // fallthrough to haversine * 1.4
        }
#endif
        // If curl not available or call failed, fallback
        // Apply 1.4x factor to estimate road distance from air distance
        return haversine(lat1, lon1, lat2, lon2) * 1.4;
}
