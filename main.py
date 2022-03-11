import datetime
import uuid
from fastapi import FastAPI, UploadFile, File, Form
from face_Algorithms import getFaceData, kBestMatch
from FileIO import getUploadBuffer, extractZip, clearFile, clearDirectory, addImagesFromFolder
from database import postgres
from face_cache import face_cache

# Set up the fast api server
app = FastAPI()

# abstract the database class
DB = postgres()

# abstract the face cache class
cache = face_cache(DB)

# establish the database connection
@app.on_event("startup")
async def startup():
    await DB.connect()


# shutdown the database connection
@app.on_event("shutdown")
async def shutdown():
    await DB.disconnect()



# Request to search for faces with various inputted parameters for strictness in match.
@app.post("/search_faces")
async def search_faces(strictness: int = Form(... , description="Strictness of face recognition, (0-100) , 0 = low , 100 = high") ,
                       k : int = Form(... , description="Number of Best matches needed"),
                       file : UploadFile = File(... , description="An image file, possible containing multiple human faces.")):

    # get the upload file stream and save it into uploads directory
    await getUploadBuffer(file)

    # Obtain the face encodings of the image.
    [totalFaces , facesData] = await getFaceData(f'uploads/{file.filename}')

    # Obtain the k best matches for the given strictness of matching the data.
    matches = kBestMatch(k , strictness , facesData , cache)
    
    if not matches or totalFaces == 0:
        return {"status":"ERROR" , "body":"No face detected in the Image"}
    else :
        return {"status":"OK" , "body":{"matches":matches}}




# Request to add a particular face to database
@app.post("/add_face")
async def add_face(Firstname: str = Form(...),
                   Lastname: str = Form(...)  ,
                   location: str =  Form(None  , description="Location where the image was taken (optional)") ,
                   Date : datetime.date = Form(None , description="yyyy-mm-dd (optional)"),
                   file : UploadFile = File(... , description="An image of single human face")):
    
    # get the upload file stream and save it into uploads directory
    await getUploadBuffer(file)
    # obtain the facial encodings of the image
    [totalFaces, faceData] = await getFaceData(f'uploads/{file.filename}')
    
    if totalFaces == 0:
        return {"status": "ERROR", "body": "No face detected in the Image"}
    elif totalFaces > 1:
        return {"status": "ERROR", "body": "Too many faces detected in the Image"}
    
    # Insert the data into the database and Update local face data cache
    name = Firstname+'_'+Lastname
    [id_response , version] = await DB.insertFace(name , faceData , location , Date , cache.cache_Names)
    await cache.updateCache(id_response , DB)

    # delete the image buffer after the use to free up memory
    clearFile(f'uploads/{file.filename}')

    return {
        "status":"OK" ,
        "body":f"Face details successfully added to database",
        "name":name,
        "id":id_response,
        "version":version,
        "location":location ,
        "date":Date
    }




# upload a Zip file containing folders of actors containing their images respectively.
# This function takes the zip file and then adds them into database.
@app.post("/add_faces_in_bulk")
async def add_faces_in_bulk(file : UploadFile = File(... , description="A ZIP file containing multiple face images. Keep directory names as the Actors Name and put the images of this actor inside this folder directory")):

    # get the upload file stream and save it into uploads directory
    await getUploadBuffer(file)
    # set a unique file path for the uploads and extract the zip on that directory.
    uploadID = uuid.uuid4()
    await extractZip(file, uploadID)
    
    # Add all the images in the directory onto the database and update cache respectively.
    response = await addImagesFromFolder(f'./uploads/{uploadID}' , cache.cache_Names , cache.updateCache , DB)

    # clear the zip file and extracted contents to free up memory.
    clearFile(f'uploads/{file.filename}')
    clearDirectory(f'./uploads/{uploadID}')

    return {"status":'OK' , "body":response}




# request to obtain a certain face detail of the user by their unique ID
@app.post("/get_face_info")
async def get_face_info(face_id: int = Form(...) ):
    data = await DB.getFace_fromId(face_id)
    if data :
        return {"status": "OK", "body":'Face ID found' , "faceDetails":data}
    else :
        return {"status": "ERROR", "body": "No face in Database with given ID"}


# function to get all face datas and version of a given face name
@app.post("/get_faces_by_name")
async def get_faces_by_name(name: str = Form(...)):
    data = await DB.getFace_fromName(name)
    return data

# function to delete all new faces added to DB. (used for testing)
@app.get("/delete_new_faces")
async def delete_new_faces():
    await DB.delete_new_faces()
    cache.__init__(DB)
    return {"status":'OK' , "body":'New faces successfully deleted'}


