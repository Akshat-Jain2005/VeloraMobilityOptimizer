# Flutter App Development Prompt - Velora Mobility Optimizer

## Project Overview

Build a Flutter mobile app (Android + iOS) that mirrors the Velora Mobility Optimizer web application. The app will connect to an existing deployed backend and provide the same route optimization functionality.

**App Name:** Velora Mobility Optimizer  
**Company:** VELORA MOBITECH  
**Tagline:** "Driven by Possibility"

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Flutter App                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │   Screens   │  │   Widgets   │  │   Services      │ │
│  │  - Home     │  │  - FileCard │  │  - ApiService   │ │
│  │  - Upload   │  │  - MapView  │  │  - FileService  │ │
│  │  - Results  │  │  - RouteCard│  │                 │ │
│  │  - Employee │  │  - Metrics  │  │                 │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
            ┌──────────────────────────────┐
            │   Backend API (Node.js)      │
            │   https://YOUR_BACKEND_URL   │
            │   - POST /api/optimize/json  │
            │   - POST /api/parse          │
            │   - GET /api/results/:id     │
            └──────────────────────────────┘
```

---

## Backend API Endpoints

The Flutter app will communicate with these endpoints:

### 1. Parse Excel File
```
POST /api/parse
Content-Type: multipart/form-data
Body: file (Excel .xlsx/.xls)

Response:
{
  "vehicles": [...],
  "requests": [...],
  "metadata": {...}
}
```

### 2. Submit Optimization (JSON)
```
POST /api/optimize/json
Content-Type: application/json
Body: {
  "config": { "allow_external_maps": false, "maps_api_key": "" },
  "vehicles": [...],
  "requests": [...],
  "metadata": { "maxDelayByPriority": { "1": 5, "2": 10, "3": 15, "4": 20, "5": 30 } }
}

Response (success):
{
  "jobId": "uuid",
  "status": "success",
  "result": {
    "routes": [...],
    "summary": {...},
    "unassigned": [...],
    "requestDetails": [...]
  }
}
```

### 3. Get Job Status
```
GET /api/optimize/:jobId/status

Response:
{
  "jobId": "uuid",
  "status": "processing" | "complete" | "error",
  "stage": "parsing" | "solving" | "transforming",
  "progress": 0-100,
  "error": "message if error"
}
```

### 4. Get Results
```
GET /api/results/:jobId

