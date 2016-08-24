from collections import Counter, OrderedDict
from itertools import groupby
import copy
from pandas import DataFrame

tetris_shapes = [
    [[1, 1, 1],
     [0, 1, 0]],

    [[0, 2, 2],
     [2, 2, 0]],

    [[3, 3, 0],
     [0, 3, 3]],

    [[4, 0, 0],
     [4, 4, 4]],

    [[0, 0, 5],
     [5, 5, 5]],

    [[6, 6, 6, 6]],

    [[7, 7],
     [7, 7]]
]

cols = 10
rows = 22

rotations_by_index = {  # number of rotations by index of piece in tetris shapes
    6: 1,
    1: 2, 2: 2, 5: 2,
    0: 4, 3: 4, 4: 4
}


def rotate_clockwise(shape):
    '''rotates the shape clockwise around [0][0]
    '''
    return [[shape[y][x]
             for y in xrange(len(shape))]
            for x in xrange(len(shape[0]) - 1, -1, -1)]


def check_collision1(board, shape, offset):
    '''makes sure a board doesn't collide with a piece, returns bool
    '''
    off_x, off_y = offset
    for cy, row in enumerate(shape):
        for cx, cell in enumerate(row):
            try:
                if cell and board[ cx + off_x ][ cy + off_y ]:
                    return True
            except IndexError:
                return True
    return False

def join_matrixes1(mat1, mat2, mat2_off):
    '''combines 2 boards and an offset
    '''
    off_x, off_y = mat2_off
    for cy, row in enumerate(mat2):
        for cx, val in enumerate(row):
            mat1[cx + off_x][cy + off_y - 1] += val
    return mat1

def join_matrixes(mat1, mat2, mat2_off):
    '''combines 2 boards and an offset
    '''
    off_x, off_y = mat2_off
    for cy, row in enumerate(mat2):
        for cx, val in enumerate(row):
            mat1[cy + off_y - 1][cx + off_x] += val
    return mat1

def check_collision(board, shape, offset):
    '''makes sure a board doesn't collide with a piece, returns bool
    '''
    off_x, off_y = offset
    for cy, row in enumerate(shape):
        for cx, cell in enumerate(row):
            try:
                if cell and board[cy + off_y][cx + off_x]:
                    return True
            except IndexError:
                return True
    return False




def get_piece_index(shape):
    '''
    Rotate a shape max 4 times to find it's index
    '''
    rotations = 0
    index = -1
    for r in range(4):
        try:
            index = tetris_shapes.index(shape)
        except ValueError:
            shape = rotate_clockwise(shape)
    return index


def get_rotations(shape):
    '''rotate until == original shape
    '''
    rotated_shape = shape
    for r in range(4):
        rotated_shape = rotate_clockwise(rotated_shape)
        yield rotated_shape

        if rotated_shape == shape:
            break


def get_piece_rotation(shape):
    '''how many rotations away is the original shape from the new shape
    '''
    rotations = rotations_by_index[get_piece_index(shape)]

    rotated_shape = shape[:]
    original_shape = tetris_shapes[get_piece_index(shape)]
    for r in range(rotations):
        if rotated_shape == original_shape:
            return r
        else:
            original_shape = rotate_clockwise(original_shape)


def get_all_moves(board, piece):
    for rotation_index, rotated_piece in enumerate(get_rotations(piece)):
        for slice_index, slice_board in board.slice_iter(len(zip(*rotated_piece))):
            yield {
                "board": board.fake_add(slice_index, rotated_piece),
                "rotation": {
                    "index": rotation_index,
                    "piece": rotated_piece
                },
                "slice": {
                    "index": slice_index,
                    "board": slice_board
                }
            }


class Row(list):
    '''Just a list object that will be expanded upon
    '''

    def __init__(self, row):
        list.__init__(self, row)
        self.is_full = all(row)
        self.spaces = self.count(0)
        self.divisions = len([group for group in groupby(self, lambda s: s != 1) if group[0]])


