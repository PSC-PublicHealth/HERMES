
try:
    from sqlalchemy import Integer, String, Float, Boolean, LargeBinary, Text, ForeignKey
    import sqlalchemy
except:
    class EmptyClass:
        def __init__(self, *args, **kwargs):
            pass

    Integer = String = Float = Boolean = ForeignKey = EmptyClass



from csv_tools import castTypes

class DataType:
    attribList = ('cast', 'emptyCast', 'dbType', 'primaryKey', 'foreignKey')

    def __init__(self, base=None, **kwargs):
        if base is not None:
            for a in self.attribList:
                setattr(self, '_'+a, getattr(base, '_'+a))

        else:
            for a in self.attribList:
                setattr(self, '_'+a, None)

        for arg,val in kwargs.items():
            if arg in self.attribList:
                setattr(self, '_'+arg, val)

    def cast(self):
        c = self._cast
        if c is None:
            c = castTypes.STRING

        if self._emptyCast is None:
            return c
        return (self._emptyCast, c)

    def dbType(self):
        return self._dbType

    def dbArgs(self):
        ret = []
        ret.append(self._dbType)
        if self._foreignKey is not None:
            ret.append(ForeignKey(self._foreignKey))
        return ret

    def dbKwargs(self):
        ret = {}
        if self._primaryKey is not None:
            ret['primary_key'] = self._primaryKey

        return ret

    


                
STRING = DataType(cast = castTypes.STRING,
                  dbType = String(250))

STRING_NONE = DataType(STRING, emptyCast = castTypes.EMPTY_IS_NONE)
STRING_NULL = DataType(STRING, emptyCast = castTypes.EMPTY_IS_NULL_STRING)

NOTES_STRING = DataType(STRING_NULL, dbType=String(4096))

BOOLEAN = DataType(cast = castTypes.BOOLEAN, 
                   dbType = Boolean)


INTEGER = DataType(cast = castTypes.INT,
                   dbType = Integer)

INTEGER_NONE = DataType(INTEGER, emptyCast = castTypes.EMPTY_IS_NONE)
INTEGER_ZERO = DataType(INTEGER, emptyCast = castTypes.EMPTY_IS_ZERO)

INTEGER_PRIMARYKEY = DataType(INTEGER, primaryKey=True)

LONG = DataType(cast = castTypes.LONG,
                dbType = Integer)

FLOAT = DataType(cast = castTypes.FLOAT,
                 dbType = Float)

FLOAT_NONE = DataType(FLOAT, emptyCast = castTypes.EMPTY_IS_NONE)
FLOAT_ZERO = DataType(FLOAT, emptyCast = castTypes.EMPTY_IS_ZERO)

BLOB = DataType(dbType=LargeBinary)
CHAR = DataType(dbType=sqlalchemy.CHAR(length=1), cast = castTypes.STRING)

