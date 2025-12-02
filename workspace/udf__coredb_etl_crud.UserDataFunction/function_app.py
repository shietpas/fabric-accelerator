import fabric.functions as fn

udf = fn.UserDataFunctions()

@udf.connection(argName="sqlDB", alias="controlDB")
@udf.function()
def write_ingestdef(
    sqlDB: fn.FabricSqlConnection,
    SourceSystemName: str,
    StreamName: str,
    SourceSystemDescription: str,
    Backend: str,
    DataFormat: str,
    EntityName: str,
    WatermarkColName: str,
    DeltaFormat: str,
    LastDeltaDate: str,
    LastDeltaNumber: int,
    LastDeltaString: str,
    MaxIntervalMinutes: int,
    MaxIntervalNumber: int,
    DataMapping: str,
    SourceFileDropFileSystem: str,
    SourceFileDropFolder: str,
    SourceFileDropFile: str,
    SourceFileDelimiter: str,
    SourceFileHeaderFlag: bool,
    SourceStructure: str,
    DestinationRawFileSystem: str,
    DestinationRawFolder: str,
    DestinationRawFile: str,
    RunSequence: int,
    MaxRetries: int,
    ActiveFlag: bool,
    L1TransformationReqdFlag: bool,
    L2TransformationReqdFlag: bool,
    DelayL1TransformationFlag: bool,
    DelayL2TransformationFlag: bool
) -> str:

    # Validate JSON fields
    if not fn.is_json(DataMapping):
        raise fn.UserThrownError("DataMapping must be valid JSON.", {"DataMapping": DataMapping})
    if not fn.is_json(SourceStructure):
        raise fn.UserThrownError("SourceStructure must be valid JSON.", {"SourceStructure": SourceStructure})

    connection = sqlDB.connect()
    cursor = connection.cursor()

    insert_query = """
    INSERT INTO [ELT].[IngestDefinition] (
        SourceSystemName, StreamName, SourceSystemDescription, Backend, DataFormat,
        EntityName, WatermarkColName, DeltaFormat, LastDeltaDate, LastDeltaNumber,
        LastDeltaString, MaxIntervalMinutes, MaxIntervalNumber, DataMapping,
        SourceFileDropFileSystem, SourceFileDropFolder, SourceFileDropFile,
        SourceFileDelimiter, SourceFileHeaderFlag, SourceStructure,
        DestinationRawFileSystem, DestinationRawFolder, DestinationRawFile,
        RunSequence, MaxRetries, ActiveFlag, L1TransformationReqdFlag,
        L2TransformationReqdFlag, DelayL1TransformationFlag, DelayL2TransformationFlag
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    cursor.execute(insert_query, SourceSystemName, StreamName, SourceSystemDescription, Backend, DataFormat,
                   EntityName, WatermarkColName, DeltaFormat, LastDeltaDate, LastDeltaNumber,
                   LastDeltaString, MaxIntervalMinutes, MaxIntervalNumber, DataMapping,
                   SourceFileDropFileSystem, SourceFileDropFolder, SourceFileDropFile,
                   SourceFileDelimiter, SourceFileHeaderFlag, SourceStructure,
                   DestinationRawFileSystem, DestinationRawFolder, DestinationRawFile,
                   RunSequence, MaxRetries, ActiveFlag, L1TransformationReqdFlag,
                   L2TransformationReqdFlag, DelayL1TransformationFlag, DelayL2TransformationFlag)

    connection.commit()
    cursor.close()
    connection.close()

    return "Ingest definition record was successfully added."
