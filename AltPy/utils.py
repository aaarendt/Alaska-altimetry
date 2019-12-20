def startEngine(connectionString):
   '''
   Instantiates a database connection from a list of credentials
   connectionString: dictionary of database credentials
   returns: SQLAlchemy database engine
   '''

   from sqlalchemy import create_engine
   from sqlalchemy.engine.url import URL as dburl

   cs = connectionString

   dbconfig = {
    "drivername": "postgresql",
    "username": cs['SQL_USERNAME'],
    "password": cs['SQL_PASSWORD'],
    "host":cs['SQL_HOSTNAME'],
    "port": cs['SQL_PORT'],
    "database": cs['SQL_DATABASE']
    }

   engine = create_engine(dburl(**dbconfig)) 

   return engine 
