

# ### Imports

import streamlit as st
from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import numpy as np
import json
import geopandas
import shapely
import time
from datetime import datetime
import yaml
import urllib.request
from emoji import emojize
import os
import glob

#### Set vars & paths

oihGraphEndpoint = "http://graph.oceaninfohub.org/blazegraph/namespace/oih/sparql"
#oihCollab = "https://ts.collaborium.io/blazegraph/namespace/oih/sparql"
#oihdevCollab = "https://ts.collaborium.io/blazegraph/namespace/development/sparql"
#oihinvemarCollab = "https://ts.collaborium.io/blazegraph/namespace/invemar/sparql"
#oihadCollab = "https://graph.collaborium.io/blazegraph/namespace/aquadocs/sparql"

odisArchGitMasterPath = "/home/apps/odis-arch-git-master-DO-NOT-TOUCH"
odisArchGitSchemaDevPath = "/home/apps/odis-arch-git-schema-dev-DO-NOT-TOUCH"
dashboardPath = "/home/apps/odis-dashboard/dashboard"

#### Support Functions

# checkout latest from branches
os.chdir(odisArchGitMasterPath)
pullMasterOutput = os.system("git pull > gitstatus.txt")
os.chdir(odisArchGitSchemaDevPath)
pullSchemaDevOutput = os.system("git pull > gitstatus.txt")

os.chdir(dashboardPath)


def get_sparql_dataframe(service, query):
    """
    Helper function to convert SPARQL results into a Pandas data frame.
    """
    sparql = SPARQLWrapper(service)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    result = sparql.query()

    processed_results = json.load(result.response)
    cols = processed_results['head']['vars']

    out = []
    for row in processed_results['results']['bindings']:
        item = []
        for c in cols:
            item.append(row.get(c, {}).get('value'))
        out.append(item)

    return pd.DataFrame(out, columns=cols)


### Queries
# 
# What follows is a set of queries designed to provide a feel 
# for the OIH graph

#### Simple Count
# 
# How many triples are there?

rq_count = """SELECT (COUNT(*) as ?Triples) 
WHERE 
  {
      { ?s ?p ?o } 
  }
"""

#@st.cache(allow_output_mutation=True)
dfCount = get_sparql_dataframe(oihGraphEndpoint, rq_count)
#dfCount["Triples"] = dfCount["Triples"].astype(int) # convert count c to int

#### List of orgs

rq_orgs = """prefix prov: <http://www.w3.org/ns/prov#>
        PREFIX con: <http://www.ontotext.com/connectors/lucene#>
        PREFIX luc: <http://www.ontotext.com/owlim/lucene#>
        PREFIX con-inst: <http://www.ontotext.com/connectors/lucene/instance#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX schema: <https://schema.org/>
        PREFIX schemaold: <http://schema.org/>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

          SELECT ?orgname
            WHERE 
             {
               ?wat rdf:name ?orgname
             }
            ORDER BY ASC(?orgname)
          """
#@st.cache(allow_output_mutation=True)
dfOrgs = get_sparql_dataframe(oihGraphEndpoint, rq_orgs)

#### PROV: count of catalogues

rq_prov = """prefix prov: <http://www.w3.org/ns/prov#>
        PREFIX con: <http://www.ontotext.com/connectors/lucene#>
        PREFIX luc: <http://www.ontotext.com/owlim/lucene#>
        PREFIX con-inst: <http://www.ontotext.com/connectors/lucene/instance#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX schema: <https://schema.org/>
        PREFIX schemaold: <http://schema.org/>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

       SELECT   ( COUNT(?hm) as ?count) ?wat  ?orgname ?domain
        WHERE
        {
           ?hm prov:wasAttributedTo ?wat .
           ?wat rdf:name ?orgname .
           ?wat rdfs:seeAlso ?domain
        }
        GROUP BY ?wat ?orgname ?domain
        """

#@st.cache(allow_output_mutation=True)     
dfProv = get_sparql_dataframe(oihGraphEndpoint, rq_prov)
dfProv['count'] = dfProv["count"].astype(int) # convert count c to int
dfProv.set_index('orgname', inplace=True)

#dfProv.info()

