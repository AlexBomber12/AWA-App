<a id="__init__"></a>

# \_\_init\_\_

<a id="repricer"></a>

# repricer

<a id="repricer.tests"></a>

# repricer.tests

<a id="repricer.tests.test_smoke"></a>

# repricer.tests.test\_smoke

<a id="repricer.tests.test_imports"></a>

# repricer.tests.test\_imports

<a id="repricer.app"></a>

# repricer.app

<a id="repricer.app.deps"></a>

# repricer.app.deps

Placeholder module for Keepa / SP-API clients.

<a id="repricer.app.schemas"></a>

# repricer.app.schemas

<a id="repricer.app.main"></a>

# repricer.app.main

<a id="repricer.app.logic"></a>

# repricer.app.logic

<a id="repricer.app.logic.MIN_MARGIN"></a>

#### MIN\_MARGIN

15 % ROI

<a id="repricer.app.logic.compute_price"></a>

#### compute\_price

```python
def compute_price(asin: str, cost: Decimal, fees: Decimal) -> Decimal
```

Toy algorithm: ensure 15 % ROI and round to cents.
Replace with real competitive logic later.

<a id="db"></a>

# db

<a id="db.utils"></a>

# db.utils

<a id="db.utils.views"></a>

# db.utils.views

<a id="db.utils.views.replace_view"></a>

#### replace\_view

```python
def replace_view(name: str, new_sql: str) -> None
```

Drop and recreate a SQL view atomically.

<a id="ingest"></a>

# ingest

<a id="ingest.tests"></a>

# ingest.tests

<a id="ingest.tests.test_smoke"></a>

# ingest.tests.test\_smoke

<a id="ingest.upload_router"></a>

# ingest.upload\_router

<a id="ingest.maintenance"></a>

# ingest.maintenance

<a id="ingest.copy_loader"></a>

# ingest.copy\_loader

<a id="ingest.copy_loader.copy_df_via_temp"></a>

#### copy\_df\_via\_temp

```python
def copy_df_via_temp(engine: Engine,
                     df: pd.DataFrame,
                     target_table: str,
                     *,
                     target_schema: str | None = None,
                     columns: Sequence[str],
                     conflict_cols: Sequence[str] | None = None,
                     analyze_after: bool = False,
                     connection: Any | None = None) -> int
```

Bulk load *df* into *target_table* using COPY and a staging table.

<a id="ingest.tasks"></a>

# ingest.tasks

<a id="ingest.tasks.task_import_file"></a>

#### task\_import\_file

```python
@celery_app.task(name="ingest.import_file", bind=True)
def task_import_file(self: Any,
                     uri: str,
                     report_type: str | None = None,
                     force: bool = False) -> dict[str, Any]
```

Import a file into Postgres using existing ETL pipeline.

<a id="ingest.email_watcher"></a>

# ingest.email\_watcher

<a id="ingest.email_watcher.main"></a>

#### main

```python
def main() -> dict[str, str]
```

Upload CSV/XLSX attachments to MinIO and trigger ingestion.

Returns {"status": "success"} when processing completes.

<a id="ingest.ingest_router"></a>

# ingest.ingest\_router

<a id="ingest.celery_app"></a>

# ingest.celery\_app

<a id="etl"></a>

# etl

<a id="etl.fba_fee_ingestor"></a>

# etl.fba\_fee\_ingestor

<a id="etl.dialects.amazon_settlements"></a>

# etl.dialects.amazon\_settlements

<a id="etl.dialects.amazon_inventory_ledger"></a>

# etl.dialects.amazon\_inventory\_ledger

<a id="etl.dialects"></a>

# etl.dialects

<a id="etl.dialects.amazon_ads_sp_cost"></a>

# etl.dialects.amazon\_ads\_sp\_cost

<a id="etl.dialects.amazon_reimbursements"></a>

# etl.dialects.amazon\_reimbursements

<a id="etl.dialects.schemas"></a>

# etl.dialects.schemas

<a id="etl.dialects.test_generic"></a>

# etl.dialects.test\_generic

<a id="etl.dialects.amazon_fee_preview"></a>

# etl.dialects.amazon\_fee\_preview

<a id="etl.dialects.amazon_returns"></a>

# etl.dialects.amazon\_returns

<a id="etl.keepa_ingestor"></a>

# etl.keepa\_ingestor

<a id="etl.db"></a>

# etl.db

<a id="etl.sp_fees"></a>

# etl.sp\_fees

<a id="api"></a>

# api

