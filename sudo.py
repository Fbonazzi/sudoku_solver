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
            if self._candidates <= v:
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
        """Find naked pairs in a unit. This method must only be called if the unit contains no unsolved singles."""
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
        """Find naked triples in a unit. This method must only be called if the unit contains no unsolved singles or pairs."""
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
        """Find naked quadruples in a unit. This method must only be called if the unit contains no unsolved singles, pairs or triples."""
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

    def find_hidden_singles(self):
        """Find hidden singles in a unit and convert them to naked singles."""
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
            if len(positions[i]) == 1:
                # We have found a hidden single: remove all other candidates from the squares which contain it
                for p in positions[i]:
                    affected_grid |= self.unsolved_squares[p].keep_candidates({i})
                if affected_grid:
                    logging.info("Found a {values} hidden single in {unit} {index}".format(
                        unit=self.unit,
                        index=self.index + 1,
                        values="".join([str(x) for x in sorted({i})])))
                    return True
        return False


    def find_hidden_pairs(self):
        """Find hidden pairs in a unit. This method must only be called if the unit contains no unsolved singles."""
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
                    # We have found a hidden pair: remove all other candidates from the squares which contain it
                    for p in union:
                        affected_grid |= self.unsolved_squares[p].keep_candidates({i, j})
                    if affected_grid:
                        logging.info("Found a {values} hidden pair in {unit} {index}".format(
                            unit=self.unit,
                            index=self.index + 1,
                            values="".join([str(x) for x in sorted({i, j})])))
                        return True
        return False

    def find_hidden_triples(self):
        """Find hidden triples in a unit. This method must only be called if the unit contains no unsolved singles."""
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
                for k in [x for x in sorted(unsolved_numbers) if x > j]:
                    union = positions[i] | positions[j] | positions[k]
                    if len(union) == 3:
                        # We have found a hidden triple: remove all other candidates from the squares which contain it
                        for p in union:
                            affected_grid |= self.unsolved_squares[p].keep_candidates({i, j, k})
                        if affected_grid:
                            logging.info("Found a {values} hidden triple in {unit} {index}".format(
                                unit=self.unit,
                                index=self.index + 1,
                                values="".join([str(x) for x in sorted({i, j, k})])))
                            return True
        return False

    def find_hidden_quadruples(self):
        """Find hidden quadruples in a unit. This method must only be called if the unit contains no unsolved singles."""
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
                for k in [x for x in sorted(unsolved_numbers) if x > j]:
                    for l in [x for x in sorted(unsolved_numbers) if x > k]:
                        union = positions[i] | positions[j] | positions[k] | positions[l]
                        if len(union) == 4:
                            # We have found a hidden quadruple: remove all other candidates from the squares which contain it
                            for p in union:
                                affected_grid |= self.unsolved_squares[p].keep_candidates({i, j, k, l})
                            if affected_grid:
                                logging.info("Found a {values} hidden quadruple in {unit} {index}".format(
                                    unit=self.unit,
                                    index=self.index + 1,
                                    values="".join([str(x) for x in sorted({i, j, k, l})])))
                                return True
        return False

    def find_naked_lines(self):
        """Find naked lines (pointing singles/pairs/triples) in a box."""
        # If all positions of a candidate in a box are aligned along a row/column, the candidate can be removed
        # from the rest of the row/column.
        affected_grid = False

        # TODO: specialize Unit into Box, Row, Column and initialise them correctly
        # TODO: remove Unit.unit attribute
        if self.unit != "Box":
            return False

        candidate_squares = {i: set() for i in Square.digits}
        # Find the candidate squares for each unsolved number in the box
        for s in self.unsolved_squares:
            for i in s.candidates:
                candidate_squares[i].add(s)
        for i, c in candidate_squares.items():
            # If we have at least one candidate square for i in the box
            if c:
                # Check for naked lines along the rows
                candidate_rows = {s.row for s in c}
                if len(candidate_rows) == 1:
                    # Found a naked line
                    for r in candidate_rows:
                        affected_this_iteration = False
                        for s in r.unsolved_squares:
                            if s not in c:
                                affected_this_iteration |= s.remove_candidate(i)
                        if affected_this_iteration:
                            affected_grid = True
                            logging.info("Found a naked line on {value}s in {unit1} {index1}, {unit2} {index2}".format(
                                unit1=self.unit,
                                index1=self.index + 1,
                                unit2=r.unit,
                                index2=r.index + 1,
                                value=i))
                # Check for naked lines along the columns
                candidate_columns = {s.column for s in c}
                if len(candidate_columns) == 1:
                    # Found a naked line
                    for r in candidate_columns:
                        affected_this_iteration = False
                        for s in r.unsolved_squares:
                            if s not in c:
                                affected_this_iteration |= s.remove_candidate(i)
                        if affected_this_iteration:
                            affected_grid = True
                            logging.info("Found a naked line on {value}s in {unit1} {index1}, {unit2} {index2}".format(
                                unit1=self.unit,
                                index1=self.index + 1,
                                unit2=r.unit,
                                index2=r.index + 1,
                                value=i))
        return affected_grid

    def find_hidden_lines(self):
        """Find hidden lines (box/line reduction) in a row or column."""
        # If all positions of a candidate in a row/column are in the same box, the candidate can be removed
        # from the rest of the box.
        affected_grid = False

        # TODO: specialize Unit into Box, Row, Column and initialise them correctly
        # TODO: remove Unit.unit attribute
        if self.unit not in ("Row", "Column"):
            return False

        candidate_squares = {i: set() for i in Square.digits}
        # Find the candidate squares for each unsolved number in the row/column
        for s in self.unsolved_squares:
            for i in s.candidates:
                candidate_squares[i].add(s)
        for i, c in candidate_squares.items():
            # If we have at least one candidate square for i in the row/column
            if c:
                candidate_boxes = {s.box for s in c}
                if len(candidate_boxes) == 1:
                    # Found a hidden line
                    for b in candidate_boxes:
                        affected_this_iteration = False
                        for s in b.unsolved_squares:
                            if s not in c:
                                affected_this_iteration |= s.remove_candidate(i)
                        if affected_this_iteration:
                            affected_grid = True
                            logging.info("Found a hidden line on {value}s in {unit1} {index1}, {unit2} {index2}".format(
                                unit1=self.unit,
                                index1=self.index + 1,
                                unit2=b.unit,
                                index2=b.index + 1,
                                value=i))
        return affected_grid

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

    @staticmethod
    def __find_x_wing(i, rows, rows_label, columns):
        """Internal function that does the actual X-Wing detection."""
        affected_grid = False
        # Look for an X-Wing in the "rows"
        positions = {j: set() for j in range(9)}
        # Find the sets of positions of number i in the "rows"
        for j, r in enumerate(rows):
            for k, s in enumerate(r.squares):
                if i in s.candidates:
                    positions[j].add(k)
        unsolved_rows = set([j for j in positions.keys() if positions[j]])
        # Look for 2 "rows" with the number i in the same 2 positions
        for j in sorted(unsolved_rows):
            for k in [x for x in sorted(unsolved_rows) if x > j]:
                union = positions[j] | positions[k]
                if len(union) == 2:
                    # We have found an X-Wing in the "rows": remove value i from all other candidates in the two "columns"
                    for c in union:
                        for z, s in enumerate(columns[c].squares):
                            if z not in {j, k}:
                                affected_grid |= s.remove_candidate(i)
                    if affected_grid:
                        logging.info("Found an X-Wing on {value}s in {label} {} and {}".format(j + 1, k + 1,
                            value=i, label=rows_label))
                        return True
        return False

    def __find_x_wing_rows(self, value):
        return self.__find_x_wing(value, self.rows, "Rows", self.columns)

    def __find_x_wing_columns(self, value):
        return self.__find_x_wing(value, self.columns, "Columns", self.rows)

    def find_x_wings(self):
        """Find X-Wings in the grid. This method can be called if the grid contains no unsolved singles."""
        # If we find a number which appears in only the same N positions in N rows, we have a N-fish in the rows.
        # The transposed version applies in the columns.

        unsolved_numbers = set.union(*[x.candidates for x in self.unsolved_squares])

        for i in unsolved_numbers:
            if self.__find_x_wing_rows(i):
                return True
            if self.__find_x_wing_columns(i):
                return True
        return False

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

        ## Simple pruning
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

        # Find hidden singles
        # Due to the current design, we convert hidden singles to naked singles here,
        # and solve them in the main function.
        for u in self.rows + self.columns + self.boxes:
            affected_grid |= u.find_hidden_singles()

        # Solve any singles before moving on to more advanced techniques
        if affected_grid:
            return

        ## Intersection removal
        while True:
            affected_this_iteration = False
            # Find pointing pairs/triples
            for u in self.boxes:
                affected_this_iteration |= u.find_naked_lines()
            # Box/line reduction
            for u in self.rows + self.columns:
                affected_this_iteration |= u.find_hidden_lines()

            if affected_this_iteration:
                affected_grid = True
            else:
                break

        # Solve any singles before moving on to more advanced techniques
        if affected_grid:
            return

        ## Hidden/naked N-sets
        # Find naked pairs
        for u in self.rows + self.columns + self.boxes:
            affected_grid |= u.find_naked_pairs()

        # Find hidden pairs
        for u in self.rows + self.columns + self.boxes:
            affected_grid |= u.find_hidden_pairs()

        # Find naked triples
        for u in self.rows + self.columns + self.boxes:
            affected_grid |= u.find_naked_triples()

        # Find hidden triples
        for u in self.rows + self.columns + self.boxes:
            affected_grid |= u.find_hidden_triples()

        if affected_grid:
            return

        # Find naked quadruples
        for u in self.rows + self.columns + self.boxes:
            affected_grid |= u.find_naked_quadruples()

        # Find hidden quadruples
        for u in self.rows + self.columns + self.boxes:
            affected_grid |= u.find_hidden_quadruples()

        if affected_grid:
            return

        ## N-fishes
        # Find X-Wings
        if self.find_x_wings():
            return

        # TODO: Find Swordfishes

        # Perform more logic
        return

    def solve(self, moves_file=None):
        if not self.is_valid():
            logging.error("Puzzle is invalid!")
            return

        if moves_file:
            # Truncate move stack file
            with open(moves_file, "w"):
                pass
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
            elif moves_file:
                # Write the move stack to file
                with open(moves_file, "a") as f_out:
                    for m in self.move_stack[current_moves:]:
                        f_out.write("{}\n".format(m))
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
    parser.add_argument("--dump_moves", nargs="?", dest="moves_file", const="moves.log", type=str,
            help="Write the move stack to file [Default: False]")
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
        p.solve(args.moves_file)
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
