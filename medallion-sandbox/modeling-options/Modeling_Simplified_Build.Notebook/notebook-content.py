# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# MARKDOWN ********************

# # Modeling simplified build
# This notebook expects the shared source CSV files under `/lakehouse/default/Files/modeling_scenarios/raw/`.
# Attach the notebook to the **Modeling_Simplified** lakehouse before running it.

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

# ## Silver joined-conformed model

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

party_attrs_enriched = (
    bronze_party_attribute.alias("v")
    .join(
        bronze_attribute_definition.alias("d"),
        F.col("v.attribute_code") == F.col("d.attribute_code"),
        "left",
    )
    .select(
        F.col("v.party_bk").alias("party_bk"),
        F.col("v.attribute_code").alias("attribute_code"),
        F.col("v.attribute_value").alias("attribute_value"),
        F.col("d.is_pii").cast("boolean").alias("is_pii"),
        F.col("d.erase_on_forget_request").cast("boolean").alias("erase_on_forget_request"),
    )
)

party_attrs_public = (
    party_attrs_enriched
    .filter(F.col("is_pii") == F.lit(False))
    .groupBy("party_bk")
    .pivot("attribute_code", ["PREFERRED_LANGUAGE", "LOYALTY_SEGMENT"])
    .agg(F.first("attribute_value"))
)

party_attrs_pii = (
    party_attrs_enriched
    .filter(F.col("is_pii") == F.lit(True))
    .groupBy("party_bk")
    .pivot("attribute_code", ["ALT_CONTACT_NAME"])
    .agg(F.first("attribute_value"))
)

party_consent_rollup = (
    bronze_consent
    .groupBy("party_bk")
    .agg(
        F.max(F.when(F.col("channel_code") == "EMAIL", F.col("consent_status"))).alias("email_consent_status"),
        F.max(F.when(F.col("channel_code") == "SMS", F.col("consent_status"))).alias("sms_consent_status"),
        F.max(F.when(F.col("channel_code") == "PHONE", F.col("consent_status"))).alias("phone_consent_status"),
    )
)

party_contact_rollup = (
    bronze_contact
    .groupBy("party_bk")
    .agg(
        F.max(F.when(F.col("contact_type") == "Email", F.col("contact_value"))).alias("primary_email"),
        F.max(F.when(F.col("contact_type") == "Phone", F.col("contact_value"))).alias("primary_phone"),
    )
)

party_address_rollup = (
    bronze_address
    .groupBy("party_bk")
    .agg(
        F.max("address_line1").alias("address_line1"),
        F.max("city").alias("city"),
        F.max("state_code").alias("state_code"),
        F.max("postal_code").alias("postal_code"),
        F.max("country_code").alias("country_code"),
    )
)

silver_party_core = (
    bronze_party.alias("p")
    .join(party_consent_rollup.alias("c"), "party_bk", "left")
    .join(party_attrs_public.alias("a"), "party_bk", "left")
    .select(
        "party_bk",
        "source_party_id",
        "party_type",
        "lifecycle_status",
        F.to_timestamp("created_at").alias("created_at"),
        F.to_timestamp("updated_at").alias("updated_at"),
        F.col("a.PREFERRED_LANGUAGE").alias("preferred_language"),
        F.col("a.LOYALTY_SEGMENT").alias("loyalty_segment"),
        "email_consent_status",
        "sms_consent_status",
        "phone_consent_status",
    )
)
overwrite_table(silver_party_core, "silver_party_core")

silver_party_pii = (
    bronze_demographics.alias("d")
    .join(bronze_name.alias("n"), "party_bk", "left")
    .join(party_contact_rollup.alias("c"), "party_bk", "left")
    .join(party_address_rollup.alias("a"), "party_bk", "left")
    .join(party_attrs_pii.alias("p"), "party_bk", "left")
    .select(
        "party_bk",
        F.to_date("birth_date").alias("birth_date"),
        "national_id_last4",
        "gender_identity",
        "full_name",
        "given_name",
        "family_name",
        "primary_email",
        "primary_phone",
        "address_line1",
        "city",
        "state_code",
        "postal_code",
        "country_code",
        F.col("p.ALT_CONTACT_NAME").alias("alt_contact_name"),
    )
)
overwrite_table(silver_party_pii, "silver_party_pii")

silver_account = (
    bronze_account.alias("a")
    .join(bronze_party_account_role.alias("r"), "account_bk", "left")
    .select(
        "account_bk",
        "source_account_id",
        "account_type",
        "account_status",
        F.to_timestamp("opened_at").alias("opened_at"),
        F.col("r.party_bk").alias("primary_party_bk"),
        "role_code",
    )
)
overwrite_table(silver_account, "silver_account")

