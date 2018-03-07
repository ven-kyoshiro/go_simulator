# -*- coding:utf-8 -*-
import numpy as np
import copy

class Sim:
    def __init__(self):
        self.st2ind={} #ket=state_indx,value = list_indx TODO:この関数initへ
        self.place2id = [] # TODO:この関数initへ
        count = 1
        for i in range(11):
            ft_sub=[]
            place2id_sub = []
            for j in range(11):
                if i*(10-i)*j*(10-j) ==0:
                    place2id_sub_sub = -1
                else:
                    self.st2ind[count] = [i,j]
                    place2id_sub_sub = count
                    count+=1
                place2id_sub.append(place2id_sub_sub)
            self.place2id.append(place2id_sub)



    def set_s(self):
        self.state = np.array([0. for i in range(84)])
        self.ban = 1.
        self.kou = []

    def get_s(self):
        return self.state,self.ban,self.kou

    def is_enclosed(self,act_num):
        # その石が死んでいるか確認
        pos = [self.st2ind[act_num][0],self.st2ind[act_num][1]]
        #TODO dbg
        print(pos)
        print(act_num)

        self.ban = 3. - self.ban
        find_table = self.get_find_table()
        find_table[pos[0]][pos[1]]= 3. - self.ban
        is_del = len(self.can_get(find_table,pos)) != 0
        self.ban = 3. - self.ban
        return is_del

    def is_kou(self,act_num):
        if act_num not in self.kou:
            return False
        self.ban = 3.0 - self.ban
        find_table_rev = self.get_find_table()
        self.ban = 3.0 - self.ban
        # num を場所に直して，４方向が全て相手でかつ
        for j in [[0,-1],[0,1],[-1,0],[1,0]]:
            # 隣接マスが相手の駒の時
            pos = [self.st2ind[act_num][0]+j[0],
                    self.st2ind[act_num][1]+j[1]]
            if find_table_rev[pos[0]][pos[1]] != 3. - self.ban:
                return False
        return True

    def regal_acts(self):
        # すでに石
        regal = [0]
        for i in range(1,82):
            if self.state[i] != 0.:  # already placed
                continue
            else: # 置ける
                if self.is_enclosed(i):  # 着手禁止点
                    find_table = self.get_find_table()
                    find_table[self.st2ind[i][0]][self.st2ind[i][1]] = self.ban
                    if len(self.get_all_can_get_ids(find_table,i)) > 0:  # 取れる
                        if self.is_kou(i): # こうか
                            continue
                        else: # こうでない
                            regal.append(i)
                    else: # 取れない
                        continue
                else: # 着手禁止点でない
                    regal.append(i)
        return regal

    def get_find_table(self):
        find_table = []
        count = 1
        for i in range(11):
            ft_sub=[]
            for j in range(11):
                if i*(10-i)*j*(10-j) ==0:
                    ft_sub_sub=self.ban
                else:
                    ft_sub_sub=self.state[count]
                    count+=1
                ft_sub.append(ft_sub_sub)
            find_table.append(ft_sub)
        return find_table

    def can_get(self,find_table,pos):
        can_get_ids = []
        print('[find]->step to next stone x1:'+str(pos[0])+',y:'+str(pos[1]))
        not_del = self.find(find_table,pos)
        if not not_del:
            print('[find]delete stones')
            new_state = np.array([0.]+\
                [find_table[self.st2ind[i][0]][
                            self.st2ind[i][1]] for i in range(1,82)])
            for i in range(len(new_state)):
                if new_state[i] == 3.:
                    can_get_ids.append(i)
        return can_get_ids

    def get_all_can_get_ids(self,find_table,act_num):
        can_get_ids = []
        ft = copy.deepcopy(find_table)
        print('[base]x:'+str(self.st2ind[act_num][0])+' y:'+str(self.st2ind[act_num][1]))
        find_table[self.st2ind[act_num][0]][self.st2ind[act_num][1]] = self.ban
        for j in [[0,-1],[0,1],[-1,0],[1,0]]:
            ft = copy.deepcopy(find_table)
            # 隣接マスが相手の駒の時
            pos = [self.st2ind[act_num][0]+j[0],
                   self.st2ind[act_num][1]+j[1]]
            if ft[pos[0]][pos[1]]== 3. - self.ban:
                can_get_ids += self.can_get(ft,pos)
        return can_get_ids

    def find(self,ft,l_id):
        ft[l_id[0]][l_id[1]] = 3.
        for i in [[0,-1],[0,1],[-1,0],[1,0]]:
            #TODO:debug
            print('[check]x: '+str(l_id[0]+i[0])+',y: '+str(l_id[1]+i[1]))
            
            if ft[l_id[0]+i[0]][l_id[1]+i[1]] == 3.0 - self.ban:
                print('[find]-->step to next stone')
                not_del = self.find(ft,[l_id[0]+i[0],l_id[1]+i[1]])
                if not_del:
                    return True
            elif ft[l_id[0]+i[0]][l_id[1]+i[1]] == 0.:
                print('[find]-->survive')
                return True
            else:
                print('[find]-->stop')

    def act(self,act_num):
        if 0<act_num:
            self.state[act_num] = self.ban
            find_table = self.get_find_table()
            # 上下左右の順に確認
            can_get_ids = self.get_all_can_get_ids(find_table, act_num)
            #TODO 帰ってきた部分を置き換える
            for i in can_get_ids:
                self.state[i] = 0.
            self.kou = can_get_ids
            self.state[81+int(self.ban)]+=len(self.kou)
            print('show find_table below')
            for ft in find_table:
                print(ft)
        self.ban = 3. -self.ban