# -*- coding: utf-8 -*-
"""
@author: Matt Dill, Bradley Erickson
@class: CS 447: Machine Learning
@date: Fall 2019
@title: Final Project: Car Classifier
"""

# imports
import csv
import cv2
import datetime
import json
import keras
import numpy as np
import random
import tensorflow as tf

## keras imports
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten, Lambda
from keras.layers import Conv2D, MaxPooling2D, Cropping2D
from keras.callbacks import ModelCheckpoint, TensorBoard
from keras.optimizers import SGD


# methods
## data processing
def get_list_from_csv(file):
    """ Import CSV to list form """
    
    with open(file, 'r') as f:
        reader = csv.reader(f)
        your_list = list(reader)
    return your_list
   

def get_car_pic_matrix(file_name, crop_points, size):
    """
        input the car file name and output the car matrix properly resized
        file_name = "00001.jpg"
        crop_points = [min_x, min_y, max_x, max_y]
        size = [pixels_x, pixels_y]
    """
    
    image = cv2.imread(file_name)
    image = image[crop_points[1]:crop_points[3], crop_points[0]:crop_points[2]]
    image = cv2.resize(image, (size[0], size[1]))
    return image


## model initialization
def initialize_model(input_shape, classes):
    """ initialize the model parameters and layers """
    
    model = Sequential()
     
    model.add(Conv2D(32, (5,5), activation="relu", strides=(2,2), input_shape=input_shape))
    model.add(MaxPooling2D(pool_size=(2,2), strides=(1,1), padding="same"))

    #model.add(Conv2D(32, (5,5), activation="relu", strides=(2,2)))
    #model.add(MaxPooling2D(pool_size=(2,2), strides=(1,1), padding="same"))
    
    model.add(Flatten())

    model.add(Dense(512, activation='relu'))
    model.add(Dropout(0.5))
    
    model.add(Dense(classes, activation="softmax"))
    
    sgd = SGD(lr=0.01, clipvalue=0.5)
    model.compile(loss=keras.losses.categorical_crossentropy, optimizer=sgd)
    model.summary()
    
    return model


## training process
### initialize callbacks and data for training
def training(data_dir, model, data, batch, epoch):
    """ train the model """
    
    # variables
    image_dir = data_dir + "/images/"
    resize = [200, 200]
    total_length = len(data)
    cutoff = int(total_length*0.9)
    
    # shuffle data
    random.seed(447)
    random.shuffle(data)
    
    # model callbacks
    callback_visualizations = TensorBoard(histogram_freq=0, batch_size=batch, write_images=True)
    callback_checkpoints = ModelCheckpoint('model_checkpoint.h5', save_best_only=True)
    
    plot_info = model.fit_generator(create_data_generator(image_dir, data, resize, 0, cutoff, batch),
                                    steps_per_epoch=int(cutoff/batch),
                                    validation_data=create_data_generator(image_dir, data, resize, cutoff, total_length, batch),
                                    validation_steps=(total_length-cutoff)/batch,
                                    epochs=epoch,
                                    callbacks=[callback_checkpoints,callback_visualizations]
                                    )
    
    return model


### create generators for training and validation
def create_data_generator(path, data, size, start, cutoff, batch):
    """ receives chunk of data list and turns it into a generator """
    
    while True:
        images = []
        labels = []
        for i in range(start, start + batch):
            image_data = data[i]
            image_path = path + image_data[5]
            crop_points = [int(i) for i in image_data[:4]]
            image = get_car_pic_matrix(image_path, crop_points, size)
            
            label = np.zeros(196)
            label[int(image_data[4]) - 1] = 1
            
            images.append(image)
            labels.append(label)
        
        images = np.array(images)
        labels = np.array(labels)
        
        yield(images,labels)
        
        start += batch
        if start + batch > cutoff:
            start = 0
        

## saving model
def save_model_to_json(model, name="model"):
    """ save the model to a json document """
    
    model.save_weights(name+'.h5')
    model_json  = model.to_json()
    title = get_model_title_string(name)
    with open(title, 'w') as f:
        json.dump(model_json, f)
        
        
def get_model_title_string(name):
    """ create the model json name """
    
    date_time = str(datetime.date.today())
    date_time = date_time.replace(' ', '_').replace(':', '-')
    title = date_time + "_" + name + ".json"
    return title

   
def run_model():
    """ run everything """
    
    DATA_DIR = "./data"
    LIST_DATA = get_list_from_csv(DATA_DIR + "/crop_size.csv")
    
    model1 = initialize_model((200,200,3), 196)
    
    model1 = training(DATA_DIR, model1, LIST_DATA, 32, 10)
    
    save_model_to_json(model1, name="car-classifier")
    

run_model()