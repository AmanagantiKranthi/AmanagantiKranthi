import sys
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, TimestampType, DecimalType
)
from awsglue.context import GlueContext
from awsglue.job import Job

args = getResolvedOptions(
    sys.argv,
    ["JOB_NAME", "SOURCE_PATH", "TARGET_PATH", "QUARANTINE_PATH"],
)

sc = SparkContext.getOrCreate()
glue_context = GlueContext(sc)
spark = glue_context.spark_session
job = Job(glue_context)
job.init(args["JOB_NAME"], args)

schema = StructType([
    StructField("order_id", StringType(), True),
    StructField("customer_id", StringType(), True),
    StructField("order_ts", StringType(), True),
    StructField("amount", StringType(), True),
    StructField("currency", StringType(), True),
])

raw = (
    spark.read
    .option("header", "true")
    .schema(schema)
    .csv(args["SOURCE_PATH"])
)

typed = (
    raw
    .withColumn("order_ts", F.to_timestamp("order_ts", "yyyy-MM-dd HH:mm:ss"))
    .withColumn("amount", F.col("amount").cast(DecimalType(18, 2)))
    .withColumn("order_id", F.trim("order_id"))
    .withColumn("customer_id", F.trim("customer_id"))
    .withColumn("currency", F.upper(F.trim("currency")))
)

invalid_condition = (
    F.col("order_id").isNull() | (F.col("order_id") == "") |
    F.col("customer_id").isNull() | (F.col("customer_id") == "") |
    F.col("order_ts").isNull() |
    F.col("amount").isNull() | (F.col("amount") < 0) |
    F.col("currency").isNull() | (F.col("currency") == "")
)

rejected = typed.filter(invalid_condition)
valid = typed.filter(~invalid_condition)

# Deterministic deduplication: retain the latest timestamp per order_id.
from pyspark.sql.window import Window

window = Window.partitionBy("order_id").orderBy(F.col("order_ts").desc())
deduplicated = (
    valid
    .withColumn("_row_num", F.row_number().over(window))
    .filter(F.col("_row_num") == 1)
    .drop("_row_num")
)

curated = (
    deduplicated
    .withColumn("order_year", F.year("order_ts"))
    .withColumn("order_month", F.month("order_ts"))
    .withColumn("order_day", F.dayofmonth("order_ts"))
)

(
    curated.write
    .mode("append")
    .format("parquet")
    .partitionBy("order_year", "order_month", "order_day")
    .save(args["TARGET_PATH"])
)

(
    rejected.write
    .mode("append")
    .format("parquet")
    .save(args["QUARANTINE_PATH"])
)

job.commit()
