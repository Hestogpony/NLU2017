import tensorflow as tf
import numpy as np
import time


import lstm
from config import cfg


def train_model(data, embeddings=None):

    print("defining the model...")
    # This is one mini-batch
    inp = tf.placeholder(dtype=tf.float32, shape=[None,cfg["sentence_length"], cfg["vocab_size"]])

    # from 3D tensor to 2D tensor, dim batch_Size x vocab_size
    # returns a list of 2D tensors
    batch_positionwise = tf.split(value=inp, num_or_size_splits = cfg["sentence_length"], axis=1)

    # We can discard the last 2D tensor from batch_positionwise
    # Cut the <eos> tags for the input data
    #x = tf.slice(input_=one_input_position_batch, begin=[0,0], size=[-1, cfg["sentence_length"] - 1])

    initializer = tf.contrib.layers.xavier_initializer()
    dtype = tf.float32


    W_emb = []
    bias_emb = []
    fc_emb_layer = []

    lstm_layer = []
    lstm_out = []

    W_out = []
    bias_out = []
    out_layer = []

    y_hat = []
    cost = []

    for i in range(cfg["sentence_length"] - 1):
        scope = tf.variable_scope('lstm' + str(i))
        lstm_layer.append(lstm.LstmCell(scope))

    for i in range(cfg["sentence_length"] - 1):

        #3. Fully connected of 100
        W_emb.append(tf.get_variable(name=str(i)+'W_emb', dtype=dtype, shape=[cfg["vocab_size"], cfg["embeddings_size"]], initializer=initializer))
        bias_emb.append(tf.get_variable(name=str(i)+'bias_emb', dtype=dtype, shape=[cfg["embeddings_size"]], initializer=initializer))


        fc_emb_layer.append(tf.nn.relu(tf.matmul(tf.squeeze(batch_positionwise[i]), W_emb[i]) + bias_emb[i]))

        #4. LSTM dim 512
        if i == 0:
            # (batch_size x lstm_size, batch_size x lstm_size)
            lstm_out.append(lstm_layer[i](X=fc_emb_layer[i],
                state=(tf.zeros(shape=[cfg["batch_size"], cfg["lstm_size"]]),
                    tf.zeros(shape=[cfg["batch_size"], cfg["lstm_size"]]))
                )
            )
        else:
            lstm_out.append(lstm_layer[i](X=fc_emb_layer[i], state=lstm_out[i-1]))

        #5. Linear FC output layer

        #Output layer
        W_out.append( tf.get_variable(name=str(i)+'W_out', dtype=dtype, shape=[cfg["lstm_size"], cfg["vocab_size"]], initializer=initializer) )
        bias_out.append( tf.get_variable(name=str(i)+'bias_out', dtype=dtype, shape=[cfg["vocab_size"]], initializer=initializer) )
        out_layer.append( tf.matmul(lstm_out[i][0], W_out[i]) + bias_out[i] )

        #6. Softmax output + cat cross entropy loss

        # we ommit the 0-th word in each sentence (namely the <bos> tag).
        # The labels start position 1
        y_hat.append( 
            tf.nn.sparse_softmax_cross_entropy_with_logits(
                labels=tf.argmax(tf.squeeze(batch_positionwise[i+1]), axis=1),
                logits=out_layer[i]) )

        cost.append(tf.reduce_mean(y_hat[i]))


    concatenated_costs = tf.stack(values=cost)
    optimizer = tf.train.AdamOptimizer()

    #Clipped gradients
    gvs = optimizer.compute_gradients(concatenated_costs)
    list_clipped, _ = tf.clip_by_global_norm(t_list=[x[0] for x in gvs], clip_norm=10) # second output not used
    train_op = optimizer.apply_gradients(zip(list_clipped, [x[1] for x in gvs]))

    # Unrestricted gradients
    # train_op = optimizer.minimize(concatenated_costs)

    sess = tf.InteractiveSession()
    tf.global_variables_initializer().run()

    for e in range(cfg["max_iterations"]):
        batch_indices = define_minibatches(data.shape[0])
        for i, batch_idx in enumerate(batch_indices):
            start = time.time()
            batch = data[batch_idx]

            print(("Starting batch %d" % i))

            sess.run(fetches=train_op, feed_dict={inp:batch})

            print(('Batch %d completed in %d seconds' % (i, time.time() - start)))
            # print('\tCosts: ' + str(costs))

            # file_writer = tf.summary.FileWriter('./train_graph', sess.graph)
            # file_writer.add_summary(summary)

def define_minibatches(length):
    # create a random permutation
    indices = np.random.permutation(length)
    
    # Cut out the last sentences in case data set is not divisible by the batch size
    rest = length % cfg["batch_size"]
    if rest is not 0:
        indices = indices[:-rest]

    batches = np.split(indices, indices_or_sections = length/cfg["batch_size"])
    return batches



 # def test_model(data, params):
 #    # Forward Prop:
 #    # Same network, with trained parameters
 #    # - Softmax outputs --> Passed to complexity functions
 #    pass



