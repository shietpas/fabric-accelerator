CREATE FUNCTION ELT.[uf_GetAestDateTime]()
RETURNS DATETIME
WITH EXECUTE AS CALLER
AS
 BEGIN
    RETURN CONVERT(datetime,CONVERT(datetimeoffset, getdate()) AT TIME ZONE 'AUS Eastern Standard Time')
END

GO