#### Types (patterns)
     
rq_types = """prefix prov: <http://www.w3.org/ns/prov#>
        PREFIX con: <http://www.ontotext.com/connectors/lucene#>
        PREFIX luc: <http://www.ontotext.com/owlim/lucene#>
        PREFIX con-inst: <http://www.ontotext.com/connectors/lucene/instance#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX schema: <https://schema.org/>
        PREFIX schemaold: <http://schema.org/>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

 
       SELECT   ( COUNT(?type) as ?count) ?type   
        WHERE
        {
        
           ?s rdf:type ?type .
           FILTER ( ?type IN (schema:ResearchProject, schema:Project, schema:Organization, schema:Dataset, schema:CreativeWork, schema:Person, schema:Map, schema:Course, schema:CourseInstance, schema:Event, schema:Vehicle) )

        }
        GROUP BY ?type  
        ORDER BY DESC(?count)
        """

#@st.cache(allow_output_mutation=True)        
dfTypes = get_sparql_dataframe(oihGraphEndpoint, rq_types)
dfTypes['count'] = dfTypes["count"].astype(int) # convert count c to int
dfTypes.set_index('type', inplace=True)
#dfTypes.head(10)

#### Keywords

rq_keywords = """prefix prov: <http://www.w3.org/ns/prov#>
        PREFIX con: <http://www.ontotext.com/connectors/lucene#>
        PREFIX luc: <http://www.ontotext.com/owlim/lucene#>
        PREFIX con-inst: <http://www.ontotext.com/connectors/lucene/instance#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX schema: <https://schema.org/>
        PREFIX schemaold: <http://schema.org/>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

        SELECT DISTINCT  ?keywords  ( COUNT(?keywords) as ?count )  
        WHERE
        {
           ?s schema:keywords ?keywords
        }
        GROUP BY ?keywords  
        ORDER BY DESC(?count)
        """

#@st.cache(allow_output_mutation=True)
dfKeywords = get_sparql_dataframe(oihGraphEndpoint, rq_keywords)
dfKeywords['count'] = dfKeywords["count"].astype(int) # convert count c to int
dfKeywords.set_index('keywords', inplace=True)
#dfKeywords.head(10)

#### Predicates

rq_pcount = """SELECT ?p (COUNT(?p) as ?pCount)
WHERE
{
  ?s ?p ?o .
}
GROUP BY ?p
"""
#@st.cache(allow_output_mutation=True)
dfPredicates = get_sparql_dataframe(oihGraphEndpoint, rq_pcount)
dfPredicates['pCount'] = dfPredicates["pCount"].astype(int) # convert count to int
dfPredicates_sorted = dfPredicates.sort_values('pCount', ascending=False)
dfPredicates_sorted.columns = dfPredicates_sorted.columns.str.replace('p', 'Predicate')
dfPredicates_sorted.columns = dfPredicates_sorted.columns.str.replace('pCount', 'Count')
dfPredicates_sorted.set_index('Predicate', inplace=True)
#dfPredicates_sorted.head(10)

#### Spatial Predicates

rq_wktcount = """SELECT (COUNT(?s) as ?sCount)
WHERE
{
  {
  ?s <http://www.opengis.net/ont/geosparql#hasGeometry> ?o .
}
UNION
{
  ?s <https://schema.org/spatialCoverage> ?o
  }
}
"""

dfWKTCount = get_sparql_dataframe(oihGraphEndpoint, rq_wktcount)
dfWKTCount['sCount'] = dfWKTCount["sCount"].astype(int) # convert count to int
# dfWKTCount.set_index('p', inplace=True)

### Join latest sitemap checker output with sources.yaml

with open(odisArchGitSchemaDevPath + '/config/sources.yaml', 'r') as f:
    dfSources = pd.json_normalize(yaml.safe_load_all(f), 'sources')

#os.system("git ls-tree --name-only HEAD > filelist.txt")
list_of_files = glob.glob(odisArchGitMasterPath + '/workflows/output/*.csv')
latest_file_path = max(list_of_files, key=os.path.getmtime)
latest_file_name = os.path.basename(latest_file_path)
latest_file_date = latest_file_name.split('T')[0] 

