import copy

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
    possibleValues = {}
    for i in range(9):
        for j in range(9):
            if state[i][j] == 0:
                possibleValues[i][j] = []

    for i in range(9):
        for j in range(9):
            for k in range(1, 10):
                if state[i][j] == 0:
                    savedState = copy.deepcopy(state)
                    savedState[i][j] = k
                    if sudokuValidator(savedState):
                        possibleValues[i][j].append(k)

    return possibleValues

def forwardSelection(state):

    while not sudokuSolution(state):
        values = possibleValues(state)
        for i, j, value in values.items():
            savedState = copy.deepcopy(state)
            savedState[i][j] = value
            newValues = possibleValues(savedState)
            if [] not in newValues:
                state = copy.deepcopy(savedState)
                break

    return state

if __name__ == '__main__':
    mat = [
        [9, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 5, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9]
    ]

    print(possibleValues(mat))