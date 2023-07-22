# 基于随机算法的模版AI
# 此处采取的算法为优先在己方领域下, 己方满则在对方领域随机下

# 参赛队伍的AI要求:
#
# 须写在Player类里
#
# 须实现两个方法:
#
# __init__(self, isFirst, array):
#   -> 初始化
#   -> 参数: isFirst是否先手, 为bool变量, isFirst = True 表示先手
#   -> 参数: array随机序列, 为一个长度等于总回合数的list
#
# output(self, currentRound, board, mode):
#   -> 给出己方的决策(下棋的位置或合并的方向)
#   -> 参数: currentRound当前轮数, 为从0开始的int
#   -> 参数: board棋盘对象
#   -> 参数: mode模式, mode = 'position' 对应位置模式, mode = 'direction' 对应方向模式, 如果为 '_position' 和 '_direction' 表示在对应模式下己方无法给出合法输出
#   -> 返回: 位置模式返回tuple (row, column), row行, 从上到下为0到3的int; column列, 从左到右为0到7的int
#   -> 返回: 方向模式返回direction = 0, 1, 2, 3 对应 上, 下, 左, 右
#   -> 返回: 在己方无法给出合法输出时, 对返回值不作要求
#
# 其余的属性与方法请自行设计


# 正文如下：
class Stack:
    def __init__(self):
        self.items = []

    def isEmpty(self):
        return self.items == []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        return self.items.pop()

    def peek(self):
        return self.items[len(self.items) - 1]

    def size(self):
        return len(self.items)