#dateToday = datetime.today().strftime('%Y-%m-%d')
sitemapCheckerRawUrl = "https://raw.githubusercontent.com/iodepo/odis-arch/master/workflows/output/" + latest_file_name
sitemapCheckerBlobUrl = "https://github.com/iodepo/odis-arch/blob/master/workflows/output/" + latest_file_name
urllib.request.urlretrieve(sitemapCheckerRawUrl, odisArchGitMasterPath + "/workflows/output/" + latest_file_name)
dfSitemap = pd.read_csv(odisArchGitMasterPath + "/workflows/output/" + latest_file_name)
#dfSitemap
# names = df['propername'].tolist()
# dates = df['dates'].tolist()
#dfJoinedRaw = dfSources.join(dfSitemap, lsuffix='name', rsuffix='name')
dfJoinedRaw = dfSources.set_index('name').join(dfSitemap.set_index('name'), lsuffix='_sources', rsuffix='_sitemap')
dfJoined = dfSources.set_index('name').join(dfSitemap.set_index('name'), lsuffix='_sources', rsuffix='_sitemap')

######
# page setup
######

#st.set_option('deprecation.showPyplotGlobalUse', False)

st.set_page_config(
    page_title="OIH Dashboard",
    page_icon="https://oceaninfohub.org/wp-content/uploads/2020/11/logo-only_OIH_EPS-CMYK-100x100.png",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
         'Report a bug': "https://github.com/iodepo/odis-arch/issues",
         'Get Help': 'https://oceaninfohub.org/contact-2/',         
         'About': "Dashboard demo by [jmckenna](https://github.com/jmckenna)"
    }   
)

# dashboard title
st.title("OIH Dashboard")
st.markdown("This dashboard will help monitor the OIH graph, as well as the nodes connected to it.")

#sidebar glossary
with st.sidebar:
    st.header('Glossary')
    st.subheader('ODIS')
    st.markdown('The Ocean Data Information System (ODIS) is managed by the [Ocean InfoHub](https://oceaninfohub.org/) (OIH) and is based on a community-maintained Knowledge Graph, that leverages the [schema.org](https://schema.org) framework.  See the [ODIS book](https://book.oceaninfohub.org/) of documentation.')    
    st.subheader('Graph')
    st.markdown('Also known as Knowledge Graph, or KG, graphs are a structured way to harvest information on the Web, by representing entities (eg. people, places, objects) as nodes, and relationships between entities.  The connection between 2 nodes is defined by triples.')
    st.subheader('Node')
    st.markdown('The ODIS graph consists of many nodes, which represent organizations, each with their own catalogue of data.')
    st.subheader('Triple')
    st.markdown('The ODIS graph connects information through a triple; *Subject, Predicate, Object*.  In the information "Leonard Nimoy was an actor who played the character Spock", LeonardNimoy is the *Subject*, "played" is the *Predicate*, and "Spock" is the *Object*.')    
    st.subheader('Types')
    st.markdown('The ODIS graph leverages core [thematic patterns](https://book.oceaninfohub.org/thematics/README.html), which are expanded from [schema.org](https://schema.org/docs/full.html) types.')    

