import csv
import random
import time
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED, ProcessPoolExecutor


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

    subStateSums = []
    for row in range(0, 9, 3):
        for col in range(0, 9, 3):
            currentSum = 0
            for i in range(row, row + 3):
                for j in range(col, col + 3):
                    currentSum += state[i][j]
            subStateSums.append(currentSum)

    for i in rowSums:
        if i != 45:
            return False

    for j in columnSums:
        if j != 45:
            return False

    for k in subStateSums:
        if k != 45:
            return False

    return True


def possibleValues(state):
    possible = {}
    for i in range(9):
        for j in range(9):
            if state[i][j] == 0:
                possible[(i, j)] = []
                original = state[i][j]
                for k in range(1, 10):
                    state[i][j] = k
                    if sudokuValidator(state):
                        possible[(i, j)].append(k)
                state[i][j] = original
    return possible


def possibleNeighbors(state, neighbors):
    possible = {}
    for (i, j) in neighbors:
        if state[i][j] == 0:
            possible[(i, j)] = []
            for k in range(1, 10):
                state[i][j] = k
                if sudokuValidator(state):
                    possible[(i, j)].append(k)
            state[i][j] = 0
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
        return True

    values = possibleValues(state)

    if any(v == [] for v in values.values()):
        return None

    for (i, j), candidates in values.items():
        stats['nodes'] += 1
        for val in candidates:
            state[i][j] = val

            neighbors = getNeighbors(i, j)
            newValues = possibleNeighbors(state, neighbors)

            if not any(v == [] for v in newValues.values()):
                result = forwardSelection(state, stats)
                if result is not None:
                    return True

            state[i][j] = 0
            stats['backtracks'] += 1
        break

    return None


def backwardSelection(state, stats):
    if sudokuSolution(state):
        return True

    for i in range(9):
        for j in range(9):
            if state[i][j] == 0:
                stats['nodes'] += 1
                for val in range(1, 10):
                    state[i][j] = val
                    if sudokuValidator(state):
                        if backwardSelection(state, stats):
                            return True
                        stats['backtracks'] += 1

                state[i][j] = 0
                return None

    return None


def minimumSelection(state, stats):
    if sudokuSolution(state):
        return True

    values = possibleValues(state)

    if any(v == [] for v in values.values()):
        return None

    (i, j) = findMRV(values)
    stats['nodes'] += 1

    for val in values[(i, j)]:
        state[i][j] = val

        neighbors = getNeighbors(i, j)
        newValues = possibleNeighbors(state, neighbors)

        if not any(v == [] for v in newValues.values()):
            result = minimumSelection(state, stats)
            if result is not None:
                return True

        state[i][j] = 0
        stats['backtracks'] += 1

    return None


def parsePuzzle(puzzleStr):
    grid = []
    for i in range(0, 81, 9):
        row = [int(x) for x in puzzleStr[i:i + 9]]
        grid.append(row)
    return grid


def solverWorker(idx, workerCount, sampledLines, solvers, puzzleCount):
    totals = [[[0 for a in range(4)] for b in range(len(solvers))] for c in range(puzzleCount)]
    print(f"worker {idx} started!")
    for i, line in enumerate(sampledLines):
        if (i % workerCount != idx):
            continue
        print(f"puzzle {i} started")
        parts = line.strip().split()
        puzzleStr = parts[1]

        for solverNum, solver in enumerate(solvers):
            stats = {'nodes': 0, 'backtracks': 0}
            state = parsePuzzle(puzzleStr)

            start = time.perf_counter()
            result = solver(state, stats)
            end = time.perf_counter()

            totals[i][solverNum][0] = (end - start)
            print(f"worker: {idx}    puzzle: {i}    solver: {solverNum}    time: {totals[i][solverNum][0]:0.2f}")
            totals[i][solverNum][1] = stats['nodes']
            totals[i][solverNum][2] = stats['backtracks']
            if result is True:
                totals[i][solverNum][3] = result
        print(f"Puzzle {i} solved.")
    print(f"worker {idx} finished!")
    return totals


def consolidateTotals(a, b):
    for i in range(len(a)):
        for j in range(len(a[i])):
            for k in range(len(a[i][j])):
                a[i][j][k] += b[i][j][k]
    return a


