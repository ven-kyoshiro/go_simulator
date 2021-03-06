# -*- coding:utf-8 -*-
#  mnist_cnn_bn.py   date. 5/21/2016
#                    date. 6/2/2017 check TF 1.1 compatibility
# copy from 
# https://gist.github.com/tomokishii/0ce3bdac1588b5cca9fa5fbdf6e1c412 from __future__ import absolute_import
from __future__ import division 
from __future__ import print_function

import os
import copy
import random
import numpy as np
import tensorflow as tf

from tensorflow.examples.tutorials.mnist import input_data
from my_nn_lib import Convolution2D, MaxPooling2D
from my_nn_lib import FullConnected, ReadOutLayer

mnist = input_data.read_data_sets("MNIST_data/", one_hot=True)
chkpt_file = 'MNIST_data/mnist_cnn.ckpt'
IS_DEBUG = False
class Nn:
    def __init__(self, restore_call = False):
        self.restore_call = restore_call

        # Variables
        self.x = tf.placeholder(tf.float32, [None,None, 784])
        self.y_ = tf.placeholder(tf.float32, [None, 10])
        self.phase_train = tf.placeholder(tf.bool, name='phase_train')
        
        self.inference(self.x, self.y_)

        # Train
        lr = 0.01
        train_step = tf.train.AdagradOptimizer(lr).minimize(self.loss)
        vars_to_train = tf.trainable_variables()    # option-1
        vars_for_bn1 = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, # TF >1.0
                                         scope='conv_1/bn')
        vars_for_bn1 = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, # TF >1.0
                                         scope='res_block/bn')
        vars_for_bn2 = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, # TF >1.0
                                         scope='conv_2/bn')
        vars_to_train = list(set(vars_to_train).union(set(vars_for_bn1)))
        vars_to_train = list(set(vars_to_train).union(set(vars_for_bn2)))
        self.saver = tf.train.Saver(vars_to_train)     # option-1
        if self.restore_call:
            vars_all = tf.all_variables()
            vars_to_init = list(set(vars_all) - set(vars_to_train))
            self.init = tf.variables_initializer(vars_to_init)   # TF >1.0
        else:
            self.init = tf.global_variables_initializer()    # TF >1.0

    def batch_norm(self,x, n_out, phase_train):
        """
        Batch normalization on convolutional maps.
        Ref.: http://stackoverflow.com/questions/33949786/how-could-i-use-batch-normalization-in-tensorflow
        Args:
            x:           Tensor, 4D BHWD input maps
            n_out:       integer, depth of input maps
            phase_train: boolean tf.Varialbe, true indicates training phase
            scope:       string, variable scope
        Return:
            normed:      batch-normalized maps
        """
        with tf.variable_scope('bn'):
            beta = tf.Variable(tf.constant(0.0, shape=[n_out]),
                                         name='beta', trainable=True)
            gamma = tf.Variable(tf.constant(1.0, shape=[n_out]),
                                          name='gamma', trainable=True)
            batch_mean, batch_var = tf.nn.moments(x, [0,1,2], name='moments')
            ema = tf.train.ExponentialMovingAverage(decay=0.5)

            def mean_var_with_update():
                ema_apply_op = ema.apply([batch_mean, batch_var])
                with tf.control_dependencies([ema_apply_op]):
                    return tf.identity(batch_mean), tf.identity(batch_var)

            mean, var = tf.cond(self.phase_train,
                                mean_var_with_update,
                                lambda: (ema.average(batch_mean), ema.average(batch_var)))
            normed = tf.nn.batch_normalization(x, mean, var, beta, gamma, 1e-3)
        return normed
#
        

    def training(self,loss, learning_rate):
        optimizer = tf.train.AdamOptimizer(learning_rate)
        # Create a variable to track the global step.
        global_step = tf.Variable(0, name='global_step', trainable=False)
        train_op = optimizer.minimize(loss, global_step=global_step)
        
        return train_op


    def evaluation(self,y_pred, y):
        correct = tf.equal(tf.argmax(y_pred, 1), tf.argmax(y, 1))
        accuracy = tf.reduce_mean(tf.cast(correct, tf.float32))
        
        return accuracy


    def res_block(self,inputs):
        conv_res1 = Convolution2D(inputs, (28, 28), 64, 64, (3, 3), activation='none')
        conv_res1_bn = self.batch_norm(conv_res1.output(), 64, self.phase_train)
        conv_res1_out = tf.nn.relu(conv_res1_bn)
        conv_res2 = Convolution2D(conv_res1_out, (28, 28), 64, 64, (3, 3), activation='none')
        conv_res2_bn = self.batch_norm(conv_res2.output(), 64, self.phase_train)
        conv_res2_out = tf.nn.relu(conv_res2_bn+inputs)
        return conv_res2_out

# Create the model
    def inference(self,x, y_):
        x_image = tf.reshape(x, [-1, 28, 28, 5])
        
        with tf.variable_scope('conv_1'):
            conv1 = Convolution2D(x, (28, 28), 5, 64, (5, 5), activation='none')
            conv1_bn = self.batch_norm(conv1.output(), 64, self.phase_train)
            conv1_out = tf.nn.relu(conv1_bn)
