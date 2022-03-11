import sqlalchemy
import databases
import json

# Reading the config.json file
filePTR = open('config.json')
config = json.load(filePTR)
filePTR.close()


# connecting to postgreSQL database
class postgres:
    def __init__(self):
        self.URL = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
        self.metadata = sqlalchemy.MetaData()
        self.database = databases.Database(self.URL)
        self.engine = sqlalchemy.create_engine(self.URL)
        self.connection = self.engine.connect()

        # Tables
        self.faces = sqlalchemy.Table(
            "faces",
            self.metadata,
            sqlalchemy.Column("id" , sqlalchemy.Integer , primary_key=True , autoincrement=True) ,
            sqlalchemy.Column("name" , sqlalchemy.String(500)) ,
            sqlalchemy.Column("data" , sqlalchemy.ARRAY(sqlalchemy.Float)) ,
            sqlalchemy.Column("version", sqlalchemy.String(500)),
            sqlalchemy.Column("location" , sqlalchemy.String(500)) ,
            sqlalchemy.Column("date" , sqlalchemy.DateTime())
        )

        # Adds Schema into table if doest exist
        self.metadata.create_all(self.engine)




    # Function to connect to the server
    async def connect(self):
        await self.database.connect()

    # Function to disconnect from the server
    async def disconnect(self):
        await self.database.disconnect()

    # Function to get the latest version of a particular Face_name
    async def getVersion(self , name):
        return await self.database.execute('select max(version) as a from faces where name = :name', {"name": name})

    # Function to insert Face
    async def insertFace(self , name , faceData , location , Date , cache_Names):
        version = 1
        if name in cache_Names:
            version = await self.getVersion(name) + 1
        query = self.faces.insert().values(name=name, data=faceData[0], date=Date, location=location, version=version)
        return [await self.database.execute(query) , version]

    # Function to get a Face data by their ID.
    async def getFace_fromId(self , face_id):
        return await self.database.fetch_one(f'select * from faces where id={face_id}')

    # Function to get a Face data by their name.
    async def getFace_fromName(self , name):
        return await self.database.fetch_all(f"select * from faces where name = :name" , {"name":name})

    # Function to delete new faces ( keep on lfw dataset )
    async def delete_new_faces(self):
        return await self.database.execute('delete from faces where id > 12980')