def totalTotals(totals, solver, data):
    dataSum = 0
    for i in range(len(totals)):
        dataSum += totals[i][solver][data]
    return dataSum


def exportTotalsCsv(totals, sampledLines, solvers, filename="results.csv"):
    solverNames = ["Backtracking", "Forward Checking", "MRV"]

    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)

        header = ["Puzzle ID", "Puzzle String"]
        for name in solverNames:
            header += [f"{name} Time", f"{name} Nodes", f"{name} Backtracks", f"{name} Solved"]
        writer.writerow(header)

        for i, line in enumerate(sampledLines):
            puzzleStr = line.strip().split()[1]
            row = [i, puzzleStr]
            for s in range(len(solvers)):
                timeVal, nodes, backtracks, solved = totals[i][s]
                row += [f"{timeVal:.4f}", nodes, backtracks, int(solved is True)]
            writer.writerow(row)

    print(f"Exported to {filename}")


def benchmark(filename):
    solvers = [backwardSelection, forwardSelection, minimumSelection]

    with open(filename, 'r') as f:
        allLines = [line for line in f if line.strip()]

    puzzleCount = 100
    puzzleCount = min(puzzleCount, len(allLines))
    sampledLines = random.sample(allLines, puzzleCount)

    workerCount = 12

    futures = []
    with ProcessPoolExecutor(max_workers=workerCount) as executor:
        for i in range(workerCount):
            futures.append(executor.submit(solverWorker, i, workerCount, sampledLines, solvers, puzzleCount))

        wait(futures)
        executor.shutdown()

    totals = [[[0 for a in range(4)] for b in range(len(solvers))] for c in range(puzzleCount)]
    for futureNum in range(len(futures)):
        futureResult = futures[futureNum].result()
        consolidateTotals(totals, futureResult)

    exportTotalsCsv(totals, sampledLines, solvers, "sudoku_results.csv")

    totalsFinal = {
        "Backtracking": {'time': 0, 'nodes': 0, 'backtracks': 0, 'solved': 0},
        "Forward Checking": {'time': 0, 'nodes': 0, 'backtracks': 0, 'solved': 0},
        "MRV": {'time': 0, 'nodes': 0, 'backtracks': 0, 'solved': 0}
    }

    totalsFinal["Backtracking"]['time'] = totalTotals(totals, 0, 0) / puzzleCount
    totalsFinal["Backtracking"]['nodes'] = totalTotals(totals, 0, 1) / puzzleCount
    totalsFinal["Backtracking"]['backtracks'] = totalTotals(totals, 0, 2) / puzzleCount
    totalsFinal["Backtracking"]['solved'] = totalTotals(totals, 0, 3) / puzzleCount

    totalsFinal["Forward Checking"]['time'] = totalTotals(totals, 1, 0) / puzzleCount
    totalsFinal["Forward Checking"]['nodes'] = totalTotals(totals, 1, 1) / puzzleCount
    totalsFinal["Forward Checking"]['backtracks'] = totalTotals(totals, 1, 2) / puzzleCount
    totalsFinal["Forward Checking"]['solved'] = totalTotals(totals, 1, 3) / puzzleCount

    totalsFinal["MRV"]['time'] = totalTotals(totals, 2, 0) / puzzleCount
    totalsFinal["MRV"]['nodes'] = totalTotals(totals, 2, 1) / puzzleCount
    totalsFinal["MRV"]['backtracks'] = totalTotals(totals, 2, 2) / puzzleCount
    totalsFinal["MRV"]['solved'] = totalTotals(totals, 2, 3) / puzzleCount

    print(f"\n{'Solver':<22} {'Avg Time (s)':>15} {'Avg Nodes':>12} {'Avg Backtracks':>18} {'Solved %':>10}")
    print('-' * 80)

    for name in totalsFinal:
        avgTime = totalsFinal[name]['time']
        avgNodes = totalsFinal[name]['nodes']
        avgBacktracks = totalsFinal[name]['backtracks']
        solvedPct = totalsFinal[name]['solved'] * 100

        print(f"{name:<22} {avgTime:>15.2f} {avgNodes:>12.2f} {avgBacktracks:>18.2f} {solvedPct:>9.2f}%")


if __name__ == '__main__':
    benchmark('Puzzles/diabolical.txt')