Response:
{
  "jobId": "uuid",
  "status": "success",
  "result": { ... same as optimize response ... }
}
```

---

## Data Models

### Vehicle
```dart
class Vehicle {
  final String vehicleId;
  final int capacity;
  final double costPerKm;
  final Location startLocation;
  final int availabilityTime;
  final double speed;
  final String type;       // "4w", "2w", "any"
  final String category;   // "normal", "premium"
  final String fuelType;   // "petrol", "diesel", "ev"
}
```

### Request (Employee)
```dart
class TransportRequest {
  final String employeeId;
  final int priority;        // 1-5 (1 = highest)
  final Location pickup;
  final Location dropoff;
  final int earlyTime;       // minutes from midnight
  final int lateTime;        // minutes from midnight
  final int load;            // typically 1
  final String vehiclePreference;  // "4w", "2w", "any"
  final int sharingLimit;    // 1 = no sharing, 4 = default
}
```

### Location
```dart
class Location {
  final double lat;
  final double lon;
}
```

### Route
```dart
class Route {
  final String vehicleId;
  final String vehicleIdStr;
  final String vehicleType;
  final String fuelType;
  final int capacity;
  final double totalDist;
  final double totalTime;
  final List<Stop> stops;
}
```

### Stop
```dart
class Stop {
  final String type;       // "pickup", "dropoff", "depot"
  final int reqId;
  final String employeeId;
  final double lat;
  final double lon;
  final double arrivalTime;
  final double waitTime;
}
```

### Summary
```dart
class Summary {
  final double totalMoneyCost;
  final double totalDistance;
  final double totalTime;
  final int vehiclesUsed;
  final int unassignedCount;
  final double globalCost;
}
```

---

## App Screens

### Screen 1: Home Page (Splash/Landing)
**Design:**
- Dark/light theme support
- "VELORA" large logo text
- "VELORA MOBITECH" company name
- "Driven by Possibility" tagline
- "Employee Transport Route Planner" description
- "BEGIN OPTIMIZATION" button
- 4 feature icons at bottom: Multi-Vehicle, Time Windows, Analytics, Optimized

**Colors (Dark Theme):**
- Background: #050a18
- Primary: #3b82f6 (blue)
- Secondary: #8b5cf6 (purple)
- Accent: #10b981 (green)
- Text: #e2e8f0

**Colors (Light Theme):**
- Background: #FAF0E6 (linen)
- Primary: #2563eb
- Secondary: #7c3aed
- Accent: #059669
- Text: #334155

### Screen 2: Upload Screen
**Design:**
- Header with back button and "VELORA" logo
- Glass card with file upload area
- Drag & drop style (tap to browse on mobile)
- Accepted files: .xlsx, .xls, .json
- Shows file name after selection with checkmark
- "Clear File" button
- Error message area
- "Optimize Now" button (enabled only when file is valid)

**File Handling:**
- Excel files → Upload to `/api/parse` → Get parsed JSON
- JSON input files → Parse locally
- JSON output files → Display results directly

### Screen 3: Results Screen (Tabbed)
**Tabs:**
1. **Visualization** - Interactive map with routes
2. **Analytics** - Cost comparison and metrics
3. **Employees** - Per-employee results
4. **Routes** - Detailed route tables

**Header:**
- "Optimization Intelligence" title
- "Download JSON" button

### Tab 1: Visualization (Map)
**Design:**
- Full-screen map using flutter_map + OpenStreetMap tiles
- Different colored polylines for each vehicle route
- Markers: 🏠 for pickup, 🏢 for dropoff
- Popup on marker tap showing employee ID, arrival time
- Route fetching from OSRM API for real road paths
- Summary stats overlay: Total Stops, Vehicles Active, Travel Distance

**OSRM Route API:**
```
GET https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson
```

### Tab 2: Analytics
**Design:**
- Two cards side by side (or stacked on mobile):

**Card 1: Economic Efficiency**
- If baseline data exists: Show baseline vs optimized cost
- Show savings percentage in circular indicator
- "Velora Optimized: ₹X,XXX"

**Card 2: Operational Metrics**
- Fuel & Distance cost
- Constraint Penalties  
- Fleet Utilization (X active)
- Unassigned Assets count

### Tab 3: Employees
**Design:**
- Scrollable list of employee cards
- Each card shows:
  - Employee ID with avatar
  - Assigned vehicle with type badge
  - Status badge: "On Time" (green), "Within Tolerance" (yellow), "Violated" (red)
  - Pickup time and window
  - Dropoff time
  - Travel duration
  - Priority star indicator (1-5)

**Status Colors:**
- On Time: #10b981 (green)
- Within Tolerance: #f59e0b (yellow)
- Violated: #ef4444 (red)

### Tab 4: Routes
**Design:**
- Collapsible list of route cards
- Each route card shows:
  - Vehicle ID with truck icon
  - Type badge (4w, 2w)
  - Quick metrics: distance, time, stop count
  - Vehicle details strip: cost per km, category, capacity
  - Expandable table with stops:
    | Type | Req ID | Employee | Coordinates | Arrival | Wait |

---

## Required Flutter Packages

```yaml
dependencies:
  flutter:
    sdk: flutter
  
  # HTTP & API
  http: ^1.2.0
  dio: ^5.4.0  # Better for file uploads with progress
  
  # State Management
  provider: ^6.1.1
  # OR
  flutter_riverpod: ^2.4.9
  
  # File Picking
  file_picker: ^6.1.1
  
  # Maps
  flutter_map: ^6.1.0
  latlong2: ^0.9.0
  
  # UI
  google_fonts: ^6.1.0  # For Inter, Space Grotesk fonts
  flutter_animate: ^4.5.0  # For animations
  shimmer: ^3.0.0  # Loading states
  
  # Icons
  lucide_icons: ^0.257.0
  # OR use flutter_lucide
  
  # JSON Parsing
  json_annotation: ^4.8.1
  
  # Local Storage (for theme preference)
  shared_preferences: ^2.2.2

dev_dependencies:
  build_runner: ^2.4.8
  json_serializable: ^6.7.1
