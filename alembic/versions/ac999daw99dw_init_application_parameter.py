from typing import Sequence, Union
import uuid
import json
import sqlalchemy as sa
from alembic import op

revision = 'ac999daw99dw'
down_revision: Union[str, Sequence[str], None] = '99b5c52e9506'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PARAM_FILE = "./alembic/parameters/init_application_parameters.json"

def parse_parameters_clean(data, path=""):
    params = {}
    for key, value in data.items():
        current_path = f"{path}.{key}" if path else key

        if isinstance(value, dict):
            if value.get("parameter") == 1:
                clean_value = {k: v for k, v in value.items() if k != "parameter"}
                params[current_path] = clean_value
            else:
                nested = parse_parameters_clean(value, current_path)
                params.update(nested)
        else:
            nested = parse_parameters_clean(value, current_path)
            params.update(nested)
            
    return params


def upgrade():
    conn = op.get_bind()
    metadata = sa.MetaData()
    metadata.reflect(bind=conn)
    table = metadata.tables['application_parameters']

    with open(PARAM_FILE, 'r') as f:
        data = json.load(f)

    parameters = parse_parameters_clean(data)

    for name, param in parameters.items():
        conn.execute(table.insert().values(
            id=str(uuid.uuid4()),
            name=name,
            kind=param.get("kind", None),
            default_value=param.get("default_value", None),
            type=param.get("type", "str"),
            visibility=param.get("visibility", "public")
        ))


def downgrade():
    conn = op.get_bind()
    metadata = sa.MetaData()
    metadata.reflect(bind=conn)
    table = metadata.tables['application_parameters']

    with open(PARAM_FILE, 'r') as f:
        data = json.load(f)

    parameters = parse_parameters_clean(data)

    for name in parameters.keys():
        conn.execute(table.delete().where(table.c.name == name))