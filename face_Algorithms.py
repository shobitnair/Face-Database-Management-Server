import face_recognition
import numpy as np

# function to get facial encodings of all the faces present in the image
async def getFaceData(path):
    face = face_recognition.load_image_file(path)
    faceData = face_recognition.face_encodings(face)
    return [len(faceData) , faceData]


# function to obtain the best k matches of a particular faceData against all the encodings.
def kBestMatch(k , strictness , facesData , cache):
    matches = []
    # 0 strictness => 0.7
    # 100 strictness => 0.43
    # face distance is ~ 0.5 for decently matching photos.
    threshold = 0.7 - 0.27 * (strictness / 100)
    person = 1
    for faceData in facesData:
        match = []
        res = face_recognition.face_distance(cache.cache_face, faceData)
        kBest = np.argsort(res)[:k]

        rank = 1
        for i in kBest:
            if res[i] <= threshold:
                match.append({f"{rank}": cache.cache_meta[i]})
            else:
                if rank > 1:
                    match.append(f"Only {rank - 1} best matches found for given strictness")
                break
            rank = rank + 1

        if match:
            matches.append({f"Face {person}": match})
        else:
            matches.append({f"Face {person}": "No match found"})
        person = person + 1

    return matches