#st.header("OIH Graph Summary")
with st.expander("OIH Graph Summary", expanded=True):

    #use markdown trick, as st.expander label cannot be styled
    #      see https://github.com/streamlit/streamlit/issues/2056
    st.markdown(
    """
    <style>
    .streamlit-expanderHeader {
      font-size: large;
    }
    </style>
    """,
    unsafe_allow_html=True,
    )

    sumCol1, sumCol2, sumCol3 = st.columns(3, gap="medium")

    with sumCol1:
        st.write("Size of OIH graph")
        st.subheader(dfCount['Triples'].values[0] + " triples")

    with sumCol2:
        st.write("Number of Nodes")
        st.subheader(len(dfOrgs))

    with sumCol3:
        st.write("Number of Catalogues")
        st.subheader(dfProv['count'].sum())
    
    sumCol4, sumCol5, sumCol6 = st.columns(3, gap="medium")

    with sumCol4:
        st.write("Sitemap status (source [csv](" + sitemapCheckerBlobUrl + "))")
        #st.write(emojize(":smiling_face_with_sunglasses:"))
        #st.write(":white_check_mark:")
        dfJoined.columns = dfJoined.columns.str.replace('code', 'Sitemap Status')
        dfJoined.columns = dfJoined.columns.str.replace('propername', 'Node')
        #dfJoined.set_index('Status', inplace=True)
        #dfJoined.loc[dfJoined['Status'] == 0, 'Status'] = 'Valid'
        #dfJoined.loc[dfJoined['Status'] == 1, 'Status'] = 'Failed'        
        #unicode emoji list: https://unicode.org/emoji/charts/emoji-list.html
        #                    https://www.htmlsymbols.xyz/unicode/U+274C
        #        streamlit:  https://streamlit-emoji-shortcodes-streamlit-app-gwckff.streamlit.app/
        dfJoined.loc[dfJoined['Sitemap Status'] == 0, 'Sitemap Status'] = "\u2705"
        dfJoined.loc[dfJoined['Sitemap Status'] == 1, 'Sitemap Status'] = "\u274C"
        #dfJoined.loc[dfJoined['Status'] == 0, 'Status'] = "\U0001F601"
        #dfJoined.loc[dfJoined['Status'] == 1, 'Status'] = "\U0001F612"
        #dfJoined.loc[dfJoined['Status'] == 0, 'Status'] = "\N{Heavy Check Mark}"
        #dfJoined.loc[dfJoined['Status'] == 1, 'Status'] = "\N{Cross Mark}"
        dfJoined.to_html(render_links=True, escape=False)        
        st.dataframe(dfJoined[['Sitemap Status', 'Node']])
        #st.write("source [csv](" + sitemapCheckerBlobUrl + ")")

    with sumCol5:
        st.write("Types indexed")
        #dfTypes.columns = dfTypes.columns.str.replace('type', 'Pattern Type')
        #dfTypes.columns = dfTypes.columns.str.replace('count', 'Count')
        dfTypes.loc['Total']= dfTypes.sum()
        st.write(dfTypes.head(50))

    with sumCol6:
        st.write("Timeline: when added to Graph")
        # #st.write(dfProv.plot.pie(y='count',legend=False, figsize=(10, 10)))
        # #st.pyplot() 
        # df = pd.read_csv('/home/apps/odis-arch-git/code/notebooks/diagrams/data/oihSources.csv')
        # names = df['propername'].tolist()
        # dates = df['dates'].tolist()
        # # Convert date strings (e.g. 2014-10-18) to datetime
        # dates = [datetime.strptime(d, "%Y-%m-%d") for d in dates]
        # st.dataframe(data=df, width=None, height=None)
   
        dfTimeline = dfSources[['dateadded', 'propername']]
        #dfTimeline.sort_values(by='dateadded', ascending = False, inplace = True)
        #dfTimeline.style.hide_index()
        dfTimeline.columns = dfTimeline.columns.str.replace('dateadded', 'Date Added')
        dfTimeline.columns = dfTimeline.columns.str.replace('propername', 'Node')        
        dfTimeline.set_index('Date Added', inplace=True)     
        st.dataframe(data=dfTimeline, width=None, height=None)          

    sumCol7, sumCol8, sumCol9 = st.columns([1, 2, 1], gap="medium")

    with sumCol7:
        st.write("Keywords")
        dfKeywords.loc['Total']= dfKeywords.sum()
        st.write(dfKeywords.head(50))
        
    with sumCol8:
        st.write("Predicates")
        dfPredicates_sorted.loc['Total']= dfPredicates_sorted.sum()
        st.write(dfPredicates_sorted)      
        
    with sumCol9:
        st.write("Spatial Predicates")
        st.subheader(dfWKTCount['sCount'].values[0])
                
    st.write("Raw Sources Report (" + latest_file_date + ")")
    #dfJoinedRaw.to_html()
    #st.dataframe(dfJoinedRaw.to_html(render_links=True, escape=False))
    st.dataframe(dfJoined)
        