<a id="api.tests.test_roi_basic_auth"></a>

# api.tests.test\_roi\_basic\_auth

<a id="api.tests.test_entrypoint"></a>

# api.tests.test\_entrypoint

<a id="api.tests.test_llm"></a>

# api.tests.test\_llm

<a id="api.tests.test_stats_future_contracts"></a>

# api.tests.test\_stats\_future\_contracts

<a id="api.tests.test_stats_sql"></a>

# api.tests.test\_stats\_sql

<a id="api.tests.test_sentry_event"></a>

# api.tests.test\_sentry\_event

<a id="api.tests.test_sentry_event.DummyTransport"></a>

## DummyTransport Objects

```python
class DummyTransport()
```

<a id="api.tests.test_sentry_event.DummyTransport.capture_envelope"></a>

#### capture\_envelope

```python
def capture_envelope(envelope)
```

Capture events sent as envelopes by Sentry SDK >= 2.0.

<a id="api.tests.test_health"></a>

# api.tests.test\_health

<a id="api.tests.test_roi_filters"></a>

# api.tests.test\_roi\_filters

<a id="api.tests.test_rate_limit"></a>

# api.tests.test\_rate\_limit

<a id="api.tests.test_rate_limit.app"></a>

#### app

noqa: E402

<a id="api.tests.test_stats_contracts"></a>

# api.tests.test\_stats\_contracts

<a id="api.tests.test_score"></a>

# api.tests.test\_score

<a id="api.tests.test_imports"></a>

# api.tests.test\_imports

<a id="api.tests.test_errors_json"></a>

# api.tests.test\_errors\_json

<a id="api.tests.test_cors"></a>

# api.tests.test\_cors

<a id="api.tests.test_sentry_scrub"></a>

# api.tests.test\_sentry\_scrub

<a id="api.errors"></a>

# api.errors

<a id="api.logging_config"></a>

# api.logging\_config

<a id="api.sentry_config"></a>

# api.sentry\_config

<a id="api.security"></a>

# api.security

<a id="api.routes"></a>

# api.routes

<a id="api.routes.roi"></a>

# api.routes.roi

<a id="api.routes.score"></a>

# api.routes.score

<a id="api.routes.repository"></a>

# api.routes.repository

<a id="api.routes.stats"></a>

# api.routes.stats

<a id="api.routes.health"></a>

# api.routes.health

<a id="api.routes.health.MAX_SKEW"></a>

#### MAX\_SKEW

seconds

<a id="api.routes.health.health"></a>

#### health

```python
@router.get("/health", include_in_schema=False)
async def health(session: AsyncSession = Depends(get_session)) -> JSONResponse
```

Return 200 when DB reachable and clocks are in sync.

<a id="api.migrations.env"></a>

# api.migrations.env

<a id="api.migrations"></a>

# api.migrations

<a id="api.migrations.versions.0022_fix_roi_view"></a>

# api.migrations.versions.0022\_fix\_roi\_view

<a id="api.migrations.versions.0002_create_roi_view"></a>

# api.migrations.versions.0002\_create\_roi\_view

<a id="api.migrations.versions"></a>

# api.migrations.versions

<a id="api.migrations.versions.0020_unified_schema"></a>

# api.migrations.versions.0020\_unified\_schema

<a id="api.migrations.versions.0004_fee_cron"></a>

# api.migrations.versions.0004\_fee\_cron

<a id="api.migrations.versions.0024_create_buybox"></a>

# api.migrations.versions.0024\_create\_buybox

<a id="api.migrations.versions.0023_add_storage_fee"></a>

# api.migrations.versions.0023\_add\_storage\_fee

<a id="api.migrations.versions.0003_vendor_prices"></a>

# api.migrations.versions.0003\_vendor\_prices

<a id="api.migrations.versions.0025_pr4_indexes_loadlog"></a>

# api.migrations.versions.0025\_pr4\_indexes\_loadlog

<a id="api.migrations.versions.0006_fix_roi_views"></a>

# api.migrations.versions.0006\_fix\_roi\_views

<a id="api.migrations.versions.0001_baseline"></a>

# api.migrations.versions.0001\_baseline

<a id="api.migrations.versions.3e9d5c5aff2c_rename_fulf_fee"></a>

# api.migrations.versions.3e9d5c5aff2c\_rename\_fulf\_fee

<a id="api.migrations.versions.0026_amazon_new_reports"></a>

# api.migrations.versions.0026\_amazon\_new\_reports

<a id="api.roi_repository"></a>

