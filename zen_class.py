#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division, unicode_literals
import os
base_dir = os.path.expanduser('~') #get home dir
import datetime
import numpy as np
from string import punctuation
import re,  collections,  random,  datetime
import psycopg2
import json
from gensim import corpora,  models,  similarities

# guarantee unicode string... #no need in python3 (will cause an error)
_u  =  lambda t: t.decode('UTF-8',  'replace') if isinstance(t,  str) else t

class Zen:
	"""Tall Labs Class"""
	def __init__(self):
		#setup
		self.stoplist  =  set('a an for of the and to in rt'.split())
		self.comment_modelB = models.Word2Vec.load(base_dir+'/emojify/models/comment_modelB')
		#self.dictionary = corpora.Dictionary.load(base_dir+'/TallLabs/models/lda_cell_dict_15')
		#LDA categories
		self.LDAcategories = {0:'Clips,  Mounts,  Holsters ', 1:'Cables,  Chargers,  Adapters', 2:'Batteries,  Battery Life', 3:'Product Description', \
		4:'USB,  Ports,  Power', 5:'Protective Covers', 6:'Prices,  Quality', 7:'Product Size', \
		8:'Car Accessories,  GPS', 9:'Screen Protector', 10:'Refunds', 11:'Bluetooth,  Headsets', 12:'WaterProof', \
		13:'Camera, Apps', 14:'Brands,  Models'}

	def clean_result(self, model_result):
		return [item[0] for item in model_result], [item[1] for item in model_result]

	def visual(self, word):
		modelB = self.comment_modelB
		word = word.lower()
		results, counts = self.clean_result(modelB.most_similar(word, topn = 5))
		source_target = []
		for result_word in results:
			#append source target,  and search next layer
			source_target.append((word, result_word, 1))
			results2, counts2 = self.clean_result(modelB.most_similar(result_word, topn = 5))
			for result_word2 in results2:
				source_target.append((result_word, result_word2, 2))
				results3, counts3 = self.clean_result(modelB.most_similar(result_word2, topn = 5))
				for result_word3 in results3:
					source_target.append((result_word2, result_word3, 3))
		return [{"source":src, "target":tar, "group":grp} for src, tar, grp in source_target]
		
	def tree(self, word):
		modelB = self.comment_modelB
		word = word.lower()
		results, counts = self.clean_result(modelB.most_similar(word))
		target = []
		child_list = []
		for result_word in results:
			target_child = []
			target.append(result_word)
			results2, counts2 = self.clean_result(modelB.most_similar(result_word))
			for result_word2 in results2:
				target_child.append(result_word2)
			child_list.append(target_child)
		return {"name":word, "children":[{"name":tar, "children":[{"name":child, "size":3} for child in child_l] }\
		 for tar, child_l in zip(target, child_list)]}
		 