with st.expander("OIH Node Summary", expanded=False):

    #use markdown trick, as st.expander label cannot be styled
    #      see https://github.com/streamlit/streamlit/issues/2056
    st.markdown(
    """
    <style>
    .streamlit-expanderHeader {
      font-size: large;
    }
    </style>
    """,
    unsafe_allow_html=True,
    )

    # top-level filters
    #node_filter = st.selectbox("Select an ODIS node", ("Marine Training EU", "AquaDocs", "Ocean Biodiversity Information System", "Ocean Best Practices", "OceanExpert UNESCO/IOC Project Office for IODE", "EDMO SeaDataNet", "EDMERP SeaDataNet", "INVEMAR documents", "INVEMAR Experts", "INVEMAR institution", "INVEMAR training", "INVEMAR vessel"))
    node_filter = st.selectbox("Select an ODIS node", dfOrgs, index=8)

    # creating a single-element container
    placeholder = st.empty()

    # dataframe filter
    dfProvFilter = dfProv[dfProv.index == node_filter]

    with placeholder.container():

        # create four columns
        nodeCol1, nodeCol2, nodeCol3, nodeCol4 = st.columns([1, 1, 1, 1], gap="small")

        with nodeCol1:
            st.write("Sitemap Status")
            #st.write(dfJoinedRaw.columns.tolist())
            dfRecord = dfJoinedRaw[dfJoinedRaw['propername'] == node_filter]
            nodeStatus = dfRecord[["code"]].values[0].item()
            #dfName = dfJoinedRaw[['code', 'propername']]
            #dfName
            #nodeStatus = dfName.loc[dfName['propername'].casefold() == node_filter.casefold(), 'code'].item()
            if nodeStatus == 0:
                st.subheader(":white_check_mark:" + " Valid")
            else:
                st.subheader(":x:" + " Error")            
            
        with nodeCol2:
            st.write("Sitemap resources")
            sitemapDesc = dfRecord[["description"]].values[0].item()
            sitemapType = dfRecord[["type"]].values[0].item()
            if sitemapType == "sitemap":
                st.subheader(sitemapDesc.split(':')[0].rstrip())
            else:
                st.subheader("sitegraph: 1")
            #st.write(sitemapResources)

        with nodeCol3:
            st.write("Number of Catalogues")
            st.subheader(dfProvFilter['count'].sum())
            
        with nodeCol4:
            st.write("Date indexed to OIH Graph")
            # df = pd.read_csv('/home/apps/odis-arch-git/code/notebooks/diagrams/data/oihSources.csv')
            # names = df['propername'].tolist()
            # dates = df['dates'].tolist()
              # # Convert date strings (e.g. 2014-10-18) to datetime
            # dates = [datetime.strptime(d, "%Y-%m-%d") for d in dates]
            # if "INVEMAR" in node_filter: 
                # mask = df['propername'].values ==  "INVEMAR"
            # else:
                # mask = df['propername'].values ==  node_filter
            # df_orgDate = df[mask]
            # st.subheader(df_orgDate['dates'].values[0])
            
            with open(odisArchGitSchemaDevPath + "/config/sources.yaml", 'r') as f:
                valuesYaml = yaml.load(f, Loader=yaml.FullLoader)

            sourcesLength = len(valuesYaml['sources'])
            #sourcesLength

            #loop through YAML
            for recNum in range(0, sourcesLength):
                properName = valuesYaml['sources'][recNum]['propername']
                #properName
                if (properName.casefold() == node_filter.casefold()):
                    dateAdded = valuesYaml['sources'][recNum]['dateadded']
                    st.subheader(dateAdded)
                    
        nodeCol5, nodeCol6, nodeCol7, nodeCol8 = st.columns([1, 1, 1, 1], gap="small")
            
        with nodeCol5:
            st.write("Sitemap URL")
            sitemapUrl = dfRecord[["url_sitemap"]].values[0].item()
            st.write(sitemapUrl)
            
        with nodeCol6:
            st.write("Catalogue Home")
            catalogueUrl = dfRecord[["catalogue"]].values[0].item()
            st.write(catalogueUrl) 

        with nodeCol7:
            st.empty()   

        with nodeCol8:
            st.write("")
            logoUrl = dfRecord[["logo"]].values[0].item()
            st.image(logoUrl, width=300)                     
            
        nodeCol9, nodeCol10, nodeCol11 = st.columns(3, gap="medium")

        with nodeCol9:
            st.write("Types indexed")
            rq_types_org1 = """prefix prov: <http://www.w3.org/ns/prov#>
                   PREFIX con: <http://www.ontotext.com/connectors/lucene#>
                   PREFIX luc: <http://www.ontotext.com/owlim/lucene#>
                   PREFIX con-inst: <http://www.ontotext.com/connectors/lucene/instance#>
                   PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                   PREFIX schema: <https://schema.org/>
                   PREFIX schemaold: <http://schema.org/>
                   PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

 
                   SELECT   ( COUNT(?type) as ?count) ?type   
                   WHERE
                   {
        
                     ?s rdf:type ?type .
                     ?wat rdf:name ?orgname .
                     FILTER ( ?type IN (schema:ResearchProject, schema:Project, schema:Organization, schema:Dataset, schema:CreativeWork, schema:Person, schema:Map, schema:Course, schema:CourseInstance, schema:Event, schema:Vehicle) )
                   """
            rq_types_org2 = "FILTER (?orgname = '" + node_filter + "') ."
            rq_types_org3 = """                   
                   }
                   GROUP BY ?type  
                   ORDER BY DESC(?count)
                   """
        
            #@st.cache(allow_output_mutation=True)
            dfTypesOrg = get_sparql_dataframe(oihGraphEndpoint, rq_types_org1 + rq_types_org2 + rq_types_org3)
            dfTypesOrg['count'] = dfTypesOrg["count"].astype(int) # convert count c to int
            dfTypesOrg.set_index('type', inplace=True)
            dfTypesOrg.loc['Total']= dfTypesOrg.sum()
            st.write(dfTypesOrg.head(50))
            #st.dataframe(data=dfTypesOrg, width=400, height=None)

        with nodeCol10:
            st.write("Keywords")
            rq_keywords_org1 = """prefix prov: <http://www.w3.org/ns/prov#>
                PREFIX con: <http://www.ontotext.com/connectors/lucene#>
                PREFIX luc: <http://www.ontotext.com/owlim/lucene#>
                PREFIX con-inst: <http://www.ontotext.com/connectors/lucene/instance#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX schema: <https://schema.org/>
                PREFIX schemaold: <http://schema.org/>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

                SELECT DISTINCT  ?keywords  ( COUNT(?keywords) as ?count )
                WHERE
                {
                   ?s schema:keywords ?keywords .
                   ?wat rdf:name ?orgname .
                """
        
            rq_keywords_org2 = "FILTER (?orgname = '" + node_filter + "') ."
            rq_keywords_org3 = """        }
                GROUP BY ?keywords
                ORDER BY DESC(?count)
                """        
            #@st.cache(allow_output_mutation=True)
            dfKeywordsOrg = get_sparql_dataframe(oihGraphEndpoint, rq_keywords_org1 + rq_keywords_org2 + rq_keywords_org3)
            dfKeywordsOrg['count'] = dfKeywordsOrg["count"].astype(int) # convert count c to int
            dfKeywordsOrg.set_index('keywords', inplace=True)
            #st.write(rq_keywords_org1 + rq_keywords_org2 + rq_keywords_org3)
            st.write(dfKeywordsOrg.head(50))  

        with nodeCol11:
            st.empty()                    

with st.expander("About the Dashboard", expanded=False):

    #use markdown trick, as st.expander label cannot be styled
    #      see https://github.com/streamlit/streamlit/issues/2056
    st.markdown(
    """
    <style>
    .streamlit-expanderHeader {
      font-size: large;
    }
    </style>
    """,
    unsafe_allow_html=True,
    )
    st.markdown("""
         The ODIS (Ocean Data and Information System) Dashboard 
         shows live queries related to 
         the ODIS Graph, including describing each node in the 
         network.  More information about how to connect to the
         ODIS network can be found at [https://book.oceaninfohub.org/](https://book.oceaninfohub.org/)
    """)
    st.image("https://oceaninfohub.org/wp-content/uploads/2020/12/logo_OIH_PNG-RGB-1.png", width=300)
