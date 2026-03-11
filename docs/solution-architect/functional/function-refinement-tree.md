
- Is a hierarchical representation refining the system purpose to individual services. 
- serve as a simple representation of the system/sub-system  ...
**Expected output**

It must be a JSON file conforming to function-refinement-tree.schema.json:

function-refinement-tree.json


# Guidelines

## Build
- MUST ALWAYS mention an enviroment goal to which it contributes
- MUST not represent system/sub-system decomposition (that belongs in decomposition diagrams)
- Responsabilities many not have a definite starting poin and may not be identifiable with a definite interaction
- The [system-services](../GLOSSARY.md) are to be ALWAYS palced as teh leafs of the tree

- The higher-level function MUST explain why a lower-level function should be present
- The lower-level functions MUST explain what a higher-level function does for the [enviroment](../GLOSSARY.md)


## Rules of Thumb

- The mission-statement.json purpose MUST sit at the root of the tree
- Represent refinement relations where higher-level explains WHY lower-level exists, and lower-level explains WHAT higher-level does

- Each node represents a function for the [**environment**](../GLOSSARY.md), not an internal component

- Refine to the level of system services but not beyond **atomic transactions** [../GLOSSARY.md]

- Distinguish product properties from design/process properties

- Distinguish requirements (needed for emergent properties) from constraints (forced by solution environment)

- Distinguish services (interactions delivering value) from quality attributes (indicators of value amount)

- Identify primary services (independent) versus features (incremental pieces)

- Include supporting services: maintenance, database administration, backup/recovery


### Validation

- Traversing UP the tree: clear motivation chain leading to the mission statement

- Traversing DOWN the tree: detailed functions realizing abstract functions

- Consistency with Mission Statement responsibilities

- Tree does not exceed atomic transaction granularity

- All [system services](../GLOSSARY.md) (This are the ones listed on the service-description.json) appear at or near leaves

- Services suffice to achieve solution goals from business specification

