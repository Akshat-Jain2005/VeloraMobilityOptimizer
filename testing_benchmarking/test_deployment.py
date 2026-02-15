#!/usr/bin/env python3
"""
Velora Mobility Optimizer - Deployment Health & Integration Tests
==================================================================

Tests for:
1. Frontend health & accessibility
2. Backend health & API endpoints
3. CORS configuration
4. Full optimization pipeline
5. Map API (OSRM/OpenRouteService) connectivity

Usage:
    python test_deployment.py                    # Run all tests
    python test_deployment.py --verbose          # Verbose output
    python test_deployment.py --env production   # Test production (default)
    python test_deployment.py --env local        # Test local development
"""

import argparse
import json
import sys
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urljoin
import ssl

# ============================================================================
# Configuration
# ============================================================================

ENVIRONMENTS = {
    "production": {
        "frontend_url": "https://velora-jext.onrender.com",
        "backend_url": "https://veloramobilityoptimizer.onrender.com",
        "api_base": "https://veloramobilityoptimizer.onrender.com/api",
    },
    "local": {
        "frontend_url": "http://localhost:5173",
        "backend_url": "http://localhost:3001",
        "api_base": "http://localhost:3001/api",
    },
}

# ============================================================================
# Test Results
# ============================================================================

@dataclass
class TestResult:
    name: str
    passed: bool
    message: str
    duration_ms: float
    details: Optional[Dict[str, Any]] = None


