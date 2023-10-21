import copy
import math
import sys
import time

from typing import List

import numpy as np

import readdata

bi, si, delta, c_ = readdata.get_data()


# 用户类
class user:
    def __init__(self, s_i: list, cite_i: list, b_i: float):
        self.delta = cite_i  # 部署约束
        self.S_i = s_i  # 用户需求
        self.B_i = b_i  # 用户出价
        self.index = 0  # 用户编号
        self.allocated = False  # 是否被分配


# 用户集类
class User_i:
    # 初始化
    def __init__(self, user_: List[user]):
        self.user = user_
        for ii in range(0, len(user_)):
            user_[ii].index = ii

    # 删除用户
    def delete_user(self, index_: int):
        for ii in self.user:
            if ii.index == index_:
                del self.user[self.user.index(ii)]

    # 获取用户
    def get_user(self, indexs: int):
        for us in self.user:
            if us.index == indexs:
                return us


class Server:  # 服务器类
    M = []  # 服务器集合
    R = []  # 服务器拥有的资源种类
    C_j = []
    B = 0

    # 初始化
    def __init__(self, r_: list, b):
        self.B = b
        self.R = r_

    # 添加服务器
    def add_M(self, capacities: list):
        self.C_j.append(capacities)  # 服务器的资源容量
        self.M.append(self)  # 服务器数量