```

---

## Key Implementation Details

### 1. API Service
```dart
class ApiService {
  static const String baseUrl = 'https://YOUR_BACKEND_URL/api';
  
  Future<Map<String, dynamic>> parseExcel(File file) async {
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(file.path),
    });
    final response = await dio.post('$baseUrl/parse', data: formData);
    return response.data;
  }
  
  Future<Map<String, dynamic>> submitOptimization(Map<String, dynamic> payload) async {
    final response = await dio.post('$baseUrl/optimize/json', data: payload);
    return response.data;
  }
  
  Future<Map<String, dynamic>> getJobStatus(String jobId) async {
    final response = await dio.get('$baseUrl/optimize/$jobId/status');
    return response.data;
  }
  
  Future<Map<String, dynamic>> getResults(String jobId) async {
    final response = await dio.get('$baseUrl/results/$jobId');
    return response.data;
  }
}
```

### 2. Theme Configuration
```dart
final darkTheme = ThemeData(
  brightness: Brightness.dark,
  scaffoldBackgroundColor: Color(0xFF050A18),
  primaryColor: Color(0xFF3B82F6),
  colorScheme: ColorScheme.dark(
    primary: Color(0xFF3B82F6),
    secondary: Color(0xFF8B5CF6),
    surface: Color(0x0C1223).withOpacity(0.85),
  ),
  fontFamily: 'Inter',
);

final lightTheme = ThemeData(
  brightness: Brightness.light,
  scaffoldBackgroundColor: Color(0xFFFAF0E6),
  primaryColor: Color(0xFF2563EB),
  colorScheme: ColorScheme.light(
    primary: Color(0xFF2563EB),
    secondary: Color(0xFF7C3AED),
    surface: Color(0xFFFFFAF0).withOpacity(0.95),
  ),
  fontFamily: 'Inter',
);
```

### 3. Glass Card Widget
```dart
class GlassCard extends StatelessWidget {
  final Widget child;
  final EdgeInsets padding;
  
  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      padding: padding ?? EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: isDark 
          ? Colors.white.withOpacity(0.03)
          : Colors.black.withOpacity(0.03),
        borderRadius: BorderRadius.circular(28),
        border: Border.all(
          color: isDark
            ? Colors.white.withOpacity(0.08)
            : Colors.black.withOpacity(0.08),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(isDark ? 0.5 : 0.1),
            blurRadius: 50,
            offset: Offset(0, 25),
          ),
        ],
      ),
      child: child,
    );
  }
}
```

### 4. Polling for Job Status
```dart
Future<void> pollJobStatus(String jobId) async {
  while (true) {
    final status = await apiService.getJobStatus(jobId);
    
    if (status['status'] == 'complete') {
      final results = await apiService.getResults(jobId);
      // Navigate to results screen
      break;
    } else if (status['status'] == 'error') {
      // Show error
      break;
    }
    
    // Update progress UI
    updateProgress(status['progress'], status['stage']);
    
    await Future.delayed(Duration(seconds: 2));
  }
}
```

### 5. Map with Routes
```dart
FlutterMap(
  options: MapOptions(
    initialCenter: LatLng(centerLat, centerLon),
    initialZoom: 12,
  ),
  children: [
    TileLayer(
      urlTemplate: isDark
        ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
        : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      subdomains: ['a', 'b', 'c'],
    ),
    // Route polylines
    PolylineLayer(
      polylines: routes.map((route) => Polyline(
        points: route.geometry,
        color: vehicleColors[route.index % vehicleColors.length],
        strokeWidth: 4,
      )).toList(),
    ),
    // Markers
    MarkerLayer(markers: [...]),
  ],
)
```

---

## Project Structure

```
velora_mobile/
├── lib/
│   ├── main.dart
│   ├── app.dart
│   │
│   ├── config/
│   │   ├── theme.dart
│   │   └── constants.dart
│   │
│   ├── models/
│   │   ├── vehicle.dart
│   │   ├── request.dart
│   │   ├── route.dart
│   │   ├── stop.dart
│   │   ├── solution.dart
│   │   └── summary.dart
│   │
│   ├── services/
│   │   ├── api_service.dart
│   │   └── file_service.dart
│   │
│   ├── providers/
│   │   ├── theme_provider.dart
│   │   ├── optimization_provider.dart
│   │   └── solution_provider.dart
│   │
│   ├── screens/
│   │   ├── home_screen.dart
│   │   ├── upload_screen.dart
│   │   └── results/
│   │       ├── results_screen.dart
│   │       ├── visualization_tab.dart
│   │       ├── analytics_tab.dart
│   │       ├── employees_tab.dart
│   │       └── routes_tab.dart
│   │
│   └── widgets/
│       ├── glass_card.dart
│       ├── file_upload_card.dart
│       ├── route_map.dart
│       ├── route_card.dart
│       ├── employee_card.dart
│       ├── metric_card.dart
│       ├── status_badge.dart
│       └── loading_overlay.dart
│
├── assets/
│   └── fonts/
│       ├── Inter-*.ttf
│       └── SpaceGrotesk-*.ttf
│
├── android/
│   └── app/
│       └── src/main/
│           └── AndroidManifest.xml  # Add internet permission
│
├── ios/
│   └── Runner/
│       └── Info.plist  # Add network permissions
│
└── pubspec.yaml
```

---

## Android vs iOS Differences

| Aspect | Android | iOS |
|--------|---------|-----|
| Build command | `flutter build apk` or `flutter build appbundle` | `flutter build ios` (requires Mac) |
| Output | APK file (can install directly) | IPA (needs Xcode/TestFlight) |
| Permissions | AndroidManifest.xml | Info.plist |
| File picker | Works same | Works same |
| Maps | Works same | Works same |

### Android Permissions (AndroidManifest.xml)
```xml
<uses-permission android:name="android.permission.INTERNET"/>
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE"/>
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
```

### iOS Permissions (Info.plist)
```xml
<key>NSPhotoLibraryUsageDescription</key>
<string>To select Excel files for optimization</string>
<key>NSLocationWhenInUseUsageDescription</key>
<string>To show your location on the map</string>
```

---

## Building the APK

```bash
# Debug APK (larger, for testing)
flutter build apk --debug

