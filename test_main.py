from asgi_lifespan import LifespanManager
from httpx import AsyncClient
from main import app
import pytest


base_url = "http://0.0.0.0"


# testing the searching of andrew and henry before inserting their images in Database
@pytest.mark.order(0)
@pytest.mark.asyncio
async def test_search_faces_before_insert():
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url=base_url) as client:
            response = await client.post(
                "/search_faces",
                data={
                    "strictness": 70,
                    "k": 4
                },
                files={"file": open("./test/henry_andrew_together.jpg", "rb")}
            )
            # No match is found since their datas dnt exist for a strictness level of 70 percent
            json = response.json()
            assert json["body"]["matches"][0]["Face 1"] == "No match found"
            assert json["body"]["matches"][1]["Face 2"] == "No match found"



# testing out a wrong face id info from the database.
@pytest.mark.order(1)
@pytest.mark.asyncio
async def test_get_face_info():
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url=base_url) as client:

            response = await client.post(
                "/get_face_info",
                data={
                    "face_id": 33334553
                }
            )
            # assert for response when wrong id is passed.
            json = response.json()
            assert json == {
              "status": "ERROR",
              "body": "No face in Database with given ID"
            }




@pytest.mark.order(2)
@pytest.mark.asyncio
async def test_add_faces_in_bulk():
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url=base_url) as client:
            # contains 8 images  ,
            # 3 of Andrew_Garfeild  ,
            # 3 of Henry_Cavill ,
            # 2 error images :-
                #   1 image with no face
                #   1 image with multiple face, ,


            response = await client.post(
                "/add_faces_in_bulk",
                files={"file": open("./test/test_add_images_in_bulk.zip", "rb")},
            )
            assert response.status_code == 200
            json = response.json()

            # checking if 8 images were evaluated
            assert len(json["body"]) == 8

            # assert there were 2 error images  , one with no face and one with many faces
            assert "actors5.jpeg has many faces" in json["body"]
            assert "no_face.jpeg has no face" in json["body"]

            # assert there are 3 images of andrew inserted into DataBase
            response = await client.post(
                "get_faces_by_name" ,
                data = {
                    "name":'Andrew_Garfeild'
                }
            )
            assert len(response.json()) == 3

            #assert there are 3 images of henry inserted in DataBase
            response = await client.post(
                "get_faces_by_name",
                data={
                    "name": 'Henry_Cavill'
                }
            )
            assert len(response.json()) == 3



# testing adding a face into database.
@pytest.mark.order(3)
@pytest.mark.asyncio
async def test_add_face():
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url=base_url) as client:
            # add a solo image of andrew garfeild
            response = await client.post(
                "/add_face",
                data={
                    "Firstname":'Andrew',
                    "Lastname":'Garfeild',
                    "location":'London',
                } ,
                files={"file": open("./test/andrew_solo.jpg", "rb")},
            )

            assert response.status_code == 200

            json = response.json()
            name  = json["name"]
            version = json["version"]

            # getting the face info using the above id to confirm insertion into DB
            response = await client.post(
                "/get_face_info" ,
                data = {"face_id":json["id"]}
            )

            json = response.json();
            assert json["faceDetails"]["name"] == name
            assert json["faceDetails"]["version"] == version


# trying out adding a wrong face (either no face or too many faces)
@pytest.mark.order(4)
@pytest.mark.asyncio
async def test_add_wrong_face():
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url=base_url) as client:

            # testing error throw if trying to add image with multiple faces for add one face function
            response = await client.post(
                "/add_face",
                data={
                    "Firstname": 'Many',
                    "Lastname": 'Faces',
                },
                files={"file": open("./test/many_face.jpeg", "rb")},
            )

            json = response.json()
            assert json == {
              "status": "ERROR",
              "body": "Too many faces detected in the Image"
            }

            # testing error throw if trying to add image with no face for add one face function
            response = await client.post(
                "/add_face",
                data={
                    "Firstname": 'No',
                    "Lastname": 'Faces',
                },
                files={"file": open("./test/no_face.jpeg", "rb")},
            )

            json = response.json()
            assert json == {
              "status": "ERROR",
              "body": "No face detected in the Image"
            }




# testing out the search faces after inserting henry and andrew into database.
# the database now has 4 images of andrew and 3 images of henry at the moment.
@pytest.mark.order(5)
@pytest.mark.asyncio
async def test_search_faces_after_insert():
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url=base_url) as client:

            # The database currently has 4 images of andrew and 3 images of henry.
            # lets find the best 4 matches for a 70percent strictness (pretty strong check)
            response = await client.post(
                "/search_faces",
                data = {
                    "strictness":70 ,
                    "k":4
                } ,
                files = {"file":open("./test/henry_andrew_together.jpg", "rb")}
            )

            # we obtain 4 expected andrew garfeild images and only 3 best matches for henry with an exception message.
            assert response.status_code == 200
            json = response.json()
            assert json["body"]["matches"][0]["Face 1"][0]["1"]["name"] == 'Andrew_Garfeild'
            assert json["body"]["matches"][0]["Face 1"][1]["2"]["name"] == 'Andrew_Garfeild'
            assert json["body"]["matches"][0]["Face 1"][2]["3"]["name"] == 'Andrew_Garfeild'
            assert json["body"]["matches"][0]["Face 1"][3]["4"]["name"] == 'Andrew_Garfeild'
            assert json["body"]["matches"][1]["Face 2"][0]["1"]["name"] == 'Henry_Cavill'
            assert json["body"]["matches"][1]["Face 2"][1]["2"]["name"] == 'Henry_Cavill'
            assert json["body"]["matches"][1]["Face 2"][2]["3"]["name"] == 'Henry_Cavill'
            assert json["body"]["matches"][1]["Face 2"][3] == "Only 3 best matches found for given strictness"

            # checking for images with no face in them.
            response = await client.post(
                "/search_faces",
                data={
                    "strictness": 70,
                    "k": 3
                },
                files={"file": open("./test/no_face.jpeg", "rb")}
            )

            assert response.status_code == 200
            json = response.json()
            assert json["status"] == "ERROR"
            assert json["body"] == "No face detected in the Image"




# delete all the new changes made during the current test.
@pytest.mark.order(6)
@pytest.mark.asyncio
async def test_delete_new_faces():
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url=base_url) as client:
            response = await client.get("/delete_new_faces")
            json = response.json()
            assert json == {
              "status": "OK",
              "body": "New faces successfully deleted"
            }
