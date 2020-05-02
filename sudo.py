DEBUG = False

class Square:
    """A Sudoku square"""

    digits = range(1,10)

    def __init__(self, grid, index, row, column, box, value):
        self._grid = grid
        self._index = index
        self._row = row
        self._column = column
        self._box = box

        grid.squares.append(self)
        row.squares.append(self)
        column.squares.append(self)
        box.squares.append(self)

        if value:
            self._value = value
            self._candidates = set()
        else:
            self._value = None
            self._candidates = set(Square.digits)
            grid.unsolved_squares.append(self)
            row.unsolved_squares.append(self)
            column.unsolved_squares.append(self)
            box.unsolved_squares.append(self)

    def __str__(self):
        return str(self._value) if self._value is not None else " ".join([str(x) for x in self._candidates])

    @property
    def grid(self):
        return self._grid

    @property
    def index(self):
        return self._index

    @property
    def row(self):
        return self._row

    @property
    def column(self):
        return self._column

    @property
    def box(self):
        return self._box

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value in Square.digits:
            self._value = value
            self.grid.move_stack.append("{}={}".format(self.index, value))

            self.row.unsolved_squares.remove(self)
            self.column.unsolved_squares.remove(self)
            self.box.unsolved_squares.remove(self)
        else:
            raise ValueError("Invalid square value {}".format(value))

    @property
    def candidates(self):
        return self._candidates

    @candidates.setter
    def candidates(self, values):
        if all([x in Square.digits for x in values]):
            self._candidates = self._candidates.intersection(set(values))
        else:
            raise ValueError("Invalid square value {}".format("".join(values)))

    def remove_candidate(self, value):
        if value in self._candidates:
            self._candidates.discard(value)
            self.grid.move_stack.append("{}-={}".format(self.index, value))
            return True
        else:
            return False

class Unit:
    """A grid unit (row, column, box)"""

    def __init__(self, grid, unit, index, size=9, squares=None):
        self._grid = grid
        self._unit = unit
        self._index = index
        self._size = size
        self._squares = squares if squares else list()
        self._unsolved_squares = [x for x in squares if not x.value] if squares else list()

    @property
    def grid(self):
        return self._grid

    @property
    def unit(self):
        return self._unit

    @property
    def index(self):
        return self._index

    @property
    def size(self):
        return self._size

    @property
    def squares(self):
        return self._squares

    @property
    def unsolved_squares(self):
        return self._unsolved_squares

    def find_naked_pairs(self):
        """Find naked pairs in an unit. This method must only be called if the unit contains no unsolved singles."""
        # If we combine N cells, and the size of the union of their candidate sets is N, we have a naked N-set.
        affected_grid = False
        for i in range(len(self.unsolved_squares)):
            for j in range(i + 1, len(self.unsolved_squares)):
                union = self.unsolved_squares[i].candidates | self.unsolved_squares[j].candidates
                if len(union) == 2:
                    # We have found a naked pair: remove values from candidates of all other squares in the unit
                    for z, s in enumerate(self.unsolved_squares):
                        if z not in (i, j):
                            for c in union:
                                affected_grid |= s.remove_candidate(c)
                    if affected_grid:
                        print("Found a naked pair in {} {}".format(self.unit, self.index))
                        return True
        return False

    def find_naked_triples(self):
        """Find naked triples in an unit. This method must only be called if the unit contains no unsolved singles or pairs."""
        # If we combine N cells, and the size of the union of their candidate sets is N, we have a naked N-set.
        affected_grid = False
        for i in range(len(self.unsolved_squares)):
            for j in range(i + 1, len(self.unsolved_squares)):
                for k in range(j + 1, len(self.unsolved_squares)):
                    union = self.unsolved_squares[i].candidates | self.unsolved_squares[j].candidates | self.unsolved_squares[k].candidates
                    if len(union) == 3:
                        # We have found a naked triple: remove values from candidates of all other squares in the unit
                        for z, s in enumerate(self.unsolved_squares):
                            if z not in (i, j, k):
                                for c in union:
                                    affected_grid |= s.remove_candidate(c)
                        if affected_grid:
                            print("Found a naked triple in {} {}".format(self.unit, self.index))
                            return True
        return False

    def find_naked_quadruples(self):
        """Find naked quadruples in an unit. This method must only be called if the unit contains no unsolved singles, pairs or triples."""
        # If we combine N cells, and the size of the union of their candidate sets is N, we have a naked N-set.
        affected_grid = False
        for i in range(len(self.unsolved_squares)):
            for j in range(i + 1, len(self.unsolved_squares)):
                for k in range(j + 1, len(self.unsolved_squares)):
                    for l in range(k + 1, len(self.unsolved_squares)):
                        union = self.unsolved_squares[i].candidates | self.unsolved_squares[j].candidates | self.unsolved_squares[k].candidates | self.unsolved_squares[l].candidates
                        if len(union) == 4:
                            # We have found a naked quadruple: remove values from candidates of all other squares in the unit
                            for z, s in enumerate(self.unsolved_squares):
                                if z not in (i, j, k, l):
                                    for c in union:
                                        affected_grid |= s.remove_candidate(c)
                            if affected_grid:
                                print("Found a naked quadruple in {} {}".format(self.unit, self.index))
                                return True
        return False

    def is_valid(self):
        """Check that the Unit has been fully initialized and does not contain duplicate values"""
        if len(self.squares) == self.size:
            values = [x.value for x in self.squares if x.value is not None]
            return len(set(values)) == len(values)
        else:
            return False

    def __str__(self):
        return "{} {}".format(self.unit, self.index)

