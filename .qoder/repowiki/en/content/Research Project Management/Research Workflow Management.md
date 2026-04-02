# Research Workflow Management

<cite>
**Referenced Files in This Document**
- [models.py](file://tasks/models.py)
- [research_views.py](file://tasks/views/research_views.py)
- [product_views.py](file://tasks/views/product_views.py)
- [forms.py](file://tasks/forms.py)
- [forms_product.py](file://tasks/forms_product.py)
- [urls.py](file://tasks/urls.py)
- [research_task_detail.html](file://tasks/templates/tasks/research_task_detail.html)
- [research_substage_detail.html](file://tasks/templates/tasks/research_substage_detail.html)
- [research_product_detail.html](file://tasks/templates/tasks/research_product_detail.html)
- [product_assign_performers.html](file://tasks/templates/tasks/product_assign_performers.html)
- [0001_initial.py](file://tasks/migrations/0001_initial.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)

## Introduction
This document describes the Research Workflow Management system that organizes scientific research projects into a three-tier hierarchy: ResearchTask (main project), ResearchStage (major phases), and ResearchSubstage (specific activities). It also supports ResearchProduct deliverables and integrates with the broader task management system and organizational structure. The system enables lifecycle management, status tracking, milestone management, performer assignment, and progress reporting across the hierarchy.

## Project Structure
The system is implemented within the tasks application and consists of:
- Models defining the research hierarchy and deliverables
- Views handling CRUD and workflow operations
- Forms for data entry and validation
- Templates rendering the UI for each hierarchy level
- URL routing connecting endpoints to views
- Migrations establishing database schema

```mermaid
graph TB
subgraph "Models"
RT["ResearchTask"]
RS["ResearchStage"]
RSub["ResearchSubstage"]
RP["ResearchProduct"]
Emp["Employee"]
Perf["ProductPerformer"]
end
subgraph "Views"
RV["research_views.py"]
PV["product_views.py"]
end
subgraph "Forms"
F1["forms.py"]
F2["forms_product.py"]
end
subgraph "Templates"
T1["research_task_detail.html"]
T2["research_substage_detail.html"]
T3["research_product_detail.html"]
T4["product_assign_performers.html"]
end
subgraph "Routing"
U["urls.py"]
end
RT --> RS
RS --> RSub
RSub --> RP
Emp -.-> RP
Emp -.-> RS
Emp -.-> RSub
Perf --> RP
RV --> RT
RV --> RS
RV --> RSub
PV --> RP
PV --> Perf
F1 --> RT
F1 --> RS
F1 --> RSub
F2 --> RP
F2 --> Perf
U --> RV
U --> PV
T1 --> RT
T2 --> RSub
T3 --> RP
T4 --> Perf
```

**Diagram sources**
- [models.py:384-791](file://tasks/models.py#L384-L791)
- [research_views.py:1-165](file://tasks/views/research_views.py#L1-L165)
- [product_views.py:1-253](file://tasks/views/product_views.py#L1-L253)
- [forms.py:71-140](file://tasks/forms.py#L71-L140)
- [forms_product.py:8-126](file://tasks/forms_product.py#L8-L126)
- [urls.py:38-100](file://tasks/urls.py#L38-L100)
- [research_task_detail.html:1-344](file://tasks/templates/tasks/research_task_detail.html#L1-L344)
- [research_substage_detail.html:1-105](file://tasks/templates/tasks/research_substage_detail.html#L1-L105)
- [research_product_detail.html:1-221](file://tasks/templates/tasks/research_product_detail.html#L1-L221)
- [product_assign_performers.html:1-594](file://tasks/templates/tasks/product_assign_performers.html#L1-L594)

**Section sources**
- [models.py:384-791](file://tasks/models.py#L384-L791)
- [urls.py:38-100](file://tasks/urls.py#L38-L100)

## Core Components
- ResearchTask: Top-level research project with metadata, timeline, and funding.
- ResearchStage: Major phases of a ResearchTask with performers and responsible person.
- ResearchSubstage: Specific activities under a stage with performers and responsible person.
- ResearchProduct: Deliverables produced during substages, with status, dates, and performers.
- ProductPerformer: Links employees to products with roles and contribution percentages.
- Employee: Organizational member with department and position associations.
- Views: Provide CRUD and workflow operations for the hierarchy and deliverables.
- Forms: Validate and present forms for creating/editing hierarchy items and performers.
- Templates: Render detailed views, progress dashboards, and performer assignment UI.

**Section sources**
- [models.py:384-791](file://tasks/models.py#L384-L791)
- [research_views.py:19-165](file://tasks/views/research_views.py#L19-L165)
- [product_views.py:9-253](file://tasks/views/product_views.py#L9-L253)
- [forms.py:71-140](file://tasks/forms.py#L71-L140)
- [forms_product.py:8-126](file://tasks/forms_product.py#L8-L126)

## Architecture Overview
The system follows a layered architecture:
- Presentation layer: Templates render views for ResearchTask, ResearchStage, ResearchSubstage, and ResearchProduct.
- Business logic layer: Views orchestrate data retrieval, updates, and redirects.
- Data access layer: Models define relationships and constraints; migrations establish schema.
- Integration layer: URLs route requests to appropriate views.

```mermaid
sequenceDiagram
participant User as "User"
participant Browser as "Browser"
participant Router as "urls.py"
participant RV as "research_views.py"
participant PV as "product_views.py"
participant Models as "models.py"
User->>Browser : Open "/research/<int : task_id>/"
Browser->>Router : Resolve URL pattern
Router->>RV : Call research_task_detail(task_id)
RV->>Models : Load ResearchTask and prefetch stages/substages/products
Models-->>RV : Hierarchical data
RV-->>Browser : Render research_task_detail.html
User->>Browser : Change product status via AJAX
Browser->>Router : POST "/research/product/<int : product_id>/status/"
Router->>PV : Call update_product_status(product_id)
PV->>Models : Update ResearchProduct.status
Models-->>PV : Updated product
PV-->>Browser : JSON success response
```

**Diagram sources**
- [urls.py:74-82](file://tasks/urls.py#L74-L82)
- [research_views.py:54-86](file://tasks/views/research_views.py#L54-L86)
- [product_views.py:29-48](file://tasks/views/product_views.py#L29-L48)
- [models.py:681-791](file://tasks/models.py#L681-L791)

## Detailed Component Analysis

### Three-Tier Hierarchy and Lifecycle
- ResearchTask: Root entity with project metadata, timeline, and funding. It aggregates ResearchStages.
- ResearchStage: Phase-level grouping with performers and responsible person. It aggregates ResearchSubstages.
- ResearchSubstage: Activity-level grouping with performers and responsible person. It aggregates ResearchProducts.
- ResearchProduct: Deliverable with status, dates, responsible person, and multiple performers via ProductPerformer.

```mermaid
classDiagram
class ResearchTask {
+title
+tz_number
+customer
+executor
+start_date
+end_date
+funding_years
}
class ResearchStage {
+stage_number
+title
+start_date
+end_date
+performers
+responsible
+research_task
}
class ResearchSubstage {
+substage_number
+title
+description
+start_date
+end_date
+performers
+responsible
+stage
}
class ResearchProduct {
+name
+description
+due_date
+research_task
+research_stage
+research_substage
+product_type
+planned_start
+planned_end
+actual_start
+actual_end
+status
+completion_percent
+notes
+responsible
}
class Employee {
+full_name
+short_name
+staff_positions
}
class ProductPerformer {
+employee
+role
+contribution_percent
+start_date
+end_date
+product
}
ResearchTask "1" --> "many" ResearchStage : "has stages"
ResearchStage "1" --> "many" ResearchSubstage : "has substages"
ResearchSubstage "1" --> "many" ResearchProduct : "produces"
Employee "many" --> "many" ResearchProduct : "performer via ProductPerformer"
ResearchProduct "1" --> "1" Employee : "responsible"
ResearchStage "1" --> "1" Employee : "responsible"
ResearchSubstage "1" --> "1" Employee : "responsible"
```

**Diagram sources**
- [models.py:384-791](file://tasks/models.py#L384-L791)

**Section sources**
- [models.py:448-531](file://tasks/models.py#L448-L531)
- [models.py:487-524](file://tasks/models.py#L487-L524)
- [models.py:681-791](file://tasks/models.py#L681-L791)

### ResearchTask Detail View: Statistics, Progress, Completion Metrics
The ResearchTask detail view aggregates:
- Stage, substage, and product counts
- Completed product count and overall progress percentage
- Per-stage and per-substage lists with links to deeper views
- Inline status updates for products via AJAX

```mermaid
flowchart TD
Start(["Load ResearchTask Detail"]) --> FetchStages["Fetch stages with substages and products"]
FetchStages --> ComputeTotals["Compute totals:<br/>stages, substages, products"]
ComputeTotals --> CountCompleted["Count completed products"]
CountCompleted --> CalcProgress["progress = completed/total * 100"]
CalcProgress --> RenderView["Render template with stats and progress"]
RenderView --> UserActions{"User actions?"}
UserActions --> |Change product status| AjaxUpdate["AJAX update status"]
AjaxUpdate --> Reload["Reload page or update UI"]
UserActions --> |Navigate| Navigate["Open stage/substage/product detail"]
```

**Diagram sources**
- [research_views.py:54-86](file://tasks/views/research_views.py#L54-L86)
- [research_task_detail.html:136-170](file://tasks/templates/tasks/research_task_detail.html#L136-L170)

**Section sources**
- [research_views.py:54-86](file://tasks/views/research_views.py#L54-L86)
- [research_task_detail.html:136-170](file://tasks/templates/tasks/research_task_detail.html#L136-L170)

### ResearchStage Detail View
Displays stage-level information, associated substages, and quick navigation to performer assignment.

**Section sources**
- [research_views.py:89-99](file://tasks/views/research_views.py#L89-L99)

### ResearchSubstage Detail View
Shows substage details, progress bar, and list of associated products with status badges and performer information.

**Section sources**
- [research_views.py:103-116](file://tasks/views/research_views.py#L103-L116)
- [research_substage_detail.html:1-105](file://tasks/templates/tasks/research_substage_detail.html#L1-L105)

### ResearchProduct Detail View and Status Tracking
- Displays product metadata, status, timeline, and notes.
- Provides a dropdown to update status and a progress bar.
- Lists assigned performers with roles and contribution percentages.

```mermaid
sequenceDiagram
participant User as "User"
participant Browser as "Browser"
participant Router as "urls.py"
participant PV as "product_views.py"
participant Models as "models.py"
User->>Browser : Select new status for product
Browser->>Router : POST "/research/product/<int : product_id>/status/"
Router->>PV : update_product_status(product_id)
PV->>Models : Set ResearchProduct.status
Models-->>PV : Persisted product
PV-->>Browser : JSON {success, status, status_display}
Browser->>Browser : Update badge and progress UI
```

**Diagram sources**
- [urls.py:81-82](file://tasks/urls.py#L81-L82)
- [product_views.py:29-48](file://tasks/views/product_views.py#L29-L48)
- [research_product_detail.html:305-326](file://tasks/templates/tasks/research_product_detail.html#L305-L326)

**Section sources**
- [research_product_detail.html:1-221](file://tasks/templates/tasks/research_product_detail.html#L1-L221)
- [product_views.py:9-26](file://tasks/views/product_views.py#L9-L26)

### Performer Assignment Across Hierarchy
- Assign performers and responsible person at ResearchStage, ResearchSubstage, and ResearchProduct levels.
- ResearchSubstage inherits performers from its parent stage if not set.
- ResearchProduct uses ProductPerformer to associate multiple employees with roles and contribution percentages.

```mermaid
sequenceDiagram
participant User as "User"
participant Browser as "Browser"
participant Router as "urls.py"
participant RV as "research_views.py"
participant PV as "product_views.py"
participant Models as "models.py"
User->>Browser : Click "Assign performers" on stage/substage/product
Browser->>Router : GET "/research/assign/<str : item_type>/<int : item_id>/"
Router->>RV : assign_research_performers(item_type, item_id)
RV-->>Browser : Render assign form with employees
User->>Browser : Submit performers and responsible
Browser->>Router : POST "/research/assign/<str : item_type>/<int : item_id>/"
Router->>RV : assign_research_performers(... post ...)
RV->>Models : Set performers and responsible
Models-->>RV : Saved item
RV-->>Browser : Redirect to detail view
User->>Browser : Assign performers to product
Browser->>Router : GET "/product/<int : product_id>/assign-performers/"
Router->>PV : product_assign_performers(product_id)
PV-->>Browser : Render assign-performers form
User->>Browser : Submit performers and responsible
Browser->>Router : POST "/product/<int : product_id>/assign-performers/"
Router->>PV : product_assign_performers(... post ...)
PV->>Models : Clear old ProductPerformer entries<br/>Create new ones
Models-->>PV : Saved performers
PV-->>Browser : Redirect to substage/task detail
```

**Diagram sources**
- [urls.py:81-82](file://tasks/urls.py#L81-L82)
- [research_views.py:118-165](file://tasks/views/research_views.py#L118-L165)
- [product_assign_performers.html:122-284](file://tasks/templates/tasks/product_assign_performers.html#L122-L284)
- [product_views.py:51-170](file://tasks/views/product_views.py#L51-L170)

**Section sources**
- [research_views.py:118-165](file://tasks/views/research_views.py#L118-L165)
- [product_assign_performers.html:122-284](file://tasks/templates/tasks/product_assign_performers.html#L122-L284)
- [product_views.py:51-170](file://tasks/views/product_views.py#L51-L170)
- [models.py:525-531](file://tasks/models.py#L525-L531)

### Practical Examples

- Creating a ResearchWorkflow
  - Use the ResearchTask form to create a project with title, customer, executor, dates, and goals.
  - Add ResearchStage entries with stage numbers and titles.
  - Add ResearchSubstage entries under each stage with activity titles and dates.
  - Create ResearchProduct entries under substages to represent deliverables.

- Managing Stage Transitions
  - Update ResearchStage start/end dates and status.
  - Assign performers/responsible at stage level; ResearchSubstage can inherit performers automatically.

- Tracking Project Completion
  - Monitor progress percentage computed from completed products.
  - Use ResearchProduct status updates to reflect completion milestones.

- Integration with Task Management and Organization
  - ResearchTask integrates with the broader task system via shared Employee and Department models.
  - Performer assignment leverages Employee and StaffPosition relationships.

**Section sources**
- [forms.py:71-140](file://tasks/forms.py#L71-L140)
- [models.py:13-162](file://tasks/models.py#L13-L162)
- [models.py:525-531](file://tasks/models.py#L525-L531)

## Dependency Analysis
- Model dependencies:
  - ResearchTask → ResearchStage
  - ResearchStage → ResearchSubstage
  - ResearchSubstage → ResearchProduct
  - Employee ↔ ResearchProduct via ProductPerformer
  - Employee ↔ ResearchStage, ResearchSubstage via ManyToMany
- View dependencies:
  - research_task_detail depends on ResearchTask and prefetches stages/substages/products.
  - product_assign_performers depends on filtering Employees by Department via StaffPosition.
- Template dependencies:
  - research_task_detail.html renders nested accordion and progress UI.
  - product_assign_performers.html provides a searchable, filterable employee grid with Select2.

```mermaid
graph LR
RT["ResearchTask"] --> RS["ResearchStage"]
RS --> RSub["ResearchSubstage"]
RSub --> RP["ResearchProduct"]
Emp["Employee"] -- "ManyToMany" --> RS
Emp -- "ManyToMany" --> RSub
Emp -- "ManyToMany" --> RP
Perf["ProductPerformer"] --> RP
Perf --> Emp
```

**Diagram sources**
- [models.py:384-791](file://tasks/models.py#L384-L791)

**Section sources**
- [models.py:384-791](file://tasks/models.py#L384-L791)
- [product_assign_performers.html:96-157](file://tasks/templates/tasks/product_assign_performers.html#L96-L157)

## Performance Considerations
- Use select_related and prefetch_related in views to minimize N+1 queries when rendering hierarchical data.
- Leverage database indexes on foreign keys and frequently filtered fields (e.g., status, dates).
- Cache organization chart data and avoid recalculating expensive computations on each request.
- Limit rendered lists to paginated subsets when dealing with large hierarchies.

## Troubleshooting Guide
- Status update failures:
  - Verify CSRF token presence in AJAX requests.
  - Confirm endpoint routes match URL patterns.
- Missing performers after assignment:
  - Ensure POST parameters include performers list and responsible ID.
  - Check that ProductPerformer entries are cleared and recreated properly.
- Inheritance issues:
  - ResearchSubstage inherit_performers_from_stage only applies when substage performers are empty.

**Section sources**
- [research_task_detail.html:305-326](file://tasks/templates/tasks/research_task_detail.html#L305-L326)
- [product_views.py:56-89](file://tasks/views/product_views.py#L56-L89)
- [models.py:525-531](file://tasks/models.py#L525-L531)

## Conclusion
The Research Workflow Management system provides a structured approach to organizing research projects across three hierarchical levels, with robust support for performer assignment, status tracking, and milestone management. Its integration with the broader task management and organizational structure ensures scalability and maintainability for complex research portfolios.