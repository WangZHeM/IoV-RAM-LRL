import copy
import sys

import numpy
import time

from typing import List

import numpy as np

import readdata

# 读入随机生成的数据!(规模大)
# from experiment_data import user_size, res_size, bids, caps, S, _delta_, server_size
#
# bi = list(bids.values())
# si = list(S.values())
# si = np.array(si)
# si = si.reshape(user_size, res_size)
# delta = _delta_
# c_ = list(caps.values())
# c_ = np.array(c_)
# c_ = c_.reshape(server_size, res_size)

bi, si, delta, c_ = readdata.get_data()


class user:
    def __init__(self, s_i: list, cite_i: list, b_i: float):
        self.delta = cite_i
        self.S_i = s_i
        self.B_i = b_i
        self._S_i = 0
        self.index = 0
        self.allocated = False


class User_i:
    def __init__(self, user_: List[user]):
        self.user = user_
        for ii in range(0, len(user_)):
            user_[ii].index = ii

    def delete_user(self, index_: int):
        for ii in self.user:
            if ii.index == index_:
                del self.user[self.user.index(ii)]


class Server:  # 服务器类
    M = []  # 服务器集合
    R = []  # 服务器拥有的资源种类
    C_j = []
    B = 0

    def __init__(self, r_: list):
        self.R = r_

    def add_M(self, capacities: list):
        self.C_j.append(capacities)  # 服务器的资源容量
        self.M.append(self)


def IS_FEASIBLE(u_: user, server_R: list, index_m, xx):
    flag_ = True
    for _r_ in range(len(server_R)):
        if (u_.S_i[_r_] > (server_R[_r_]) * xx) | (u_.delta[index_m] == 0) | u_.allocated:
            flag_ = False
            break
    return flag_


def get_di(user_: user, cpr: list, index_m):
    sum_r = 0
    for _r_ in range(len(cpr)):
        sum_r = user_.S_i[_r_] / cpr[_r_] + sum_r
    di = user_.B_i / (sum_r ** 0.5)
    return di


def G_win(users: User_i, server: Server):
    V_p = [0] * len(server.M)  # 总的Vp
    X_p = []  # 总的用户分配Xp
    for m in range(len(server.M)):
        C_p = list(c_[m])  # 物理机的资源容量集合
        _U_ = []  # 请求能被完全满足的用户集合U^
        _x_ = [0] * len(users.user)  # 判别矩阵x^
        for i in users.user:
            if IS_FEASIBLE(i, C_p, m, 1):
                _U_.append(i)
        # _U_ = User_i(_U_)
        # {first phase}________--
        _V_ = 0
        if len(_U_) > 0:
            j = 0
            max_bi = 0
            for i in _U_:
                if i.B_i > max_bi:
                    max_bi = i.B_i
                    j = i.index  # 确定 j
            _V_ = max_bi  # 确定 V^
            _x_[j] = 1  # 确定x^j
        # print(_x_)
        # print(_V_)
        # {Second phase}----------------------
        U_ = []  # 请求不超过资源有效容量一半的用户集U~
        x_ = [0] * len(users.user)  # 判别矩阵x~
        for i in _U_:
            if IS_FEASIBLE(i, C_p, m, 0.5):
                U_.append(i)
        dis = []
        # sorted_U_ = []  # 排好序的U~
        idx_dis = []
        if len(U_) != 0:
            for i in U_:
                dis.append([i.index, get_di(i, C_p, m)])
            sorted_dis = sorted(dis, key=lambda yy: yy[1], reverse=True)
            idx_dis = [i[0] for i in sorted_dis]
        # print(sorted_U_)
        # -------------------------------------------------
        U__ = []  # 选中的用户集合
        C_p_ = [0] * len(server.R)  # 资源容量Cp~
        flag = True
        # -------------------------------------------------
        while (len(idx_dis) != 0) & flag:
            for r in range(len(server.R)):
                if C_p_[r] > (C_p[r] / 2):
                    flag = False
            if flag:
                idx_i = idx_dis[0]
                x_[idx_i] = 1
                U__.append(users.user[idx_i])
                del idx_dis[0]
                for r in range(len(C_p)):
                    C_p_[r] = C_p_[r] + users.user[idx_i].S_i[r]
        # ---------------------------------------------------
        V_ = 0  # 社会福利V~
        C_p__ = [0] * len(server.R)  # 资源容量Cp-
        j_ = 0
        delta_j = [0] * len(server.R)  # delta_jr
        if len(U__) != 0:
            idx_ = 0
            for i in U__:
                if idx_ == len(U__) - 1:
                    j_ = i.index
                    break
                V_ = V_ + i.B_i
                for r in range(len(server.R)):
                    C_p__[r] = C_p__[r] + users.user[i.index].S_i[r]
                idx_ = idx_ + 1
            # -------------------------
            for r in range(len(server.R)):
                delta_j[r] = int(C_p[r] / 2) - C_p__[r]
            flag = True
            # -------------------------
            for r in range(len(server.R)):
                if users.user[j_].S_i[r] > delta_j[r]:
                    flag = False
                    break
            # -------------------------
            if flag:
                for r in range(len(server.R)):
                    delta_j[r] = users.user[j_].S_i[r]
            # -------------------------
            ss = 0
            for r in range(len(server.R)):
                ss = delta_j[r] / c_[m][r] + ss
            for disx in dis:
                if disx[0] == j_:
                    b_j_ = disx[1] * (ss ** 0.5)  # 计算bj-
                    V_ = V_ + b_j_
                    break
        # # {Third phase}
        if _V_ >= V_:
            V_p[m] = _V_
            X_p.append(_x_)
            print('————————')
            ssum = [0 for i in range(3)]
            for x1 in range(len(_x_)):
                if _x_[x1] == 1:
                    print("用户", x1, "已被分配")
                    for r in range(3):
                        ssum[r] = users.user[x1].S_i[r] + ssum[r]
                    users.user[x1].allocated = True
            print(ssum, C_p)
        else:
            V_p[m] = V_
            X_p.append(x_)
            print('————————')
            ssum = [0 for i in range(3)]
            for x2 in range(len(x_)):
                if x_[x2] == 1:
                    print("用户", x2, "已被分配")
                    for r in range(3):
                        ssum[r] = users.user[x2].S_i[r] + ssum[r]
                    users.user[x2].allocated = True
            print(ssum, C_p)
        # for xp in X_p[m]:
        #     if xp == 1:
        #         del U[X_p[m].index(xp)]
    return X_p, V_p