if __name__ == '__main__':
    # 创建用户——————————————————————————————————————————————————
    _user_ = []
    for i in range(len(bi)):
        uuu = user(si[i], delta[i], bi[i])
        _user_.append(uuu)
    # 总用户集
    User = User_i(_user_)
    # 创建服务器————————————————————————————————————————————————
    server = Server(["CPU核数", "内存", "硬盘"], 10000)
    for j in range(len(c_)):
        server.add_M(c_[j])
    # 初始化数据————————————————————————————————————————————————
    gp = [0.0] * len(server.R)  # 全局价格
    cite = 0.1  # 全局价格步进
    A = copy.deepcopy(User)  # 初始化活跃用户集合A
    X = [[0 for i in range(len(server.M))] for j in range(len(User.user))]  # 判决矩阵X
    pay = 0  # 总收益pay
    P = [0] * len(User.user)  # 用户支付集合
    feasible = False  # 可行性指标
    # ——————————————————————————————————————————————————————————————
    # 可行性判断
    start = time.perf_counter()
    # 计算总出价
    sum_b = 0
    for i in User.user:
        sum_b += i.B_i
    # 判断可行性
    if sum_b < server.B:
        print("Server's B too high, Not feasible____________________")
        end = time.perf_counter()
        print('执行时间为：', end - start)
        sys.exit()

    while (feasible is False) & (len(A.user) != 0):
        # 计算价格提升参数
        for r in range(len(server.R)):
            sum_si = 0
            sum_cj = 0
            # 计算用户对r资源的总需求
            for i in A.user:
                sum_si += i.S_i[r]
            # 计算服务器r资源的总容量
            for c in c_:
                sum_cj = sum_cj + c[r]
            # 计算r资源的价格提升参数
            lambda_b = (sum_si - sum_cj) / sum_cj
            lambda__ = max(lambda_b, 0)
            # 计算r资源的全局价格
            gp[r] += ((math.e ** lambda__) * cite)
            # gp[r] += cite
        # 更新活跃用户集A
        dele = []  # 将要被删除的用户集合
        for i in A.user:
            # 计算gp*Si
            gp_s = 0
            # 计算i用户的r资源定价
            for r in range(len(server.R)):
                gp_s += (gp[r] * i.S_i[r])
            # 判断i用户出价是否达标
            if i.B_i < gp_s:
                dele.append(i.index)
        # 删除未达标用户
        if len(dele) != 0:
            for z in dele:
                A.delete_user(z)

        # 活跃用户为空，退出
        if len(A.user) == 0:
            print('Has delete all, Not feasible________________________')
            feasible = False
            break

        # 计算服务器j可分配用户集Aj
        A_j = []
        for j in range(len(server.M)):
            Aj_ = []
            for i in A.user:
                if i.delta[j] == 1:
                    Aj_.append(i.index)
            A_j.append(Aj_)

        # print('A_j = ', A_j)
        # 准备进行分配
        C_ = copy.deepcopy(server.C_j)

        # 计算S_i的模
        S_i = []
        for i in A.user:
            sum_sr = 0
            # 计算用户i各资源的模
            for r in range(0, len(server.R)):
                sum_c_j = 0
                for j in server.C_j:
                    sum_c_j += j[r]
                _si_ = i.S_i[r] / sum_c_j
                sum_sr += (_si_ ** 2)
            S_i.append([i.index, abs(sum_sr ** 0.5)])
        # 将S_i降序
        sorted_S_i = sorted(S_i, key=lambda y: y[1], reverse=True)
        idx_S_i = [i[0] for i in sorted_S_i]
        # S_i = [i[1] for i in sorted_S_i]
        # ----------------------------------------
        no = 0
        for iu in idx_S_i:
            # 将A_j的模升序
            sum_aj = [[]] * len(server.M)
            for j in range(len(server.M)):
                sum_aj[j] = [j, len(A_j[j])]
            # 开始升序
            sorted_aj = sorted(sum_aj, key=lambda x: x[1])
            idx_a_j = [i[0] for i in sorted_aj]
            # 开始分配
            for j in idx_a_j:
                # 计算是否可以分配
                if A.get_user(iu).delta[j] == 1:
                    # 计算服务器j资源是否足够
                    feasi = True
                    for r in range(0, len(server.R)):
                        if C_[j][r] - A.get_user(iu).S_i[r] < 0:
                            feasi = False
                    # 计算分配和支付
                    if feasi:
                        # 确定决策矩阵X
                        X[iu][j] = 1
                        # 计算定价pi
                        pi = 0
                        for r_r in range(len(server.R)):
                            # 计算用户iu对r_r资源的支付
                            pi += (gp[r_r] * A.get_user(iu).S_i[r_r])
                            # 更新服务器资源容量
                            C_[j][r_r] -= A.get_user(iu).S_i[r_r]
                        # 确定用户支付
                        P[iu] = round(pi)
                        # 更新收益
                        pay = pay + pi
                        # 更新活跃用户集A和可分配用户集
                        for jn in range(len(server.M)):
                            if A.get_user(iu).delta[jn] == 1:
                                A.get_user(iu).delta[jn] = 0
                            for ui in range(len(A_j[jn])):
                                if A_j[jn][ui] == iu:
                                    del A_j[jn][ui]
                                    break
                        break
        if pay >= server.B:
            feasible = True
        else:
            print('pay = ', pay, ',未达到目标收益，进入下一轮')
            X = [[0 for i in range(len(server.M))] for j in range(len(User.user))]
            pay = 0
            P = [0] * len(User.user)
            A = copy.deepcopy(User)
    if feasible is False:
        end = time.perf_counter()
        print('Not feasible!!!')
    else:
        end = time.perf_counter()
        print('X = ', X)
        print('P = ', P)
        print('收益 pay = ', round(pay))
        sumbi = 0
        ids = []
        sumcpu = 0
        sumram = 0
        sumhardware = 0
        for i in range(len(P)):
            if sum(X[i]) != 0:
                for zz in X[i]:
                    if zz == 1:
                        sumbi = bi[i] + sumbi
                        ids.append(i)
                        sumcpu += si[i][0]
                        sumram += si[i][1]
                        sumhardware += si[i][2]
        cpus = 0
        rams = 0
        hardwares = 0
        for cap in c_:
            cpus += cap[0]
            rams += cap[1]
            hardwares += cap[2]
        print('资源利用率为： CPU： %f  RAM: %f  Hardware: %f' % (sumcpu / cpus, sumram / rams, sumhardware / hardwares))
        print('社会福利为：', sumbi)
        print('全局价格为：CPU = %f RAM = %f Hardware = %f' % (gp[0], gp[1], gp[2]))
    print('执行时间为：', end - start)
