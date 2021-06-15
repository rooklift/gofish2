#!/usr/bin/env python3

class ParserFail(Exception):
	pass

class ParseResult:
	def __init__(self, root, readcount):
		self.root = root
		self.readcount = readcount

# -------------------------------------------------------------------------------------------------

class Board:

	def __init__(self, width, height, state = None, ko = None, active = "b", caps_by_b = 0, caps_by_w = 0):

		self.width = width
		self.height = height
		self.state = []
		self.ko = ko
		self.active = active
		self.caps_by_b = caps_by_b
		self.caps_by_w = caps_by_w

		for x in range(width):
			self.state.append([])
			for y in range(height):
				if state:
					self.state[x].append(state[x][y])
				else:
					self.state[x].append("")


	def copy(self):
		return Board(self.width, self.height, self.state, self.ko, self.active, self.caps_by_b, self.caps_by_w)


	def dump(self):

		ko_x, ko_y = s_to_xy(self.ko)

		for y in range(0, self.height):
			for x in range(0, self.width):
				char = "X" if self.state[x][y] == "b" else "O" if self.state[x][y] == "w" else " " if (ko_x == x and ko_y == y) else "."
				print(char, end = " ")
			print()


	def state_at(self, s):
		x, y = s_to_xy(s)
		if x >= 0 and x < self.width and y >= 0 and y < self.height:
			return self.state[x][y]
		else:
			return ""


	def set_at(self, s, colour):
		assert(colour == "b" or colour == "w" or colour == "")
		x, y = s_to_xy(s)
		if x >= 0 and x < self.width and y >= 0 and y < self.height:
			self.state[x][y] = colour


	def one_liberty_singleton(self, s):

		colour = self.state_at(s)

		if not colour:
			return False

		liberties = 0

		for neighbour in self.neighbours(s):
			neighbour_colour = self.state_at(neighbour)
			if neighbour_colour == colour:
				return False
			if not neighbour_colour:
				liberties += 1

		return liberties == 1


	def neighbours(self, s):
		x, y = s_to_xy(s)
		if x < 0 or x >= self.width or y < 0 or y >= self.height:
			return []
		ret = []
		if x < self.width - 1:
			ret.append(xy_to_s(x + 1, y))
		if x > 0:
			ret.append(xy_to_s(x - 1, y))
		if y < self.height - 1:
			ret.append(xy_to_s(x, y + 1))
		if y > 0:
			ret.append(xy_to_s(x, y - 1))
		return ret


	def ko_square_finder(self, s):

		for neighbour in self.neighbours(s):
			if not self.state_at(neighbour):
				return neighbour

		return None


	def destroy_group(self, s):

		colour = self.state_at(s)
		if not colour:
			return 0

		self.set_at(s, "")

		if colour == "b":
			self.caps_by_w += 1
		else:
			self.caps_by_b += 1

		caps = 1;

		for neighbour in self.neighbours(s):
			if self.state_at(neighbour) == colour:
				caps += self.destroy_group(neighbour)

		return caps


	def has_liberties(self, s):

		if not self.state_at(s):
			return False

		touched = dict()

		return self.has_liberties_recurse(s, touched)


	def has_liberties_recurse(self, s, touched):

		touched[s] = True

		colour = self.state_at(s)

		for neighbour in self.neighbours(s):

			if neighbour in touched:
				continue

			neighbour_colour = self.state_at(neighbour)

			if not neighbour_colour:
				return True

			if neighbour_colour == colour:
				if self.has_liberties_recurse(neighbour, touched):
					return True

		return False


	def legal_move(self, s):
		return self.legal_move_colour(s, self.active)


	def legal_move_colour(self, s, colour):		# Note: does not consider passes as "legal moves".

		assert(colour == "b" or colour == "w")

		x, y = s_to_xy(s)

		if x < 0 or x >= self.width or y < 0 or y >= self.height:
			return False
		if self.state_at(s):
			return False
		if self.ko == s:
			return False

		# Move will be legal as long as it's not suicide...

		neighbours = self.neighbours(s)

		for neighbour in neighbours:
			if not self.state_at(neighbour):
				return True						# New stone has a liberty.

		opposite_colour = "b" if colour == "w" else "w"

		for neighbour in neighbours:
			if self.state_at(neighbour) == colour:
				touched = dict()
				touched[s] = True
				if self.has_liberties_recurse(neighbour, touched):
					return True					# One of the groups we're joining has a liberty other than s.
			elif self.state_at(neighbour) == opposite_colour:
				touched = dict()
				touched[s] = True
				if not self.has_liberties_recurse(neighbour, touched):
					return True					# One of the enemy groups has no liberties other than s.

		return False


	def play_move_or_pass(self, s, colour):

		assert(colour == "b" or colour == "w")

		self.ko = None
		self.active = "b" if colour == "w" else "w"

		x, y = s_to_xy(s)

		if x < 0 or x >= self.width or y < 0 or y >= self.height:
			return					# Treat as a pass.

		self.set_at(s, colour)
		caps = 0

		for neighbour in self.neighbours(s):

			neighbour_colour = self.state_at(neighbour)

			if neighbour_colour and neighbour_colour != colour:
				if not self.has_liberties(neighbour):
					caps += self.destroy_group(neighbour)

		if not self.has_liberties(s):
			self.destroy_group(s)

		if caps == 1:
			if self.one_liberty_singleton(s):
				self.ko = self.ko_square_finder(s)

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


	def make_board(self):								# Returns a copy in gofish2

		if self.__board:
			return self.__board.copy()

		if not self.parent:
			self.__board = Board(self.width, self.height)
		else:
			self.__board = self.parent.make_board()

		for s in self.all_values("AE"):
			self.__board.set_at(s, "")

		for s in self.all_values("AB"):
			self.__board.set_at(s, "b")
			self.__board.active = "w"

		for s in self.all_values("AW"):
			self.__board.set_at(s, "w")
			self.__board.active = "b"

		for s in self.all_values("B"):
			self.__board.play_move_or_pass(s, "b")		# Will treat s as a pass if it's not a valid move.

		for s in self.all_values("W"):
			self.__board.play_move_or_pass(s, "w")		# Will treat s as a pass if it's not a valid move.

		pl = self.get("PL");
		if pl == "B" or pl == "b":
			self.__board.active = "b"
		if pl == "W" or pl == "w":
			self.__board.active = "w"

		return self.__board.copy()


	def get_root(self):

		node = self
		while node.parent:
			node = node.parent
		return node


	def get_end(self):

		node = self
		while len(node.children) > 0:
			node = node.children[0]
		return node


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


	def all_values(self, key):
		ret = [];
		if key not in self.props:
			return ret
		for value in self.props[key]:
			ret.append(value)
		return ret;


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

			if len(node.children) == 0 or move_count >= 71:
				break

			node = node.children[0]

		return dyer[20] + dyer[40] + dyer[60] + dyer[31] + dyer[51] + dyer[71]


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

def s_to_xy(s):

	if not isinstance(s, str):
		return (-1, -1)

	if len(s) != 2:
		return (-1, -1)

	x_ascii = ord(s[0])
	y_ascii = ord(s[1])

	if x_ascii >= 97 and x_ascii <= 122:
		x = x_ascii - 97
	elif x_ascii >= 65 and x_ascii <= 90:
		x = x_ascii - 65 + 26
	else:
		return (-1, -1)

	if y_ascii >= 97 and y_ascii <= 122:
		y = y_ascii - 97
	elif y_ascii >= 65 and y_ascii <= 90:
		y = y_ascii - 65 + 26
	else:
		return (-1, -1)

	return (x, y)


def xy_to_s(x, y):

	assert(x >= 0 and x < 52 and y >= 0 and y < 52)

	s = ""

	if x < 26:
		s += chr(x + 97)
	else:
		s += chr(x + 65 - 26)

	if y < 26:
		s += chr(y + 97)
	else:
		s += chr(y + 65 - 26)

	return s

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


