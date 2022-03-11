import os
import shutil
import zipfile
from face_Algorithms import getFaceData
import filetype

# utility function to accept upload buffers , combine them and save it locally into a directory.
async def getUploadBuffer(file):
    with open(f'uploads/{file.filename}' , "wb") as buffer:
        shutil.copyfileobj(file.file , buffer)

# utility function to extract zip from a location to a destination location.
async def extractZip(file , uploadID):
    # we abstract the zip from the uploads directory and then extract after creating a unique folder from (uuid).
    with zipfile.ZipFile(f'uploads/{file.filename}', 'r') as zip_ref:
        zip_ref.extractall(f'./uploads/{uploadID}')


# IO function to delete a specific file
def clearFile(path):
    os.remove(path)


# IO function to delete a certain directory and all files inside it.
def clearDirectory(path):
    #recursively delete all file contents inside the folder
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        if os.path.isdir(file_path):
            shutil.rmtree(file_path)

    #delete the directory after clearing all the files inside it..
    shutil.rmtree(path)



# utility function to add image to DB from a file directory.
async def addImagesFromFolder(path , cache_Names , updateCache , DB):
    response = []
    for i in os.walk(path):
        name = i[0].split('\\')[-1]
        file = i[0]
        images = i[2]

        # recursively walk through the file directory.
        paths = []
        for img in images:
            path =  file + '/' + img

            # if file is an image , then add it to Database and Update local cache.
            if filetype.is_image(path):
                paths.append(path)


                # Obtain the face encodings in the image.
                [totalFaces , faceData] = await getFaceData(path)

                if totalFaces == 1:
                    # insert into database
                    [id_response,version] = await DB.insertFace(name , faceData , None , None  , cache_Names )

                    # update the local cache.
                    await updateCache(id_response , DB)

                    # add the status to the response
                    response.append({
                            "status": "OK",
                            "body": f"Face details detected and added.",
                            "name": name ,
                            "id": id_response,
                            "version": version,
                            "location":None,
                            "date":None
                        }
                    )

                # handle corner cases.
                elif totalFaces == 0:
                    response.append(f"{img} has no face")
                else :
                    response.append(f"{img} has many faces")

    return response
