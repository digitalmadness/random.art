from bot import config
from neuralnet import classify,face_detect
import cv2
import tempfile
import os
import tensorflow as tf
import uuid
import argparse
from sys import exit
from random import choice
from pyfiglet import Figlet
from glob import glob


def neuralnetwork(filename):
    results = []
    label_lines = [line.strip() for line in tf.gfile.GFile(str(os.path.dirname(os.path.abspath(__file__)))+'/neuralnet/face_labels.txt')]
    graph = tf.Graph()
    graph_def = tf.GraphDef()
    with tf.gfile.FastGFile(str(os.path.dirname(os.path.abspath(__file__)))+'/neuralnet/face_graph.pb', 'rb') as f:
        graph_def.ParseFromString(f.read())
    with graph.as_default():
        tf.import_graph_def(graph_def, name='')
    print('\nMoeFlow model initialized')

    with tempfile.NamedTemporaryFile(mode='wb', suffix='.jpg') as input_jpg:
        faces_detected = True
        # Run face detection with animeface-2009
        detected_faces = face_detect.run_face_detection(filename)
        # This operation will rewrite detected faces to 96 x 96 px
        resize_faces(detected_faces)
        # Classify with TensorFlow
        if not detected_faces:  # Use overall image as default
            faces_detected = False
            print('\nfaces not detected..\n')
            detected_faces = [filename]
        for face in detected_faces:
            predictions = classify.classify_resized_face(face, label_lines, graph)
            face_name = uuid.uuid4().hex + '.jpg'
            results.append(predictions[0])
            if __name__ == '__main__':
                print('\nfound 2d girl!\n',predictions[0],'\n')
        
        return results,faces_detected


def resize_faces(image_files, width=96, height=96):
    for image_file in image_files:
        image = cv2.imread(image_file)
        resized_image = cv2.resize(
            image,
            (width, height),
            interpolation=cv2.INTER_AREA
        )
        cv2.imwrite(image_file, resized_image)


if __name__ == '__main__':
    print(Figlet(font='slant').renderText('''moeflow''')) #welcome message
    if config.source_folder == '/replace/with/path_to_pics_folder/':
        exit('you forgot to replace default pictures folder in settings.txt!')
    waifu = choice(glob(config.source_folder + '*'))
    print('recognizing characters in',waifu)
    neuralnetwork(waifu)
