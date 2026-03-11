# modules, modules, modules

- Interaction between modules is only through interfaces.
    - The following guidelines apply:
        - Heavily rely on encapsulation and abstraction.
            - Split up your code into modules and try to make as few dependencies between them as possible.

            - Try to make each class a self-sufficient black box that does its job, and the user of this black box 
            does not need to know exactly how the class is implemented (domain expert agent reviewer).
        - Avoid over-abstraction. (This needs further revision by the reviewer or further guidelines)
        
      
        - Never use more than 3 inheritance levels:
            - Level 1 being an interface
            - Level 2 - an implementation
            - Level 3 - a slightly modified implementation for some special case,
        as an example: GenericGPUBuffer -> OpenGLGPUBuffer -> HostAccessibleGPUBuffer. 

        - ALWAYS prioritize composition over inheritance.
        - Only use inheritance for the sake of polymorphism (being able to call functions of an interface having a pointer to an implementation of that interface).

        - Rely heavily on diagrams to place interfaces. How? See below.

        In the organigram (SuD diagram shared by the modeling team):      
            - Look for objects that are used by only one other object. Ask:

            Are these both fixed?
                If they are unlikely to change or are likely to change together as the system evolves, 
                    then consider combining them.
                If they change independently,
                    it is not a good area to consider for encapsulation.

                Send your changes to the reviewer and apply feedback.

        In the layering diagram, look for collections of objects that are always used together. Ask:
  
        Can these be grouped together in a higher-level interface to manage the objects?
         
        - Can they be broken apart and simplified?
        - Can the dependencies be grouped together?
        - Can the interfaces between vertical neighbors be described in a few sentences?

For every single one of these questions, send them to the reviewer and always wait for feedback before proceeding.

That makes it a good place for encapsulation to help you create an interface (for others to reuse your code or just for ease of testing).

