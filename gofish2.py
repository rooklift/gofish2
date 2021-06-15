#!/usr/bin/env python3

class ParserFail(Exception):
	pass

class ParseResult:
	def __init__(self, root, readcount):
		self.root = root
		self.readcount = readcount

# -------------------------------------------------------------------------------------------------

class Node:

	def __init__(self, parent = None):

		self.parent = parent
		self.children = []
		self.props = dict()
		self.__board = None

		if parent:
			parent.children.append(self)


	@property
	def width(self):

		if self.__board:
			return self.__board.width

		root = self.get_root()
		sz = root.get("SZ")

		if sz == None:
			return 19

		if ":" in sz:
			width_string = sz.split(":")[0]
		else:
			width_string = sz

		try:
			return int(width_string)
		except:
			return 19


	@property
	def height(self):

		if self.__board:
			return self.__board.height

		root = self.get_root()
		sz = root.get("SZ")

		if sz == None:
			return 19

		if ":" in sz:
			height_string = sz.split(":")[1]
		else:
			height_string = sz

		try:
			return int(height_string)
		except:
			return 19


	def get_root(self):

		node = self
		while True:
			if not node.parent:
				return node
			node = node.parent


	def set(self, key, value):

		key = str(key)
		value = str(value)
		self.mutor_check(key)

		self.props[key] = [value]


	def get(self, key):

		key = str(key)

		if key not in self.props:
			return None
		return self.props[key][0]


	def add_value(self, key, value):

		key = str(key)
		value = str(value)
		self.mutor_check(key)

		if key not in self.props:
			self.props[key] = []
		self.props[key].append(value)


	def add_value_fast(self, key, value):

		if key not in self.props:
			self.props[key] = []
		self.props[key].append(value)


	def delete_key(self, key):

		key = str(key)
		self.mutor_check(key)

		self.props.pop(key, None)


	def mutor_check(self, key):		# These are board-altering keys and so we must clear any board caches recursively

		if key in ["B", "W", "AB", "AW", "AE", "PL", "SZ"]:
			self.clear_board_recursive()


	def clear_board_recursive(self):

		node = self

		while True:

			node.__board = None

			if len(node.children) == 0:
				break
			elif len(node.children) == 1:
				node = node.children[0]
			else:
				for child in node.children:
					child.clear_board_recursive()
				break


	def dyer(self):

		root = self.get_root()
		node = root
		dyer = {20: "??", 40: "??", 60: "??", 31: "??", 51: "??", 71: "??"}
		move_count = 0;

		while True:

			s = None
			if "B" in node.props:
				s = node.props["B"][0]
			elif "W" in node.props:
				s = node.props["W"][0]

			if s != None:
				move_count += 1
				if move_count in [20, 40, 60, 31, 51, 71]:
					p = root.validated_move_string(s)
					if p:
						dyer[move_count] = p

			if (len(node.children) == 0 or move_count >= 71):
				break

			node = node.children[0]

		dyer_string = dyer[20] + dyer[40] + dyer[60] + dyer[31] + dyer[51] + dyer[71]
		return dyer_string


	def validated_move_string(self, s):

		# Returns s if s is an on-board SGF string, otherwise returns ""

		if len(s) != 2:
			return ""

		x_ascii = ord(s[0])
		y_ascii = ord(s[1])

		if x_ascii >= 97 and x_ascii <= 122:
			x = x_ascii - 97
		elif x_ascii >= 65 and x_ascii <= 90:
			x = x_ascii - 65 + 26
		else:
			return ""

		if y_ascii >= 97 and y_ascii <= 122:
			y = y_ascii - 97
		elif y_ascii >= 65 and y_ascii <= 90:
			y = y_ascii - 65 + 26
		else:
			return ""

		if x >= 0 and x < self.width and y >= 0 and y < self.height:
			return s
		else:
			return ""


	def subtree_size(self):			# Including self

		node = self
		n = 0

		while True:

			n += 1

			if len(node.children) == 0:
				return n
			elif len(node.children) == 1:
				node = node.children[0]
			else:
				for child in node.children:
					n += child.subtree_size()
				return n


	def tree_size(self):
		return self.get_root().subtree_size()

# -------------------------------------------------------------------------------------------------

def load(filename):

	# Returns an array of roots (except load_sgf() will throw if it cannot get at least 1 root).

	with open(filename, "rb") as infile:
		buf = infile.read()

	return load_sgf(buf)


def load_sgf(buf):

	# Always returns at least 1 game; or throws if it cannot.

	if type(buf) is str:
		buf = bytearray(buf.encode(encoding="utf-8", errors="replace"))

	ret = []
	off = 0

	while True:

		if len(buf) - off < 3:
			break

		try:
			o = load_sgf_recursive(buf, off, None)
			ret.append(o.root)
			off += o.readcount
		except:
			if len(ret) > 0:
				break
			else:
				raise ParserFail

	if len(ret) == 0:
		raise ParserFail

	return ret


def load_sgf_recursive(buf, off, parent_of_local_root):

	root = None
	node = None
	tree_started = False
	inside_value = False
	escape_flag = False

	value = bytearray()
	key = bytearray()
	keycomplete = False

	i = off - 1
	while i + 1 < len(buf):

		i += 1
		c = buf[i]

		if not tree_started:
			if c <= 32:
				continue
			elif c == 40:								# (
				tree_started = True
				continue
			else:
				raise ParserFail

		if inside_value:

			if escape_flag:
				value.append(buf[i])
				escape_flag = False
				continue
			elif c == 92:								# \
				escape_flag = True
				continue
			elif c == 93:								# ]
				inside_value = False
				if not node:
					raise ParserFail
				node.add_value_fast(key.decode(encoding="utf-8", errors="replace"), value.decode(encoding="utf-8", errors="replace"))
				continue
			else:
				value.append(c)
				continue

		else:

			if c <= 32 or (c >= 97 and c <= 122):		# a-z
				continue
			elif c == 91:								# [
				if not node:
					node = Node(parent_of_local_root)
					root = node
				value = bytearray()
				inside_value = True
				keycomplete = True
				if len(key) == 0:
					raise ParserFail
				if (key == b'B' or key == b'W') and ("B" in node.props or "W" in node.props):
					raise ParserFail
				continue
			elif c == 40:								# (
				if not node:
					raise ParserFail
				chars_to_skip = load_sgf_recursive(buf, i, node).readcount
				i += chars_to_skip - 1	# Subtract 1: the ( character we have read is also counted by the recurse.
				continue
			elif c == 41:								# )
				if not root:
					raise ParserFail
				return ParseResult(root = root, readcount = i + 1 - off)
			elif c == 59:								# ;
				if not node:
					node = Node(parent_of_local_root)
					root = node
				else:
					node = Node(node)
				key = bytearray()
				keycomplete = False
				continue
			elif c >= 65 and c <= 90:					# A-Z
				if keycomplete:
					key = bytearray()
					keycomplete = False
				key.append(c)
				continue
			else:
				raise ParserFail

	raise ParserFail


