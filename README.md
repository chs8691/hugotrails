# hugotrails
Manage and refurbish your activity files (e.g. tcx), enrich the data with additional attributs  and host them as static website with HUGO

@startuml component
actor client
node app
database db

db -> app
app -> client
@enduml
