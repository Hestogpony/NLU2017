import numpy as np
import math

class Measure(object):
    """docstring for Measure"""
    def __init__(self, cfg, embbeding_path_from_chatbot_args_parameter):
        self.cfg = cfg
        self.model = self.load_model(embbeding_path_from_chatbot_args_parameter)
        self.emb_size = 100

    def load_model(self,fpath):

        embeddings_file = fpath
        return Word2Vec.load(embeddings_file)

    def perplexity(self, cfg, predicted_softmax_vecs, input_sentence, word_dictionary):
        """
        predicted_softmax_vecs      sentence length x 1 x vocab_size
        input_sentence              dim: vector of words in sentence
        word_dictionary             dictionary incl. pad, unk, bos and eos.  id -> word
        """

        i = 0                       # Word index in current sentence
        perp_sum = 0

        while i < len(input_sentence) and input_sentence[i] != self.cfg['PAD_ID'] and i < self.cfg['TEST_MAX_LENGTH']: # only 29 output nodes

            # These pred
            word_probability = predicted_softmax_vecs[i][0][input_sentence[i]]
            perp_sum += math.log(word_probability, 2)
            i += 1

        # As specified in task description: ./docs/task_description
        # perp = 2^{(-1/n)*\sum^{n}_{t}(log_2(p(w_t | w_1, ... , w_t-1))} -
        perp = math.pow(2, (-1/i) * perp_sum)
        return perp

    def vector_extrema_dist(self, reference, output):
            """
            reference       string
            output          string
            """
            def normalize(v):
                norm=np.linalg.norm(v)
                if norm==0: 
                    return v
                return v/norm

            def extrema(sentence):
                sentence = sentence.split(" ")
                vector_extrema = np.zeros(shape=(emb_size))
                for i, word in enumerate(sentence):
                    if word in self.model.wv.vocab:
                        n = self.model[word]
                        abs_n = np.abs(n)
                        #print("abs")
                        abs_v = np.abs(vector_extrema)
                        for e in range(emb_size):
                            if abs_n[e] > abs_v[e]:
                                vector_extrema[e] = n[e]

                return vector_extrema

            ref_ext = extrema(reference)
            out_ext = extrema(output)

            return scipy.spatial.distance.cosine(normalize(ref_ext), normalize(out_ext))