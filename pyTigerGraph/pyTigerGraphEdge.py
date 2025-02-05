"""Edge Functions

Functions to upsert, retrieve and delete edges.
All functions in this module are called as methods on a link:https://docs.tigergraph.com/pytigergraph/current/core-functions/base[`TigerGraphConnection` object].
"""
import json
import logging
import warnings

from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    import pandas as pd

from pyTigerGraph.pyTigerGraphException import TigerGraphException
from pyTigerGraph.pyTigerGraphQuery import pyTigerGraphQuery

logger = logging.getLogger(__name__)


class pyTigerGraphEdge(pyTigerGraphQuery):

    def getEdgeTypes(self, force: bool = False) -> list:
        """Returns the list of edge type names of the graph.

        Args:
            force:
                If `True`, forces the retrieval the schema metadata again, otherwise returns a
                cached copy of edge type metadata (if they were already fetched previously).

        Returns:
            The list of edge types defined in the current graph.
        """
        logger.info("entry: getEdgeTypes")
        if logger.level == logging.DEBUG:
            logger.debug("params: " + self._locals(locals()))

        ret = []
        for et in self.getSchema(force=force)["EdgeTypes"]:
            ret.append(et["Name"])

        if logger.level == logging.DEBUG:
            logger.debug("return: " + str(ret))
        logger.info("exit: getEdgeTypes")

        return ret

    def getEdgeType(self, edgeType: str, force: bool = False) -> dict:
        """Returns the details of the edge type.

        Args:
            edgeType:
                The name of the edge type.
            force:
                If `True`, forces the retrieval the schema details again, otherwise returns a cached
                copy of edge type details (if they were already fetched previously).

        Returns:
            The metadata of the edge type.
        """
        logger.info("entry: getEdgeType")
        if logger.level == logging.DEBUG:
            logger.debug("params: " + self._locals(locals()))

        for et in self.getSchema(force=force)["EdgeTypes"]:
            if et["Name"] == edgeType:
                if logger.level == logging.DEBUG:
                    logger.debug("return: " + str(et))
                logger.info("exit: getEdgeType (found)")

                return et

        logger.warning("Edge type `" + edgeType + "` was not found.")
        logger.info("exit: getEdgeType (not found)")

        return {}

    def getEdgeSourceVertexType(self, edgeType: str) -> Union[str, set]:
        """Returns the type(s) of the edge type's source vertex.

        Args:
            edgeType:
                The name of the edge type.

        Returns:
            - A single source vertex type name string if the edge has a single source vertex type.
            - "*" if the edge can originate from any vertex type (notation used in 2.6.1 and earlier
                versions).
                See https://docs.tigergraph.com/v/2.6/dev/gsql-ref/ddl-and-loading/defining-a-graph-schema#creating-an-edge-from-or-to-any-vertex-type
            - A set of vertex type name strings (unique values) if the edge has multiple source
                vertex types (notation used in 3.0 and later versions). /
                Even if the source vertex types were defined as `"*"`, the REST API will list them as
                pairs (i.e. not as `"*"` in 2.6.1 and earlier versions), just like as if there were
                defined one by one (e.g. `FROM v1, TO v2 | FROM v3, TO v4 | …`).

            The returned set contains all source vertex types, but it does not certainly mean that
                the edge is defined between all source and all target vertex types. You need to look
                at the individual source/target pairs to find out which combinations are
                valid/defined.
        """
        logger.info("entry: getEdgeSourceVertexType")
        if logger.level == logging.DEBUG:
            logger.debug("params: " + self._locals(locals()))

        edgeTypeDetails = self.getEdgeType(edgeType)

        # Edge type with a single source vertex type
        if edgeTypeDetails["FromVertexTypeName"] != "*":
            ret = edgeTypeDetails["FromVertexTypeName"]

            if logger.level == logging.DEBUG:
                logger.debug("return: " + str(ret))
            logger.info("exit: getEdgeSourceVertexType (single source)")

            return ret

        # Edge type with multiple source vertex types
        if "EdgePairs" in edgeTypeDetails:
            # v3.0 and later notation
            vts = set()
            for ep in edgeTypeDetails["EdgePairs"]:
                vts.add(ep["From"])

            if logger.level == logging.DEBUG:
                logger.debug("return: " + str(vts))
            logger.info("exit: getEdgeSourceVertexType (multi source)")

            return vts
        else:
            # 2.6.1 and earlier notation
            if logger.level == logging.DEBUG:
                logger.debug("return: *")
            logger.info("exit: getEdgeSourceVertexType (multi source, pre-3.x)")

            return "*"

    def getEdgeTargetVertexType(self, edgeType: str) -> Union[str, set]:
        """Returns the type(s) of the edge type's target vertex.

        Args:
            edgeType:
                The name of the edge type.

        Returns:
            - A single target vertex type name string if the edge has a single target vertex type.
            - "*" if the edge can end in any vertex type (notation used in 2.6.1 and earlier
                versions).
                See https://docs.tigergraph.com/v/2.6/dev/gsql-ref/ddl-and-loading/defining-a-graph-schema#creating-an-edge-from-or-to-any-vertex-type
            - A set of vertex type name strings (unique values) if the edge has multiple target
                vertex types (notation used in 3.0 and later versions). /
                Even if the target vertex types were defined as "*", the REST API will list them as
                pairs (i.e. not as "*" in 2.6.1 and earlier versions), just like as if there were
                defined one by one (e.g. `FROM v1, TO v2 | FROM v3, TO v4 | …`).

            The returned set contains all target vertex types, but does not certainly mean that the
                edge is defined between all source and all target vertex types. You need to look at
                the individual source/target pairs to find out which combinations are valid/defined.
        """
        logger.info("entry: getEdgeTargetVertexType")
        if logger.level == logging.DEBUG:
            logger.debug("params: " + self._locals(locals()))

        edgeTypeDetails = self.getEdgeType(edgeType)

        # Edge type with a single target vertex type
        if edgeTypeDetails["ToVertexTypeName"] != "*":
            ret = edgeTypeDetails["ToVertexTypeName"]

            if logger.level == logging.DEBUG:
                logger.debug("return: " + str(ret))
            logger.info("exit: getEdgeTargetVertexType (single target)")

            return ret

        # Edge type with multiple target vertex types
        if "EdgePairs" in edgeTypeDetails:
            # v3.0 and later notation
            vts = set()
            for ep in edgeTypeDetails["EdgePairs"]:
                vts.add(ep["To"])

            if logger.level == logging.DEBUG:
                logger.debug("return: " + str(vts))
            logger.info("exit: getEdgeTargetVertexType (multi target)")

            return vts
        else:
            # 2.6.1 and earlier notation
            if logger.level == logging.DEBUG:
                logger.debug("return: *")
            logger.info("exit: getEdgeTargetVertexType (multi target, pre-3.x)")

            return "*"

    def isDirected(self, edgeType: str) -> bool:
        """Is the specified edge type directed?

        Args:
            edgeType:
                The name of the edge type.

        Returns:
            `True`, if the edge is directed.
        """
        logger.info("entry: isDirected")
        if logger.level == logging.DEBUG:
            logger.debug("params: " + self._locals(locals()))

        ret = self.getEdgeType(edgeType)["IsDirected"]

        if logger.level == logging.DEBUG:
            logger.debug("return: " + str(ret))
        logger.info("exit: isDirected")

        return ret

    def getReverseEdge(self, edgeType: str) -> str:
        """Returns the name of the reverse edge of the specified edge type, if applicable.

        Args:
            edgeType:
                The name of the edge type.

        Returns:
            The name of the reverse edge, if it was defined.
        """
        logger.info("entry: getReverseEdge")
        if logger.level == logging.DEBUG:
            logger.debug("params: " + self._locals(locals()))

        if not self.isDirected(edgeType):
            logger.error(edgeType + " is not a directed edge")
            logger.info("exit: getReverseEdge (not directed)")

            return ""

        config = self.getEdgeType(edgeType)["Config"]
        if "REVERSE_EDGE" in config:
            ret = config["REVERSE_EDGE"]

            if logger.level == logging.DEBUG:
                logger.debug("return: " + str(ret))
            logger.info("exit: getReverseEdge (reverse edge found)")

            return ret

        logger.info("exit: getReverseEdge (reverse edge not found)")

        return ""
        # TODO Should return some other value or raise exception?

    def getEdgeCountFrom(self, sourceVertexType: str = "", sourceVertexId: Union[str, int] = None,
            edgeType: str = "", targetVertexType: str = "", targetVertexId: Union[str, int] = None,
            where: str = "") -> dict:
        """Returns the number of edges from a specific vertex.

        Args:
            sourceVertexType:
                The name of the source vertex type.
            sourceVertexId:
                The primary ID value of the source vertex instance.
            edgeType:
                The name of the edge type.
            targetVertexType:
                The name of the target vertex type.
            targetVertexId:
                The primary ID value of the target vertex instance.
            where:
                A comma separated list of conditions that are all applied on each edge's attributes.
                The conditions are in logical conjunction (i.e. they are "AND'ed" together).

        Returns:
            A dictionary of `edge_type: edge_count` pairs.

        Uses:
            - If `edgeType` = "*": edge count of all edge types (no other arguments can be specified
                in this case).
            - If `edgeType` is specified only: edge count of the given edge type.
            - If `sourceVertexType`, `edgeType`, `targetVertexType` are specified: edge count of the
                given edge type between source and target vertex types.
            - If `sourceVertexType`, `sourceVertexId` are specified: edge count of all edge types
                from the given vertex instance.
            - If `sourceVertexType`, `sourceVertexId`, `edgeType` are specified: edge count of all
                edge types from the given vertex instance.
            - If `sourceVertexType`, `sourceVertexId`, `edgeType`, `where` are specified: the edge
                count of the given edge type after filtered by `where` condition.
            - If `targetVertexId` is specified, then `targetVertexType` must also be specified.
            - If `targetVertexType` is specified, then `edgeType` must also be specified.

        Endpoints:
            - `GET /graph/{graph_name}/edges/{source_vertex_type}/{source_vertex_id}`
                See https://docs.tigergraph.com/tigergraph-server/current/api/built-in-endpoints#_list_edges_of_a_vertex
            - `POST /builtins/{graph_name}`
                See https://docs.tigergraph.com/tigergraph-server/current/api/built-in-endpoints#_run_built_in_functions_on_graph
        """
        logger.info("entry: getEdgeCountFrom")
        if logger.level == logging.DEBUG:
            logger.debug("params: " + self._locals(locals()))

        # If WHERE condition is not specified, use /builtins else user /vertices
        if where or (sourceVertexType and sourceVertexId):
            if not sourceVertexType or not sourceVertexId:
                raise TigerGraphException(
                    "If where condition is specified, then both sourceVertexType and sourceVertexId"
                    " must be provided too.", None)
            url = self.restppUrl + "/graph/" + self._safeChar(self.graphname) + "/edges/" + \
                  self._safeChar(sourceVertexType) + "/" + self._safeChar(sourceVertexId)
            if edgeType:
                url += "/" + self._safeChar(edgeType)
                if targetVertexType:
                    url += "/" + self._safeChar(targetVertexType)
                    if targetVertexId:
                        url += "/" + self._safeChar(targetVertexId)
            url += "?count_only=true"
            if where:
                url += "&filter=" + self._safeChar(where)
            res = self._get(url)
        else:
            if not edgeType:  # TODO Is this a valid check?
                raise TigerGraphException(
                    "A valid edge type or \"*\" must be specified for edge type.", None)
            data = '{"function":"stat_edge_number","type":"' + edgeType + '"' \
                   + (',"from_type":"' + sourceVertexType + '"' if sourceVertexType else '') \
                   + (',"to_type":"' + targetVertexType + '"' if targetVertexType else '') \
                   + '}'
            res = self._post(self.restppUrl + "/builtins/" + self.graphname, data=data)

        if len(res) == 1 and res[0]["e_type"] == edgeType:
            ret = res[0]["count"]

            if logger.level == logging.DEBUG:
                logger.debug("return: " + str(ret))
            logger.info("exit: getEdgeCountFrom (single edge type)")

            return ret

        ret = {}
        for r in res:
            ret[r["e_type"]] = r["count"]

        if logger.level == logging.DEBUG:
            logger.debug("return: " + str(ret))
        logger.info("exit: getEdgeCountFrom  (multiple edge types)")

        return ret

    def getEdgeCount(self, edgeType: str = "*", sourceVertexType: str = "",
            targetVertexType: str = "") -> dict:
        """Returns the number of edges of an edge type.

        This is a simplified version of `getEdgeCountFrom()`, to be used when the total number of
        edges of a given type is needed, regardless which vertex instance they are originated from.
        See documentation of `getEdgeCountFrom` above for more details.

        Args:
            edgeType:
                The name of the edge type.
            sourceVertexType:
                The name of the source vertex type.
            targetVertexType:
                The name of the target vertex type.

        Returns:
            A dictionary of `edge_type: edge_count` pairs.
        """
        logger.info("entry: getEdgeCount")
        if logger.level == logging.DEBUG:
            logger.debug("params: " + self._locals(locals()))

        ret = self.getEdgeCountFrom(edgeType=edgeType, sourceVertexType=sourceVertexType,
            targetVertexType=targetVertexType)

        if logger.level == logging.DEBUG:
            logger.debug("return: " + str(ret))
        logger.info("exit: getEdgeCount")

        return ret

    def upsertEdge(self, sourceVertexType: str, sourceVertexId: str, edgeType: str,
            targetVertexType: str, targetVertexId: str, attributes: dict = None) -> int:
        """Upserts an edge.

        Data is upserted:

        - If edge is not yet present in graph, it will be created (see special case below).
        - If it's already in the graph, it is updated with the values specified in the request.
        - If `vertex_must_exist` is True then edge will only be created if both vertex exists
            in graph. Otherwise missing vertices are created with the new edge; the newly created
            vertices' attributes (if any) will be created with default values.

        Args:
            sourceVertexType:
                The name of the source vertex type.
            sourceVertexId:
                The primary ID value of the source vertex instance.
            edgeType:
                The name of the edge type.
            targetVertexType:
                The name of the target vertex type.
            targetVertexId:
                The primary ID value of the target vertex instance.
            attributes:
                A dictionary in this format:
                ```
                {<attribute_name>, <attribute_value>|(<attribute_name>, <operator>), …}
                ```
                Example:
                ```
                {"visits": (1482, "+"), "max_duration": (371, "max")}
                ```
                For valid values of `<operator>` see https://docs.tigergraph.com/dev/restpp-api/built-in-endpoints#operation-codes .

        Returns:
            A single number of accepted (successfully upserted) edges (0 or 1).

        Endpoint:
            - `POST /graph/{graph_name}`
                See https://docs.tigergraph.com/dev/restpp-api/built-in-endpoints#upsert-data-to-graph

        TODO Add ack, new_vertex_only, vertex_must_exist, update_vertex_only and atomic_level
            parameters and functionality.
        """
        logger.info("entry: upsertEdge")
        if logger.level == logging.DEBUG:
            logger.debug("params: " + self._locals(locals()))

        if attributes is None:
            attributes = {}

        vals = self._upsertAttrs(attributes)
        data = json.dumps({
            "edges": {
                sourceVertexType: {
                    sourceVertexId: {
                        edgeType: {
                            targetVertexType: {
                                targetVertexId: vals
                            }
                        }
                    }
                }
            }
        })

        ret = self._post(self.restppUrl + "/graph/" + self.graphname, data=data)[0][
            "accepted_edges"]

        if logger.level == logging.DEBUG:
            logger.debug("return: " + str(ret))
        logger.info("exit: upsertEdge")

        return ret

    def upsertEdges(self, sourceVertexType: str, edgeType: str, targetVertexType: str,
            edges: list) -> int:
        """Upserts multiple edges (of the same type).

        Args:
            sourceVertexType:
                The name of the source vertex type.
            edgeType:
                The name of the edge type.
            targetVertexType:
                The name of the target vertex type.
            edges:
                A list in of tuples in this format:
                ```
                [
                    (<source_vertex_id>, <target_vertex_id>, {<attribute_name>: <attribute_value>, …}),
                    (<source_vertex_id>, <target_vertex_id>, {<attribute_name>: (<attribute_value>, <operator>), …})
                    ⋮
                ]
                ```
                Example:
                ```
                [
                    (17, "home_page", {"visits": (35, "+"), "max_duration": (93, "max")}),
                    (42, "search", {"visits": (17, "+"), "max_duration": (41, "max")})
                ]
                ```
                For valid values of `<operator>` see https://docs.tigergraph.com/dev/restpp-api/built-in-endpoints#operation-codes .

        Returns:
            A single number of accepted (successfully upserted) edges (0 or positive integer).

        Endpoint:
            - `POST /graph/{graph_name}`
                See https://docs.tigergraph.com/dev/restpp-api/built-in-endpoints#upsert-data-to-graph

        TODO Add ack, new_vertex_only, vertex_must_exist, update_vertex_only and atomic_level
            parameters and functionality.
        """
        logger.info("entry: upsertEdges")
        if logger.level == logging.DEBUG:
            logger.debug("params: " + self._locals(locals()))

        data = {sourceVertexType: {}}
        l1 = data[sourceVertexType]
        for e in edges:
            if len(e) > 2:
                vals = self._upsertAttrs(e[2])
            else:
                vals = {}
            # fromVertexId
            if e[0] not in l1:
                l1[e[0]] = {}
            l2 = l1[e[0]]
            # edgeType
            if edgeType not in l2:
                l2[edgeType] = {}
            l3 = l2[edgeType]
            # targetVertexType
            if targetVertexType not in l3:
                l3[targetVertexType] = {}
            l4 = l3[targetVertexType]
            # targetVertexId
            l4[e[1]] = vals
        data = json.dumps({"edges": data})

        ret = self._post(self.restppUrl + "/graph/" + self.graphname, data=data)[0][
            "accepted_edges"]

        if logger.level == logging.DEBUG:
            logger.debug("return: " + str(ret))
        logger.info("exit: upsertEdges")

        return ret

    def upsertEdgeDataFrame(self, df: 'pd.DataFrame', sourceVertexType: str, edgeType: str,
            targetVertexType: str, from_id: str = "", to_id: str = "",
            attributes: dict = None) -> int:
        """Upserts edges from a Pandas DataFrame.

        Args:
            df:
                The DataFrame to upsert.
            sourceVertexType:
                The type of source vertex for the edge.
            edgeType:
                The type of edge to upsert data to.
            targetVertexType:
                The type of target vertex for the edge.
            from_id:
                The field name where the source vertex primary id is given. If omitted, the
                dataframe index would be used instead.
            to_id:
                The field name where the target vertex primary id is given. If omitted, the
                dataframe index would be used instead.
            attributes:
                A dictionary in the form of `{target: source}` where source is the column name in
                the dataframe and target is the attribute name in the graph vertex. When omitted,
                all columns would be upserted with their current names. In this case column names
                must match the vertex's attribute names.

        Returns:
            The number of edges upserted.
        """
        logger.info("entry: upsertEdgeDataFrame")
        if logger.level == logging.DEBUG:
            logger.debug("params: " + self._locals(locals()))

        json_up = []

        for index in df.index:
            json_up.append(json.loads(df.loc[index].to_json()))
            json_up[-1] = (
                index if from_id is None else json_up[-1][from_id],
                index if to_id is None else json_up[-1][to_id],
                json_up[-1] if attributes is None
                else {target: json_up[-1][source] for target, source in attributes.items()}
            )

        ret = self.upsertEdges(sourceVertexType, edgeType, targetVertexType, json_up)

        if logger.level == logging.DEBUG:
            logger.debug("return: " + str(ret))
        logger.info("exit: upsertEdgeDataFrame")

        return ret

    def getEdges(self, sourceVertexType: str, sourceVertexId: str, edgeType: str = "",
            targetVertexType: str = "", targetVertexId: str = "", select: str = "", where: str = "",
            limit: Union[int, str] = None, sort: str = "", fmt: str = "py", withId: bool = True,
            withType: bool = False, timeout: int = 0) -> Union[dict, str, 'pd.DataFrame']:
        """Retrieves edges of the given edge type originating from a specific source vertex.

        Only `sourceVertexType` and `sourceVertexId` are required.
        If `targetVertexId` is specified, then `targetVertexType` must also be specified.
        If `targetVertexType` is specified, then `edgeType` must also be specified.

        Args:
            sourceVertexType:
                The name of the source vertex type.
            sourceVertexId:
                The primary ID value of the source vertex instance.
            edgeType:
                The name of the edge type.
            targetVertexType:
                The name of the target vertex type.
            targetVertexId:
                The primary ID value of the target vertex instance.
            select:
                Comma separated list of edge attributes to be retrieved or omitted.
            where:
                Comma separated list of conditions that are all applied on each edge's attributes.
                The conditions are in logical conjunction (i.e. they are "AND'ed" together).
            sort:
                Comma separated list of attributes the results should be sorted by.
            limit:
                Maximum number of edge instances to be returned (after sorting).
            fmt:
                Format of the results returned:
                - "py":   Python objects
                - "json": JSON document
                - "df":   pandas DataFrame
            withId:
                (When the output format is "df") Should the source and target vertex types and IDs
                be included in the dataframe?
            withType:
                (When the output format is "df") Should the edge type be included in the dataframe?
            timeout:
                Time allowed for successful execution (0 = no time limit, default).

        Returns:
            The (selected) details of the (matching) edge instances (sorted, limited) as dictionary,
            JSON or pandas DataFrame.

        Endpoint:
            - `GET /graph/{graph_name}/edges/{source_vertex_type}/{source_vertex_id}`
                See https://docs.tigergraph.com/dev/restpp-api/built-in-endpoints#list-edges-of-a-vertex
        """
        logger.info("entry: getEdges")
        if logger.level == logging.DEBUG:
            logger.debug("params: " + self._locals(locals()))

        # TODO Change sourceVertexId to sourceVertexIds and allow passing both str and list<str> as
        #   parameter
        if not sourceVertexType or not sourceVertexId:
            raise TigerGraphException(
                "Both source vertex type and source vertex ID must be provided.", None)
        url = self.restppUrl + "/graph/" + self.graphname + "/edges/" + sourceVertexType + "/" + \
              str(sourceVertexId)
        if edgeType:
            url += "/" + edgeType
            if targetVertexType:
                url += "/" + targetVertexType
                if targetVertexId:
                    url += "/" + str(targetVertexId)
        isFirst = True
        if select:
            url += "?select=" + select
            isFirst = False
        if where:
            url += ("?" if isFirst else "&") + "filter=" + where
            isFirst = False
        if limit:
            url += ("?" if isFirst else "&") + "limit=" + str(limit)
            isFirst = False
        if sort:
            url += ("?" if isFirst else "&") + "sort=" + sort
            isFirst = False
        if timeout and timeout > 0:
            url += ("?" if isFirst else "&") + "timeout=" + str(timeout)
        ret = self._get(url)

        if fmt == "json":
            ret = json.dumps(ret)
        elif fmt == "df":
            ret = self.edgeSetToDataFrame(ret, withId, withType)

        if logger.level == logging.DEBUG:
            logger.debug("return: " + str(ret))
        logger.info("exit: getEdges")

        return ret

    def getEdgesDataFrame(self, sourceVertexType: str, sourceVertexId: str, edgeType: str = "",
            targetVertexType: str = "", targetVertexId: str = "", select: str = "", where: str = "",
            limit: Union[int, str] = None, sort: str = "", timeout: int = 0) -> 'pd.DataFrame':
        """Retrieves edges of the given edge type originating from a specific source vertex.

        This is a shortcut to ``getEdges(..., fmt="df", withId=True, withType=False)``.
        Only ``sourceVertexType`` and ``sourceVertexId`` are required.
        If ``targetVertexId`` is specified, then ``targetVertexType`` must also be specified.
        If ``targetVertexType`` is specified, then ``edgeType`` must also be specified.

        Args:
            sourceVertexType:
                The name of the source vertex type.
            sourceVertexId:
                The primary ID value of the source vertex instance.
            edgeType:
                The name of the edge type.
            targetVertexType:
                The name of the target vertex type.
            targetVertexId:
                The primary ID value of the target vertex instance.
            select:
                Comma separated list of edge attributes to be retrieved or omitted.
            where:
                Comma separated list of conditions that are all applied on each edge's attributes.
                The conditions are in logical conjunction (i.e. they are "AND'ed" together).
            sort:
                Comma separated list of attributes the results should be sorted by.
            limit:
                Maximum number of edge instances to be returned (after sorting).
            timeout:
                Time allowed for successful execution (0 = no limit, default).

        Returns:
            The (selected) details of the (matching) edge instances (sorted, limited) as dictionary,
            JSON or pandas DataFrame.
        """
        logger.info("entry: getEdgesDataFrame")
        if logger.level == logging.DEBUG:
            logger.debug("params: " + self._locals(locals()))

        ret = self.getEdges(sourceVertexType, sourceVertexId, edgeType, targetVertexType,
            targetVertexId, select, where, limit, sort, fmt="df", timeout=timeout)

        if logger.level == logging.DEBUG:
            logger.debug("return: " + str(ret))
        logger.info("exit: getEdgesDataFrame")

        return ret

    def getEdgesDataframe(self, sourceVertexType: str, sourceVertexId: str, edgeType: str = "",
            targetVertexType: str = "", targetVertexId: str = "", select: str = "", where: str = "",
            limit: Union[int, str] = None, sort: str = "", timeout: int = 0) -> 'pd.DataFrame':
        """DEPRECATED

        Use `getEdgesDataFrame()` instead.
        """
        warnings.warn(
            "The `getEdgesDataframe()` function is deprecated; use `getEdgesDataFrame()` instead.",
            DeprecationWarning)

        return self.getEdgesDataFrame(sourceVertexType, sourceVertexId, edgeType, targetVertexType,
            targetVertexId, select, where, limit, sort, timeout)

    def getEdgesByType(self, edgeType: str, fmt: str = "py", withId: bool = True,
            withType: bool = False) -> Union[dict, str, 'pd.DataFrame']:
        """Retrieves edges of the given edge type regardless the source vertex.

        Args:
            edgeType:
                The name of the edge type.
            fmt:
                Format of the results returned:
                - "py":   Python objects
                - "json": JSON document
                - "df":   pandas DataFrame
            withId:
                (When the output format is "df") Should the source and target vertex types and IDs
                be included in the dataframe?
            withType:
                (When the output format is "df") should the edge type be included in the dataframe?

        Returns:
            The details of the edge instances of the given edge type as dictionary, JSON or pandas
            DataFrame.

        TODO Add limit parameter
        """
        logger.info("entry: getEdgesByType")
        if logger.level == logging.DEBUG:
            logger.debug("params: " + self._locals(locals()))

        if not edgeType:
            logger.warning("Edge type is not specified")
            logger.info("exit: getEdgesByType")

            return {}

        sourceVertexType = self.getEdgeSourceVertexType(edgeType)
        # TODO Support edges with multiple source vertex types
        if isinstance(sourceVertexType, set) or sourceVertexType == "*":
            raise TigerGraphException(
                "Edges with multiple source vertex types are not currently supported.", None)

        queryText = \
            'INTERPRET QUERY () FOR GRAPH $graph { \
            SetAccum<EDGE> @@edges; \
            start = {ANY}; \
            res = \
                SELECT s \
                FROM   start:s-(:e)->ANY:t \
                WHERE  e.type == "$edgeType" \
                   AND s.type == "$sourceEdgeType" \
                ACCUM  @@edges += e; \
            PRINT @@edges AS edges; \
        }'

        queryText = queryText.replace("$graph", self.graphname) \
            .replace('$sourceEdgeType', sourceVertexType) \
            .replace('$edgeType', edgeType)
        ret = self.runInterpretedQuery(queryText)

        ret = ret[0]["edges"]

        if fmt == "json":
            ret = json.dumps(ret)
        elif fmt == "df":
            ret = self.edgeSetToDataFrame(ret, withId, withType)

        if logger.level == logging.DEBUG:
            logger.debug("return: " + str(ret))
        logger.info("exit: _upsertAttrs")

        return ret

    # TODO getEdgesDataFrameByType

    def getEdgeStats(self, edgeTypes: Union[str, list], skipNA: bool = False) -> dict:
        """Returns edge attribute statistics.

        Args:
            edgeTypes:
                A single edge type name or a list of edges types names or '*' for all edges types.
            skipNA:
                Skip those edges that do not have attributes or none of their attributes have
                statistics gathered.

        Returns:
            Attribute statistics of edges; a dictionary of dictionaries.

        Endpoint:
            - `POST /builtins/{graph_name}`
                See https://docs.tigergraph.com/dev/restpp-api/built-in-endpoints#run-built-in-functions-on-graph
        """
        logger.info("entry: getEdgeStats")
        if logger.level == logging.DEBUG:
            logger.debug("params: " + self._locals(locals()))

        ets = []
        if edgeTypes == "*":
            ets = self.getEdgeTypes()
        elif isinstance(edgeTypes, str):
            ets = [edgeTypes]
        elif isinstance(edgeTypes, list):
            ets = edgeTypes
        else:
            logger.warning("The `edgeTypes` parameter is invalid.")
            logger.info("exit: getEdgeStats")

            return {}

        ret = {}
        for et in ets:
            data = '{"function":"stat_edge_attr","type":"' + et + '","from_type":"*","to_type":"*"}'
            res = self._post(self.restppUrl + "/builtins/" + self.graphname, data=data, resKey="",
                skipCheck=True)
            if res["error"]:
                if "stat_edge_attr is skip" in res["message"] or \
                        "No valid edge for the input edge type" in res["message"]:
                    if not skipNA:
                        ret[et] = {}
                else:
                    raise TigerGraphException(res["message"],
                        (res["code"] if "code" in res else None))
            else:
                res = res["results"]
                for r in res:
                    ret[r["e_type"]] = r["attributes"]

        if logger.level == logging.DEBUG:
            logger.debug("return: " + str(ret))
        logger.info("exit: getEdgeStats")

        return ret

    def delEdges(self, sourceVertexType: str, sourceVertexId: str, edgeType: str = "",
            targetVertexType: str = "", targetVertexId: str = "", where: str = "",
            limit: str = "", sort: str = "", timeout: int = 0) -> dict:
        """Deletes edges from the graph.

        Only `sourceVertexType` and `sourceVertexId` are required.
        If `targetVertexId` is specified, then `targetVertexType` must also be specified.
        If `targetVertexType` is specified, then `edgeType` must also be specified.

        Args:
            sourceVertexType:
                The name of the source vertex type.
            sourceVertexId:
                The primary ID value of the source vertex instance.
            edgeType:
                The name of the edge type.
            targetVertexType:
                The name of the target vertex type.
            targetVertexId:
                The primary ID value of the target vertex instance.
            where:
                Comma separated list of conditions that are all applied on each edge's attributes.
                The conditions are in logical conjunction (they are connected as if with an `AND` statement).
            limit:
                Maximum number of edge instances to be returned after sorting.
            sort:
                Comma-separated list of attributes the results should be sorted by.
            timeout:
                Time allowed for successful execution. The default is `0`, or no limit.

        Returns:
             A dictionary of `edge_type: deleted_edge_count` pairs.

        Endpoint:
            - `DELETE /graph/{graph_name}/edges/{source_vertex_type}/{source_vertex_id}/{edge_type}/{target_vertex_type}/{target_vertex_id}`
                See https://docs.tigergraph.com/dev/restpp-api/built-in-endpoints#delete-an-edge
        """
        logger.info("entry: delEdges")
        if logger.level == logging.DEBUG:
            logger.debug("params: " + self._locals(locals()))

        if not sourceVertexType or not sourceVertexId:
            raise TigerGraphException("Both sourceVertexType and sourceVertexId must be provided.",
                None)

        url = self.restppUrl + "/graph/" + self.graphname + "/edges/" + sourceVertexType + "/" + str(
            sourceVertexId)

        if edgeType:
            url += "/" + edgeType
            if targetVertexType:
                url += "/" + targetVertexType
                if targetVertexId:
                    url += "/" + str(targetVertexId)

        isFirst = True
        if where:
            url += ("?" if isFirst else "&") + "filter=" + where
            isFirst = False
        if limit and sort:  # These two must be provided together
            url += ("?" if isFirst else "&") + "limit=" + str(limit) + "&sort=" + sort
            isFirst = False
        if timeout and timeout > 0:
            url += ("?" if isFirst else "&") + "timeout=" + str(timeout)

        res = self._delete(url)
        ret = {}
        for r in res:
            ret[r["e_type"]] = r["deleted_edges"]

        if logger.level == logging.DEBUG:
            logger.debug("return: " + str(ret))
        logger.info("exit: delEdges")

        return ret

    def edgeSetToDataFrame(self, edgeSet: list, withId: bool = True,
            withType: bool = False) -> 'pd.DataFrame':
        """Converts an edge set to Pandas DataFrame

        Edge sets contain instances of the same edge type. Edge sets are not generated "naturally"
        like vertex sets. Instead, you need to collect edges in (global) accumulators, like when you
        want to visualize them in GraphStudio or by other tools.

        For example:
        ```
        SetAccum<EDGE> @@edges;

        start = {country.*};

        result =
            SELECT trg
            FROM   start:src -(city_in_country:e)- city:trg
            ACCUM  @@edges += e;

        PRINT start, result, @@edges;
        ```

        The `@@edges` is an edge set.
        It contains, for each edge instance, the source and target vertex type and ID, the edge type,
        a directedness indicator and the (optional) attributes. /

        [NOTE]
        `start` and `result` are vertex sets.

        An edge set has this structure (when serialised as JSON):

        [source.wrap, json]
        ----
        [
            {
                "e_type": <edge_type_name>,
                "from_type": <source_vertex_type_name>,
                "from_id": <source_vertex_id>,
                "to_type": <target_vertex_type_name>,
                "to_id": <targe_vertex_id>,
                "directed": <true_or_false>,
                "attributes":
                    {
                        "attr1": <value1>,
                        "attr2": <value2>,
                         ⋮
                    }
            },
                ⋮
        ]
        ----

        Args:
            edgeSet:
                A JSON array containing an edge set in the format returned by queries (see below).
            withId:
                Whether to include the type and primary ID of source and target vertices as a column. Default is `True`.
            withType:
                Whether to include edge type info as a column. Default is `False`.

        Returns:
            A pandas DataFrame containing the edge attributes and optionally the type and primary
            ID or source and target vertices, and the edge type.

        """
        logger.info("entry: edgeSetToDataFrame")
        if logger.level == logging.DEBUG:
            logger.debug("params: " + self._locals(locals()))

        try:
            import pandas as pd
        except ImportError:
            raise ImportError("Pandas is required to use this function. "
                              "Download pandas using 'pip install pandas'.")

        df = pd.DataFrame(edgeSet)
        cols = []
        if withId:
            cols.extend([df["from_type"], df["from_id"], df["to_type"], df["to_id"]])
        if withType:
            cols.append(df["e_type"])
        cols.append(pd.DataFrame(df["attributes"].tolist()))

        ret = pd.concat(cols, axis=1)

        if logger.level == logging.DEBUG:
            logger.debug("return: " + str(ret))
        logger.info("exit: edgeSetToDataFrame")

        return ret