class Grid:
    """A Sudoku grid"""

    def __init__(self, values):
        self.squares = []
        self.rows = [Unit(self, "Row", i) for i in range(9)]
        self.columns = [Unit(self, "Column", i) for i in range(9)]
        self.boxes = [Unit(self, "Box", i) for i in range(9)]
        self.unsolved_squares = []

        for i, v in enumerate(values):
            # Determine cell position
            row_index = i // 9
            column_index = i % 9
            box_index = ((row_index // 3) * 3) + (column_index // 3)

            # Create the Square instance
            s = Square(self, i, self.rows[row_index], self.columns[column_index], self.boxes[box_index], v)

    def is_solved(self):
        for s in self.squares:
            if s.value is None:
                return False
        return True

    def is_valid(self):
        return all([x.is_valid() for x in self.rows + self.columns + self.boxes])

    def __str__(self):
        out = ""
        for i, r in enumerate(self.rows):
            # Print each row of candidates for each square
            # print("Row: ({}/{})".format(i + 1, len(self.rows)))
            for c_r in range(3):
                # print("Candidate Row: ({}/{})".format(c_r + 1, 3))
                for j, s in enumerate(r.squares):
                    # print("Square: ({}/{})".format(j + 1, r.size))
                    # Print a single value
                    if s.value is not None:
                        if c_r == 1:
                            out += "   {}  ".format(s.value)
                        else:
                            out += "      "
                    else:
                        for e in range((c_r * 3) + 1, (c_r + 1) * 3 + 1):
                            out += " {}".format(e if e in s.candidates else " ")
                    separator = " │"
                    if j in (2, 5):
                        separator = " ║"
                    if j == 8:
                        separator = "\n"
                    out += separator
            if i < 8:
                for j in range(r.size):
                    if i in (2, 5):
                        separator = "═══════"
                        corner = "╪"
                        if j in (2, 5):
                            corner = "╬"
                        if j == 8:
                            corner = "\n"
                    else:
                        separator = "───────"
                        corner = "┼"
                        if j in (2, 5):
                            corner = "╫"
                        if j == 8:
                            corner = "\n"

                    out += "{}{}".format(separator, corner)
        return out

class Puzzle(Grid):
    """A Sudoku puzzle"""

    def __init__(self, values):
        if len(values) != 9*9:
            raise ValueError("Wrong number of cells!")
        integer_values = [int(x) for x in values]
        Grid.__init__(self, integer_values)
        self.move_stack = []

    def update_notation(self):
        affected_grid = False

        # Remove candidates affected by solved squares
        for s in self.unsolved_squares:
            for v in set([x.value for x in s.row.squares if x.value]):
                affected_grid |= s.remove_candidate(v)
            for v in set([x.value for x in s.column.squares if x.value]):
                affected_grid |= s.remove_candidate(v)
            for v in set([x.value for x in s.box.squares if x.value]):
                affected_grid |= s.remove_candidate(v)
        if affected_grid:
            print("Updated notation based on new solved squares")
            return

        # Find naked sets (pair, triple, quadruple)
        # If we got here, we don't have singles. Therefore, we can find naked sets
        # by using the following logic.
        # If we combine N cells, and the size of the union of their candidate sets
        # is N, we have a naked N-set.
        # Find naked pairs
        for u in self.rows + self.columns + self.boxes:
            affected_grid |= u.find_naked_pairs()
        # Find naked triples
        for u in self.rows + self.columns + self.boxes:
            affected_grid |= u.find_naked_triples()
        # Find naked quadruples
        for u in self.rows + self.columns + self.boxes:
            affected_grid |= u.find_naked_quadruples()
        if affected_grid:
            return

        # Perform more logic
        return

    def solve(self):
        if not self.is_valid():
            print("Puzzle is invalid!")
            return

        current_moves = len(self.move_stack)
        iterations = 0
        while(self.is_solved() == False):
            iterations += 1

            print("\nIteration {}".format(iterations))
            # Perform moves

            # Update notation
            self.update_notation()

            if DEBUG and current_moves != len(self.move_stack):
                print(self)

            solved_this_round = []
            # Solve singles
            for s in self.unsolved_squares:
                if len(s.candidates) == 1:
                    s.value = s.candidates.pop()
                    solved_this_round.append(s)
            # Remove solved squares from unsolved
            for s in solved_this_round:
                self.unsolved_squares.remove(s)

            if solved_this_round:
                print("Solved singles")

            if DEBUG and solved_this_round:
                print("Solved singles:")
                print(self)

            if current_moves == len(self.move_stack):
                # If I did not perform any move this turn I am stuck
                print("Cannot make further progress!")
                break
            current_moves = len(self.move_stack)

            # If we somehow ended up with an invalid puzzle, abort
            if not self.is_valid():
                print("Puzzle is invalid!")
                break
        print("Performed {} moves in {} iterations".format(len(self.move_stack), iterations))
        return

# Very Easy
# p = Puzzle("981003040" "000079250" "070106083" "090407502" "008010700" "703605010" "310704090" "069230000" "050900324")

# Easy
# p = Puzzle("007000006" "020670000" "864091037" "006304070" "208000603" "040506800" "480760159" "000052060" "600000300")

# Moderate
# p = Puzzle("007080200" "600702000" "090501060" "700009008" "400307002" "300800009" "010408050" "000905006" "008060900")

# Challenging
# p = Puzzle("960200000" "050000600" "300100005" "403910000" "090000070" "000025104" "600004001" "008000020" "000002036")

# Tricky
# p = Puzzle("004010006" "600002004" "000070302" "098700003" "100000007" "300001540" "809030000" "200900001" "500040200")
# p = Puzzle("001700500" "000000030" "503200400" "100093200" "050000040" "002640001" "004009807" "060000000" "005007300")
# p = Puzzle("237090008" "000100005" "004800602" "000000920" "900000003" "051000000" "803009500" "400006000" "100070249")
# p = Puzzle("190467000" "070380000" "000000000" "820000609" "706204308" "901000025" "000000000" "000028060" "000753092")
p = Puzzle("030206050" "600708001" "000030000" "340109065" "002000900" "580403027" "000070000" "700902008" "010605070")

print(p)

p.solve()

print(p)
