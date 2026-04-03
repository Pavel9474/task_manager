# JavaScript Components and Interactivity

<cite>
**Referenced Files in This Document**
- [main.js](file://static/js/main.js)
- [organization.js](file://static/js/organization.js)
- [organization_chart.html](file://tasks/templates/tasks/organization_chart.html)
- [organization_tree.html](file://tasks/templates/tasks/partials/organization_tree.html)
- [tree_node.html](file://tasks/templates/tasks/partials/tree_node.html)
- [base.html](file://tasks/templates/base.html)
- [organization.css](file://static/css/organization.css)
- [style.css](file://static/css/style.css)
- [employee_detail.html](file://tasks/templates/tasks/employee_detail.html)
</cite>

## Update Summary
**Changes Made**
- Added comprehensive Gantt chart visualization component with Frappe Gantt integration
- Enhanced DOM query optimization with intersection observer for dynamic color application
- Implemented scrollToToday() function for automatic timeline navigation
- Improved bar group styling with bar-closest-group class for highlighted tasks
- Added advanced event handling for scroll-based color re-application

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Gantt Chart Visualization System](#gantt-chart-visualization-system)
7. [Dependency Analysis](#dependency-analysis)
8. [Performance Considerations](#performance-considerations)
9. [Troubleshooting Guide](#troubleshooting-guide)
10. [Conclusion](#conclusion)

## Introduction
This document explains the JavaScript components and frontend interactivity for the task manager's organizational structure page and Gantt chart visualization system. It covers the global utilities, DOM manipulation patterns, event handling, AJAX interactions, interactive tree visualization, and the advanced Gantt chart implementation with Frappe Gantt library. It also documents how jQuery and Bootstrap are integrated, how notifications and error handling work, and how to extend the system with additional components.

## Project Structure
The frontend is organized around multiple JavaScript modules:
- Global utilities and helpers shared across the project
- Organization-specific tree navigation, filtering, and UI controls
- Advanced Gantt chart visualization with Frappe Gantt integration
- Intersection observer-based DOM optimization for dynamic content loading

These scripts integrate with Django templates and Bootstrap to deliver interactive experiences with sophisticated timeline visualization capabilities.

```mermaid
graph TB
subgraph "Templates"
OC["organization_chart.html"]
OT["organization_tree.html"]
TN["tree_node.html"]
ED["employee_detail.html"]
BH["base.html"]
end
subgraph "Static Assets"
JS_MAIN["static/js/main.js"]
JS_ORG["static/js/organization.js"]
CSS_ORG["static/css/organization.css"]
CSS_STYLE["static/css/style.css"]
end
OC --> JS_ORG
OC --> JS_MAIN
OC --> CSS_ORG
OC --> CSS_STYLE
OT --> JS_ORG
TN --> JS_ORG
ED --> JS_MAIN
BH --> JS_MAIN
BH --> CSS_STYLE
```

**Diagram sources**
- [organization_chart.html:1-131](file://tasks/templates/tasks/organization_chart.html#L1-L131)
- [organization_tree.html:1-55](file://tasks/templates/tasks/partials/organization_tree.html#L1-L55)
- [tree_node.html:1-57](file://tasks/templates/tasks/partials/tree_node.html#L1-L57)
- [employee_detail.html:1-1113](file://tasks/templates/tasks/employee_detail.html#L1-L1113)
- [base.html:1-118](file://tasks/templates/base.html#L1-L118)
- [main.js:1-174](file://static/js/main.js#L1-L174)
- [organization.js:1-179](file://static/js/organization.js#L1-L179)
- [organization.css:1-591](file://static/css/organization.css#L1-L591)
- [style.css:1-314](file://static/css/style.css#L1-L314)

**Section sources**
- [organization_chart.html:1-131](file://tasks/templates/tasks/organization_chart.html#L1-L131)
- [organization_tree.html:1-55](file://tasks/templates/tasks/partials/organization_tree.html#L1-L55)
- [tree_node.html:1-57](file://tasks/templates/tasks/partials/tree_node.html#L1-L57)
- [employee_detail.html:1-1113](file://tasks/templates/tasks/employee_detail.html#L1-L1113)
- [base.html:1-118](file://tasks/templates/base.html#L1-L118)
- [main.js:1-174](file://static/js/main.js#L1-L174)
- [organization.js:1-179](file://static/js/organization.js#L1-L179)
- [organization.css:1-591](file://static/css/organization.css#L1-L591)
- [style.css:1-314](file://static/css/style.css#L1-L314)

## Core Components
- Global utilities module (DOM helpers, date utilities, notification system, AJAX helpers)
- Organization tree module (tree navigation, block toggles, staff lists, search/filter)
- Advanced Gantt chart module (timeline visualization, color management, scroll navigation)
- Template integrations (organization chart page, tree partials, base layout, employee detail page)

Key responsibilities:
- Provide reusable DOM utilities and cross-page AJAX helpers
- Manage interactive tree expansion/collapse and search
- Coordinate Bootstrap and jQuery integration via the base template
- Deliver user feedback through a centralized notification system
- Implement sophisticated timeline visualization with Frappe Gantt
- Optimize DOM queries using intersection observers for performance

**Section sources**
- [main.js:6-174](file://static/js/main.js#L6-L174)
- [organization.js:6-179](file://static/js/organization.js#L6-L179)
- [employee_detail.html:730-1113](file://tasks/templates/tasks/employee_detail.html#L730-L1113)
- [base.html:113-116](file://tasks/templates/base.html#L113-L116)

## Architecture Overview
The system follows a modular pattern with enhanced Gantt chart capabilities:
- Templates define UI and bind to global JavaScript objects
- Global utilities provide cross-cutting concerns (AJAX, notifications)
- Organization module encapsulates tree-specific logic
- Gantt module handles advanced timeline visualization with Frappe Gantt
- Intersection observer optimizes DOM queries for performance
- Styles define responsive layouts and animations

```mermaid
graph TB
TPL["organization_chart.html<br/>Defines UI and binds JS calls"]
PART_OT["organization_tree.html<br/>Renders tree nodes"]
PART_TN["tree_node.html<br/>Recursive node rendering"]
UTILS["main.js<br/>DomUtils, DateUtils, Notify, Ajax"]
ORG["organization.js<br/>OrgTree, MainBlocks, Staff, Search"]
GANTT["employee_detail.html<br/>Frappe Gantt, scrollToToday, Intersection Observer"]
BOOT["Bootstrap CSS/JS"]
JQ["jQuery"]
TPL --> ORG
TPL --> UTILS
PART_OT --> ORG
PART_TN --> ORG
ED --> GANTT
ED --> UTILS
TPL --> BOOT
TPL --> JQ
UTILS --> BOOT
```

**Diagram sources**
- [organization_chart.html:1-131](file://tasks/templates/tasks/organization_chart.html#L1-L131)
- [organization_tree.html:1-55](file://tasks/templates/tasks/partials/organization_tree.html#L1-L55)
- [tree_node.html:1-57](file://tasks/templates/tasks/partials/tree_node.html#L1-L57)
- [employee_detail.html:1-1113](file://tasks/templates/tasks/employee_detail.html#L1-L1113)
- [main.js:1-174](file://static/js/main.js#L1-L174)
- [organization.js:1-179](file://static/js/organization.js#L1-L179)
- [base.html:113-116](file://tasks/templates/base.html#L113-L116)

## Detailed Component Analysis

### Global Utilities Module (main.js)
Responsibilities:
- DOM helpers: get/query/queryAll, add/remove/toggle classes, show/hide/toggle
- Date utilities: format, diff in days, overdue check
- Notification system: show success/error/warning/info with icons and auto-remove
- AJAX helpers: GET, POST (JSON and FormData), CSRF token extraction

Patterns:
- Encapsulation via IIFE-like globals exported to window
- Centralized error logging and user feedback
- Fetch-based async requests with try/catch and user notifications

```mermaid
classDiagram
class DomUtils {
+get(id)
+query(selector)
+queryAll(selector)
+addClass(element, className)
+removeClass(element, className)
+toggleClass(element, className)
+show(element)
+hide(element)
+toggle(element)
}
class DateUtils {
+format(date, format)
+diffDays(date1, date2)
+isOverdue(date)
}
class Notify {
+show(message, type, duration)
+success(message)
+error(message)
+warning(message)
+info(message)
}
class Ajax {
+get(url)
+post(url, data)
+postForm(url, formData)
}
window --> DomUtils
window --> DateUtils
window --> Notify
window --> Ajax
```

**Diagram sources**
- [main.js:6-174](file://static/js/main.js#L6-L174)

**Section sources**
- [main.js:6-174](file://static/js/main.js#L6-L174)

### Organization Tree Module (organization.js)
Responsibilities:
- Tree navigation: expand/collapse per node, expand/collapse all
- Block toggles: show/hide scientific and organizational sections
- Staff lists: reveal department/lab staff
- Search/filter: live search across tree nodes with parent visibility

Patterns:
- Stateful toggling using a Set to track expanded nodes
- DOM queries and style toggling for visibility
- Event-driven initialization on DOMContentLoaded
- Template-driven click handlers invoking module functions

```mermaid
classDiagram
class OrgTree {
-expandedNodes : Set
+toggleNode(nodeId, element)
+expandAll()
+collapseAll()
}
class MainBlocks {
-scienceOpen : boolean
-organizationOpen : boolean
+toggleScience()
+toggleOrganization()
}
class Staff {
+showDepartmentStaff(deptId)
+showLabStaff(labId)
}
class Search {
-searchInput
+init()
+performSearch(event)
+clear()
}
window --> OrgTree
window --> MainBlocks
window --> Staff
window --> Search
```

**Diagram sources**
- [organization.js:6-179](file://static/js/organization.js#L6-L179)

**Section sources**
- [organization.js:6-179](file://static/js/organization.js#L6-L179)

### Template Integrations
- Base template loads Bootstrap CSS/JS and jQuery, and injects global main.js
- Organization chart page defines control buttons, search box, and containers for tree sections
- Tree partials render recursive nodes and attach click handlers bound to OrgTree and Staff
- Employee detail page integrates Frappe Gantt for timeline visualization

Key integration points:
- Control buttons call OrgTree.expandAll()/collapseAll()
- Search input delegates to Search.performSearch()
- Node cards call OrgTree.toggleNode()
- Staff toggles call Staff.showDepartmentStaff()/showLabStaff()
- Gantt chart initialization uses Frappe Gantt library

**Section sources**
- [base.html:113-116](file://tasks/templates/base.html#L113-L116)
- [organization_chart.html:65-125](file://tasks/templates/tasks/organization_chart.html#L65-L125)
- [organization_tree.html:5-50](file://tasks/templates/tasks/partials/organization_tree.html#L5-L50)
- [tree_node.html:9-47](file://tasks/templates/tasks/partials/tree_node.html#L9-L47)
- [employee_detail.html:730-1113](file://tasks/templates/tasks/employee_detail.html#L730-L1113)

### Event Handling Mechanisms
- DOMContentLoaded initializes Search and hides containers
- Click handlers on UI elements delegate to module functions
- Keyboard events on search input trigger filtering logic
- No explicit event delegation is used; handlers are attached directly to interactive elements
- Intersection observer handles visibility-based DOM optimizations

Best practices observed:
- Keep event handlers minimal and delegate to module functions
- Use template-driven onclick attributes for quick bindings
- Initialize only after DOM is ready
- Implement intersection observer for performance optimization

**Section sources**
- [organization.js:157-173](file://static/js/organization.js#L157-L173)
- [organization_chart.html:84-93](file://tasks/templates/tasks/organization_chart.html#L84-L93)
- [employee_detail.html:1016-1031](file://tasks/templates/tasks/employee_detail.html#L1016-L1031)

### AJAX Interactions and CSRF Handling
- Ajax.get/post/postForm provide unified async request patterns
- CSRF token is extracted from cookies and included in headers for POST requests
- Errors are caught and surfaced via Notify.error with console logging

Common usage patterns:
- Load dynamic content via GET
- Submit forms via POST (JSON) or FormData
- Handle errors gracefully with user-visible notifications

**Section sources**
- [main.js:89-135](file://static/js/main.js#L89-L135)
- [main.js:138-151](file://static/js/main.js#L138-L151)

### DOM Manipulation Patterns
- Use DomUtils for consistent DOM queries and manipulations
- Toggle visibility by setting display styles
- Add/remove CSS classes for state changes
- Append notifications to a dedicated container
- Optimize DOM queries using querySelectorAll with intersection observer

**Section sources**
- [main.js:6-29](file://static/js/main.js#L6-L29)
- [organization.js:10-27](file://static/js/organization.js#L10-L27)

### Interactive Filtering System
- Live search filters tree nodes by name
- Minimum input length threshold prevents premature filtering
- Parent nodes are revealed when a child matches the search term
- Clearing the input restores all nodes

```mermaid
flowchart TD
Start(["User types in search box"]) --> GetTerm["Read input value"]
GetTerm --> LengthCheck{"Length >= 2?"}
LengthCheck --> |No| ShowAll["Show all nodes"]
LengthCheck --> |Yes| Iterate["Iterate all tree nodes"]
Iterate --> Match{"Name includes term?"}
Match --> |Yes| ShowNode["Show node and parents"]
Match --> |No| HideNode["Hide node"]
ShowAll --> End(["Done"])
ShowNode --> End
HideNode --> End
```

**Diagram sources**
- [organization.js:111-154](file://static/js/organization.js#L111-L154)

**Section sources**
- [organization.js:111-154](file://static/js/organization.js#L111-L154)

### Organization Chart Visualization
- Two-level tree rendering with connecting lines and animated transitions
- Responsive grid layouts for leadership cards and staff lists
- Control buttons switch views and manage expansion state
- Icons from Bootstrap Icons enhance visual cues

**Section sources**
- [organization.css:6-591](file://static/css/organization.css#L6-L591)
- [organization_chart.html:10-126](file://tasks/templates/tasks/organization_chart.html#L10-L126)

### jQuery and Bootstrap Integration
- Bootstrap CSS/JS and Bootstrap Icons are loaded globally
- jQuery is included for compatibility and potential third-party plugins
- Notifications leverage Bootstrap alert classes and icons

**Section sources**
- [base.html:10-23](file://tasks/templates/base.html#L10-L23)
- [base.html:113-116](file://tasks/templates/base.html#L113-L116)
- [main.js:61-86](file://static/js/main.js#L61-L86)

## Gantt Chart Visualization System

**Updated** Enhanced with comprehensive Frappe Gantt integration, intersection observer optimization, and advanced timeline features

The Gantt chart system provides sophisticated timeline visualization for research projects and tasks with the following capabilities:

### Core Features
- **Timeline Visualization**: Interactive Gantt charts using Frappe Gantt library
- **Dynamic Color Application**: Automatic color assignment to project bars
- **Closest Task Highlighting**: Special styling for currently relevant tasks
- **Scroll Navigation**: Automatic positioning to today's date
- **Responsive Design**: Adaptive timeline that works across different screen sizes
- **View Mode Switching**: Multiple timeline perspectives (Day, Week, Month)

### Implementation Details

#### Frappe Gantt Integration
The system integrates with the Frappe Gantt library for professional timeline visualization:

```javascript
// Initialize Gantt chart with enhanced configuration
currentGantt = new Gantt("#ganttChartContainer", tasks, {
    on_click: function(task) { ... },
    bar_height: 45,
    bar_corner_radius: 4,
    padding: 25,
    view_mode: currentViewMode,
    date_format: 'YYYY-MM-DD',
    language: 'ru'
});
```

#### Scroll to Today Functionality
The `scrollToToday()` function automatically positions the timeline to the current date:

```javascript
function scrollToToday() {
    if (!currentGantt) return;
    
    const ganttContainer = document.querySelector('#ganttChartContainer .gantt');
    if (!ganttContainer) return;
    
    const todayLine = document.querySelector('.gantt .today-line, .gantt .current-date-line');
    if (todayLine) {
        const x = parseFloat(todayLine.getAttribute('x1') || todayLine.getAttribute('x'));
        if (!isNaN(x)) {
            const container = document.getElementById('ganttChartContainer');
            const containerWidth = container.clientWidth;
            container.scrollLeft = Math.max(0, x - containerWidth / 2);
        }
    }
}
```

#### Intersection Observer Optimization
Advanced DOM optimization using intersection observer for performance:

```javascript
let ganttObserver = null;
function setupVisibilityObserver() {
    const container = document.getElementById('ganttChartContainer');
    if (!container || ganttObserver) return;
    
    ganttObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Re-apply colors when Gantt becomes visible
                setTimeout(applyColors, 50);
            }
        });
    }, { threshold: 0.1 });
    
    ganttObserver.observe(container);
}
```

#### Enhanced Bar Group Styling
Improved styling system with the `bar-closest-group` class for highlighting relevant tasks:

```css
/* Red highlight for closest products - only target the bar rect, not the wrapper */
.gantt .bar-closest .bar,
.gantt .bar-group.bar-closest-group .bar {
    stroke: #ff0000 !important;
    stroke-width: 4px !important;
}

/* Highlighted (closest) bars have bold black text */
.gantt .bar-group:has(.bar-closest) .bar-label,
.gantt .bar-closest-group .bar-label,
.gantt .bar-group.bar-closest-group .bar-label {
    fill: #000 !important;
    font-weight: 700 !important;
}
```

#### Dynamic Color Management
Smart color assignment and re-application system:

```javascript
function applyColors() {
    if (!GANTT_DATA || GANTT_DATA.length === 0) return;
    
    const barGroups = document.querySelectorAll('.gantt .bar-group');
    
    barGroups.forEach((group, index) => {
        const bar = group.querySelector('.bar');
        const label = group.querySelector('.bar-label');
        
        const task = GANTT_DATA[index];
        if (!task || !bar) return;
        
        // Apply red highlight for closest product
        if (task.is_closest) {
            bar.setAttribute('fill', '#dc3545');
            bar.style.fill = '#dc3545';
            group.classList.add('bar-closest-group');
        } else if (task.color) {
            bar.setAttribute('fill', task.color);
            bar.style.fill = task.color;
        }
    });
}
```

### Advanced Event Handling
The system implements sophisticated event handling for optimal user experience:

```javascript
// Initialize on page load with intersection observer
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Gantt with data:', GANTT_DATA);
    initGantt();
    setupVisibilityObserver();
    
    // Re-apply colors on scroll (for when Gantt re-enters viewport)
    let scrollTimeout;
    window.addEventListener('scroll', function() {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(function() {
            applyColors();
        }, 100);
    });
});
```

### Template Integration
The Gantt system is integrated into the employee detail template with comprehensive styling and functionality:

```html
<!-- Frappe Gantt CDN -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/frappe-gantt/dist/frappe-gantt.css">
<script src="https://cdn.jsdelivr.net/npm/frappe-gantt/dist/frappe-gantt.umd.js"></script>

<div id="ganttChartContainer" class="gantt-container"></div>
```

**Section sources**
- [employee_detail.html:730-1113](file://tasks/templates/tasks/employee_detail.html#L730-L1113)
- [employee_detail.html:799-835](file://tasks/templates/tasks/employee_detail.html#L799-L835)
- [employee_detail.html:902-1078](file://tasks/templates/tasks/employee_detail.html#L902-L1078)

## Dependency Analysis
- Templates depend on organization.js and main.js for interactivity
- organization.js depends on DomUtils for DOM operations
- main.js provides Ajax and Notify used across pages
- employee_detail.html depends on Frappe Gantt library for timeline visualization
- Stylesheets define responsive behavior and animations
- Intersection observer optimizes DOM query performance

```mermaid
graph LR
BH["base.html"] --> JS_MAIN["main.js"]
OC["organization_chart.html"] --> JS_ORG["organization.js"]
OC --> CSS_ORG["organization.css"]
OT["organization_tree.html"] --> JS_ORG
TN["tree_node.html"] --> JS_ORG
ED["employee_detail.html"] --> GANTT_LIB["Frappe Gantt Library"]
ED --> JS_MAIN
JS_ORG --> DOMU["DomUtils (main.js)"]
JS_MAIN --> BOOT["Bootstrap & Icons"]
JS_MAIN --> JQ["jQuery"]
GANTT_LIB --> INTERSECT_OBS["Intersection Observer"]
```

**Diagram sources**
- [base.html:10-23](file://tasks/templates/base.html#L10-L23)
- [organization_chart.html:1-131](file://tasks/templates/tasks/organization_chart.html#L1-L131)
- [organization_tree.html:1-55](file://tasks/templates/tasks/partials/organization_tree.html#L1-L55)
- [tree_node.html:1-57](file://tasks/templates/tasks/partials/tree_node.html#L1-L57)
- [employee_detail.html:730-1113](file://tasks/templates/tasks/employee_detail.html#L730-L1113)
- [main.js:1-174](file://static/js/main.js#L1-L174)
- [organization.js:1-179](file://static/js/organization.js#L1-L179)
- [organization.css:1-591](file://static/css/organization.css#L1-L591)

**Section sources**
- [base.html:10-23](file://tasks/templates/base.html#L10-L23)
- [organization_chart.html:1-131](file://tasks/templates/tasks/organization_chart.html#L1-L131)
- [organization_tree.html:1-55](file://tasks/templates/tasks/partials/organization_tree.html#L1-L55)
- [tree_node.html:1-57](file://tasks/templates/tasks/partials/tree_node.html#L1-L57)
- [employee_detail.html:730-1113](file://tasks/templates/tasks/employee_detail.html#L730-L1113)
- [main.js:1-174](file://static/js/main.js#L1-L174)
- [organization.js:1-179](file://static/js/organization.js#L1-L179)
- [organization.css:1-591](file://static/css/organization.css#L1-L591)

## Performance Considerations
- Minimize DOM queries by caching selectors when reused frequently
- Batch DOM updates (e.g., toggling multiple icons) to reduce reflows
- Debounce search input if performance becomes an issue with large trees
- Prefer CSS transitions/animations over heavy JavaScript animations
- Use efficient selectors (IDs over class queries) where possible
- **Intersection observer optimization**: Use intersection observer to defer DOM operations until elements become visible
- **Scroll-based optimization**: Re-apply colors only when Gantt chart re-enters viewport
- **Query optimization**: Cache DOM queries and reuse them across functions

## Troubleshooting Guide
Common issues and resolutions:
- Notifications not appearing: ensure the alerts container exists and is appended to the body during initialization
- AJAX failures: verify CSRF token retrieval and header inclusion; check browser network tab for 403/404 errors
- Tree nodes not expanding: confirm element IDs match the expected pattern and that icons are updated
- Search not working: ensure the search input has the correct ID and that event listeners are attached after DOMContentLoaded
- **Gantt chart not displaying**: verify Frappe Gantt library is loaded and GANTT_DATA contains valid task objects
- **Scroll to today not working**: ensure today's line element exists in the Gantt chart DOM
- **Color application failing**: check that bar groups have the correct structure and task data matches indices
- **Intersection observer not triggering**: verify container element exists and observer is properly configured

**Section sources**
- [main.js:154-168](file://static/js/main.js#L154-L168)
- [main.js:138-151](file://static/js/main.js#L138-L151)
- [organization.js:157-173](file://static/js/organization.js#L157-L173)
- [employee_detail.html:902-1078](file://tasks/templates/tasks/employee_detail.html#L902-L1078)

## Conclusion
The JavaScript components provide a clean separation of concerns with enhanced Gantt chart capabilities: global utilities handle cross-cutting needs, while the organization module encapsulates tree-specific behavior. The new Gantt chart system delivers sophisticated timeline visualization using Frappe Gantt with advanced features like intersection observer optimization, dynamic color application, and automatic scroll positioning. The integration with Django templates and Bootstrap delivers a responsive, interactive experience with professional timeline visualization. Extending the system involves adding new modules alongside existing patterns, leveraging the global utilities for AJAX and notifications, following the established DOM manipulation and event handling conventions, and utilizing the intersection observer pattern for performance optimization.