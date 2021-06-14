#!/usr/bin/env python3


class ParserFail(Exception):
	pass


class Node:

	def __init__(self, parent = None):

		self.parent = parent
		self.children = []
		self.props = dict()
		self.__board = None

		if parent:
			parent.children.append(self)

	@property
	def width(self):		# FIXME

		if self.__board:
			return self.__board.width

		root = self.get_root_node()
		sz = root.get_value("SZ")

		try:
			return int(sz)
		except:
			return 19

	@property
	def height(self):		# FIXME

		if self.__board:
			return self.__board.height

		root = self.get_root_node()
		sz = root.get_value("SZ")

		try:
			return int(sz)
		except:
			return 19

	def get_root_node(self):

		node = self
		while True:
			if not node.parent:
				return node
			node = node.parent

	def set_value(self, key, value):

		key = str(key)
		value = str(value)
		self.mutor_check(key)

		self.props[key] = [value]

	def get_value(self, key):

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

		node = self.get_root_node()
		dyer = {20: "??", 40: "??", 60: "??", 31: "??", 51: "??", 71: "??"}

		move_count = 0;

		while True:

			if "B" in node.props or "W" in node.props:

				move_count += 1
				if move_count in [20, 40, 60, 31, 51, 71]:
					mv = node.move_coords()
					if mv:
						dyer[move_count] = chr(mv[0] + 97) + chr(mv[1] + 97)

			if (len(node.children) == 0 or move_count >= 71):
				break

			node = node.children[0]

		dyer_string = dyer[20] + dyer[40] + dyer[60] + dyer[31] + dyer[51] + dyer[71]
		return dyer_string

	def move_coords(self):          # A pass causes None to be returned.
		for key in ["B", "W"]:
			if key in self.props:
				movestring = self.props[key][0]
				if len(movestring) != 2:
					return None
				x = ord(movestring[0]) - 97
				y = ord(movestring[1]) - 97
				if x < 0 or x >= self.width or y < 0 or y >= self.height:
					return None
				return (x, y)
		return None


class ParseResult:

	def __init__(self, root, readcount):
		self.root = root
		self.readcount = readcount


def load(filename):

	# Returns an array of roots (except load_sgf() will throw if it cannot get at least 1 root).

	with open(filename, "rb") as infile:
		buf = infile.read()

	return load_sgf(buf)


def load_sgf(buf):

	# Always returns at least 1 game; or throws if it cannot.

	ret = []
	off = 0

	while True:
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
			if c <= ord(" "):
				continue
			elif c == ord("("):
				tree_started = True
				continue
			else:
				raise ParserFail

		if inside_value:

			if escape_flag:
				value.append(buf[i])
				escape_flag = False
				continue
			elif c == ord("\\"):
				escape_flag = True
				continue
			elif c == ord("]"):
				inside_value = False
				if not node:
					raise ParserFail
				node.add_value_fast(key.decode(), value.decode())
				continue
			else:
				value.append(c)
				continue

		else:

			if c <= ord(" ") or (c >= ord("a") and c <= ord("z")):
				continue
			elif c == ord("["):
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
			elif c == ord("("):
				if not node:
					raise ParserFail
				chars_to_skip = load_sgf_recursive(buf, i, node).readcount
				i += chars_to_skip - 1	# Subtract 1: the ( character we have read is also counted by the recurse.
				continue
			elif c == ord(")"):
				if not root:
					raise ParserFail
				return ParseResult(root = root, readcount = i + 1 - off)
			elif c == ord(";"):
				if not node:
					node = Node(parent_of_local_root)
					root = node
				else:
					node = Node(node)
				key = bytearray()
				keycomplete = False
				continue
			elif c >= ord("A") and c <= ord("Z"):
				if keycomplete:
					key = bytearray()
					keycomplete = False
				key.append(c)
				continue
			else:
				raise ParserFail

	raise ParserFail


