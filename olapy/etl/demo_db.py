from olapy.etl.etl import run_olapy_etl

import dotenv, logging
dotenv.load_dotenv(dotenv.find_dotenv())
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

if __name__ == '__main__':
    dims_infos = {
        # 'dimension': ['col_id'],
        'Geography': ['geography_key'],
        'Product': ['product_key']
    }

    facts_ids = ['geography_key', 'product_key']

    from bonobo.commands.run import get_default_services
    services = get_default_services(__file__)
    run_olapy_etl(source_type='db',dims_infos=dims_infos, facts_table='sales_facts', facts_ids=facts_ids,services=services)
