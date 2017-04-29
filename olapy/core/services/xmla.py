# -*- encoding: utf8 -*-

from __future__ import absolute_import, division, print_function

import os
from datetime import datetime
from os.path import expanduser

from lxml import etree
from spyne import AnyXml, Application, ServiceBase, rpc
from spyne.error import InvalidCredentialsError
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

from ..mdx.tools.config_file_parser import ConfigParser
from ..services.models import DiscoverRequest  # , AuthenticationError
from ..services.models import ExecuteRequest, Session
from .xmla_discover_tools import XmlaDiscoverTools
from .xmla_execute_tools import XmlaExecuteTools
from .xmla_execute_xsds import execute_xsd


class XmlaProviderService(ServiceBase):
    """

    The main class to active soap services between xmla clients and olapy

    """

    # IMPORTANT : all xsd and soap responses are written manually (not generated by Spyne lib)
    # because Spyne doesn't support encodingStyle and other namespaces required by Excel,
    # check it <http://stackoverflow.com/questions/25046837/the-encodingstyle-attribute-is-not-allowed-in-spyne>

    # we have to instantiate XmlaDiscoverTools and declare variables
    # as class variable so we can access them in Discovery and Execute functions
    # this problem is related with Spyne architecture, NO CHOICE

    discover_tools = XmlaDiscoverTools()
    SessionId = discover_tools.SessionId

    @rpc(DiscoverRequest,
         _returns=AnyXml,
         _body_style="bare",
         _out_header=Session,
         _throws=InvalidCredentialsError
         # _throws=AuthenticationError
        )
    def Discover(ctx, request):
        """
        the first principle function of xmla protocol

        :param request: Discover function must take 3 argument ( JUST 3 ! ) RequestType,
        Restrictions and Properties , we encapsulate them in DiscoverRequest object

        :return: Discover response in xmla format

        """
        # ctx is the 'context' parameter used by Spyne
        # (which cause problems when we want to access xmla_provider instantiation variables)

        discover_tools = XmlaProviderService.discover_tools
        ctx.out_header = Session(SessionId=str(XmlaProviderService.SessionId))

        config_parser = ConfigParser(discover_tools.executer.cube_path)
        if config_parser.xmla_authentication():

            # TODO call (labster) login function or create login with token (according to labster db)
            if ctx.transport.req_env['QUERY_STRING'] != 'admin':

                raise InvalidCredentialsError(
                    fault_string='You do not have permission to access this resource',
                    fault_object=None)

                # raise AuthenticationError()

        if request.RequestType == "DISCOVER_DATASOURCES":
            return discover_tools.discover_datasources_response()

        elif request.RequestType == "DISCOVER_PROPERTIES":
            return discover_tools.discover_properties_response(request)

        elif request.RequestType == "DISCOVER_SCHEMA_ROWSETS":
            return discover_tools.discover_schema_rowsets_response(request)

        elif request.RequestType == "DISCOVER_LITERALS":
            return discover_tools.discover_literals_response(request)

        elif request.RequestType == "MDSCHEMA_SETS":
            return discover_tools.discover_mdschema_sets_response(request)

        elif request.RequestType == "MDSCHEMA_KPIS":
            return discover_tools.discover_mdschema_kpis_response(request)

        elif request.RequestType == "DBSCHEMA_CATALOGS":
            return discover_tools.discover_dbschema_catalogs_response(request)

        elif request.RequestType == "MDSCHEMA_CUBES":
            return discover_tools.discover_mdschema_cubes_response(request)

        elif request.RequestType == "DBSCHEMA_TABLES":
            return discover_tools.discover_dbschema_tables_response(request)

        elif request.RequestType == "MDSCHEMA_MEASURES":
            return discover_tools.discover_mdschema_measures__response(request)

        elif request.RequestType == "MDSCHEMA_DIMENSIONS":
            return discover_tools.discover_mdschema_dimensions_response(request)

        elif request.RequestType == "MDSCHEMA_HIERARCHIES":
            return discover_tools.discover_mdschema_hierarchies_response(
                request)

        elif request.RequestType == "MDSCHEMA_LEVELS":
            return discover_tools.discover_mdschema_levels__response(request)

        elif request.RequestType == "MDSCHEMA_MEASUREGROUPS":
            return discover_tools.discover_mdschema_measuresgroups_response(
                request)

        elif request.RequestType == "MDSCHEMA_MEASUREGROUP_DIMENSIONS":
            return discover_tools.discover_mdschema_measuresgroups_dimensions_response(
                request)

        elif request.RequestType == "MDSCHEMA_PROPERTIES":
            return discover_tools.discover_mdschema_properties_response(request)

        elif request.RequestType == "MDSCHEMA_MEMBERS":
            return discover_tools.discover_mdschema_members_response(request)

    # Execute function must take 2 argument ( JUST 2 ! ) Command and Properties
    # we encapsulate them in ExecuteRequest object
    @rpc(ExecuteRequest,
         _returns=AnyXml,
         _body_style="bare",
         _out_header=Session)
    def Execute(ctx, request):
        """
        the second principle function of xmla protocol

        :param request: Execute function must take 2 argument ( JUST 2 ! ) Command and Properties,
        we encapsulate them in ExecuteRequest object

        :return: Execute response in xml format
        """

        ctx.out_header = Session(SessionId=str(XmlaProviderService.SessionId))

        if request.Command.Statement == '':
            # check if command contains a query
            return etree.fromstring("""
            <return>
                <root xmlns="urn:schemas-microsoft-com:xml-analysis:empty"/>
            </return>
            """)
        else:
            XmlaProviderService.discover_tools.change_catalogue(
                request.Properties.PropertyList.Catalog)
            executer = XmlaProviderService.discover_tools.executer
            executer.mdx_query = request.Command.Statement
            df = executer.execute_mdx()
            xmla_tools = XmlaExecuteTools(executer)

            return etree.fromstring("""
            <return>
                <root xmlns="urn:schemas-microsoft-com:xml-analysis:mddataset"
                xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    {0}
                    <OlapInfo>
                        <CubeInfo>
                            <Cube>
                                <CubeName>Sales</CubeName>
                                <LastDataUpdate
                                xmlns="http://schemas.microsoft.com/analysisservices/2003/engine">{7}</LastDataUpdate>
                                <LastSchemaUpdate
                                xmlns="http://schemas.microsoft.com/analysisservices/2003/engine">{7}</LastSchemaUpdate>
                            </Cube>
                        </CubeInfo>
                        <AxesInfo>
                            {1}
                            {2}
                        </AxesInfo>
                            {3}
                    </OlapInfo>
                    <Axes>
                        {4}
                        {5}
                    </Axes>
                    <CellData>
                        {6}
                    </CellData>
                </root>
            </return>
            """.format(execute_xsd,
                       xmla_tools.generate_axes_info(df),
                       xmla_tools.generate_axes_info_slicer(df),
                       xmla_tools.generate_cell_info(),
                       xmla_tools.generate_xs0(df),
                       xmla_tools.generate_slicer_axis(df),
                       xmla_tools.generate_cell_data(df),
                       datetime.now().strftime('%Y-%m-%dT%H:%M:%S')).replace(
                           '&', '&amp;'))

            # Problem:
            # An XML parser returns the error “xmlParseEntityRef: noname”
            #
            # Cause:
            # There is a stray ‘&’ (ampersand character) somewhere in the XML text eg. some text & some more text
            # Solution
            # .replace('&', '&amp;')


