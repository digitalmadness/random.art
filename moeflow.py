import cv2
import tempfile
import tensorflow as tf
import uuid
import argparse
from random import choice
from glob import glob
from classify import classify_resized_face
from face_detect import run_face_detection
from config import source_folder


def neuralnetwork(filename):
    label_lines = [line.strip() for line in tf.gfile.GFile("face_labels.txt")]
    graph = tf.Graph()
    graph_def = tf.GraphDef()
    with tf.gfile.FastGFile("face_graph.pb", 'rb') as f:
        graph_def.ParseFromString(f.read())
    with graph.as_default():
        tf.import_graph_def(graph_def, name='')
    print("MoeFlow model initialized")

    with tempfile.NamedTemporaryFile(mode="wb", suffix='.jpg') as input_jpg:
        results = []
        # Run face detection with animeface-2009
        detected_faces = run_face_detection(filename)
        # This operation will rewrite detected faces to 96 x 96 px
        resize_faces(detected_faces)
        # Classify with TensorFlow
        if not detected_faces:  # Use overall image as default
            detected_faces = [filename]
        for face in detected_faces:
            predictions = classify_resized_face(
                face,
                label_lines,
                graph
                )
            face_name = uuid.uuid4().hex + ".jpg"
            results.append({
                "image_name": face_name,
                "prediction": predictions
            })
            print(predictions)
            return(predictions)
        print(results)


def resize_faces(image_files, width=96, height=96):
    for image_file in image_files:
        image = cv2.imread(image_file)
        resized_image = cv2.resize(
            image,
            (width, height),
            interpolation=cv2.INTER_AREA
        )
        cv2.imwrite(image_file, resized_image)


if __name__ == "__main__":
    waifu = choice(glob(source_folder + "*"))
    print('recognizing characters in',waifu)
    neuralnetwork(waifu)
