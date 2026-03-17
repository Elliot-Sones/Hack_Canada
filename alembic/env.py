from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.models import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL_SYNC)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

BETTER_AUTH_TABLES = {"user", "session", "account", "verification"}

# PostGIS extension tables that Alembic should never touch
POSTGIS_SCHEMAS = {"tiger", "tiger_data", "topology"}
POSTGIS_TABLE_PREFIXES = (
    "spatial_ref_sys", "geography_columns", "geometry_columns", "raster_columns",
    "raster_overviews", "topology", "layer",
    # postgis_tiger_geocoder tables
    "addr", "addrfeat", "bg", "county", "county_lookup", "countysub_lookup",
    "cousub", "direction_lookup", "edges", "faces", "featnames", "geocode_settings",
    "geocode_settings_default", "loader_", "pagc_", "place", "place_lookup",
    "secondary_unit_lookup", "state", "state_lookup", "street_type_lookup",
    "tabblock", "tabblock20", "tract", "zcta5", "zip_lookup", "zip_state",
)


def include_name(name, type_, parent_names):
    if type_ == "table":
        if name in BETTER_AUTH_TABLES:
            return False
        if any(name.startswith(p) for p in POSTGIS_TABLE_PREFIXES):
            return False
    if type_ == "schema":
        return name not in POSTGIS_SCHEMAS
    return True


def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and reflected and compare_to is None:
        # Table exists in DB but not in models — skip it (don't drop)
        if any(name.startswith(p) for p in POSTGIS_TABLE_PREFIXES):
            return False
        if name in BETTER_AUTH_TABLES:
            return False
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"}, include_name=include_name, include_object=include_object)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, include_name=include_name, include_object=include_object)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
