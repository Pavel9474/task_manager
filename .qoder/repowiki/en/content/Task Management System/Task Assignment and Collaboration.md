# Task Assignment and Collaboration

<cite>
**Referenced Files in This Document**
- [models.py](file://tasks/models.py)
- [task_views.py](file://tasks/views/task_views.py)
- [employee_views.py](file://tasks/views/employee_views.py)
- [subtask_views.py](file://tasks/views/subtask_views.py)
- [research_views.py](file://tasks/views/research_views.py)
- [product_views.py](file://tasks/views/product_views.py)
- [forms.py](file://tasks/forms.py)
- [0002_add_m2m_performers.py](file://tasks/migrations/0002_add_m2m_performers.py)
- [product_assign_performers.html](file://tasks/templates/tasks/product_assign_performers.html)
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
This document explains the task assignment and collaboration features in the system, focusing on:
- The many-to-many relationship between tasks and employees
- Assignment workflows and performer management
- The task_assign_employees view, filtering by department and search
- Bulk assignment operations
- Assignment validation, conflict resolution, and assignment history tracking
- How assignments propagate through the task hierarchy (task → subtasks and research stages)

## Project Structure
The assignment and collaboration features span models, views, forms, migrations, and templates:
- Models define the relationships and hierarchy (Task, Subtask, Employee, Research* models)
- Views implement assignment workflows and filtering
- Forms constrain selections and enforce validation
- Migrations introduce performer relationships
- Templates provide the UI for assignment and filtering

```mermaid
graph TB
subgraph "Models"
E["Employee"]
T["Task"]
S["Subtask"]
RS["ResearchStage"]
RSub["ResearchSubstage"]
RP["ResearchProduct"]
PP["ProductPerformer"]
end
subgraph "Views"
TV["task_views.py"]
EV["employee_views.py"]
SV["subtask_views.py"]
RV["research_views.py"]
PV["product_views.py"]
end
subgraph "Forms"
F["forms.py"]
end
subgraph "Migrations"
M["0002_add_m2m_performers.py"]
end
subgraph "Templates"
TP["product_assign_performers.html"]
end
T -- "ManyToMany: assigned_to" --> E
S -- "ManyToMany: performers" --> E
S -- "ForeignKey: responsible" --> E
RS -- "ManyToMany: performers" --> E
RS -- "ForeignKey: responsible" --> E
RSub -- "ManyToMany: performers" --> E
RSub -- "ForeignKey: responsible" --> E
RP -- "ManyToMany: performers" --> E
RP -- "ForeignKey: responsible" --> E
RP -- "OneToMany: product_performers" --> PP
TV --> T
EV --> E
SV --> S
RV --> RS
PV --> RP
F --> T
M --> RP
TP --> PV
```

**Diagram sources**
- [models.py:165-382](file://tasks/models.py#L165-L382)
- [models.py:448-531](file://tasks/models.py#L448-L531)
- [models.py:681-791](file://tasks/models.py#L681-L791)
- [task_views.py:301-340](file://tasks/views/task_views.py#L301-L340)
- [employee_views.py:18-332](file://tasks/views/employee_views.py#L18-L332)
- [subtask_views.py:10-65](file://tasks/views/subtask_views.py#L10-L65)
- [research_views.py:118-165](file://tasks/views/research_views.py#L118-L165)
- [product_views.py:50-170](file://tasks/views/product_views.py#L50-L170)
- [forms.py:5-44](file://tasks/forms.py#L5-L44)
- [0002_add_m2m_performers.py:1-16](file://tasks/migrations/0002_add_m2m_performers.py#L1-L16)
- [product_assign_performers.html:1-594](file://tasks/templates/tasks/product_assign_performers.html#L1-L594)

**Section sources**
- [models.py:165-382](file://tasks/models.py#L165-L382)
- [models.py:448-531](file://tasks/models.py#L448-L531)
- [models.py:681-791](file://tasks/models.py#L681-L791)
- [task_views.py:301-340](file://tasks/views/task_views.py#L301-L340)
- [employee_views.py:18-332](file://tasks/views/employee_views.py#L18-L332)
- [subtask_views.py:10-65](file://tasks/views/subtask_views.py#L10-L65)
- [research_views.py:118-165](file://tasks/views/research_views.py#L118-L165)
- [product_views.py:50-170](file://tasks/views/product_views.py#L50-L170)
- [forms.py:5-44](file://tasks/forms.py#L5-L44)
- [0002_add_m2m_performers.py:1-16](file://tasks/migrations/0002_add_m2m_performers.py#L1-L16)
- [product_assign_performers.html:1-594](file://tasks/templates/tasks/product_assign_performers.html#L1-L594)

## Core Components
- Task and Employee many-to-many relationship via assigned_to
- Subtask performer management via performers and responsible
- Research hierarchy performer management via ResearchStage, ResearchSubstage, ResearchProduct
- ProductPerformer for ResearchProduct to capture roles and contributions
- Forms validating time ranges and constraining selections to active employees
- Migrations introducing performer relationships for ResearchProduct

Key implementation references:
- Task assigned_to relationship: [models.py:191-197](file://tasks/models.py#L191-L197)
- Subtask performers/responsible: [models.py:269-285](file://tasks/models.py#L269-L285)
- Research hierarchy performers/responsible: [models.py:462-475](file://tasks/models.py#L462-L475), [models.py:502-515](file://tasks/models.py#L502-L515)
- ResearchProduct performers via ProductPerformer: [models.py:681-791](file://tasks/models.py#L681-L791), [models.py:793-800](file://tasks/models.py#L793-L800)
- Task assignment view (department and search): [task_views.py:301-340](file://tasks/views/task_views.py#L301-L340)
- Bulk subtask creation with performer assignment: [subtask_views.py:134-189](file://tasks/views/subtask_views.py#L134-L189)
- Research performer assignment: [research_views.py:118-165](file://tasks/views/research_views.py#L118-L165)
- ResearchProduct performer assignment: [product_views.py:50-170](file://tasks/views/product_views.py#L50-L170)
- Form constraints for active employees: [forms.py:27-30](file://tasks/forms.py#L27-L30), [forms.py:112-115](file://tasks/forms.py#L112-L115), [forms.py:135-139](file://tasks/forms.py#L135-L139)
- ResearchProduct performers migration: [0002_add_m2m_performers.py:1-16](file://tasks/migrations/0002_add_m2m_performers.py#L1-L16)

**Section sources**
- [models.py:165-382](file://tasks/models.py#L165-L382)
- [models.py:448-531](file://tasks/models.py#L448-L531)
- [models.py:681-791](file://tasks/models.py#L681-L791)
- [task_views.py:301-340](file://tasks/views/task_views.py#L301-L340)
- [subtask_views.py:134-189](file://tasks/views/subtask_views.py#L134-L189)
- [research_views.py:118-165](file://tasks/views/research_views.py#L118-L165)
- [product_views.py:50-170](file://tasks/views/product_views.py#L50-L170)
- [forms.py:27-30](file://tasks/forms.py#L27-L30)
- [forms.py:112-115](file://tasks/forms.py#L112-L115)
- [forms.py:135-139](file://tasks/forms.py#L135-L139)
- [0002_add_m2m_performers.py:1-16](file://tasks/migrations/0002_add_m2m_performers.py#L1-L16)

## Architecture Overview
Assignment workflows are implemented as view handlers that:
- Filter employees by department and search terms
- Set ManyToMany relationships for tasks and subtasks
- Assign responsible persons for subtasks and research items
- Persist assignments and provide feedback

```mermaid
sequenceDiagram
participant U as "User"
participant V as "task_views.py"
participant M as "models.py"
participant DB as "Database"
U->>V : "GET task/<id>/assign_employees/"
V->>M : "Query Task and Employees (filtered)"
M-->>V : "Task + filtered Employees"
V-->>U : "Render assignment form"
U->>V : "POST assign employees"
V->>M : "Set Task.assigned_to IDs"
M->>DB : "Update m2m rows"
DB-->>M : "OK"
M-->>V : "Saved Task"
V-->>U : "Redirect with success message"
```

**Diagram sources**
- [task_views.py:301-340](file://tasks/views/task_views.py#L301-L340)
- [models.py:165-197](file://tasks/models.py#L165-L197)

**Section sources**
- [task_views.py:301-340](file://tasks/views/task_views.py#L301-L340)
- [models.py:165-197](file://tasks/models.py#L165-L197)

## Detailed Component Analysis

### Task Assignment Workflow
- Endpoint: task/<int:task_id>/assign_employees/
- Filters:
  - Department: GET parameter "department" applied to Employee.filter(department=...)
  - Search: GET parameter "search" applied to Employee filter by name/email
- Operation:
  - On POST: collect selected employee IDs and set Task.assigned_to
  - On GET: prepare employee list, current assignment IDs, and filters

```mermaid
flowchart TD
Start(["Open task assignment"]) --> Load["Load Task and Employees"]
Load --> FilterDept{"Department filter?"}
FilterDept --> |Yes| ApplyDept["Filter employees by department"]
FilterDept --> |No| SkipDept["Skip"]
ApplyDept --> FilterSearch{"Search filter?"}
SkipDept --> FilterSearch
FilterSearch --> |Yes| ApplySearch["Filter by name/email"]
FilterSearch --> |No| SkipSearch["Skip"]
ApplySearch --> Render["Render form with current assignments"]
SkipSearch --> Render
Render --> Submit{"POST submit?"}
Submit --> |Yes| Save["Set Task.assigned_to IDs"]
Submit --> |No| End(["Exit"])
Save --> End
```

**Diagram sources**
- [task_views.py:301-340](file://tasks/views/task_views.py#L301-L340)

**Section sources**
- [task_views.py:301-340](file://tasks/views/task_views.py#L301-L340)

### Subtask Performer Assignment and Propagation
- Subtasks maintain a ManyToMany performers and a responsible Employee
- Automatic responsible assignment when a single performer is set
- Bulk creation supports parsing performer names and auto-assigning responsible if only one performer is found

```mermaid
sequenceDiagram
participant U as "User"
participant SV as "subtask_views.py"
participant S as "Subtask Model"
participant DB as "Database"
U->>SV : "POST bulk-create"
SV->>SV : "Parse stage_data and find Employees"
SV->>S : "Create Subtask"
S->>DB : "Insert Subtask"
SV->>S : "Set performers (ManyToMany)"
S->>DB : "Update m2m rows"
SV->>S : "Auto-responsible if single performer"
S->>DB : "Update Subtask.responsible"
SV-->>U : "Success message"
```

**Diagram sources**
- [subtask_views.py:134-189](file://tasks/views/subtask_views.py#L134-L189)
- [models.py:269-285](file://tasks/models.py#L269-L285)

**Section sources**
- [subtask_views.py:134-189](file://tasks/views/subtask_views.py#L134-L189)
- [models.py:269-285](file://tasks/models.py#L269-L285)

### Research Hierarchy Performer Assignment
- ResearchStage and ResearchSubstage support ManyToMany performers and a responsible Employee
- ResearchProduct uses ProductPerformer to track multiple performers with roles and optional contributions

```mermaid
classDiagram
class ResearchStage {
+ManyToMany performers
+ForeignKey responsible
}
class ResearchSubstage {
+ManyToMany performers
+ForeignKey responsible
}
class ResearchProduct {
+ManyToMany performers
+ForeignKey responsible
}
class ProductPerformer {
+ForeignKey product
+ForeignKey employee
+role
+contribution_percent
}
ResearchProduct --> ProductPerformer : "has many"
ResearchStage --> ResearchProduct : "parent"
ResearchSubstage --> ResearchProduct : "parent"
```

**Diagram sources**
- [models.py:462-475](file://tasks/models.py#L462-L475)
- [models.py:502-515](file://tasks/models.py#L502-L515)
- [models.py:681-791](file://tasks/models.py#L681-L791)
- [models.py:793-800](file://tasks/models.py#L793-L800)

**Section sources**
- [models.py:462-475](file://tasks/models.py#L462-L475)
- [models.py:502-515](file://tasks/models.py#L502-L515)
- [models.py:681-791](file://tasks/models.py#L681-L791)
- [models.py:793-800](file://tasks/models.py#L793-L800)

### Research Performer Assignment View
- Supports item_type: stage, substage, product
- Accepts POST lists of performers and a responsible
- Redirects to appropriate detail page after saving

```mermaid
sequenceDiagram
participant U as "User"
participant RV as "research_views.py"
participant RS as "ResearchStage/Substage/Product"
participant DB as "Database"
U->>RV : "POST assign_research_performers"
RV->>RS : "Set performers (ManyToMany)"
RV->>RS : "Set responsible"
RS->>DB : "Update rows"
RV-->>U : "Redirect to detail page"
```

**Diagram sources**
- [research_views.py:118-165](file://tasks/views/research_views.py#L118-L165)

**Section sources**
- [research_views.py:118-165](file://tasks/views/research_views.py#L118-L165)

### ResearchProduct Performer Assignment View
- Provides department-based filtering and advanced search across name and position
- Clears existing ProductPerformer entries and recreates with new performers
- Supports selecting a responsible person

```mermaid
flowchart TD
Start(["Open product_assign_performers"]) --> Load["Load Product and Employees"]
Load --> DeptFilter{"Department filter?"}
DeptFilter --> |Yes| ApplyDept["Filter by staff_positions.department"]
DeptFilter --> |No| SkipDept["Skip"]
ApplyDept --> SearchFilter{"Search query?"}
SkipDept --> SearchFilter
SearchFilter --> |Yes| ApplySearch["Filter by name/position"]
SearchFilter --> |No| SkipSearch["Skip"]
ApplySearch --> Render["Render form with current performers"]
SkipSearch --> Render
Render --> Submit{"POST submit?"}
Submit --> |Yes| Clear["Delete existing ProductPerformer entries"]
Clear --> Create["Create new ProductPerformer for each selected"]
Create --> Responsible["Set product.responsible"]
Responsible --> End(["Redirect to detail"])
Submit --> |No| End
```

**Diagram sources**
- [product_views.py:50-170](file://tasks/views/product_views.py#L50-L170)
- [product_assign_performers.html:1-594](file://tasks/templates/tasks/product_assign_performers.html#L1-L594)

**Section sources**
- [product_views.py:50-170](file://tasks/views/product_views.py#L50-L170)
- [product_assign_performers.html:1-594](file://tasks/templates/tasks/product_assign_performers.html#L1-L594)

### Assignment Validation and Conflict Resolution
- Time range validation in TaskForm prevents invalid start/end/due dates
- Constraints limit selection to active employees in forms
- Subtask automatic responsible assignment reduces manual conflict
- ResearchProduct assignment clears previous performers to avoid conflicts

Validation references:
- Task time validation: [forms.py:32-44](file://tasks/forms.py#L32-L44)
- Active employee constraints: [forms.py:27-30](file://tasks/forms.py#L27-L30), [forms.py:112-115](file://tasks/forms.py#L112-L115), [forms.py:135-139](file://tasks/forms.py#L135-L139)
- Subtask responsible auto-assignment: [models.py:328-340](file://tasks/models.py#L328-L340)
- ResearchProduct performer reset: [product_views.py:60-76](file://tasks/views/product_views.py#L60-L76)

**Section sources**
- [forms.py:32-44](file://tasks/forms.py#L32-L44)
- [forms.py:27-30](file://tasks/forms.py#L27-L30)
- [forms.py:112-115](file://tasks/forms.py#L112-L115)
- [forms.py:135-139](file://tasks/forms.py#L135-L139)
- [models.py:328-340](file://tasks/models.py#L328-L340)
- [product_views.py:60-76](file://tasks/views/product_views.py#L60-L76)

### Assignment History Tracking
- No explicit audit log or history model is present in the analyzed files
- Signals clear organizational cache on Employee/Department/StaffPosition changes, indirectly supporting consistency

References:
- Cache clearing signals: [signals.py:7-32](file://tasks/signals.py#L7-L32)

**Section sources**
- [signals.py:7-32](file://tasks/signals.py#L7-L32)

## Dependency Analysis
- Task.assigned_to ↔ Employee (many-to-many)
- Subtask.performers ↔ Employee (many-to-many)
- Subtask.responsible ↔ Employee (foreign key)
- ResearchStage.performers ↔ Employee (many-to-many)
- ResearchStage.responsible ↔ Employee (foreign key)
- ResearchSubstage.performers ↔ Employee (many-to-many)
- ResearchSubstage.responsible ↔ Employee (foreign key)
- ResearchProduct.performers ↔ Employee (many-to-many)
- ResearchProduct.responsible ↔ Employee (foreign key)
- ResearchProduct → ProductPerformer (one-to-many) for roles and contributions

```mermaid
erDiagram
EMPLOYEE {
int id PK
string last_name
string first_name
string email
boolean is_active
}
TASK {
int id PK
string title
}
SUBTASK {
int id PK
int task_id FK
string stage_number
string title
}
RESEARCH_STAGE {
int id PK
int research_task_id FK
int stage_number
}
RESEARCH_SUBSTAGE {
int id PK
int stage_id FK
}
RESEARCH_PRODUCT {
int id PK
int research_task_id FK
int research_stage_id FK
int research_substage_id FK
}
PRODUCT_PERFORMER {
int id PK
int product_id FK
int employee_id FK
string role
}
TASK ||--o{ EMPLOYEE : "assigned_to"
SUBTASK ||--o{ EMPLOYEE : "performers"
SUBTASK }o--|| EMPLOYEE : "responsible"
RESEARCH_STAGE ||--o{ EMPLOYEE : "performers"
RESEARCH_STAGE }o--|| EMPLOYEE : "responsible"
RESEARCH_SUBSTAGE ||--o{ EMPLOYEE : "performers"
RESEARCH_SUBSTAGE }o--|| EMPLOYEE : "responsible"
RESEARCH_PRODUCT ||--o{ EMPLOYEE : "performers"
RESEARCH_PRODUCT }o--|| EMPLOYEE : "responsible"
RESEARCH_PRODUCT ||--o{ PRODUCT_PERFORMER : "product_performers"
```

**Diagram sources**
- [models.py:165-197](file://tasks/models.py#L165-L197)
- [models.py:269-285](file://tasks/models.py#L269-L285)
- [models.py:462-475](file://tasks/models.py#L462-L475)
- [models.py:502-515](file://tasks/models.py#L502-L515)
- [models.py:681-791](file://tasks/models.py#L681-L791)
- [models.py:793-800](file://tasks/models.py#L793-L800)

**Section sources**
- [models.py:165-197](file://tasks/models.py#L165-L197)
- [models.py:269-285](file://tasks/models.py#L269-L285)
- [models.py:462-475](file://tasks/models.py#L462-L475)
- [models.py:502-515](file://tasks/models.py#L502-L515)
- [models.py:681-791](file://tasks/models.py#L681-L791)
- [models.py:793-800](file://tasks/models.py#L793-L800)

## Performance Considerations
- Filtering by department on employees uses database indexes; ensure indexes exist on Employee.department and Employee.is_active
- Bulk operations (subtask bulk create, ResearchProduct performer reset) iterate over lists; consider batching for very large sets
- Use select_related/prefetch_related in views to minimize N+1 queries when rendering assignment pages
- Caching organizational structure is cleared on Employee/Department/StaffPosition changes to keep UI consistent

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common issues and resolutions:
- Invalid time ranges on Task: ensure start_time ≤ end_time and start_time ≤ due_date
- Employees not selectable: verify they are active and included in form querysets
- Subtask responsible missing: ensure a single performer is set so auto-assignment triggers
- ResearchProduct performers not updating: confirm the view clears existing ProductPerformer entries before re-creating

References:
- Time validation: [forms.py:32-44](file://tasks/forms.py#L32-L44)
- Active employee constraints: [forms.py:27-30](file://tasks/forms.py#L27-L30), [forms.py:112-115](file://tasks/forms.py#L112-L115), [forms.py:135-139](file://tasks/forms.py#L135-L139)
- Auto-responsible: [models.py:328-340](file://tasks/models.py#L328-L340)
- Reset performers: [product_views.py:60-76](file://tasks/views/product_views.py#L60-L76)

**Section sources**
- [forms.py:32-44](file://tasks/forms.py#L32-L44)
- [forms.py:27-30](file://tasks/forms.py#L27-L30)
- [forms.py:112-115](file://tasks/forms.py#L112-L115)
- [forms.py:135-139](file://tasks/forms.py#L135-L139)
- [models.py:328-340](file://tasks/models.py#L328-L340)
- [product_views.py:60-76](file://tasks/views/product_views.py#L60-L76)

## Conclusion
The system implements robust task assignment and collaboration through:
- Clear many-to-many relationships between tasks and employees
- Dedicated assignment views with department and search filtering
- Bulk assignment capabilities for subtasks and research items
- Validation and conflict resolution via form constraints and automatic responsible assignment
- Extensible performer management for research hierarchies using ProductPerformer