# api.roi\_repository

<a id="api.db"></a>

# api.db

<a id="api.main"></a>

# api.main

<a id="api.main.ready"></a>

#### ready

```python
@app.get("/ready", status_code=status.HTTP_200_OK, include_in_schema=False)
async def ready(session: AsyncSession = Depends(get_session)) -> dict[str,
                                                                      str]
```

Return 200 only when migrations are at head.

<a id="api.config"></a>

# api.config

<a id="api.models"></a>

# api.models

<a id="api.models.fee"></a>

# api.models.fee

<a id="price_importer"></a>

# price\_importer

<a id="price_importer.services_common.db_url"></a>

# price\_importer.services\_common.db\_url

<a id="price_importer.services_common.db_url.build_url"></a>

#### build\_url

```python
def build_url(async_: bool = True) -> str
```

Return Postgres DSN from environment variables.

<a id="price_importer.services_common.llm"></a>

# price\_importer.services\_common.llm

<a id="price_importer.services_common.base"></a>

# price\_importer.services\_common.base

<a id="price_importer.services_common"></a>

# price\_importer.services\_common

<a id="price_importer.services_common.models_vendor"></a>

# price\_importer.services\_common.models\_vendor

<a id="price_importer.services_common.keepa"></a>

# price\_importer.services\_common.keepa

<a id="price_importer.services_common.db"></a>

# price\_importer.services\_common.db

<a id="price_importer.services_common.db.build_sqlalchemy_url"></a>

#### build\_sqlalchemy\_url

```python
def build_sqlalchemy_url() -> str
```

Return Postgres URL for SQLAlchemy engines.

<a id="price_importer.services_common.db.build_asyncpg_dsn"></a>

#### build\_asyncpg\_dsn

```python
def build_asyncpg_dsn() -> str
```

Return DSN suitable for asyncpg (without driver suffix).

<a id="price_importer.services_common.db.refresh_mvs"></a>

#### refresh\_mvs

```python
def refresh_mvs(conn: Engine | Connection) -> None
```

Refresh materialized views, using CONCURRENTLY when safe.

<a id="price_importer.services_common.settings"></a>

# price\_importer.services\_common.settings

<a id="price_importer.import"></a>

# price\_importer.import

<a id="price_importer.tests.test_reader"></a>

# price\_importer.tests.test\_reader

<a id="price_importer.tests"></a>

# price\_importer.tests

<a id="price_importer.tests.test_smoke"></a>

# price\_importer.tests.test\_smoke

<a id="price_importer.tests.test_normaliser"></a>

# price\_importer.tests.test\_normaliser

<a id="price_importer.tests.test_imports"></a>

# price\_importer.tests.test\_imports

<a id="price_importer.tests.conftest"></a>

# price\_importer.tests.conftest

<a id="price_importer.normaliser"></a>

# price\_importer.normaliser

<a id="price_importer.repository"></a>

# price\_importer.repository

<a id="price_importer.reader"></a>

# price\_importer.reader

<a id="price_importer.common.db_url"></a>

# price\_importer.common.db\_url

<a id="price_importer.common.db_url.make_dsn"></a>

#### make\_dsn

```python
def make_dsn(async_: bool = False) -> str
```

Return DSN using shared builder.

<a id="price_importer.common.db_url.build_url"></a>

#### build\_url

```python
def build_url(async_: bool = False) -> str
```

Return Postgres DSN built from environment variables.

<a id="price_importer.common.base"></a>

# price\_importer.common.base

<a id="price_importer.common"></a>

# price\_importer.common

<a id="price_importer.common.models_vendor"></a>

# price\_importer.common.models\_vendor

<a id="llm_server"></a>

# llm\_server

<a id="llm_server.app"></a>

# llm\_server.app

<a id="emailer"></a>

# emailer

<a id="emailer.tests"></a>

# emailer.tests

<a id="emailer.tests.test_smoke"></a>

# emailer.tests.test\_smoke

<a id="emailer.tests.test_import_emailer"></a>

# emailer.tests.test\_import\_emailer

<a id="emailer.generate_body"></a>

# emailer.generate\_body

<a id="fees_h10"></a>

# fees\_h10

<a id="fees_h10.tests"></a>

# fees\_h10.tests

<a id="fees_h10.tests.test_smoke"></a>

# fees\_h10.tests.test\_smoke

<a id="fees_h10.repository"></a>

# fees\_h10.repository

<a id="fees_h10.repository.upsert_fees_raw"></a>

#### upsert\_fees\_raw

