from asyncio import tasks
from urllib import request
#from lib_metadata import metadata
from parso import split_lines
from typing import TYPE_CHECKING, Union
if TYPE_CHECKING:
    from ..pyTigerGraph import TigerGraphConnection

from .utilities import random_string
import os
from os.path import join as pjoin
import re
import random
import string
import requests
import json
#import pandas as pd


class Featurizer:
    def __init__(
    self, 
    conn: "TigerGraphConnection"):
    
        """Class for Feature Extraction.
        The job of a feature extracter is to install and run the current algorithms in graph data science libarary.
        Currently, a set of graph algorithms are moved to the gsql folder and have been saved into a dictionary along with their output type.
        To add a specific algorithm, it should be added both to the gsql folder and class variable dictionary. 
        Args:
            conn (TigerGraphConnection): 
                Connection to the TigerGraph database.
        """

        self.conn = conn
        self.queryResult_type_dict = {"tg_pagerank":"Float","tg_article_rank":"Float","tg_betweenness_cent":"Float","tg_closeness_cent":"Float","tg_closeness_cent_approx":"Float","tg_degree_cent":"INT","tg_eigenvector_cent":"Float","tg_harmonic_cent":"INT","tg_pagerank_wt":"Float","tg_scc":"INT","tg_kcore":"INT","tg_lcc":"Float","tg_bfs":"INT","tg_shortest_ss_no_wt":"INT","tg_fastRP":"List<Double>","tg_label_prop":"INT","tg_louvain":"INT"}#type of features generated by graph algorithms
        self.params_dict = {}#input parameter for the desired algorithm to be run
        self.query = ""
        self.algo_dict = {
            "Centrality":{"pagerank":{"global":{"weigthed":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Centrality/pagerank/global/weighted/tg_pagerank_wt.gsql","unweighted":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Centrality/pagerank/global/unweighted/tg_pagerank.gsql"}},"article_rank":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Centrality/article_rank/tg_article_rank.gsql","Betweenness":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Centrality/betweenness/tg_betweenness_cent.gsql","closeness":{"approximate":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Centrality/closeness/approximate/tg_closeness_cent_approx.gsql","exact":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Centrality/closeness/exact/tg_closeness_cent.gsql"},"degree":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Centrality/degree/tg_degree_cent.gsql","eigenvector":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Centrality/eigenvector/tg_eigenvector_cent.gsql","harmonic":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Centrality/harmonic/tg_harmonic_cent.gsql"},"Classification":{"maximal_independent_set":{"deterministic":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Classification/maximal_independent_set/deterministic/tg_maximal_indep_set.gsql"}}
            ,"Community":{'connected_components': {'strongly_connected_components': {'standard': 'https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Community/connected_components/strongly_connected_components/standard/tg_scc.gsql'}},'k_core': 'https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Community/k_core/tg_kcore.gsql','label_propagation': 'https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Community/label_propagation/tg_label_prop.gsql','local_clustering_coefficient': 'https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Community/local_clustering_coefficient/tg_lcc.gsql','louvain': 'https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Community/louvain/tg_louvain.gsql','triangle_counting': {'fast': 'https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Community/triangle_counting/fast/tg_tri_count_fast.gsql'}}
            ,"Embeddings":{ "FastRP":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/GraphML/Embeddings/FastRP/tg_fastRP.gsql"}
            ,"Path":{ "bfs":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Path/bfs/tg_bfs.gsql","cycle_detection":{"count":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Path/cycle_detection/count/tg_cycle_detection_count.gsql"},"shortest_path":{"unweighted":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Path/shortest_path/unweighted/tg_shortest_ss_no_wt.gsql"}}  
            ,"Topological Link Prediction": {"common_neighbors":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Topological%20Link%20Prediction/common_neighbors/tg_common_neighbors.gsql","preferential_attachment":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Topological%20Link%20Prediction/preferential_attachment/tg_preferential_attachment.gsql","same_community":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Topological%20Link%20Prediction/same_community/tg_same_community.gsql","total_neighbors":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Topological%20Link%20Prediction/total_neighbors/tg_total_neighbors.gsql"} #List of graph algorithms 
        }
        # {
        #     "Centrality":{"pagerank":{"personalized":{"all_pairs":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Centrality/pagerank/personalized/all_pairs/tg_pagerank_pers_ap_batch.gsql","multi_source":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Centrality/pagerank/personalized/multi_source/tg_pagerank_pers.gsql"},"global":{"weigthed":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Centrality/pagerank/global/weighted/tg_pagerank_wt.gsql","unweighted":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Centrality/pagerank/global/unweighted/tg_pagerank.gsql"}},"article_rank":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Centrality/article_rank/tg_article_rank.gsql","Betweenness":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Centrality/betweenness/tg_betweenness_cent.gsql","closeness":{"approximate":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Centrality/closeness/approximate/tg_closeness_cent_approx.gsql","exact":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Centrality/closeness/exact/tg_closeness_cent.gsql"},"degree":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Centrality/degree/tg_degree_cent.gsql","eigenvector":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Centrality/eigenvector/tg_eigenvector_cent.gsql","harmonic":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Centrality/harmonic/tg_harmonic_cent.gsql","influence_maximization":{"CELF":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Centrality/influence_maximization/CELF/tg_influence_maximization_CELF.gsql","greedy":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Centrality/influence_maximization/greedy/tg_influence_maximization_greedy.gsql"}}    ,"Classification":{"greedy_graph_coloring":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Classification/greedy_graph_coloring/tg_greedy_graph_coloring.gsql","k_nearest_neighbors":{"all_pairs":{"all_pairs_sub": "https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Classification/k_nearest_neighbors/all_pairs/tg_knn_cosine_all_sub.gsql","all_pairs_all": "https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Classification/k_nearest_neighbors/all_pairs/tg_knn_cosine_all.gsql"},"cross_validation":{"cross_validation_sub":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Classification/k_nearest_neighbors/cross_validation/tg_knn_cosine_cv_sub.gsql","cross_validation_all": "https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Classification/k_nearest_neighbors/cross_validation/tg_knn_cosine_cv.gsql"},"single_source":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Classification/k_nearest_neighbors/single_source/tg_knn_cosine_ss.gsql"},"maximal_independent_set":{"deterministic":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Classification/maximal_independent_set/deterministic/tg_maximal_indep_set.gsql","random":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Classification/maximal_independent_set/random/tg_maximal_indep_set_random.gsql"}}
    
        #     ,"Community":{'connected_components': {'strongly_connected_components': {'small_world': 'https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Community/connected_components/strongly_connected_components/small_world/tg_scc_small_world.gsql','standard': 'https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Community/connected_components/strongly_connected_components/standard/tg_scc.gsql'},'weakly_connected_components': {'small_world': 'https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Community/connected_components/weakly_connected_components/small_world/tg_algo_wcc_small_world.gsql','standard': 'https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Community/connected_components/weakly_connected_components/standard/tg_wcc.gsql'}},'k_core': 'https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Community/k_core/tg_kcore.gsql','k_means': {'k_means_sub': 'https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Community/k_means/tg_kmeans_sub.gsql','k_means_all': 'https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Community/k_means/tg_kmeans.gsql'},'label_propagation': 'https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Community/label_propagation/tg_label_prop.gsql','local_clustering_coefficient': 'https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Community/local_clustering_coefficient/tg_lcc.gsql','louvain': 'https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Community/louvain/tg_louvain.gsql','map_equation': 'https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Community/map_equation/tg_map_equation.gsql','speaker-listener_label_propagation': 'https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Community/speaker-listener_label_propagation/tg_slpa.gsql','triangle_counting': {'fast': 'https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Community/triangle_counting/fast/tg_tri_count_fast.gsql','standard': 'https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Community/triangle_counting/standard/tg_tri_count.gsql'}}
        #     #,"GraphML":{"Embeddings":{"EmbeddingSimilarity":{"pairwise":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/GraphML/Embeddings/EmbeddingSimilarity/pairwise/tg_embedding_pairwise_cosine_sim.gsql","single_source":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/GraphML/Embeddings/EmbeddingSimilarity/single_source/tg_embedding_cosine_sim.gsql"},"FastRP":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/GraphML/Embeddings/FastRP/tg_fastRP.gsql","Node2Vec":{"tg_weighted_random_walk_sub": "https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/GraphML/Embeddings/Node2Vec/tg_weighted_random_walk_sub.gsql","tg_weighted_random_walk_batch": "https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/GraphML/Embeddings/Node2Vec/tg_weighted_random_walk_batch.gsql","tg_weighted_random_walk": "https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/GraphML/Embeddings/Node2Vec/tg_weighted_random_walk.gsql","tg_random_walk_batch": "https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/GraphML/Embeddings/Node2Vec/tg_random_walk_batch.gsql","tg_random_walk": "https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/GraphML/Embeddings/Node2Vec/tg_random_walk.gsql","tg_node2vec": "https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/GraphML/Embeddings/Node2Vec/tg_node2vec.gsql"}}}
        #     ,"Embeddings":{"EmbeddingSimilarity":{"pairwise":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/GraphML/Embeddings/EmbeddingSimilarity/pairwise/tg_embedding_pairwise_cosine_sim.gsql","single_source":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/GraphML/Embeddings/EmbeddingSimilarity/single_source/tg_embedding_cosine_sim.gsql"},"FastRP":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/GraphML/Embeddings/FastRP/tg_fastRP.gsql","Node2Vec":{"tg_weighted_random_walk_sub": "https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/GraphML/Embeddings/Node2Vec/tg_weighted_random_walk_sub.gsql","tg_weighted_random_walk_batch": "https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/GraphML/Embeddings/Node2Vec/tg_weighted_random_walk_batch.gsql","tg_weighted_random_walk": "https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/GraphML/Embeddings/Node2Vec/tg_weighted_random_walk.gsql","tg_random_walk_batch": "https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/GraphML/Embeddings/Node2Vec/tg_random_walk_batch.gsql","tg_random_walk": "https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/GraphML/Embeddings/Node2Vec/tg_random_walk.gsql","tg_node2vec": "https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/GraphML/Embeddings/Node2Vec/tg_node2vec.gsql"}}
            
        #     ,"Path":{"astar_shortest_path":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Path/astar_shortest_path/tg_astar.gsql","bfs":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Path/bfs/tg_bfs.gsql","cycle_detection":{"count":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Path/cycle_detection/count/tg_cycle_detection_count.gsql","full_result":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Path/cycle_detection/full_result/tg_cycle_detection.gsql"},"estimated_diameter":{"approximate":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Path/estimated_diameter/approximate/tg_estimate_diameter.gsql","max_bfs":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Path/estimated_diameter/max_bfs/tg_max_BFS_depth.gsql"},"maxflow":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Path/maxflow/tg_maxflow.gsql","minimum_spanning_forest":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Path/minimum_spanning_forest/tg_msf.gsql","minimum_spanning_tree":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Path/minimum_spanning_tree/tg_mst.gsql","shortest_path":{"unweighted":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Path/shortest_path/unweighted/tg_shortest_ss_no_wt.gsql","weighted":{"any_sign":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Path/shortest_path/weighted/any_sign/tg_shortest_ss_any_wt.gsql","positive":{"summary":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Path/shortest_path/weighted/positive/summary/tg_shortest_ss_pos_wt.gsql","traceback":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Path/shortest_path/weighted/positive/traceback/tg_shortest_ss_pos_wt_tb.gsql"}}}}
            
        #     ,"Patterns":{"frequent_pattern_mining":{"tg_fpm_pre":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Patterns/frequent_pattern_mining/tg_fpm_pre.gsql","tg_fpm":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Patterns/frequent_pattern_mining/tg_fpm.gsql"}}
            
        #     ,"Similarity":{"approximate_nearest_neighbors":"","cosine":{"all_pairs":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Similarity/cosine/all_pairs/tg_cosine_nbor_ap_batch.gsql","single_source":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Similarity/cosine/single_source/tg_cosine_nbor_ss.gsql"},"jaccard":{"all_pairs":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Similarity/jaccard/all_pairs/tg_jaccard_nbor_ap_batch.gsql","single_source":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Similarity/jaccard/single_source/tg_jaccard_nbor_ss.gsql"} }
  

        #     ,"Topological Link Prediction": {"adamic_adar":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Topological%20Link%20Prediction/adamic_adar/tg_adamic_adar.gsql","common_neighbors":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Topological%20Link%20Prediction/common_neighbors/tg_common_neighbors.gsql","preferential_attachment":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Topological%20Link%20Prediction/preferential_attachment/tg_preferential_attachment.gsql","resource_allocation":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Topological%20Link%20Prediction/resource_allocation/tg_resource_allocation.gsql","same_community":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Topological%20Link%20Prediction/same_community/tg_same_community.gsql","total_neighbors":"https://raw.githubusercontent.com/tigergraph/gsql-graph-algorithms/master/algorithms/Topological%20Link%20Prediction/total_neighbors/tg_total_neighbors.gsql"}  
  
        # }    

        
        
    def _print_dict(self,d:dict, category:str=None,indent:int=0):
        '''
        Print the specified category of algorithms if category is not None, otherwise will print all list of algorithmms
        Args:
            d (dict): 
                The nested dictionary of all algorithms in GDS.
            category (str): 
                The list of specified category of algorithmms to be printed like Centrality.
            indent (int):
                indentation for printing the list of categories.
        '''
        if category!=None:
            if category in d.keys():
                d = d[category]
            else:
                raise ValueError("There is no such category within the algorithms.")
        for key, value in d.items():
            print(' ' * indent + str(key)+": ")
            if isinstance(value, dict):
                self._print_dict(d=value, indent=indent+1)
            else:
                if value != "":
                    value = "https://github.com/tigergraph/gsql-graph-algorithms/blob/master"+value.split('master')[1]
                print(' ' * (indent+1) + str(value)+". ")
    
    def _get_values(self,d):
        '''
        Check if d is a nested dictionary and return values of the most inner dictionary 
        Args:
            d (dict): 
                The nested dictionary.
        '''
        for v in d.values():
            if isinstance(v, dict):
                yield from self._get_values(v)
            else:
                yield v

    def listAlgorithms(self,category:str=None):
        '''
        Print the list of avalaible algorithms in GDS.
        Args:
            category (str): 
                The class of the algorithms, if it is None the entire list will be printed out.
        '''
        if category!=None:
            print("Available algorithms for category", category,"in the GDS (https://github.com/tigergraph/gsql-graph-algorithms):")
        else:
            print("The list of the categories for available algorithms in the GDS (https://github.com/tigergraph/gsql-graph-algorithms):")
        self._print_dict(d=self.algo_dict,category=category)

    def _is_query_installed(self, query_name: str) -> bool:
        '''
        If the query id already installed return true
        Args:
            query_name (str): 
                The name of the query
        '''
        resp = "GET /query/{}/{}".format(self.conn.graphname, query_name)
        queries = self.conn.getInstalledQueries()
        return resp in queries

    def _get_query(self,query_name:str):
        '''
        Get the query name, and download it from the github.
        Args:
            query_name (str): 
                The name of the query
        '''
        algo_list = list(self._get_values(self.algo_dict))
        query = ""
        for query_url in algo_list:
            if query_name == query_url.split('/')[-1][:-5]:
                query = requests.get(query_url).text
        if query == "":
            self.listAlgorithms()
            raise ValueError("The query name is not included in the list of queries.")
        return query

    def _get_query_url(self,query_name:str):
        '''
        Get the query name, and return its url from the github.
        Args:
            query_name (str): 
                The name of the query
        '''
        algo_list = list(self._get_values(self.algo_dict))
        flag = False
        for query_url in algo_list:
            if query_name == query_url.split('/')[-1][:-5]:
                flag = True
                return "https://github.com/tigergraph/gsql-graph-algorithms/blob/master"+query_url.split('master')[1]
        if not flag: 
            self.listAlgorithms()
            raise ValueError("The query name is not included in the list of queries.")
        

    def _install_query_file(self, query_name: str, replace: dict = None):
        '''
        Reads the first line of the query file to get the query name, e.g, CREATE QUERY query_name ...
        Args:
            query_name (str): 
                The name of the query
            replace (dict): 
                If the suffix name needs to be replaced 
        '''
        # If a suffix is to be added to query name
        if replace and ("{QUERYSUFFIX}" in replace):
            query_name = query_name.replace("{QUERYSUFFIX}",replace["{QUERYSUFFIX}"])
        # If query is already installed, skip.
        if self._is_query_installed(query_name.strip()):
            return query_name
        # Otherwise, install query from its Github address
        query = self._get_query(query_name)
        # Replace placeholders with actual content if given
        if replace:
            for placeholder in replace:
                query = query.replace(placeholder, replace[placeholder])
        self.query = query
        # TODO: Check if Distributed query is needed.
        query = ("USE GRAPH {}\n".format(self.conn.graphname) + query + "\ninstall Query {}\n".format(query_name))
        print("Installing and optimizing the queries, it might take a minute")
        resp = self.conn.gsql(query)
        status = resp.splitlines()[-1]
        if "Failed" in status:
            raise ConnectionError(status)
        return query_name 

    def installAlgorithm(self,query_name:str):
        '''
        Checks if the query is already installed, if not it will install the query and change the schema if an attribute needs to be added.        
        Args:
            query_name (str): 
                The name of query to be installed
        '''
        resp = self._install_query_file(query_name)
        return resp.strip() 

    def _add_attribute(self, schema_type: str, attr_type: str,attr_name: str=None,schema_name: list[str]=None):
        '''
        If the current attribute is not already added to the schema, it will create the schema job to do that.
        Check whether to add the attribute to vertex(vertices) or edge(s)
        Args:
            schema_type (str): 
                Vertex or edge
            attr_type (str): 
                Type of attribute which can be INT, DOUBLE,FLOAT,BOOL, or LIST
            attr_name (str): 
                An attribute name that needs to be added to the vertex/edge
            schema_name:
                List of Vertices/Edges that the attr_name need to added to them.
        '''
        # Check whether to add the attribute to vertex(vertices) or edge(s)
        self.result_attr = attr_name
        v_type = False
        if schema_type.upper() == "VERTEX":
            target = self.conn.getVertexTypes()
            v_type = True
        elif schema_type.upper() == "EDGE":
            target = self.conn.getEdgeTypes()
        else:
            raise Exception('schema_type has to be VERTEX or EDGE')
        # If attribute should be added to a specific vertex/edge name
        if schema_name != None:
            target.clear()
            target.append(schema_name)
        # For every vertex or edge type
        tasks = []
        for t in target:
            attributes = []
            if v_type:
                meta_data =  self.conn.getVertexType(t)
            else:
                meta_data = self.conn.getEdgeType(t)
            for i in range(len(meta_data['Attributes'])):
                attributes.append(meta_data['Attributes'][i]['AttributeName'])
            # If attribute is not in list of vertex attributes, do the schema change to add it
            if attr_name != None and attr_name  not in attributes:
                tasks.append("ALTER {} {} ADD ATTRIBUTE ({} {});\n".format(
                        schema_type, t, attr_name, attr_type))
        # If attribute already exists for schema type t, nothing to do
        if not tasks:
            return "Attribute already exists"
        # Create schema change job 
        job_name = "add_{}_attr_{}".format(schema_type,random_string(6)) 
        job = "USE GRAPH {}\n".format(self.conn.graphname) + "CREATE GLOBAL SCHEMA_CHANGE JOB {} {{\n".format(
            job_name) + ''.join(tasks) + "}}\nRUN GLOBAL SCHEMA_CHANGE JOB {}".format(job_name)
        # Submit the job
        resp = self.conn.gsql(job)
        status = resp.splitlines()[-1]
        if "Failed" in status:
            raise ConnectionError(status)
        else:
            print(status)
        return 'Global schema change succeeded.'

    
    def _get_Params(self,query_name:str):
        '''
        Returns default query parameters by parsing the query header.
        Args:
            query_name (str):
                The name of the query to be executed.
        '''
        _dict = {}
        query = self._get_query(query_name)
        if query == "":
            self.listAlgorithms()
            raise ValueError("The query name is not included in the list of defined queries ")

        try:
            input_params = query[query.find('(')+1:query.find(')')]
            list_params =input_params.split(',')
            for i in range(len(list_params)):
                if "=" in list_params[i]:
                    params_type = list_params[i].split('=')[0].split()[0]
                    if params_type.lower() == 'float' or params_type.lower() == 'double':
                        _dict[list_params[i].split('=')[0].split()[1]] = float(list_params[i].split('=')[1])
                    if params_type.lower() == 'bool':
                        _dict[list_params[i].split('=')[0].split()[1]] = bool(list_params[i].split('=')[1])
                    if params_type.lower() == 'int':
                        _dict[list_params[i].split('=')[0].split()[1]] = int(list_params[i].split('=')[1])
                    if params_type.lower() == 'string':
                        _dict[list_params[i].split('=')[0].split()[1]] = list_params[i].split('=')[1].split()[0][1:-2]
                else:
                    _dict[list_params[i].split()[1]] =  None
        except:
            print("The algorithm does not have any input parameter.")
        self.params_dict[query_name] = _dict
        return _dict  
               
    def runAlgorithm(self,query_name:str,params:dict = None,schema_type:str="VERTEX",feat_name:str=None,schema_name:list[str]=None,timeout:int=2147480,sizeLimit:int=None):
        '''
        Runs an installed query.
        The query must be already created and installed in the graph.
        If the query accepts input parameters and the parameters have not been provided, they will be initialized by parsing the query.
        If the initialized parameters contain any None value, the function will raise the ValueError.
        Args:
            query_name (str):
                The name of the query to be executed.
            params (dict):
                Query parameters. a dictionary.
            schema_type (str): 
                Vertex or edge, default value is VERTEX
            feat_name (str): 
                An attribute name that needs to be added to the vertex/edge
            schema_name:
                List of Vertices/Edges that the attr_name need to added to them.    
            timeout (int):
                Maximum duration for successful query execution (in milliseconds).
                See https://docs.tigergraph.com/tigergraph-server/current/api/#_gsql_query_timeout
            sizeLimit (int):
                Maximum size of response (in bytes).
                See https://docs.tigergraph.com/tigergraph-server/current/api/#_response_size

        Returns:
            The output of the query, a list of output elements (vertex sets, edge sets, variables,
            accumulators, etc.
        '''
        if params == None:
            params = self._get_Params(query_name)
            print("Default parameters are:",params)
            if params:
                if None in params.values():
                    query_ulr= self._get_query_url(query_name)
                    raise ValueError("Query parameters which are not initialized by default need to be initialized, visit "+query_ulr+".")
            else:
                result = self.conn.runInstalledQuery(query_name,timeout=timeout,sizeLimit = sizeLimit,usePost=True)
                if result != None:
                    return result
        else:
            defualt_params = self._get_Params(query_name)
            if feat_name:
                if "result_attr" in defualt_params.keys():
                    params["result_attr"] = feat_name
                    _ = self._add_attribute(schema_type,self.queryResult_type_dict[query_name],feat_name,schema_name)
                else:
                    query_ulr= self._get_query_url(query_name)
                    raise ValueError("The algorithm does not provide any feature, see the algorithm details:"+query_ulr+".")
            result = self.conn.runInstalledQuery(query_name, params,timeout=timeout,sizeLimit = sizeLimit,usePost=True)
            if result != None:
                return result   
            


    