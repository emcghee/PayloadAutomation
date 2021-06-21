What is Payload Automation?
=================

Payload Automation is a collection of Python classes for automating payload development, testing, opsec checking, and deployment with Cobalt Strike.

Please check out the examples folder for pre-made scripts taking advantage of the functionality provided.

Included Libraries:
 - Striker: A set of functions to interact with Cobalt Strike and execute functionality typically only accessible via Sleep/GUI.
 - Compyler: A set of functions to compile various payloads from platform or cross-platform.
 - Artifactor: A set of functions to inspect and review artifacts and collect and track IoCs.
 - Sleepy: A set of functions to help facilitate a bridge between Sleep objects and Python objects.
 - Detemplate: An incomplete idea of mine to automate the population of template files based on YAML configurations. Meant to be used with more complex payloads with multiple replacements and/or embedding.

Other associated work and credits:
 - Original idea for Striker and some code snipets came from the functionality of Verizon's redshell tool (https://github.com/Verizon/redshell)
 - A similar tool called pycobalt (https://github.com/dcsync/pycobalt) which is worth checking out to see if it better fits your use cases

TODO:
 - Add additional error checking, specifically for application dependencies
 - Expand compyler to include remote builds and mingw
 - Add email functionality to Striker
