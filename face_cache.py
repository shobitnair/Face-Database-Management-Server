import numpy as np

# class that handles the local cache of the database
class face_cache:

    def __init__(self , DB):
        cache = DB.connection.execute("select * from faces").fetchall()
        self.cache_face = [np.array(row[2]) for row in cache]
        self.cache_meta = [{
            'id': row[0],
            'name': row[1],
            'version': row[3],
            'location': row[4],
            'date': row[5]
        } for row in cache]
        self.cache_Names = set(i['name'] for i in self.cache_meta)

    # utility function to update cache
    async def updateCache(self , id: int , DB):
        row = DB.connection.execute(f'select * from faces where id = {id}').fetchone()
        self.cache_face.append(row[2])
        self.cache_meta.append({
            'id': row[0],
            'name': row[1],
            'version': row[3],
            'location': row[4],
            'date': row[5]
        })
        self.cache_Names.add(row[1])