```python
def upsert_fees_raw(engine: Engine,
                    rows: Iterable[Mapping[str, Any]],
                    *,
                    testing: bool = False) -> dict[str, int] | None
```

Idempotent upsert for fees.

TESTING-only: returns counts for inserted/updated/skipped rows.
Assumes logical key (asin, marketplace, fee_type).
Only updates when one of the mutable fields changes.

<a id="fees_h10.worker"></a>

# fees\_h10.worker

<a id="fees_h10.worker.list_active_asins"></a>

#### list\_active\_asins

```python
def list_active_asins() -> list[str]
```

Return known ASINs or an empty list if unavailable.

<a id="fees_h10.client"></a>

# fees\_h10.client

<a id="alert_bot"></a>

# alert\_bot

<a id="alert_bot.tests"></a>

# alert\_bot.tests

<a id="alert_bot.tests.test_smoke"></a>

# alert\_bot.tests.test\_smoke

<a id="alert_bot.alert_bot"></a>

# alert\_bot.alert\_bot

<a id="alert_bot.rules"></a>

# alert\_bot.rules

<a id="logistics_etl"></a>

# logistics\_etl

Daily logistics ETL job.

<a id="logistics_etl.tests.test_client"></a>

# logistics\_etl.tests.test\_client

<a id="logistics_etl.tests"></a>

# logistics\_etl.tests

<a id="logistics_etl.tests.test_smoke"></a>

# logistics\_etl.tests.test\_smoke

<a id="logistics_etl.tests.test_imports"></a>

# logistics\_etl.tests.test\_imports

<a id="logistics_etl.tests.test_repository"></a>

# logistics\_etl.tests.test\_repository

<a id="logistics_etl.tests.conftest"></a>

# logistics\_etl.tests.conftest

<a id="logistics_etl.tests.test_cron"></a>

# logistics\_etl.tests.test\_cron

<a id="logistics_etl.cron"></a>

# logistics\_etl.cron

<a id="logistics_etl.repository"></a>

# logistics\_etl.repository

<a id="logistics_etl.flow"></a>

# logistics\_etl.flow

<a id="logistics_etl.db"></a>

# logistics\_etl.db

<a id="logistics_etl.__main__"></a>

# logistics\_etl.\_\_main\_\_

<a id="logistics_etl.client"></a>

# logistics\_etl.client

<a id="common"></a>

# common

<a id="common.db_url"></a>

# common.db\_url

<a id="common.db_url.build_url"></a>

#### build\_url

```python
def build_url(async_: bool = True) -> str
```

Return Postgres DSN from environment variables.

<a id="common.llm"></a>

# common.llm

<a id="common.base"></a>

# common.base

<a id="common.base.Base"></a>

## Base Objects

```python
class Base(DeclarativeBase)
```

Base class for SQLAlchemy models.

<a id="common.models_vendor"></a>

# common.models\_vendor

<a id="common.models_vendor.Vendor"></a>

## Vendor Objects

```python
class Vendor(Base)
```

Vendor of inventory items.

<a id="common.models_vendor.VendorPrice"></a>

## VendorPrice Objects

```python
class VendorPrice(Base)
```

Association table linking vendors to pricing.

<a id="common.keepa"></a>

# common.keepa

<a id="common.dsn"></a>

# common.dsn

<a id="common.dsn.build_dsn"></a>

#### build\_dsn

```python
def build_dsn(sync: bool = True) -> str
```

Return a Postgres DSN, validating required variables.

The function prefers explicit DSNs via ``PG_SYNC_DSN`` / ``PG_ASYNC_DSN`` or
``DATABASE_URL``.  If those are absent it assembles a connection string from
``PG_HOST`` and related variables and raises a helpful error when any are
missing.

<a id="common.db"></a>

# common.db

<a id="common.db.build_sqlalchemy_url"></a>

#### build\_sqlalchemy\_url

```python
def build_sqlalchemy_url() -> str
```

Return Postgres URL for SQLAlchemy engines.

<a id="common.db.build_asyncpg_dsn"></a>

#### build\_asyncpg\_dsn

```python
def build_asyncpg_dsn() -> str
```

Return DSN suitable for asyncpg (without driver suffix).

<a id="common.db.refresh_mvs"></a>

#### refresh\_mvs

```python
def refresh_mvs(conn: Engine | Connection) -> None
```

Refresh materialized views, using CONCURRENTLY when safe.

<a id="common.settings"></a>

# common.settings

<a id="common.config"></a>

# common.config
