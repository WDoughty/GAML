# -*- coding: utf-8 -*-
"""VDS.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1F7lOmOuj5SFZ0Kg5RhSVAaPtLGZ9wXa7
"""

import tensorflow as tf
from tensorflow import keras
from keras import layers
from keras.models import Sequential
from keras.layers import Convolution2D, MaxPooling2D, Dense, Dropout, Activation, Flatten, Conv2D
import random
import numpy as np
import matplotlib.pyplot as plt
import os

x_path = '/content/X_range_0eigenV_1000windows_air_soil.npy'
y_path = '/content/Y_classfication_0eigen_1000windows_air_soil.npy'

x = np.load(x_path)
y = np.load(y_path)

# Spltting the x and y data into different sets
from sklearn.model_selection import train_test_split
data_train, data_test, labels_train, labels_test = train_test_split(x,y,test_size=.20, random_state=23)

#Create a directory where the model and modeldata text file will be saved
if not os.path.exists("modelData"):
  os.mkdir("modelData")

BATCH_SIZE = [4,4,8,8]
#BATCH_SIZE = [4,8,16,32]
#monitor= tf.keras.callbacks.EarlyStopping(monitor='loss', mode='max', verbose=1, patience=2)
monitor= tf.keras.callbacks.EarlyStopping(monitor='val_loss', mode='max', verbose=1, patience=2)
checkpointer=tf.keras.callbacks.ModelCheckpoint(filepath="modelData/model.hdf5",verbose=1,save_best_only=True)
VAL_LOSS_DATA = list()
GACallbacks = [monitor, checkpointer]
num_classes = 2

class DNA:
  def __init__(self,filters,bt_size):
    self.filters = filters
    self.num_layers = len(self.filters)
    self.bt_size = bt_size
    
    
    self.layers_DNA = [*(self.encode(self.num_layers - 1,'02b'))]
    self.bt_DNA = [*(self.encode(self.bt_size,'02b'))]
    self.filters_DNA = list()
    for i in range(0, len(self.filters)):
      if self.filters[i] == 0:
        self.filters[i] = 1
      self.filters_DNA.append([*(self.encode(self.filters[i] - 1,'06b'))])

    
    self.model = self.build_model()
    self.history =  self.model.fit(
        data_train,
        labels_train,
        epochs = 100,
        batch_size = BATCH_SIZE[self.bt_size],
        callbacks= GACallbacks,
        validation_split = 0.1 )
    self.metrics = self.history.history['val_loss']
    #self.metrics = self.history.history['loss']
    self.metrics.sort()
    self.fitness = self.metrics[0]

  def build_model(self):
    self.m1 = tf.keras.Sequential()
    
    self.m1.add(layers.Conv2D(self.filters[0], (3,3), activation='relu'))
    self.m1.add(layers.MaxPooling2D(pool_size=(2,2),padding='same'))
    self.m1.add(layers.Dropout(rate=0.4)) 
    for i in range(1,self.num_layers):
      self.m1.add(layers.Conv2D(self.filters[i], (3,3), activation='relu'))
      self.m1.add(layers.MaxPooling2D(pool_size=(2,2), padding='same'))
      self.m1.add(layers.Dropout(rate=0.4)) 

    self.m1.add(layers.Flatten())
    #512 uses to much memory even with dropout
    #self.m1.add(layers.Dense(512,activation='relu'))
    self.m1.add(layers.Dense(64,activation='relu'))
    self.m1.add(layers.Dense(num_classes,activation = 'softmax'))                      
   
    self.m1.compile(loss='binary_crossentropy',optimizer='adam',metrics='accuracy')
    return self.m1

  def encode(self,n,bit):
    return format(n,bit)

  def decode(self,binary):
    return int(binary,2)
  
  def update_filters(self):
    self.filters.clear()
    for i in range(0,len(self.filters_DNA)):
      self.filters.append(self.decode(bin(int(''.join(map(str,self.filters_DNA[i])),2))) + 1)

  def update_filters_DNA(self):
    self.filters_DNA.clear()
    for i in range(0,self.num_layers):
      self.filters_DNA.append([*(self.encode(self.filters[i] - 1,'06b'))])
    

  def update_batch(self):
    self.bt_size = int(''.join(map(str,self.bt_DNA)))

  def update_layers(self):
    self.num_layers = int(''.join(map(str,self.layers_DNA)),2) + 1

  def update(self):
    self.update_layers
    self.update_batch
    self.update_filters
    self.update_filters_DNA

  def update_num_layers_filters(self):
    while self.num_layers > len(self.filters) and self.num_layers <=4 and self.num_layers >=1:
      self.filters.append(random.randint(1,64))
    self.update_filters_DNA()

    if self.num_layers < len(self.filters):
      self.num_layers = len(self.filters)
      self.update_layers()

