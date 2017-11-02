import numpy as np
import tensorflow as tf

DATA_PATH = '../data/'


# https://www.oreilly.com/learning/perform-sentiment-analysis-with-lstms-using-tensorflow

word_list = np.load(DATA_PATH + 'wordsList.npy')
word_list = [word.decode('UTF-8') for word in word_list.tolist()]

word_vectors = np.load(DATA_PATH + 'wordVectors.npy')


# word_list is a list | --> word_vectors is a numpy array 
print ('dimension of word list is {}\ndimension of word vectors is {}'.format(len(word_list), word_vectors.shape))


baseball_idx = word_list.index('baseball')
print (word_vectors[baseball_idx])


batchSize = 24
lstmUnits = 64
numClasses = 2
iterations = 100000



