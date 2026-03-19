- is the most general specification $S$ of the system/sub-system under development

- serves as the foundational document from which all other documentation derives meaning. 


**Expected output**

It must be a JSON file conforming to mission-stament.schema.json:

# Guidelines

### Purpose
- MUST articulate why someone would pay for the service.

### Responsibilities

- MUST be organized by kind of added value delivered. (Specific sentence structures and verbs allowed)

- MUST start with "It is a responsibility to support ___ $g_i$" where $g_i$ is any of the solution goals

- MUST be described in only one or two sentences maximum
- MUST map one-to-many to the refinement of the environment goal into subgoals from the goal-tree.json

- Every responsibility must reference the environment goal it serves

### Exclusion

- MUST be described in only one or two sentences maximum
- MUST state responsibilities the system/sub-system will not have
- MUST start with "The system will not support ..."

## Rules of Thumb

- Write a statement of purpose that summarizes the business solution goals to be realized and that can finish the statement

"The purpose of the system/sub-system is ..."

- Organize system responsibilities according to:
    - The business goals they contribute to
    - The business process in which they are used
    - The external entities that are needed to exercise responsibilities
    - CRITICAL: The kind of added value they deliver to the [environment](../GLOSSARY.md)

- Include the reason why a particular functionality or responsibility has been excluded from the scope of the system/sub-system under development