import docplex.mp.model as cpx
import pandas as pd
import numpy as np
import time

# 读入随机生成的数据!(规模大)
# from experiment_data import user_size, res_size, bids, caps, S, server_size, delta
import readdata

bi, si, _delta_, c_ = readdata.get_data()

# 写死的小例子, 用于测试 (规模小)
# user_size, ecs_size, req_size = 3, 2, 2  # 用户数量, ECS数量, 资源类型数量
# bids = {1: 15, 2: 10, 3: 20}  # 用户出价
#
# S = {(1, 1): 4, (1, 2): 1,  # 用户资源需求(N x R)
#      (2, 1): 4, (2, 2): 2,
#      (3, 1): 4, (3, 2): 4}
#
# caps = {(1, 1): 5, (1, 2): 50,  # 服务器资源容量(M x R)
#         (2, 1): 5, (2, 2): 50}
#
# delta = {(1, 1): 1, (1, 2): 0,  # 部署矩阵(N x M)
#          (2, 1): 1, (2, 2): 1,
#          (3, 1): 0, (3, 2): 1}

# 定义一些用于计算的全局变量！
ecs_size = len(c_)
user_size = len(bi)
res_size = len(c_[0])

bids = {}
for i in range(user_size):
    bids[i + 1] = bi[i]

S = {}
for i in range(user_size):
    for j in range(res_size):
        # f.write('d %d %d %d\n' % (i + 1, j + 1, num))
        S[(i + 1, j + 1)] = si[i][j]

caps = {}
for j in range(ecs_size):
    for r in range(res_size):
        caps[(j + 1, r + 1)] = c_[j][r]

delta = {}
for i in range(user_size):
    for j in range(ecs_size):
        delta[(i + 1, j + 1)] = _delta_[i][j]

alloc_ret, pay, social_welfare, total_pay = None, [0.0] * user_size, 0.0, 0.0
set_I, set_J, set_R = range(1, user_size + 1), range(1, ecs_size + 1), range(1, res_size + 1)
start_time, end_time = None, None


def opt_alloc():
    # 创建模型
    opt_model = cpx.Model(name="Binary Model")

    # 定义决策变量
    x_vars = {(i, j): opt_model.binary_var(name="x_{0}_{1}".format(i, j))
              for i in set_I for j in set_J}  # (N x M)
    # x_vars = {(i, j): opt_model.integer_var(name="x_{0}_{1}".format(i, j))
    #           for i in set_I for j in set_J}  # (N x M)

    # 添加约束条件(共2个)
    # 1.服务器资源容量约束!
    constraints1 = {(j, r): opt_model.add_constraint(
        ct=opt_model.sum(S[i, r] * delta[i, j] * x_vars[i, j] for i in set_I) <= caps[j, r],
        ctname="constraint_{0}_{1}".format(j, r)) for j in set_J for r in set_R}  # (M x R)
    # 2.每个用户的需求最多只能被某一台服务器满足!
    constraints2 = {i: opt_model.add_constraint(
        ct=opt_model.sum(delta[i, j] * x_vars[i, j] for j in set_J) <= 1,
        ctname="constraint_{0}".format(i)) for i in set_I}

    # 定义目标函数
    objective = opt_model.sum(bids[i] * delta[i, j] * x_vars[i, j] for i in set_I for j in set_J)

    # 最大化目标
    opt_model.maximize(objective)

    # 求解模型
    sol = opt_model.solve()
    # print(sol, end='')

    value = opt_model.objective_value
    print(value)
    # 处理求解结果: 将Cplex求解的结果转换成list并返回.
    opt_df = pd.DataFrame.from_dict(x_vars, orient="index", columns=["variable_object"])
    opt_df.index = pd.MultiIndex.from_tuples(opt_df.index, names=["column_i", "column_j"])
    opt_df.reset_index(inplace=True)
    opt_df["solution_value"] = opt_df["variable_object"].apply(lambda item: item.solution_value)
    opt_df.drop(columns=["variable_object"], inplace=True)
    tmp_alloc = opt_df['solution_value'].tolist()

    # 返回一个(N x M)的list, 即分配的结果!
    return value, np.array(tmp_alloc).reshape(user_size, ecs_size).astype(int).tolist()


def opt_vcg():
    global alloc_ret, pay, total_pay, social_welfare
    for i in range(user_size):
        if sum(alloc_ret[i]):  # 如果第i + 1个用户胜出了!
            # 首先保存第i + 1个用户的出价!
            tmp_bid = bids[i + 1]
            # 接着将第i + 1个用户的出价设置为一个任意负数(相当于是踢出了第i + 1个用户!)
            bids[i + 1] = -10000

            val, tmp_alloc = opt_alloc()  # 重新计算最优分配
            print("踢出第" + str(i + 1) + "个用户后的分配结果:", tmp_alloc)

            bids[i + 1] = tmp_bid  # 计算完后别忘了将第i + 1个用户添加回来!

            # # 计算不包含第i + 1个用户时的社会福利!
            # social_welfare_except_i = 0.0
            # for j in range(user_size):
            #     if sum(tmp_alloc[j]):
            #         social_welfare_except_i += bids[j + 1]

            # 计算第i + 1个用户的支付费用! (social_welfare是始终不变的哦.)
            pay[i] = round(val - (social_welfare - bids[i + 1]))
            print("因此第" + str(i + 1) + "个用户的支付费用: %s - %s = %s" %
                  (val, (social_welfare - bids[i + 1]), pay[i]))
            print("---------------------------------------------------------------")
            # 同时计算总的收益.
            total_pay += pay[i]


def opt_alloc_and_vcg():
    global alloc_ret, social_welfare, start_time, end_time

    # 计算算法的执行时间.
    start_time = time.perf_counter()

    # 包含所有用户时的最优分配!
    social_welfare, tmp_alloc = opt_alloc()
    alloc_ret = [[x_i_j for x_i_j in x_i] for x_i in tmp_alloc]
    print('包含所有用户时的最优分配:', alloc_ret)
    print()
    print("###################### 接着为所有获胜用户计算支付 ###################")

    # 计算总的社会福利.
    # for i in range(user_size):
    #     if sum(alloc_ret[i]):
    #         social_welfare += bids[i + 1]

    # 为所有获胜的用户计算vcg支付!
    opt_vcg()

    end_time = time.perf_counter()


# 计算服务器资源利用率! (计算的方式不唯一, 请先确定怎么计算后再修改代码!)
def calc_rur():
    allocated_res = [0] * res_size
    for i in range(user_size):
        if sum(alloc_ret[i]):
            for j in range(res_size):
                allocated_res[j] += S[(i + 1, j + 1)]

    server_caps = [0] * res_size
    for j in range(ecs_size):
        for r in range(res_size):
            server_caps[r] += caps[j + 1, r + 1]

    # print('################################################')
    # print(allocated_res)
    # print(server_caps)
    # print('################################################')
    return [allocated_res[i] / server_caps[i] for i in range(res_size)]


def show_info():
    print("分配结果：", alloc_ret)
    print("支付结果：", pay)
    print("用户总支付：%f, 社会福利：%f" % (total_pay, round(social_welfare)))
    print("资源利用率：", calc_rur())


print()
print('所有用户的出价:', list(bids.values()))
# print(opt_alloc())    # 仅查看分配结果！

opt_alloc_and_vcg()  # 计算分配以及所有用户的支付！

print()
print("########################### 最终结果如下 #########################")
show_info()  # 查看所有论文需要的相关信息!

execute_time = end_time - start_time
print('执行时间为：%f' % execute_time)