# Release APK (optimized, for distribution)
flutter build apk --release

# Split APKs by architecture (recommended for Play Store)
flutter build apk --split-per-abi

# Output location: build/app/outputs/flutter-apk/
```

---

## Configuration Before Building

1. **Set Backend URL:**
   ```dart
   // lib/config/constants.dart
   const String API_BASE_URL = 'https://your-deployed-backend.com/api';
   ```

2. **Update App Name & Package:**
   - Android: `android/app/build.gradle` → applicationId
   - iOS: Xcode → Bundle Identifier

3. **Add App Icons:**
   - Use `flutter_launcher_icons` package
   - Or manually add to `android/app/src/main/res/` and `ios/Runner/Assets.xcassets/`

---

## Sample Vehicle Colors (for route visualization)
```dart
const List<Color> vehicleColors = [
  Color(0xFF2563EB),  // Deep Blue
  Color(0xFF7C3AED),  // Deep Violet
  Color(0xFF059669),  // Forest Green
  Color(0xFFD97706),  // Burnt Orange
  Color(0xFFDC2626),  // Deep Rose
  Color(0xFF0891B2),  // Ocean Blue
  Color(0xFFDB2777),  // Deep Pink
];
```

---

## Time Formatting Helper
```dart
String formatTime(num? minutes) {
  if (minutes == null) return '-';
  final hours = (minutes / 60).floor();
  final mins = (minutes % 60).floor();
  return '${hours.toString().padLeft(2, '0')}:${mins.toString().padLeft(2, '0')}';
}
```

---

## Summary

This Flutter app should:
1. ✅ Mirror the web app's full functionality
2. ✅ Connect to the same backend API
3. ✅ Support Excel and JSON file uploads
4. ✅ Display interactive maps with routes
5. ✅ Show analytics, employee results, and route details
6. ✅ Support dark/light themes
7. ✅ Work on both Android and iOS from single codebase
8. ✅ Generate APK for Android distribution

**Backend URL to configure:** `[SET YOUR DEPLOYED BACKEND URL]`

---

## Next Steps

1. Create Flutter project: `flutter create velora_mobile`
2. Add dependencies to `pubspec.yaml`
3. Implement API service first
4. Build screens in order: Home → Upload → Results
5. Test with your deployed backend
6. Build APK: `flutter build apk --release`
