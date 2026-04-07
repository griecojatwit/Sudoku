import copy
import time

def sudokuValidator(state):
    rows = [set() for _ in range(9)]
    cols = [set() for _ in range(9)]
    subStates = [set() for _ in range(9)]

    for row in range(9):
        for col in range(9):
            value = state[row][col]

            if value == 0:
                continue

            if value in rows[row]:
                return False
            rows[row].add(value)

            if value in cols[col]:
                return False
            cols[col].add(value)

            idx = (row // 3) * 3 + (col // 3)
            if value in subStates[idx]:
                return False
            subStates[idx].add(value)

    return True

def sudokuSolution(state):
    rowSums = [sum(row) for row in state]
    columnSums = [sum(col) for col in zip(*state)]

    subStatesSums = []
    for row in range(0, 9, 3):
        for col in range(0, 9, 3):
            currentSum = 0
            for i in range(row, row + 3):
                for j in range(col, col + 3):
                    currentSum += state[i][j]
            subStatesSums.append(currentSum)

    for i in rowSums:
        if i != 45:
            return False

    for j in columnSums:
        if j != 45:
            return False

    for k in subStatesSums:
        if k != 45:
            return False

    return True

def possibleValues(state):
    possible = {}
    for i in range(9):
        for j in range(9):
            if state[i][j] == 0:
                possible[(i, j)] = []

    for i in range(9):
        for j in range(9):
            for k in range(1, 10):
                if state[i][j] == 0:
                    savedState = copy.deepcopy(state)
                    savedState[i][j] = k
                    if sudokuValidator(savedState):
                        possible[(i, j)].append(k)

    return possible

def possibleNeighbors(state, neighbors):
    possible = {}
    for (i, j) in neighbors:
        if state[i][j] == 0:
            possible[(i, j)] = []
            for k in range(1, 10):
                savedState = copy.deepcopy(state)
                savedState[i][j] = k
                if sudokuValidator(savedState):
                    possible[(i, j)].append(k)
    return possible

def getNeighbors(i, j):
    neighbors = set()

    for col in range(9):
        if col != j:
            neighbors.add((i, col))

    for row in range(9):
        if row != i:
            neighbors.add((row, j))

    boxRow = (i // 3) * 3
    boxCol = (j // 3) * 3
    for r in range(boxRow, boxRow + 3):
        for c in range(boxCol, boxCol + 3):
            if (r, c) != (i, j):
                neighbors.add((r, c))

    return neighbors

def findMRV(values):
    return min(values, key=lambda cell: len(values[cell]))

def forwardSelection(state, stats):
    if sudokuSolution(state):
        return state

    values = possibleValues(state)

    if any(v == [] for v in values.values()):
        return None

    for (i, j), candidates in values.items():
        stats['nodes'] += 1
        for val in candidates:
            savedState = copy.deepcopy(state)
            savedState[i][j] = val

            neighbors = getNeighbors(i, j)
            newValues = possibleNeighbors(savedState, neighbors)

            if not any(v == [] for v in newValues.values()):
                result = forwardSelection(savedState, stats)
                if result is not None:
                    return result
            stats['backtracks'] += 1
        break

    return None

def backwardSelection(state, stats):
    if sudokuSolution(state):
        return state

    for i in range(9):
        for j in range(9):
            if state[i][j] == 0:
                stats['nodes'] += 1
                for val in range(1, 10):
                    savedState = copy.deepcopy(state)
                    savedState[i][j] = val

                    if sudokuValidator(savedState):
                        result = backwardSelection(savedState, stats)
                        if result is not None:
                            return result
                        stats['backtracks'] += 1

                return None

    return None

def minimumSelection(state, stats):
    if sudokuSolution(state):
        return state

    values = possibleValues(state)

    if any(v == [] for v in values.values()):
        return None

    (i, j) = findMRV(values)
    stats['nodes'] += 1

    for val in values[(i, j)]:
        savedState = copy.deepcopy(state)
        savedState[i][j] = val

        neighbors = getNeighbors(i, j)
        newValues = possibleNeighbors(savedState, neighbors)

        if not any(v == [] for v in newValues.values()):
            result = forwardSelection(savedState, stats)
            if result is not None:
                return result
        stats['backtracks'] += 1

    return None

def parsePuzzle(puzzleStr):
    grid = []
    for i in range(0, 81, 9):
        row = [int(x) for x in puzzleStr[i:i+9]]
        grid.append(row)
    return grid

def benchmark(filename):
    solvers = [
        ('Backtracking', backwardSelection),
        ('Forward Checking', forwardSelection),
        ('MRV', minimumSelection),
    ]

    totals = {
        name: {'time': 0, 'nodes': 0, 'backtracks': 0, 'solved': 0}
        for name, _ in solvers
    }

    puzzleCount = 0

    with open(filename, 'r') as f:
        for line in f:
            parts = line.strip().split()
            puzzleStr = parts[1]

            state = parsePuzzle(puzzleStr)
            puzzleCount += 1

            for name, solver in solvers:
                stats = {'nodes': 0, 'backtracks': 0}
                stateCopy = copy.deepcopy(state)

                start = time.perf_counter()
                result = solver(stateCopy, stats)
                end = time.perf_counter()

                totals[name]['time'] += (end - start) * 1000
                totals[name]['nodes'] += stats['nodes']
                totals[name]['backtracks'] += stats['backtracks']
                if result is not None:
                    totals[name]['solved'] += 1

    print(f"\n{'Solver':<22} {'Avg Time (ms)':>15} {'Avg Nodes':>12} {'Avg Backtracks':>18} {'Solved %':>10}")
    print('-' * 80)

    for name in totals:
        avgTime = totals[name]['time'] / puzzleCount
        avgNodes = totals[name]['nodes'] / puzzleCount
        avgBacktracks = totals[name]['backtracks'] / puzzleCount
        solvedPct = (totals[name]['solved'] / puzzleCount) * 100

        print(f"{name:<22} {avgTime:>15.2f} {avgNodes:>12.2f} {avgBacktracks:>18.2f} {solvedPct:>9.2f}%")

if __name__ == '__main__':
    benchmark('Puzzles/easy.txt')