def G_getpayment(users: User_i, server: Server, u_back: User_i):
    payment = [0] * len(users.user)
    for i in users.user:
        if i.allocated:
            # l_b = i.S_i[0] * cpu + i.S_i[1] * ram + i.S_i[2] * hardware
            l_b = 0
            u_b = i.B_i
            while u_b - l_b >= 1:
                uus = copy.deepcopy(u_back)
                v_i_c = (u_b + l_b) / 2
                if users.user[i.index].allocated:
                    uus.user[i.index].B_i = v_i_c
                    x_p, v_p = G_win(uus, server)
                    if uus.user[i.index].allocated:
                        u_b = v_i_c
                    else:
                        l_b = v_i_c
            payment[i.index] = round(u_b)
            print(i.index, payment[i.index])
    return payment


if __name__ == '__main__':
    # 创建用户——————————————————————————————————————————————————
    _user_ = []
    for i_s in range(len(bi)):
        uuu = user(si[i_s], delta[i_s], bi[i_s])
        _user_.append(uuu)
    user_set = User_i(_user_)
    print("载入用户完成——————————")
    # 创建服务器————————————————————————————————————————————————
    servers = Server(["CPU核数", "内存", "硬盘"])
    for j_s in range(len(c_)):
        servers.add_M(c_[j_s])
    print("服务器载入完成——————————————————————")
    # 初始化----------------------------------------------------------------
    U = []  # 未被选上的用户集
    deltas = []  # 用户的delta集合
    rp_i = []  # 用户的rp_i集合
    user_back = copy.deepcopy(user_set)
    start = time.perf_counter()
    X_p_win, V_p_win = G_win(user_set, servers)
    pay = G_getpayment(user_set, servers, user_back)
    end = time.perf_counter()
    print("分配结果为：\r\n", X_p_win)
    print("pay = ", pay)
    print("社会福利为：", round(sum(V_p_win)))
    print("总支付为：", sum(pay))
    cpus = 0
    rams = 0
    hardware = 0
    for y in range(len(pay)):
        if pay[y] != 0:
            cpus += si[y][0]
            rams += si[y][1]
            hardware += si[y][2]
    sumc = 0
    sumram = 0
    sumhardware = 0
    for cc in c_:
        sumc += cc[0]
        sumram += cc[1]
        sumhardware += cc[2]
    print('资源利用率为： CPU：%f  RAM:%f  Hardware:%f' % (cpus / sumc, rams / sumram, hardware / sumhardware))
    print('执行时间为：', end - start)