application = Application(
    [XmlaProviderService],
    'urn:schemas-microsoft-com:xml-analysis',
    in_protocol=Soap11(validator='soft'),
    out_protocol=Soap11(validator='soft'))

# validator='soft' or nothing, this is important because spyne doesn't support encodingStyle until now !!!!

wsgi_application = WsgiApplication(application)


def start_server(write_on_file=False):
    """
    start the xmla server

    :param write_on_file = :
     - False -> server logs will be displayed on console
     - True  -> server logs will be saved in file

    :return: server instance
    """
    import logging

    from wsgiref.simple_server import make_server

    # log to the console
    # logging.basicConfig(level=logging.DEBUG")
    # log to the file
    # TODO FIX it with os
    if write_on_file:
        home_directory = expanduser("~")
        if not os.path.isdir(os.path.join(home_directory, 'logs')):
            os.makedirs(os.path.join(home_directory, 'logs'))
        logging.basicConfig(
            level=logging.DEBUG,
            filename=os.path.join(home_directory, 'logs', 'xmla.log'))
    else:
        logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('spyne.protocol.xml').setLevel(logging.DEBUG)
    logging.info("listening to http://127.0.0.1:8000/xmla")
    logging.info("wsdl is at: http://localhost:8000/xmla?wsdl")
    server = make_server('127.0.0.1', 8000, wsgi_application)
    # server = make_server('192.168.101.139', 8000, wsgi_application)
    server.serve_forever()


if __name__ == '__main__':
    start_server(write_on_file=True)