#        pool1 = MaxPooling2D(conv1_out)
#        pool1_out = pool1.output()

        with tf.variable_scope('res_block'):
            # input
            res_block_out1 = self.res_block(conv1_out)
            res_block_out2 = self.res_block(res_block_out1)
            res_block_out3 = self.res_block(res_block_out2)
            res_block_out4 = self.res_block(res_block_out3)
            res_block_out5 = self.res_block(res_block_out4)
            res_block_out6 = self.res_block(res_block_out5)
            res_block_out7 = self.res_block(res_block_out6)
            res_block_out8 = self.res_block(res_block_out7)
            res_block_out9 = self.res_block(res_block_out8)

        with tf.variable_scope('conv_2'):
            conv2 = Convolution2D(res_block_out9, (28, 28), 64, 2, (1, 1), 
                                                              activation='none')
            conv2_bn = self.batch_norm(conv2.output(), 2, self.phase_train)
            conv2_out = tf.nn.relu(conv2_bn)
               
            # pool2 = MaxPooling2D(conv2_out)
            # pool2_out = pool2.output()    
            pool2_flat = tf.reshape(conv2_out, [-1, 28*28*2])
        
        # with tf.variable_scope('fc1'):
            # fc1 = FullConnected(pool2_flat, 28*28*2, 1024)
            # fc1_out = fc1.output()
            # fc1_dropped = tf.nn.dropout(fc1_out)
        
        self.y_pred = ReadOutLayer(pool2_flat, 28*28*2, 10).output()
        cross_entropy = tf.reduce_mean(-tf.reduce_sum(y_ * tf.log(self.y_pred+1e-7), 
                                        reduction_indices=[1]))
        self.loss = cross_entropy
        self.train_step = self.training(self.loss, 1.e-4)
        self.accuracy = self.evaluation(self.y_pred, y_)

def main():

   # インスタンス作る
    nn_kun = Nn(restore_call = True)

    # 学習データを用意
    # stack_mnistの訓練セットを作成 
    train_data = mnist.train.images
    train_labels = mnist.train.labels
    train_id = [[random.randrange(
              0, len(train_data)) for j in range(5)] for i in range(len(train_data))]
    # train_id は　[index が５個]の配列になってる
    train_data_stack = []
    train_labels_stack = []
    for ids in train_id:
        train_data_stack.append([train_data[i] for i in ids])
        labels_sub = copy.deepcopy(train_labels[ids[0]])
        if IS_DEBUG: print('[dbg] train_labels[ids[0]] = {0}'.format(train_labels[ids[0]]))
        # if IS_DEBUG: print('[dgb] labels_subの初期 = {0}'.format(labels_sub))
        for i in ids[1:]:
            labels_sub += train_labels[i]
            if IS_DEBUG: print('[dbg] train_labels[{0}] = {1}'.format(i,train_labels[i]))
        # if IS_DEBUG: print('[dgb] labels_subの足したあと = {0}'.format(labels_sub))
        labels_sub = labels_sub/5.0
        if IS_DEBUG: print('[dbg] ids = {0}, np.sum(labels_sub) = {1}'.format(ids,np.sum(labels_sub)))
        # if IS_DEBUG: print('[dgb] labels_subの５で割った = {0}'.format(labels_sub))
        train_labels_stack.append(labels_sub)

    # テスト用のセット作成 
    test_data = mnist.test.images
    test_labels = mnist.test.labels
    test_id = [[random.randrange(
          0, len(test_data)) for j in range(5)] for i in range(len(test_data))]
    test_data_stack = []
    test_labels_stack = []
    for ids in test_id:
        test_data_stack.append([test_data[i] for i in ids])
        labels_sub = copy.deepcopy(test_labels[ids[0]])
        # debug
        for i in ids[1:]:
            labels_sub += test_labels[i]
        labels_sub = labels_sub/5.0
        test_labels_stack.append(labels_sub)
   
    train_data_stack = np.array(train_data_stack)
    train_labels_stack = np.array(train_labels_stack)
    test_data_stack = np.array(test_data_stack)
    test_labels_stack = np.array(test_labels_stack)
    
    # そろそろNNを動かします
    with tf.Session() as sess: # if TASK == 'train':              # add in option-2 case
        sess.run(nn_kun.init)                     # option-1
        if nn_kun.restore_call:
            # Restore variables from disk.
            nn_kun.saver.restore(sess, chkpt_file) 

        # 学習
        print('\n Training...')
        for i in range(201):
            tr_ids = np.random.choice(range(len(train_labels_stack)),100)
            batch_xs = np.array([train_data_stack[j] for j in tr_ids])
            batch_ys = np.array([train_labels_stack[j] for j in tr_ids])
            # 100個選んで学習させる
            nn_kun.train_step.run({nn_kun.x: batch_xs, nn_kun.y_: batch_ys,
                nn_kun.phase_train: True})
            # 途中経過を見る
            if i % 100 == 0:
                cv_fd = {nn_kun.x: batch_xs, nn_kun.y_: batch_ys, 
                                               nn_kun.phase_train: False}
                train_loss = nn_kun.loss.eval(cv_fd)
                print('---test---')
                print('[dbg] batch_ys[0]*5 = {0}'.format(np.round([b*5 for b in batch_ys[0]],2)))
                print('[dbg] y_pred[0]*5   = {0}'.format(np.round([b*5 for b in nn_kun.y_pred.eval(cv_fd)[0]],2)))
                train_accuracy = nn_kun.accuracy.eval(cv_fd)
                
                print('  step, loss, accurary = %6d: %8.4f, %8.4f' % (i, 
                    train_loss, train_accuracy))
        save_path = nn_kun.saver.save(sess, chkpt_file)
        print("Model saved in file: %s" % save_path)


        # 評価
        # Test trained model
        # TODO: バッチサイズ＝１で評価できるかの確認
        test_fd = {nn_kun.x: np.array([test_data_stack[0],]), nn_kun.y_: np.array([test_labels_stack[0],]), 
                   nn_kun.phase_train: False}
        print(' accuracy = %8.4f' % nn_kun.accuracy.eval(test_fd))


if __name__ == '__main__':
    main()
