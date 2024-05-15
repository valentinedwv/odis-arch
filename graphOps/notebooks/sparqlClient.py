import sparqldataframe


local = "http://localhost:7878/query"
oih = "http://graph.oceaninfohub.org/blazegraph/namespace/ocd/sparql"


rp1 = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
prefix prov: <http://www.w3.org/ns/prov#>
PREFIX schema: <https://schema.org/>


SELECT DISTINCT (?s as ?id)  ?type ?name ?url ?description ?headline ?g
WHERE {
      graph ?g {

         ?s rdf:type ?type .
        OPTIONAL { ?s schema:name ?name . }
        OPTIONAL { ?s schema:description ?description . }
        OPTIONAL { ?s schema:url ?url . }
        OPTIONAL { ?s schema:headline ?headline . }
     }
 }
"""

df = sparqldataframe.query(local, rp1)

print(df.info())