class Population:
  def __init__(self,size):
    self.fittest =0
    self.DNA_Array = []
    self.population_size = size
    self.build_population(self.population_size)

  def build_population(self,size):
    for i in range(0,size):
      num_layers = random.randint(1,4)
      filters = list()
      bt_size = random.randint(0,3)
      for j in range(0,num_layers):
        filters.append(random.randint(1,64))
      self.DNA_Array.append(DNA(filters,bt_size))
  
  def get_fittest(self):
    max_fit = self.DNA_Array[0].fitness
    max_fit_i = 0
    for i in range(0, len(self.DNA_Array)):
      if max_fit >= self.DNA_Array[i].fitness:
        max_fit = self.DNA_Array[i].fitness
        max_fit_i = i
    self.fittest = self.DNA_Array[max_fit_i].fitness
    return self.DNA_Array[max_fit_i]

class GeneticAlgorithm:

  def __init__(self,size,num_generations):
    self.generation_count =0
    self.population = Population(size)
    self.fittest = self.population.get_fittest()
    self.write_to_file()
    VAL_LOSS_DATA.append(self.fittest.fitness)

    while self.generation_count<num_generations:
      new_pool = list()
      self.generation_count+=1
      new_pool.clear()
      new_pool.append(DNA(self.fittest.filters,self.fittest.bt_size))

      for i in range(0, self.population.population_size):
        partner_a = random.randint(0,self.population.population_size - 1)
        partner_b = random.randint(0,self.population.population_size - 1)  
        while partner_a == partner_b:
          partner_b = random.randint(0,self.population.population_size - 1)
        child = self.crossover(self.population.DNA_Array[partner_a], self.population.DNA_Array[partner_b])
        # mutate_rate = random.randint(0,100)
        # if mutate_rate < 5:
        #    child = self.mutate(child)
        new_pool.append(child)
      self.population.DNA_Array.clear()
      self.population.DNA_Array.extend(new_pool) 
      self.fittest = self.population.get_fittest()
      VAL_LOSS_DATA.append(self.fittest.fitness)
      self.write_to_file()

  def crossover(self,partner_a,partner_b):
    temp_a = DNA(partner_a.filters,partner_a.bt_size)
    temp_b = DNA(partner_b.filters,partner_b.bt_size)

    crossover_points_filter = list()


    s = temp_a.num_layers if temp_a.num_layers < temp_b.num_layers else temp_b.num_layers
    for i in range(0,s):
      p1 = random.randint(0,4)
      p2 = random.randint(p1,5)
      for j in range(p1, p2):
        temp_a.filters_DNA[i][j] = partner_b.filters_DNA[i][j]
        temp_b.filters_DNA[i][j] = partner_a.filters_DNA[i][j]
    temp_a.update_filters()
    temp_b.update_filters()


    layer_crossover = random.randint(0,1) # this needs to be changed to the number of bits in the layer
    t = temp_a.layers_DNA[layer_crossover]
    temp_a.layers_DNA[layer_crossover] = temp_b.layers_DNA[layer_crossover]
    temp_b.layers_DNA[layer_crossover] = t
    temp_a.update_layers()
    temp_b.update_layers()
    temp_a.update_num_layers_filters
    temp_b.update_num_layers_filters




    batch_crossover = random.randint(0,1)
    t = temp_a.bt_DNA[batch_crossover]
    temp_a.bt_DNA[batch_crossover] = temp_b.bt_DNA[batch_crossover]
    temp_b.bt_DNA[batch_crossover] = t


    temp_a.update()
    temp_b.update() 

    c1 = DNA(temp_a.filters,temp_a.bt_size)
    c2 = DNA(temp_b.filters,temp_b.bt_size)
    return c1 if c1.fitness < c2.fitness  else c2


  def write_to_file(self):
    f = open("modelData/data.txt","a")
    s = "Generation count: {gen}\n" .format(gen = self.generation_count)
    s = s + "Number of Layers: {layers}\n" .format(layers = self.fittest.num_layers)
    for j in range(0,self.fittest.num_layers):
      s = s + "Layer #: {layer} \t Number of filters: {filters} \n" .format(layer = j+1, filters = self.fittest.filters[j])
    s = s + "Fitness: {fitness}\n" .format(fitness = self.fittest.fitness)
    s = s + "Batch Size: {batch}\n" .format(batch = BATCH_SIZE[self.fittest.bt_size])

    f.write(str(s))
    f.write("--------------------------------------------------------\n")
    f.close()

# Population Size, Number of generations
go = GeneticAlgorithm(10,100)

plt.plot(VAL_LOSS_DATA)
plt.title("Genetic Algorithm Fitness")
plt.xlabel('Generation')
plt.ylabel("Validation Loss")
plt.show()