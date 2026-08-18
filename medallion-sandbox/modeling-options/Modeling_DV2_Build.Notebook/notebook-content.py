# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# MARKDOWN ********************

# # Modeling DV2 build
# This notebook expects the shared source CSV files under `/lakehouse/default/Files/modeling_scenarios/raw/`.
# Attach the notebook to the **Modeling_DV2** lakehouse before running it.

# CELL ********************

from pyspark.sql import functions as F

RAW_BASE = "/lakehouse/default/Files/modeling_scenarios/raw"
RAW_TABLES = [
    "party",
    "person_demographics",
    "person_name",
    "contact_method",
    "address",
    "consent_preference",
    "account",
    "party_account_role",
    "product",
    "transaction_header",
    "transaction_line",
    "service_event",
    "attribute_definition",
    "party_attribute_value",
    "transaction_attribute_value",
    "forget_request",
]


def hash_key(*columns: str):
    return F.sha2(F.concat_ws("||", *[F.coalesce(F.col(col).cast("string"), F.lit("")) for col in columns]), 256)


def overwrite_table(df, table_name: str) -> None:
    df.write.mode("overwrite").format("delta").option("overwriteSchema", "true").saveAsTable(table_name)


def load_raw_csv(table_name: str):
    return (
        spark.read.option("header", True)
        .option("inferSchema", False)
        .csv(f"{RAW_BASE}/{table_name}.csv")
        .withColumn("_load_ts", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Bronze

# CELL ********************

for raw_table in RAW_TABLES:
    overwrite_table(load_raw_csv(raw_table), f"bronze_{raw_table}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Silver Raw Vault

# CELL ********************

bronze_party = spark.table("bronze_party")
bronze_demographics = spark.table("bronze_person_demographics")
bronze_name = spark.table("bronze_person_name")
bronze_contact = spark.table("bronze_contact_method")
bronze_address = spark.table("bronze_address")
bronze_consent = spark.table("bronze_consent_preference")
bronze_account = spark.table("bronze_account")
bronze_party_account_role = spark.table("bronze_party_account_role")
bronze_product = spark.table("bronze_product")
bronze_transaction_header = spark.table("bronze_transaction_header")
bronze_transaction_line = spark.table("bronze_transaction_line")
bronze_service_event = spark.table("bronze_service_event")
bronze_attribute_definition = spark.table("bronze_attribute_definition")
bronze_party_attribute = spark.table("bronze_party_attribute_value")
bronze_transaction_attribute = spark.table("bronze_transaction_attribute_value")
bronze_forget_request = spark.table("bronze_forget_request")

hub_party = (
    bronze_party
    .select(
        hash_key("party_bk").alias("hk_party"),
        "party_bk",
        "_load_ts",
    )
    .dropDuplicates(["party_bk"])
)
overwrite_table(hub_party, "silver_hub_party")

hub_account = (
    bronze_account
    .select(
        hash_key("account_bk").alias("hk_account"),
        "account_bk",
        "_load_ts",
    )
    .dropDuplicates(["account_bk"])
)
overwrite_table(hub_account, "silver_hub_account")

hub_product = (
    bronze_product
    .select(
        hash_key("product_bk").alias("hk_product"),
        "product_bk",
        "_load_ts",
    )
    .dropDuplicates(["product_bk"])
)
overwrite_table(hub_product, "silver_hub_product")

hub_transaction = (
    bronze_transaction_header
    .select(
        hash_key("transaction_bk").alias("hk_transaction"),
        "transaction_bk",
        "_load_ts",
    )
    .dropDuplicates(["transaction_bk"])
)
overwrite_table(hub_transaction, "silver_hub_transaction")

hub_service_event = (
    bronze_service_event
    .select(
        hash_key("service_event_bk").alias("hk_service_event"),
        "service_event_bk",
        "_load_ts",
    )
    .dropDuplicates(["service_event_bk"])
)
overwrite_table(hub_service_event, "silver_hub_service_event")

hub_attribute_definition = (
    bronze_attribute_definition
    .select(
        hash_key("attribute_code").alias("hk_attribute_definition"),
        "attribute_code",
        "_load_ts",
    )
    .dropDuplicates(["attribute_code"])
)
overwrite_table(hub_attribute_definition, "silver_hub_attribute_definition")

link_party_account = (
    bronze_party_account_role
    .select(
        hash_key("party_bk", "account_bk", "role_code").alias("hk_link_party_account"),
        hash_key("party_bk").alias("hk_party"),
        hash_key("account_bk").alias("hk_account"),
        "role_code",
        F.to_timestamp("effective_at").alias("effective_at"),
        "_load_ts",
    )
    .dropDuplicates(["hk_link_party_account"])
)
overwrite_table(link_party_account, "silver_link_party_account")

link_transaction_party = (
    bronze_transaction_header
    .select(
        hash_key("transaction_bk", "party_bk").alias("hk_link_transaction_party"),
        hash_key("transaction_bk").alias("hk_transaction"),
        hash_key("party_bk").alias("hk_party"),
        "_load_ts",
    )
    .dropDuplicates(["hk_link_transaction_party"])
)
overwrite_table(link_transaction_party, "silver_link_transaction_party")

link_transaction_account = (
    bronze_transaction_header
    .select(
        hash_key("transaction_bk", "account_bk").alias("hk_link_transaction_account"),
        hash_key("transaction_bk").alias("hk_transaction"),
        hash_key("account_bk").alias("hk_account"),
        "_load_ts",
    )
    .dropDuplicates(["hk_link_transaction_account"])
)
overwrite_table(link_transaction_account, "silver_link_transaction_account")

link_transaction_product = (
    bronze_transaction_line
    .select(
        hash_key("transaction_bk", "line_number", "product_bk").alias("hk_link_transaction_product"),
        hash_key("transaction_bk").alias("hk_transaction"),
        hash_key("product_bk").alias("hk_product"),
        F.col("line_number").cast("int").alias("line_number"),
        "_load_ts",
    )
    .dropDuplicates(["hk_link_transaction_product"])
)
overwrite_table(link_transaction_product, "silver_link_transaction_product")

link_service_event_party = (
    bronze_service_event
    .select(
        hash_key("service_event_bk", "party_bk").alias("hk_link_service_event_party"),
        hash_key("service_event_bk").alias("hk_service_event"),
        hash_key("party_bk").alias("hk_party"),
        "_load_ts",
    )
    .dropDuplicates(["hk_link_service_event_party"])
)
overwrite_table(link_service_event_party, "silver_link_service_event_party")

sat_party_core = (
    bronze_party
    .select(
        hash_key("party_bk").alias("hk_party"),
        "source_party_id",
        "party_type",
        "lifecycle_status",
        F.to_timestamp("created_at").alias("created_at"),
        F.to_timestamp("updated_at").alias("updated_at"),
        "_load_ts",
    )
)
overwrite_table(sat_party_core, "silver_sat_party_core")

sat_party_demographics_sensitive = (
    bronze_demographics
    .select(
        hash_key("party_bk").alias("hk_party"),
        F.to_date("birth_date").alias("birth_date"),
        "national_id_last4",
        "gender_identity",
        F.to_timestamp("effective_at").alias("effective_at"),
        "_load_ts",
    )
)
overwrite_table(sat_party_demographics_sensitive, "silver_sat_party_demographics_sensitive")

sat_party_name_sensitive = (
    bronze_name
    .select(
        hash_key("party_bk").alias("hk_party"),
        "name_type",
        "full_name",
        "given_name",
        "family_name",
        F.to_timestamp("effective_at").alias("effective_at"),
        "_load_ts",
    )
)
overwrite_table(sat_party_name_sensitive, "silver_sat_party_name_sensitive")

sat_party_contact_sensitive = (
    bronze_contact
    .select(
        hash_key("party_bk").alias("hk_party"),
        "contact_method_bk",
        "contact_type",
        "contact_value",
        F.col("is_primary").cast("boolean").alias("is_primary"),
        F.to_timestamp("effective_at").alias("effective_at"),
        "_load_ts",
    )
)
overwrite_table(sat_party_contact_sensitive, "silver_sat_party_contact_sensitive")

sat_party_address_sensitive = (
    bronze_address
    .select(
        hash_key("party_bk").alias("hk_party"),
        "address_bk",
        "address_type",
        "address_line1",
        "city",
        "state_code",
        "postal_code",
        "country_code",
        F.to_timestamp("effective_at").alias("effective_at"),
        "_load_ts",
    )
)
overwrite_table(sat_party_address_sensitive, "silver_sat_party_address_sensitive")

sat_party_consent = (
    bronze_consent
    .select(
        hash_key("party_bk").alias("hk_party"),
        "channel_code",
        "consent_status",
        F.to_timestamp("consent_captured_at").alias("consent_captured_at"),
        "_load_ts",
    )
)
overwrite_table(sat_party_consent, "silver_sat_party_consent")

party_attribute_enriched = (
    bronze_party_attribute.alias("v")
    .join(
        bronze_attribute_definition.alias("d"),
        F.col("v.attribute_code") == F.col("d.attribute_code"),
        "left",
    )
    .select(
        hash_key("v.party_bk").alias("hk_party"),
        F.col("v.attribute_code").alias("attribute_code"),
        F.col("v.attribute_value").alias("attribute_value"),
        F.to_timestamp("v.effective_at").alias("effective_at"),
        F.col("d.is_pii").cast("boolean").alias("is_pii"),
        F.col("d.sensitivity_class").alias("sensitivity_class"),
        F.col("d.erase_on_forget_request").cast("boolean").alias("erase_on_forget_request"),
        "_load_ts",
    )
)
overwrite_table(
    party_attribute_enriched.filter(F.col("is_pii") == F.lit(False)),
    "silver_sat_party_attribute_non_sensitive",
)
overwrite_table(
    party_attribute_enriched.filter(F.col("is_pii") == F.lit(True)),
    "silver_sat_party_attribute_sensitive",
)

sat_transaction_status = (
    bronze_transaction_header
    .select(
        hash_key("transaction_bk").alias("hk_transaction"),
        hash_key("party_bk").alias("hk_party"),
        hash_key("account_bk").alias("hk_account"),
        F.to_timestamp("transaction_ts").alias("transaction_ts"),
        "channel_code",
        "transaction_status",
        F.col("gross_amount").cast("decimal(10,2)").alias("gross_amount"),
        "_load_ts",
    )
)
overwrite_table(sat_transaction_status, "silver_sat_transaction_status")

transaction_attribute_enriched = (
    bronze_transaction_attribute.alias("v")
    .join(
        bronze_attribute_definition.alias("d"),
        F.col("v.attribute_code") == F.col("d.attribute_code"),
        "left",
    )
    .select(
        hash_key("v.transaction_bk").alias("hk_transaction"),
        F.col("v.attribute_code").alias("attribute_code"),
        F.col("v.attribute_value").alias("attribute_value"),
        F.to_timestamp("v.effective_at").alias("effective_at"),
        F.col("d.is_pii").cast("boolean").alias("is_pii"),
        F.col("d.erase_on_forget_request").cast("boolean").alias("erase_on_forget_request"),
        "_load_ts",
    )
)
overwrite_table(
    transaction_attribute_enriched.filter(F.col("is_pii") == F.lit(False)),
    "silver_sat_transaction_attribute_non_sensitive",
)
overwrite_table(
    transaction_attribute_enriched.filter(F.col("is_pii") == F.lit(True)),
    "silver_sat_transaction_attribute_sensitive",
)

subject_resolution = (
    bronze_party
    .select("party_bk", F.lit("source_party_id").alias("lookup_type"), F.col("source_party_id").alias("lookup_value"))
    .unionByName(
        bronze_contact.select("party_bk", F.lower("contact_type").alias("lookup_type"), F.col("contact_value").alias("lookup_value"))
    )
    .unionByName(
        bronze_account.alias("a")
        .join(bronze_party_account_role.alias("r"), "account_bk", "inner")
        .select(F.col("r.party_bk").alias("party_bk"), F.lit("source_account_id").alias("lookup_type"), F.col("a.source_account_id").alias("lookup_value"))
    )
    .dropDuplicates(["party_bk", "lookup_type", "lookup_value"])
)
overwrite_table(subject_resolution, "silver_subject_resolution")

overwrite_table(
    bronze_forget_request.select(
        "request_id",
        "party_lookup_type",
        "party_lookup_value",
        "request_status",
        F.to_timestamp("requested_at").alias("requested_at"),
    ),
    "silver_forget_request_queue",
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Gold

# CELL ********************

party_attrs_public = (
    spark.table("silver_sat_party_attribute_non_sensitive")
    .groupBy("hk_party")
    .pivot("attribute_code", ["PREFERRED_LANGUAGE", "LOYALTY_SEGMENT"])
    .agg(F.first("attribute_value"))
)

party_contact_rollup = (
    spark.table("silver_sat_party_contact_sensitive")
    .groupBy("hk_party")
    .agg(
        F.max(F.when(F.col("contact_type") == "Email", F.col("contact_value"))).alias("primary_email"),
        F.max(F.when(F.col("contact_type") == "Phone", F.col("contact_value"))).alias("primary_phone"),
    )
)

party_name_rollup = (
    spark.table("silver_sat_party_name_sensitive")
    .groupBy("hk_party")
    .agg(F.max("full_name").alias("full_name"))
)

party_address_rollup = (
    spark.table("silver_sat_party_address_sensitive")
    .groupBy("hk_party")
    .agg(
        F.max("address_line1").alias("address_line1"),
        F.max("city").alias("city"),
        F.max("state_code").alias("state_code"),
        F.max("postal_code").alias("postal_code"),
    )
)

gold_dim_party = (
    spark.table("silver_hub_party").alias("h")
    .join(spark.table("silver_sat_party_core").alias("s"), "hk_party", "left")
    .join(party_attrs_public.alias("a"), "hk_party", "left")
    .select(
        "hk_party",
        "party_bk",
        "party_type",
        "lifecycle_status",
        F.col("a.PREFERRED_LANGUAGE").alias("preferred_language"),
        F.col("a.LOYALTY_SEGMENT").alias("loyalty_segment"),
    )
)
overwrite_table(gold_dim_party, "gold_dim_party")

gold_secure_party_profile = (
    spark.table("silver_hub_party").alias("h")
    .join(party_name_rollup.alias("n"), "hk_party", "left")
    .join(party_contact_rollup.alias("c"), "hk_party", "left")
    .join(party_address_rollup.alias("a"), "hk_party", "left")
    .join(spark.table("silver_sat_party_demographics_sensitive").alias("d"), "hk_party", "left")
    .select(
        "hk_party",
        "party_bk",
        "full_name",
        "primary_email",
        "primary_phone",
        "address_line1",
        "city",
        "state_code",
        "postal_code",
        "birth_date",
        "national_id_last4",
        "gender_identity",
    )
)
overwrite_table(gold_secure_party_profile, "gold_secure_party_profile")

gold_dim_account = (
    spark.table("silver_hub_account").alias("h")
    .join(spark.table("silver_link_party_account").alias("l"), "hk_account", "left")
    .join(
        bronze_account.select(
            hash_key("account_bk").alias("hk_account"),
            "account_bk",
            "account_type",
            "account_status",
            F.to_timestamp("opened_at").alias("opened_at"),
        ).alias("a"),
        "hk_account",
        "left",
    )
    .select("hk_account", "account_bk", "account_type", "account_status", "opened_at")
    .dropDuplicates(["hk_account"])
)
overwrite_table(gold_dim_account, "gold_dim_account")

gold_dim_product = (
    bronze_product
    .select(
        hash_key("product_bk").alias("hk_product"),
        "product_bk",
        "sku_code",
        "product_name",
        "product_category",
        F.col("unit_price").cast("decimal(10,2)").alias("unit_price"),
    )
    .dropDuplicates(["product_bk"])
)
overwrite_table(gold_dim_product, "gold_dim_product")

transaction_coupon = (
    spark.table("silver_sat_transaction_attribute_non_sensitive")
    .groupBy("hk_transaction")
    .pivot("attribute_code", ["COUPON_CODE"])
    .agg(F.first("attribute_value"))
)

transaction_line_rollup = (
    bronze_transaction_line
    .groupBy("transaction_bk")
    .agg(
        F.count("*").alias("line_count"),
        F.sum(F.col("net_amount").cast("decimal(10,2)")).alias("net_amount"),
    )
    .select(hash_key("transaction_bk").alias("hk_transaction"), "line_count", "net_amount")
)

gold_fact_transaction = (
    spark.table("silver_sat_transaction_status").alias("t")
    .join(transaction_line_rollup.alias("l"), "hk_transaction", "left")
    .join(transaction_coupon.alias("c"), "hk_transaction", "left")
    .select(
        "hk_transaction",
        "hk_party",
        "hk_account",
        "transaction_ts",
        "channel_code",
        "transaction_status",
        "gross_amount",
        "line_count",
        "net_amount",
        F.col("c.COUPON_CODE").alias("coupon_code"),
    )
)
overwrite_table(gold_fact_transaction, "gold_fact_transaction")

gold_fact_service_event = (
    bronze_service_event
    .select(
        hash_key("service_event_bk").alias("hk_service_event"),
        hash_key("party_bk").alias("hk_party"),
        "service_event_bk",
        "case_type",
        "event_status",
        F.to_timestamp("opened_at").alias("opened_at"),
        F.to_timestamp("resolved_at").alias("resolved_at"),
    )
)
overwrite_table(gold_fact_service_event, "gold_fact_service_event")