class TestRunner:
    def __init__(self, env: str = "production", verbose: bool = False):
        self.env = env
        self.config = ENVIRONMENTS[env]
        self.verbose = verbose
        self.results: List[TestResult] = []
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE

    def log(self, msg: str):
        if self.verbose:
            print(f"  {msg}")

    def request(self, url: str, method: str = "GET", data: Optional[dict] = None, 
                headers: Optional[dict] = None, timeout: int = 30) -> tuple:
        """Make HTTP request and return (status_code, response_body, headers)"""
        req_headers = {"User-Agent": "VeloraTestRunner/1.0"}
        if headers:
            req_headers.update(headers)
        
        body = None
        if data:
            body = json.dumps(data).encode("utf-8")
            req_headers["Content-Type"] = "application/json"

        req = Request(url, data=body, headers=req_headers, method=method)
        
        try:
            with urlopen(req, timeout=timeout, context=self.ctx) as resp:
                return resp.status, resp.read().decode("utf-8"), dict(resp.headers)
        except HTTPError as e:
            return e.code, e.read().decode("utf-8") if e.fp else "", {}
        except URLError as e:
            raise ConnectionError(f"Failed to connect: {e.reason}")

    def run_test(self, name: str, test_func):
        """Execute a test and record the result"""
        start = time.time()
        try:
            passed, message, details = test_func()
            duration = (time.time() - start) * 1000
            result = TestResult(name, passed, message, duration, details)
        except Exception as e:
            duration = (time.time() - start) * 1000
            result = TestResult(name, False, f"Exception: {str(e)}", duration)
        
        self.results.append(result)
        status = "✅" if result.passed else "❌"
        print(f"{status} {result.name} ({result.duration_ms:.0f}ms)")
        if not result.passed:
            print(f"   └─ {result.message}")
        elif self.verbose and result.details:
            for key, value in result.details.items():
                print(f"   └─ {key}: {value}")
        
        return result

    # ========================================================================
    # Frontend Tests
    # ========================================================================

    def test_frontend_accessible(self):
        """Test if frontend is accessible and returns HTML"""
        url = self.config["frontend_url"]
        self.log(f"GET {url}")
        
        status, body, _ = self.request(url)
        
        if status != 200:
            return False, f"HTTP {status}", None
        
        if "<!doctype html>" not in body.lower() and "<html" not in body.lower():
            return False, "Response is not HTML", None
        
        has_react = "react" in body.lower() or "vite" in body.lower() or "_app" in body.lower()
        has_title = "velora" in body.lower()
        
        return True, "Frontend serving HTML", {
            "has_react_markers": has_react,
            "has_velora_title": has_title
        }

    def test_frontend_assets(self):
        """Test if frontend static assets are accessible"""
        base_url = self.config["frontend_url"]
        
        # First get the index.html to find asset paths
        status, body, _ = self.request(base_url)
        if status != 200:
            return False, "Cannot access frontend", None
        
        # Look for JS/CSS assets
        import re
        js_matches = re.findall(r'src="(/assets/[^"]+\.js)"', body)
        css_matches = re.findall(r'href="(/assets/[^"]+\.css)"', body)
        
        if not js_matches and not css_matches:
            return True, "No bundled assets found (may be inline)", {"note": "Check if using inline bundles"}
        
        # Test first JS asset if found
        if js_matches:
            asset_url = urljoin(base_url, js_matches[0])
            self.log(f"GET {asset_url}")
            status, _, _ = self.request(asset_url)
            if status != 200:
                return False, f"JS asset returned HTTP {status}", None
        
        return True, "Static assets accessible", {
            "js_assets": len(js_matches),
            "css_assets": len(css_matches)
        }

    # ========================================================================
    # Backend Tests
    # ========================================================================

    def test_backend_health(self):
        """Test backend health endpoint"""
        url = f"{self.config['api_base']}/health"
        self.log(f"GET {url}")
        
        status, body, _ = self.request(url)
        
        if status != 200:
            return False, f"HTTP {status}", None
        
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return False, "Invalid JSON response", None
        
        if data.get("status") != "ok":
            return False, f"Status: {data.get('status')}", data
        
        solver_found = data.get("solver") == "found"
        parser_found = data.get("parser") == "found"
        
        if not solver_found:
            return False, "Solver binary not found", data
        if not parser_found:
            return False, "Parser script not found", data
        
        return True, "Backend healthy", {
            "solver": data.get("solver"),
            "parser": data.get("parser"),
            "timestamp": data.get("timestamp")
        }

    def test_backend_root(self):
        """Test backend root endpoint returns API info"""
        url = self.config["backend_url"]
        self.log(f"GET {url}")
        
        status, body, _ = self.request(url)
        
        if status != 200:
            return False, f"HTTP {status}", None
        
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return False, "Invalid JSON response", None
        
        if "endpoints" not in data:
            return False, "Missing endpoints info", None
        
        return True, "API info available", {
            "endpoints": list(data.get("endpoints", {}).keys())
        }

    # ========================================================================
    # CORS Tests
    # ========================================================================

    def test_cors_preflight(self):
        """Test CORS preflight request from frontend origin"""
        url = f"{self.config['api_base']}/optimize/json"
        frontend_origin = self.config["frontend_url"]
        
        self.log(f"OPTIONS {url}")
        self.log(f"Origin: {frontend_origin}")
        
        headers = {
            "Origin": frontend_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        try:
            status, _, resp_headers = self.request(url, method="OPTIONS", headers=headers)
        except ConnectionError as e:
            return False, str(e), None
        
        # Check CORS headers
        allow_origin = resp_headers.get("Access-Control-Allow-Origin", "")
        allow_methods = resp_headers.get("Access-Control-Allow-Methods", "")
        
        # Handle case variations
        for key in resp_headers:
            if key.lower() == "access-control-allow-origin":
                allow_origin = resp_headers[key]
            if key.lower() == "access-control-allow-methods":
                allow_methods = resp_headers[key]
        
        if not allow_origin:
            return False, "Missing Access-Control-Allow-Origin header", None
        
        # Check exact match (no trailing slash)
        if allow_origin != frontend_origin and allow_origin != "*":
            return False, f"CORS origin mismatch: got '{allow_origin}', expected '{frontend_origin}'", {
                "received_origin": allow_origin,
                "expected_origin": frontend_origin
            }
        
        return True, "CORS configured correctly", {
            "allow_origin": allow_origin,
            "allow_methods": allow_methods
        }

    # ========================================================================
    # Pipeline Tests
    # ========================================================================

    def test_optimization_pipeline(self):
        """Test full optimization pipeline with minimal input"""
        url = f"{self.config['api_base']}/optimize/json"
        self.log(f"POST {url}")
        
        # Minimal valid input
        payload = {
            "config": {
                "allow_external_maps": False,
                "tolerances": {"1": 5, "2": 10, "3": 15},
                "weights": {"cost": 0.7, "time": 0.3}
            },
            "vehicles": [
                {
                    "id": 0,
                    "vehicle_id": "V01",
                    "capacity": 4,
                    "costPerKm": 10.0,
                    "avg_speed_kmph": 30.0,
                    "startLoc": {"lat": 12.9716, "lon": 77.5946},
                    "availabilityTime": 480
                }
            ],
            "requests": [
                {
                    "id": 0,
                    "employee_id": "E001",
                    "pickup": {"lat": 12.9800, "lon": 77.6000},
                    "dropoff": {"lat": 12.9716, "lon": 77.5946},
                    "priority": 2,
                    "earlyTime": 0,
                    "lateTime": 60
                }
            ]
        }
        
        try:
            status, body, _ = self.request(url, method="POST", data=payload, timeout=60)
        except ConnectionError as e:
            return False, f"Connection failed: {e}", None
        
        if status != 200:
            return False, f"HTTP {status}: {body[:200]}", None
        
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return False, "Invalid JSON response", {"body": body[:500]}
        
        # Check for error response
        if "error" in data:
            return False, f"API error: {data.get('error')}", data
        
        # Check for success indicators
        if data.get("status") != "success":
            return False, f"Status: {data.get('status')}", data
        
        result = data.get("result", {})
        routes = result.get("routes", [])
        summary = result.get("summary", {})
        
        return True, "Pipeline executed successfully", {
            "routes_count": len(routes),
            "vehicles_used": summary.get("vehiclesUsed", 0),
            "unassigned": summary.get("unassignedCount", 0),
            "distance_method": summary.get("distanceMethod", {}).get("fallbackUsed", "unknown")
        }

    def test_validation_error_handling(self):
        """Test that invalid input returns proper validation errors"""
        url = f"{self.config['api_base']}/optimize/json"
        self.log(f"POST {url} (with invalid data)")
        
        # Invalid input - missing required fields
        payload = {
            "vehicles": [],
            "requests": []
        }
        
        status, body, _ = self.request(url, method="POST", data=payload)
        
        if status != 400:
            return False, f"Expected HTTP 400, got {status}", None
        
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return False, "Invalid JSON error response", None
        
        if "error" not in data:
            return False, "Missing error field in response", data
        
        return True, "Validation errors handled correctly", {
            "error_type": data.get("error"),
            "details_count": len(data.get("details", []))
        }

    # ========================================================================
    # Map API Tests
    # ========================================================================

    def test_map_api_status(self):
        """Test optimization with external maps enabled to check API status"""
        url = f"{self.config['api_base']}/optimize/json"
        self.log(f"POST {url} (with external maps)")
        
        # Input with external maps enabled (but no API key - will use fallback)
        payload = {
            "config": {
                "allow_external_maps": True,
                "maps_api_key": "",  # Empty key - should fallback gracefully
                "map_timeout_ms": 3000,
                "tolerances": {"1": 5, "2": 10, "3": 15},
                "weights": {"cost": 0.7, "time": 0.3}
            },
            "vehicles": [
                {
                    "id": 0,
                    "vehicle_id": "V01",
                    "capacity": 4,
                    "costPerKm": 10.0,
                    "avg_speed_kmph": 30.0,
                    "startLoc": {"lat": 12.9716, "lon": 77.5946},
                    "availabilityTime": 480
                }
            ],
            "requests": [
                {
                    "id": 0,
                    "employee_id": "E001",
                    "pickup": {"lat": 12.9800, "lon": 77.6000},
                    "dropoff": {"lat": 12.9716, "lon": 77.5946},
                    "priority": 2,
                    "earlyTime": 0,
                    "lateTime": 60
                }
            ]
        }
        
        try:
            status, body, _ = self.request(url, method="POST", data=payload, timeout=90)
        except ConnectionError as e:
            return False, f"Connection failed: {e}", None
        
        if status != 200:
            return False, f"HTTP {status}", None
        
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return False, "Invalid JSON response", None
        
        summary = data.get("result", {}).get("summary", {})
        distance_method = summary.get("distanceMethod", {})
        
        api_calls = distance_method.get("apiCalls", 0)
        api_success = distance_method.get("apiSuccess", 0)
        fallback_used = distance_method.get("fallbackUsed", True)
        provider = distance_method.get("provider", "unknown")
        
        details = {
            "provider": provider,
            "api_calls": api_calls,
            "api_success": api_success,
            "fallback_used": fallback_used,
            "external_enabled": distance_method.get("externalEnabled", False)
        }
        
        if fallback_used and api_success == 0:
            return True, "Using Haversine fallback (API not available)", details
        elif api_success > 0:
            return True, f"Map API working ({api_success}/{api_calls} successful)", details
        else:
            return True, "Distance calculation working", details

    def test_osrm_direct(self):
        """Test direct OSRM API connectivity"""
        # Test public OSRM demo server
        osrm_url = "https://router.project-osrm.org/route/v1/driving/77.5946,12.9716;77.6000,12.9800"
        self.log(f"GET {osrm_url}")
        
        try:
            status, body, _ = self.request(osrm_url, timeout=10)
        except ConnectionError as e:
            return True, f"OSRM demo server not reachable (expected): {e}", {
                "note": "Public OSRM is often unavailable"
            }
        except Exception as e:
            return True, f"OSRM connection issue: {e}", None
        
        if status != 200:
            return True, f"OSRM returned HTTP {status} (may be rate limited)", None
        
        try:
            data = json.loads(body)
            if data.get("code") == "Ok":
                routes = data.get("routes", [])
                if routes:
                    distance = routes[0].get("distance", 0) / 1000  # meters to km
                    duration = routes[0].get("duration", 0) / 60  # seconds to minutes
                    return True, "OSRM API accessible", {
                        "distance_km": round(distance, 2),
                        "duration_min": round(duration, 2)
                    }
        except:
            pass
        
        return True, "OSRM response received but format unexpected", None

    # ========================================================================
    # Run All Tests
    # ========================================================================

    def run_all(self):
        """Run all tests and return summary"""
        print(f"\n{'='*60}")
        print(f"Velora Deployment Tests - {self.env.upper()}")
        print(f"{'='*60}\n")

        print("Frontend Tests:")
        print("-" * 40)
        self.run_test("Frontend Accessible", self.test_frontend_accessible)
        self.run_test("Frontend Assets", self.test_frontend_assets)
        
        print("\nBackend Tests:")
        print("-" * 40)
        self.run_test("Backend Health", self.test_backend_health)
        self.run_test("Backend Root", self.test_backend_root)
        
        print("\nCORS Tests:")
        print("-" * 40)
        self.run_test("CORS Preflight", self.test_cors_preflight)
        
        print("\nPipeline Tests:")
        print("-" * 40)
        self.run_test("Optimization Pipeline", self.test_optimization_pipeline)
        self.run_test("Validation Handling", self.test_validation_error_handling)
        
        print("\nMap API Tests:")
        print("-" * 40)
        self.run_test("Map API Status", self.test_map_api_status)
        self.run_test("OSRM Direct", self.test_osrm_direct)
        
        # Summary
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total_time = sum(r.duration_ms for r in self.results)
        
        print(f"\n{'='*60}")
        print(f"SUMMARY: {passed}/{len(self.results)} tests passed ({total_time:.0f}ms total)")
        print(f"{'='*60}")
        
        if failed > 0:
            print("\nFailed Tests:")
            for r in self.results:
                if not r.passed:
                    print(f"  ❌ {r.name}: {r.message}")
        
        return failed == 0


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Velora Deployment Health Tests")
    parser.add_argument("--env", choices=["production", "local"], default="production",
                        help="Environment to test (default: production)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose output")
    args = parser.parse_args()
    
    runner = TestRunner(env=args.env, verbose=args.verbose)
    success = runner.run_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