class Column(list):
    '''Column object is just a list with some analytic structure ontop
    '''

    def __init__(self, col_list):
        list.__init__(self, col_list)
        self.height_gap = False
        self.height = False
        self.spaces = False

    def remove_space(self, index):
        '''delete index and add 0 at end. represents the 'clearing' of a line
        '''
        if index in range(len(self)):
            del self[index]
            self = Column([0] + self)
            self.calc_data()

    def calc_data(self, update=False):
        '''calculates 3 pieces of data about a column
        '''
        if not self.height_gap or update:
            self.calc_height_gap()
        if not self.height or update:
            self.height = len(self) - self.height_gap
        if not self.spaces or update:
            self.spaces = self.count(0) - self.height_gap
        return self

    def calc_height_gap(self):
        '''gets the gap between the height and max ceiling
        '''
        for i, j in enumerate(self):
            if j != 0:
                self.height_gap = i
                break


class Board(list):
    '''
    Board object contains columns

    provides more advanced analysis by providing more data.
    Also allows you to "fake add" piece and iterate through slices of the board
    '''

    def __init__(self, board_list):
        list.__init__(self, [Column(col).calc_data() for col in board_list])

        self.max = False
        self.min = False
        self.average = False
        self.mode = False
        self.total_spaces = False
        self.full_rows = False
        self.row_completeness = False

    def invert(self):
        '''return just a new list in "row" format
        '''
        return [Row(list(row)) for row in zip(*self)]

    def get_feature_dict(self):
        '''returns a long dict of features from a board
        '''
        self.calc_data()

        feature_dict = OrderedDict()

        feature_dict["max"] = self.max
        feature_dict["min"] = self.min
        feature_dict["avg"] = self.average
        feature_dict["mode"] = self.mode
        feature_dict["spaces"] = self.total_spaces
        feature_dict["rows"] = self.full_rows
        feature_dict["completeness"] = self.row_completeness

        # add the heights of each column
        for i, c in enumerate(self):
            feature_dict["col" + str(i)] = c.height

        # add row information
        for i, r in enumerate(self.invert()):
            feature_dict["row" + str(i) + "_spaces"] = r.spaces
            feature_dict["row" + str(i) + "_divisions"] = r.divisions

        return feature_dict

    def calc_data(self, update=False):


        if not self.full_rows or self.row_completeness or update:

            # by default there will always be one complete row
            self.full_rows = 1
            self.row_completeness = 1

            row_board = self.invert()

            if len(row_board[0]) == cols:

                row_board_reversed = reversed(row_board[:-1])

                # find the completeness of each row by getting %
                for index, row in enumerate(row_board_reversed):
                    perc_complete = float(len(row) - row.count(0)) / len(row)
                    row_complete = perc_complete / (index + 1)
                    self.row_completeness += row_complete

                # iterator exausted, gotta make a new one
                row_board_reversed = reversed(row_board[:-1])

                for index, row in enumerate(row_board_reversed):
                    if all(row):
                        for col in self: col.remove_space(index)
                        self.full_rows += 1
                        self.row_completeness /= rows
        # general stats about the baord

        if not self.max or update:
            self.max = max(col.height for col in self)
        if not self.min or update:
            self.min = min(col.height for col in self)
        if not self.average or update:
            self.average = sum(col.height for col in self) / len(self)
        if not self.mode or update:
            heights = [col.height for col in self]
            self.mode = max(heights, key=heights.count)
        if not self.total_spaces or update:
            self.total_spaces = sum(col.spaces for col in self)
        return self
    def calc_data1(self, update=False):

        if not self.full_rows or self.row_completeness or update:

            # by default there will always be one complete row
            self.full_rows = 1
            self.row_completeness = 1

            row_board = self
            row_board_reversed = row_board

            # find the completeness of each row by getting %
            for index, row in enumerate(row_board_reversed):
                perc_complete = float(cols - row.count(0)) / cols  # TODO speed this up
                row_complete = perc_complete / ((rows - index) + 1)
                self.row_completeness += row_complete

            self.full_rows = self.get_full_rows()
            self.row_completeness /= rows

        # general stats about the board
        heights = self.get_heights()

        if not self.max or update:
            self.max = max(heights)
        if not self.min or update:
            self.min = min(heights)
        if not self.average or update:
            self.average = sum(heights) / cols
        if not self.mode or update:
            self.mode = max(heights, key=heights.count)
        if not self.total_spaces or update:
            self.total_spaces = self.get_spaces()


        return self

    def get_full_rows(self):

        total = 0
        for row in self:

            add = 1
            for cell in row:
                if cell == 0:
                    add = 0
            total += add
        return total

    def get_spaces(self):
        total = 0
        for row in self:
            for cell in row:
                if cell == 0:
                    total += 1
        return total

    def get_heights(self):
        heights = [0] * (cols + 1)
        for idx, row in  enumerate(self):

            for cell in (row):

                if idx == 0:
                    continue
                heights[idx] += 1 if cell != 0 else 0

        return heights

    def data(self):
        '''print the data to console
        '''
        print "Max: %d" % (self.max)
        print "Min: %d" % (self.min)
        print "Avg: %f" % (self.average)
        print "Mode: %d" % (self.mode)
        print "Spaces: %d" % (self.total_spaces)
        print "Rows: %d" % (self.full_rows)
        print '\n'

    def calc_col_data(self):
        for col in self:
            col.calc_data(True)

    def slice_iter(self, width):
        '''iterator that returns a "slice" of a board and its index
        '''
        assert 1 <= width <= len(self), "Width not within bounds of board"

        for col in range(0, len(self) - width + 1):
            yield (col, Board(self[col:col + width][:]))
    def copy(self):
        board = copy.deepcopy(self)
        for col in board:
            print col
    def pprint(self, matrix):
        s = [[str(e) for e in row] for row in matrix]
        lens = [max(map(len, col)) for col in zip(*s)]
        fmt = '\t'.join('{{:{}}}'.format(x) for x in lens)
        table = [fmt.format(*row) for row in s]
        print '\n'.join(table)

    def fake_add(self, x, piece):
        '''returns board object with piece "insta_dropped" at an x
        '''

        row_board = self.invert()
        #self.copy()
        board = copy.deepcopy(self)
        #board.append(([1] * (rows + 1)))
        assert x in [0] + range(len(self) - len(zip(*piece)) + 1), "X not within bounds"

        # start from top down, once there is a collision, add and return new board
        # ORIGINAL CODE:
        #for y in range(1, rows + 1):
        #   if check_collision1(board, piece, (x, y)):
        #        row_board_with_piece = join_matrixes(row_board, piece, (x, y))
        #        return Board(zip(*row_board_with_piece))
        #raise Exception("NO COLLISIONS DETECTED")

        # NEW CODE:
        # ALEX. I DON'T KNOW WHAT !*&@!$ SIDE EFFECTS THIS CODE RELIES ON
        # FIX IT
        for y in range(1, rows+1):
            # check_collision1 is the optimized one, check_collision is the old unoptimized one
            assert check_collision1(board, piece, (x, y)) == check_collision(row_board, piece, (x, y))
            # the left is the original board creation procedure, the left is a (slightly bloated) but optimized version.
            assert Board(zip(*join_matrixes(row_board, piece, (x, y)))) == Board([tuple(e) for e in join_matrixes1((board), piece, (x, y))])

            # SINCE BOTH ARE CLEARLY EQUAL, WHY DOES THIS NOT WORK!?!?!?!!
            if check_collision1(board, piece, (x, y)):
                return Board([tuple(e) for e in join_matrixes1((board), piece, (x, y))])

        raise Exception("NO COLLISIONS DETECTED")
