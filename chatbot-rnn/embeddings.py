from gensim.models.word2vec import Word2Vec
import gensim
import numpy as np
import argparse
import os
import time

def get_input_file_list(data_dir):
    suffixes = ['.txt', '.bz2']
    input_file_list = []
    if os.path.isdir(data_dir):
        for walk_root, walk_dir, walk_files in os.walk(data_dir):
            for file_name in walk_files:
                if file_name.startswith("."): continue
                file_path = os.path.join(walk_root, file_name)
                if file_path.endswith(suffixes[0]) or file_path.endswith(suffixes[1]):
                    input_file_list.append(file_path)
    else:
        raise ValueError("Not a directory: {}".format(data_dir))
    
    return sorted(input_file_list)

def train(args):
    sentences = []
    files = get_input_file_list(args.data_dir)
    for file in files:
        sentences += gensim.models.word2vec.LineSentence(file)

    start = time.time()
    model = Word2Vec(sentences=sentences, size=args.size, window=5, min_count=args.min_count, workers=args.workers)
    print('Word embeddings created in %f s and saved to \'%s\'' % (time.time() - start, args.save_path))
    #print(model['jhsdgfkshfgsd'])
    if not os.path.isdir(args.save_path):
        os.mkdir(args.save_path)
    model.save(args.save_path+'/'+args.save_path)
    

def main():
    """
    This is simplistic. Technically, the embeddings should only be trained on answers, not the questions.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str,
                        help='Preprocessed text documents that the word embeddings are trained on')
    parser.add_argument('--save_path', type=str,
                        help='Where the embeddings should be stored')
    parser.add_argument('--size', type=int, default=100,
                        help='Embeddings size')
    parser.add_argument('--min_count', type=int, default=2,
                        help='Words have to occur this many times to become part of the vocab') # adapt this to the vocab of the baseline
    parser.add_argument('--workers', type=int, default=4,
                        help='Number of threads to use')
    args = parser.parse_args()
    train(args)

if __name__ == '__main__':
    main()