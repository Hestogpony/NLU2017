import os
os.environ['TF_CPP_MIN_LOG_LEVEL']='2'
import tensorflow as tf
import numpy as np
import sys
import time

def seq2seq_f(self, encoder_inputs, decoder_inputs):
        return tf.contrib.legacy_seq2seq.embedding_rnn_seq2seq(
            encoder_inputs = encoder_inputs,
            decoder_inputs = decoder_inputs,
            cell = tf.contrib.rnn.BasicLSTMCell(self.cfg["lstm_size"]),
            num_encoder_symbols = self.cfg["vocab_size"],
            num_decoder_symbols = self.cfg["vocab_size"],
            embedding_size = self.cfg["embeddings_size"],
            output_projection=None,
            feed_previous=False,
            dtype=tf.float32,
            scope=None
        )


class Model(object):
    def __init__(self, cfg):
        self.cfg = cfg
        self.tfconfig = tf.ConfigProto()
        self.model_dtype = tf.float32

        self.model_session = tf.Session(config=self.tfconfig)

    def build_forward_prop(self):

        print("building the forward model...")


        # initializer = tf.contrib.layers.xavier_initializer()

        # We suppose that all samples in one batch fall into the same bucket, i.e. have the same length with padding
        self.input_forward = tf.placeholder(dtype=tf.int32, shape=[None, None])
        self.decoder_inputs = tf.placeholder(dtype=tf.int32, shape=[None, None])
        targets = tf.slice(self.decoder_inputs, [0,1], [-1,-1])
        # self.bucket_size = tf.placeholder(dtype=tf.int32, shape=())

        # Weights to avoid including the loss of pad labels when training
        self.target_weights = tf.placeholder(dtype=self.model_dtype, shape=[None, None])
        target_weights_sliced = tf.slice(self.target_weights, [0,1], [-1,-1])

        # Transpose everything, as model with buckets requires the batch size to be the last dimension
        input_forward_t = tf.unstack(tf.transpose(self.input_forward), num=50)
        decoder_inputs_t = tf.unstack(tf.transpose(self.decoder_inputs), num=50)
        target_weights_t = tf.unstack(tf.transpose(target_weights_sliced), num=50)
        targets_t = tf.unstack(tf.transpose(targets), num=50)


        # TODO: Maybe apply splitting word-wise

        # W_embeddings = tf.get_variable(name='W_emb', dtype=self.model_dtype, shape=[self.cfg["vocab_size"], self.cfg["embeddings_size"]],
                                    # initializer=initializer)
        # embeddings = tf.nn.embedding_lookup(params=W_embeddings, ids=self.input_forward)

        # state not used now
        self.outputs, self.total_loss = tf.contrib.legacy_seq2seq.model_with_buckets(
            encoder_inputs = input_forward_t,
            decoder_inputs = decoder_inputs_t,
            targets = targets_t,
            weights = target_weights_t,
            buckets = zip(self.cfg["buckets"], self.cfg["buckets"]),
            seq2seq = lambda x,y: seq2seq_f(self, x ,y),
            softmax_loss_function = lambda x,y: tf.nn.sparse_softmax_cross_entropy_with_logits(labels=x, logits=y)
        )

    def build_backprop(self):
        print("building the backprop model...")

        # params = tf.trainable_variables()

        # self.gradient_norms = []
        # self.updates = []
        # opt = tf.train.AdamOptimizer()
        # for b in xrange(len(self.cfg["buckets"])):
        #     gradients = tf.gradients(self.total_loss[b], params)
        #     clipped_gradients, norm = tf.clip_by_global_norm(gradients, 10)
        #     self.updates.append(opt.apply_gradients(
        #         zip(clipped_gradients, params)))
        
        self.train_ops = []
        optimizer = tf.train.AdamOptimizer()
        for t in self.total_loss:
            self.train_ops.append(optimizer.minimize(t))
        # # Clipped gradients
        # gvs = optimizer.compute_gradients(self.total_loss)
        # grads = [x[0] for x in gvs]
        # vars = [x[1] for x in gvs]

        # clipped_grads, _ = tf.clip_by_global_norm(t_list=grads, clip_norm=10)  # second output not used
        # self.train_op = optimizer.apply_gradients(list(zip(clipped_grads, vars)))

    def validation_loss(self, data):
        return ""

    def train(self, train_data, train_buckets_with_ids):
        # train_data        tuple of whatever the data structure is
        # 
        # Initialize variables
        if "load_model_path" in self.cfg:
            self.load_model(self.model_session, self.cfg["load_model_path"])
        else:
            tf.global_variables_initializer().run(session=self.model_session)

        td0 = np.array(train_data[0])
        td1 = np.array(train_data[1])

        for e in range(self.cfg["max_iterations"]):
            print("Starting epoch %d..." % e)
            start_epoch = start_batches = time.time()

            batch_indices = self.define_minibatches(train_buckets_with_ids)
            for i, (bid, batch_idx) in enumerate(batch_indices):

                enc_batch = td0[batch_idx]
                dec_batch = td1[batch_idx]

                # create target weights on the fly, list of
                train_target_weights = np.ones(shape=(len(batch_idx), self.cfg["buckets"][bid]), dtype=np.float32)
                
                print(np.array(enc_batch))
                print(np.array(dec_batch))
                print(train_target_weights)

                food = {
                    self.input_forward: np.array(enc_batch),
                    self.decoder_inputs: np.array(dec_batch),
                    self.target_weights: train_target_weights,
                    # self.bucket_size: b_size
                }
                print(self.train_ops[bid])

                print('Running into bucket %d' % bid)
                self.model_session.run(fetches=self.train_ops[bid], feed_dict=food)

                # Log test loss every so often
                #if self.cfg["out_batch"] > 0 and i > 0 and (i % (self.cfg["out_batch"]) == 0) :
                #    print("\tBatch chunk %d - %d finished in %d seconds" % (i-self.cfg["out_batch"], i, time.time() - start_batches))
                #    print("\tTest loss (mean per sentence) at batch %d: %f" % (i, float(self.validation_loss(test_data))))
                #    start_batches = time.time()

            print("Epoch completed in %d seconds." % (time.time() - start_epoch))

        if "save_model_path" in self.cfg:
            self.save_model(path=self.cfg["save_model_path"])

    def test(self, data):
        pass

    def save_model(self, path):
        saver = tf.train.Saver()
        save_path = saver.save(self.model_session, path)
        print("Model saved in file: %s" % save_path)
        config.save_cfg(path)


    def load_model(self, path):
        saver = tf.train.Saver()
        saver.restore(self.model_session, path)
        print("Model from %s restored" % path)


    def define_minibatches(self, buckets_with_ids, permute=False):
        """
        buckets_with_ids     list of list of samples that are in each bucket, sorted by bucket_id
        return:             list of lists of ndarrays
        """
        batches = []
        for i, b in enumerate(buckets_with_ids):            
            if permute:
                # create a random permutation (for training over multiple epochs)
                # this np command creates a copy
                indices = np.random.permutation(buckets_with_ids[i])
            else:
                # use the indices in a sequential manner (for testing)
                indices = buckets_with_ids[i]

            # Hold out the last sentences in case data set is not divisible by the batch size
            rest = len(b) % self.cfg["batch_size"]
            if rest is not 0:
                indices_even = np.array(indices[:-rest])
                indices_rest = np.array(indices[len(indices_even):])

                batch_list = np.split(indices_even, indices_or_sections=len(indices_even) / self.cfg["batch_size"])
                batch_list.append(np.array(indices_rest))
            else:
                batch_list = np.split(indices, indices_or_sections=len(indices) / self.cfg["batch_size"])

            #append the bucket size
            batch_tuples = [(i, x) for x in batch_list]
            batches.extend(batch_tuples)

        if permute:
            batches = np.random.permutation(batches)

        # print(batches)
        return batches