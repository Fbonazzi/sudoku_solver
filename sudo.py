import argparse
import logging

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
            self._given = True
        else:
            self._value = None
            self._candidates = set(Square.digits)
            grid.unsolved_squares.append(self)
            row.unsolved_squares.append(self)
            column.unsolved_squares.append(self)
            box.unsolved_squares.append(self)
            self._given = False

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
    def given(self):
        return self._given

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
        v = set(values)
        # All values must be valid digits, and the set of values must be a subset of the set of candidates
        if all([x in Square.digits for x in v]) and self._candidates >= v:
            self._candidates = v
            self.grid.move_stack.append("{}={}".format(self.index, "".join([str(x) for x in v])))
        else:
            raise ValueError("Invalid square candidates {}".format("".join([str(x) for x in v])))

    def keep_candidates(self, values):
        v = set(values)
        # Remove all candidates not in the provided set
        if all([x in Square.digits for x in v]) and (self._candidates & v):
            if self._candidates == v:
                # No change
                return False
            else:
                self._candidates = self._candidates & v
                self.grid.move_stack.append("{}-={}".format(self.index, "".join([str(x) for x in set(self._candidates - v)])))
                return True
        else:
            raise ValueError("Invalid square candidates {}".format("".join([str(x) for x in v])))

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
                        logging.info("Found a {values} naked pair in {unit} {index}".format(unit=self.unit,
                            index=self.index + 1,
                            values="".join([str(x) for x in sorted(union)])))
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
                            logging.info("Found a {values} naked triple in {unit} {index}".format(unit=self.unit,
                                index=self.index + 1,
                                values="".join([str(x) for x in sorted(union)])))
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
                                logging.info("Found a {values} naked quadruple in {unit} {index}".format(
                                    unit=self.unit,
                                    index=self.index + 1,
                                    values="".join([str(x) for x in sorted(union)])))
                                return True
        return False

    def find_hidden_pairs(self):
        """Find hidden pairs in a unit. This method must only be called if the unity contains no unsolved singles."""
        # If we find N numbers which, combined, occupy only N squares in a unit, we have a hidden N-set.
        affected_grid = False
        positions = {i: set() for i in Square.digits}
        # Save the sets of positions for each unsolved number in the unit
        for p, s in enumerate(self.unsolved_squares):
            for i in s.candidates:
                positions[i].add(p)
        # Detect overlapping sets
        unsolved_numbers = set([i for i in positions.keys() if positions[i]])
        for i in sorted(unsolved_numbers):
            for j in [x for x in sorted(unsolved_numbers) if x > i]:
                union = positions[i] | positions[j]
                if len(union) == 2:
                    # We have found a hidden pair: remove all other candidates from the squares containing the pair
                    for p in union:
                        affected_grid |= self.unsolved_squares[p].keep_candidates({i, j})
                    if affected_grid:
                        logging.info("Found a {values} hidden pair in {unit} {index}".format(
                            unit=self.unit,
                            index=self.index + 1,
                            values="".join([str(x) for x in sorted({i, j})])))
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
            # logging.debug("Row: ({}/{})".format(i + 1, len(self.rows)))
            for c_r in range(3):
                # logging.debug("Candidate Row: ({}/{})".format(c_r + 1, 3))
                for j, s in enumerate(r.squares):
                    # logging.debug("Square: ({}/{})".format(j + 1, r.size))
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

    @staticmethod
    def from_file(f):
        s = ""
        with open(f, "r") as f_in:
            # Read 81 decimal digits from file. If the file contains anything else it is malformed.
            while True:
                b = f_in.read(1)
                if not b:
                    # We reached end of file
                    break
                if b.isspace():
                    # Ignore spaces and newlines
                    continue
                if b.isdigit():
                    s += b
                    if len(s) == 81:
                        # Only read 81 digits
                        break
                else:
                    logging.error("Invalid file {}:\nInvalid character \"{}\"".format(f, b))
                    return None
        if len(s) == 81:
            return Puzzle(s)
        else:
            logging.error("Invalid file {}:\nFile too short (found {} characters, expected {})".format(f, len(s), 81))
            return None



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
            logging.info("Updated notation based on new solved squares")
            return

        # Find hidden sets (pair, triple, quadruple)
        # If we got here, we don't have singles. Therefore, we can find hidden sets
        # by using the following logic.
        # If we combine N numbers, and the size of the union of their candidate squares
        # is N, we have a hidden N-set.
        # Find hidden pairs
        for u in self.rows + self.columns + self.boxes:
            affected_grid |= u.find_hidden_pairs()
        if affected_grid:
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
            logging.error("Puzzle is invalid!")
            return

        current_moves = len(self.move_stack)
        iterations = 0
        while(self.is_solved() == False):
            iterations += 1

            logging.info("Iteration {}".format(iterations))
            # Perform moves

            # Update notation
            self.update_notation()

            # TODO: add interactive mode
            # if current_moves != len(self.move_stack):
            #    print(self)

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
                logging.info("Solved singles")

            # TODO: add interactive mode
            #if DEBUG and solved_this_round:
            #    print("Solved singles:")
            #    print(self)

            if current_moves == len(self.move_stack):
                # If I did not perform any move this turn I am stuck
                logging.error("Cannot make further progress!")
                break
            current_moves = len(self.move_stack)

            # If we somehow ended up with an invalid puzzle, abort
            if not self.is_valid():
                logging.error("Puzzle is invalid!")
                break
        logging.info("Performed {} moves in {} iterations".format(len(self.move_stack), iterations))
        return

def main():
    parser = argparse.ArgumentParser(description="A simple sudoku solver")
    parser.add_argument('file', metavar='FILE', type=str,
            help="A Sudoku file in text format. Zeroes are used to represent empty cells.")
    g_action = parser.add_mutually_exclusive_group()
    g_action.add_argument("-s", "--solve", action='store_const', dest="action", const="solve", default="solve",
            help="Solve the puzzle and exit [Default: True]")
    g_action.add_argument("-p", "--print", action='store_const', dest="action", const="print",
            help="Print the puzzle and exit [Default: False]")
    g_action.add_argument("-i", "--interactive", action='store_const', dest="action", const="interactive",
            help="Solve interactively [Default: False]")
    g_logging = parser.add_mutually_exclusive_group()
    g_logging.add_argument("-v", "--verbose", action="store_const", dest="logging", const=logging.INFO,
            help="Show solution steps [Default: False]")
    g_logging.add_argument("--debug", action="store_const", dest="logging", const=logging.DEBUG,
            help="Print debug information [Default: False]")

    args = parser.parse_args()

    # Configure logging if required
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    if args.logging:
        logging.basicConfig(level=args.logging)

    # Initialise puzzle
    p = Puzzle.from_file(args.file)

    # Perform user action
    if args.action == "solve":
        p.solve()
        print(p)
    elif args.action == "print":
        print(p)
    elif args.action == "interactive":
        logging.warning("Not supported")
    else:
        logging.warning("Not supported")

    return

if __name__ == "__main__":
    main()