class Player:
    def __init__(self, isFirst, array):
        # 初始化
        self.isFirst = isFirst
        self.array = array
        self.board = None
        self.best_direction = None
        self.best_position = None
        self.depth = 3
        self.another = None  # 轮到己方下棋时，若下在己方棋盘则应该下的位置
        self.current_round = 0  # 表示当前进行的回合数
        self.prev_stack = Stack()  # 用于回溯之前的棋盘，即用于cancel move

    def output(self, currentRound, board, mode):
        self.board = board.copy()  # 注意：不能用deepcopy，会报错，chessboard类的copy方法已经是深拷贝
        self.current_round = currentRound

        if mode == 'position':  # 给出己方下棋的位置
            self.another = self.board.getNext(self.isFirst, currentRound)
            return self.choose_position()
        elif mode == 'direction':  # 给出己方合并的方向
            return self.choose_direction()
        else:  # mode参数为_position或者_direction
            return

    def choose_position(self):
        # 优先进攻，其次下在自己这里，其次下在对方那里（具体下在哪个位置？需要决策！）
        self.best_position = self.another
        if self.best_position != ():
            return self.best_position
        else:  # self.another可能为()（己方棋盘满了）
            available = self.board.getNone(not self.isFirst)  # 对方的允许落子点
            if not available:  # 整个棋盘已满
                return None
            else:
                from random import choice
                return choice(available)

    def choose_direction(self):
        self.best_direction = None
        self.get_ChoiceValue(self.depth, -1000000000, 1000000000, -1, self.isFirst, 'direction')
        if self.best_direction is not None:
            return self.best_direction
        # 若迭代深搜得出的最佳方向是非法的，则随机选择
        from random import shuffle
        directionList = [0, 1, 2, 3]
        shuffle(directionList)
        for direction in directionList:
            if self.board.move(self.isFirst, direction):
                return direction

    def get_BoardValue(self, player):  # player=-1时为己方，player=1时为对方
        isFirst = self.isFirst if player == -1 else (not self.isFirst)  # 表示当前玩家是先手or后手
        selfvalue = self.estimateValue(isFirst)
        enemyvalue = self.estimateValue(not isFirst)
        return selfvalue - enemyvalue

    # 运用negamax算法和alpha-beta剪枝获取这一步决策的value值
    def get_ChoiceValue(self, depth, alpha, beta, player, isFirst, mode):  # isFirst表示当前player是否为先手(bool)
        if depth == 0:
            return self.get_BoardValue(player)
        if self.current_round >= len(self.array) - 3:  # 迭代到的回合数快超过总回合数时，剪掉搜索枝
            return self.get_BoardValue(player)

        if mode == 'direction':
            # 以下是防守主义：若四个方向合并得到的盘面value一样则优先选择往己方的后方合并。
            if isFirst:
                directionList = [0, 1, 3, 2]
            else:
                directionList = [0, 1, 2, 3]

            for direction in directionList:
                current_board = self.board.copy()
                if self.board.move(isFirst, direction):  # 此合并方向合法时make move
                    self.prev_stack.push(current_board)
                    # 进行递归
                    if isFirst:  # 本层player为先手方，即下一步是另一方选择方向进行合并
                        value = -self.get_ChoiceValue(depth - 1, -beta, -alpha, -player, not isFirst, 'direction')
                    else:  # 本层player为后手方，即下一步是另一方选择位置下棋
                        self.current_round += 1  # 下一步就是下一回合了
                        value = -self.get_ChoiceValue(depth - 1, -beta, -alpha, -player, not isFirst, 'position')

                    self.board = self.prev_stack.pop()  # cancel move

                    # 进行alpha-beta剪枝
                    if value >= beta:
                        if depth == self.depth:
                            self.best_direction = direction
                        return beta
                    if value > alpha:
                        if depth == self.depth:  # 回合数为现实回合时选择best direction
                            self.best_direction = direction
                        alpha = value

                else:  # 此合并方向非法时，继续尝试下一个方向
                    self.board = current_board  # if判断时移动了盘面，应及时恢复盘面
                    continue

            return alpha

        else:  # mode == 'position'
            another = self.board.getNext(isFirst, self.current_round)
            if another != ():
                self.board.add(isFirst, another)
            else:
                available = self.board.getNone(not isFirst)
                if available:
                    from random import choice
                    self.board.add(isFirst, choice(available))
            isFirst = not isFirst  # 交换下棋方
            another = self.board.getNext(isFirst, self.current_round)
            if another != ():
                self.board.add(isFirst, another)
            else:
                available = self.board.getNone(not isFirst)
                if available:
                    from random import choice
                    self.board.add(isFirst, choice(available))
            isFirst = not isFirst  # 交换下棋方

            # 双方下棋结束，当前盘面为双方add后的盘面

            # 以下是防守主义：若四个方向合并得到的盘面value一样则优先选择往己方的后方合并。
            if isFirst:
                directionList = [0, 1, 3, 2]
            else:
                directionList = [0, 1, 2, 3]

            for direction in directionList:
                current_board = self.board.copy()
                if self.board.move(isFirst, direction):  # 此合并方向合法时make move
                    self.prev_stack.push(current_board)
                    # 进行递归
                    if isFirst:  # 本层player为先手方，即下一步是另一方选择方向进行合并
                        value = -self.get_ChoiceValue(depth - 1, -beta, -alpha, -player, not isFirst, 'direction')
                    else:  # 本层player为后手方，即下一步是另一方选择位置下棋
                        self.current_round += 1  # 下一步就是下一回合了，所以要更新
                        value = -self.get_ChoiceValue(depth - 1, -beta, -alpha, -player, not isFirst, 'position')

                    self.board = self.prev_stack.pop()  # cancel move

                    # 进行alpha-beta剪枝
                    if value >= beta:
                        if depth == self.depth:  # 回合数为现实回合时选择best direction
                            self.best_direction = direction
                        return beta
                    if value > alpha:
                        if depth == self.depth:
                            self.best_direction = direction
                        alpha = value

                else:  # 此合并方向非法时，继续尝试下一个方向
                    self.board = current_board
                    continue

            return alpha

    # 此函数为客观评价函数，即输入参数 阵营(isFirst) ，输出该阵营在此棋面下的value，不附带有主观性，敌我均可用
    # 将isFirst代表的阵营称为对象方，另一方则称为对方（这也深刻体现了该函数的客观性）
    # isFirst为bool值，isFirst = True相当于isFirst = 1，isFirst = False相当于isFirst = -1
    def estimateValue(self, isFirst):  # 计算先手或后手方的棋面value
        monotonicityWeight = 0.23  # 单调性权重
        emptyCellsWeight = 0.21  # 空格数权重
        figureWeight = 0.42  # 棋子级别权重

        value = monotonicityWeight * self.monotonicityValue(isFirst) + \
                emptyCellsWeight * self.emptyCellsValue(isFirst) + \
                figureWeight * self.figureValue(isFirst)
        return value

    def figureValue(self, isFirst):  # 将对象方棋子的级别加权求和,得到棋子级别大小和数量提供的value
        selfside = isFirst
        selfscore = self.board.getScore(selfside)
        figurevalue = 0
        # 棋子级别越高，函数的增长速度越快
        for i in selfscore:
            if i >= 7:
                figurevalue += 3 ** i
            elif i >= 5:
                figurevalue += 2 ** i
            elif i >= 3:
                figurevalue += i * 2
        return figurevalue

    def emptyCellsValue(self, isFirst):  # 计算对象方空位数value
        selfSide = isFirst
        selfEmptyCellsNums = len(self.board.getNone(selfSide))  # 对象方空位数
        emptyCellsvalue = selfEmptyCellsNums ** 0.5
        return emptyCellsvalue

    # 当一行或者一列内的棋子级别是单调增加或者减少时，更容易进行合并，因此好的单调性会贡献value
    # 对于对象方棋盘内的每一行和每一列进行单调性评估，仅当该列或行的棋子均为对象方棋子且级别单调变化时，才考虑其value贡献
    def monotonicityValue(self, isFirst):
        selfSide = isFirst
        monotonicityvalue = 0
        # 遍历每一行
        for row in range(4):
            # 引入单调性因子，表征单行或者单列的单调性好坏
            monotonicityFactor = 0
            # 列数从对象方棋盘的最左列到最右列
            col = (1 - isFirst) * 4
            while col < (1 - isFirst) * 4 + 3:
                # 当前格子的级别
                currentValue = self.board.getValue((row, col))
                # 下一格的坐标
                nextrow = row
                nextcol = col + 1
                # 有内鬼，则终止交易，转至下一行
                if selfSide != self.board.getBelong((row, col)) or \
                        selfSide != self.board.getBelong((nextrow, nextcol)):
                    monotonicityFactor = 0
                    break  # 只是跳出while循环
                # 无内鬼，计算下一格的级别，单调性因子变化
                else:
                    nextValue = self.board.getValue((nextrow, nextcol))
                    monotonicityFactor += nextValue - currentValue
                # 列数加一，继续下一格
                col += 1
            # 此行的单调性因子计算完毕，加至value中
            monotonicityvalue += abs(monotonicityFactor)
        # 遍历对象方棋盘每一列
        for col in range((1 - isFirst) * 4, (1 - isFirst) * 4 + 4):
            monotonicityFactor = 0
            row = 0
            while row < 3:
                currentValue = self.board.getValue((row, col))
                nextrow = row + 1
                nextcol = col
                if selfSide != self.board.getBelong((row, col)) or \
                        selfSide != self.board.getBelong((nextrow, nextcol)):
                    monotonicityFactor = 0
                    break
                else:
                    nextValue = self.board.getValue((nextrow, nextcol))
                    monotonicityFactor += nextValue - currentValue
                row += 1
            monotonicityvalue += abs(monotonicityFactor)
        return monotonicityvalue