silver_service_event = (
    bronze_service_event
    .select(
        "service_event_bk",
        "party_bk",
        "case_type",
        "event_status",
        F.to_timestamp("opened_at").alias("opened_at"),
        F.to_timestamp("resolved_at").alias("resolved_at"),
    )
)
overwrite_table(silver_service_event, "silver_service_event")

transaction_attr_enriched = (
    bronze_transaction_attribute.alias("v")
    .join(
        bronze_attribute_definition.alias("d"),
        F.col("v.attribute_code") == F.col("d.attribute_code"),
        "left",
    )
    .select(
        F.col("v.transaction_bk").alias("transaction_bk"),
        F.col("v.attribute_code").alias("attribute_code"),
        F.col("v.attribute_value").alias("attribute_value"),
        F.col("d.is_pii").cast("boolean").alias("is_pii"),
    )
)

transaction_attr_public = (
    transaction_attr_enriched
    .filter(F.col("is_pii") == F.lit(False))
    .groupBy("transaction_bk")
    .pivot("attribute_code", ["COUPON_CODE"])
    .agg(F.first("attribute_value"))
)

transaction_attr_pii = (
    transaction_attr_enriched
    .filter(F.col("is_pii") == F.lit(True))
    .groupBy("transaction_bk")
    .pivot("attribute_code", ["GIFT_MESSAGE"])
    .agg(F.first("attribute_value"))
)

transaction_line_rollup = (
    bronze_transaction_line
    .groupBy("transaction_bk")
    .agg(
        F.count("*").alias("line_count"),
        F.sum(F.col("net_amount").cast("decimal(10,2)")).alias("net_amount"),
        F.max("product_bk").alias("last_product_bk"),
    )
)

silver_transaction = (
    bronze_transaction_header.alias("h")
    .join(transaction_line_rollup.alias("l"), "transaction_bk", "left")
    .join(transaction_attr_public.alias("a"), "transaction_bk", "left")
    .select(
        "transaction_bk",
        "account_bk",
        "party_bk",
        F.to_timestamp("transaction_ts").alias("transaction_ts"),
        "channel_code",
        "transaction_status",
        F.col("gross_amount").cast("decimal(10,2)").alias("gross_amount"),
        "line_count",
        "net_amount",
        "last_product_bk",
        F.col("a.COUPON_CODE").alias("coupon_code"),
    )
)
overwrite_table(silver_transaction, "silver_transaction")

silver_transaction_pii = (
    transaction_attr_pii
    .select("transaction_bk", F.col("GIFT_MESSAGE").alias("gift_message"))
)
overwrite_table(silver_transaction_pii, "silver_transaction_pii")

silver_subject_resolution = (
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
overwrite_table(silver_subject_resolution, "silver_subject_resolution")

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

gold_dim_customer = (
    spark.table("silver_party_core")
    .select(
        "party_bk",
        "source_party_id",
        "party_type",
        "lifecycle_status",
        "preferred_language",
        "loyalty_segment",
        "email_consent_status",
        "sms_consent_status",
        "phone_consent_status",
    )
)
overwrite_table(gold_dim_customer, "gold_dim_customer")

gold_secure_customer_profile = (
    spark.table("silver_party_core").alias("c")
    .join(spark.table("silver_party_pii").alias("p"), "party_bk", "left")
    .select(
        "party_bk",
        "source_party_id",
        "full_name",
        "given_name",
        "family_name",
        "primary_email",
        "primary_phone",
        "address_line1",
        "city",
        "state_code",
        "postal_code",
        "birth_date",
        "national_id_last4",
        "gender_identity",
        "alt_contact_name",
    )
)
overwrite_table(gold_secure_customer_profile, "gold_secure_customer_profile")

gold_dim_account = (
    spark.table("silver_account")
    .select(
        "account_bk",
        "source_account_id",
        "account_type",
        "account_status",
        "opened_at",
        "primary_party_bk",
        "role_code",
    )
)
overwrite_table(gold_dim_account, "gold_dim_account")

gold_dim_product = (
    bronze_product
    .select(
        "product_bk",
        "sku_code",
        "product_name",
        "product_category",
        F.col("unit_price").cast("decimal(10,2)").alias("unit_price"),
    )
)
overwrite_table(gold_dim_product, "gold_dim_product")

gold_fact_transaction = (
    spark.table("silver_transaction")
    .select(
        "transaction_bk",
        "account_bk",
        "party_bk",
        "transaction_ts",
        "channel_code",
        "transaction_status",
        "gross_amount",
        "line_count",
        "net_amount",
        "last_product_bk",
        "coupon_code",
    )
)
overwrite_table(gold_fact_transaction, "gold_fact_transaction")

gold_fact_service_event = (
    spark.table("silver_service_event")
    .select(
        "service_event_bk",
        "party_bk",
        "case_type",
        "event_status",
        "opened_at",
        "resolved_at",
    )
)
overwrite_table(gold_fact_service_event, "gold_fact_service_event")
