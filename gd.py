import csv
import json
from scipy import spatial
import datetime
import random

#эта штука сравнивает 2 заказа с помощью косинусов
#и выдает схожесть от 0 до 1000000
def compare_orders(order1, order2):
    all_id = []
    
    for i in order1:
        if i[0] not in all_id:
            all_id.append(i[0])
    for i in order2:
        if i[0] not in all_id:
            all_id.append(i[0])

    mid1 = [i[0] for i in order1]
    mid2 = [i[0] for i in order2]
    mam1 = [i[1] for i in order1]
    mam2 = [i[1] for i in order2]

    ans1 = []
    ans2 = []
    
    for i in all_id:
        if i in mid1:
            ans1.append(mam1[mid1.index(i)])
        else:
            ans1.append(0)

        if i in mid2:
            ans2.append(mam2[mid2.index(i)])
        else:
            ans2.append(0)

    a = (1 - (spatial.distance.cosine(ans1, ans2)))*1000000
    return int(a)
    


#эта штука меняет jsonку в нужный мне формат
#(хоть и потом мы поняли, что можно было сделать без этого)
def change_json(jsond, ind):
    mass = []
    for i in range(len(jsond)):
        d = ' 0123456789'
        if jsond[i]==':':
            ans = ''
            k = 1
            while jsond[i+k] in d:
                ans += jsond[i+k]
                k += 1
            mass.append(ans)

    mfinal = []
    for i in range(0, len(mass), 3):
        if mass[i] != ' ':
            mfinal.append([int(mass[i].replace(' ', '')), int(mass[i+1].replace(' ', '')), int(mass[i+2].replace(' ', '')), ind])

    return mfinal
                

#этот модуль выдает рекомендации на основе пользовательских покупок
#например если кто-то каждую неделю покупает морковку,
#то она будет рекомендоваться ему каждую неделю
def module1(inn):

    name = 'jsons/'+str(inn)+'.json'

    with open(name,"r") as jsondata:
        mass_returns = []
        data = json.loads(jsondata.read())

        ids = []
        ids_data = []

        #здесь мы читаем json
        contracts = data["contracts"]
        for i in contracts:
            time = i["publish_time"]
            STE = json.loads(i["ste"])
            for j in STE:
                mId = j["Id"]
                if mId:
                    if mId not in ids:
                        ids.append(mId)
                        ids_data.append([mId, []])
                    ids_data[ids.index(mId)][1].append(time[:10])


        ids_final = []
        for i in ids_data:
            if len(i[1]) > 2:
                ids_final.append(i)


        #здесь читаем разницу между датами, чтобы понять, есть ли
        #какая-нибудь зависимость/закономерность или что-то вроде того
        diff_final = []
    
        for i in ids_final:
            item_id = i[0]
            #i = [1217102, ['2018-12-24', '2021-03-23', '2019-12-26', '2019-08-19']]
            item_times = []
            for a in range(len(i[1])):
                #item_times.append(datatime.datatime(int(i[1][a].split('-')[0]), int(i[1][a].split('-')[1]), int(i[1][a].split('-')[2]))
                item_times.append(datetime.datetime.strptime(i[1][a], '%Y-%m-%d'))


            item_times = sorted(item_times)
            item_times.append(datetime.datetime.now())
        
            differences = []
            for a in range(len(i[1])):
                differences.append(int((item_times[a+1]-item_times[a]).total_seconds()/60/60/24))

            if differences[-1] < differences[-2] and differences not in diff_final:
                diff_final.append([item_id, differences])

        #а здесь мы смотрим подходит ли последовательность
        #например [5, 7, 4, 6] пройдет
        #а [5, 100, 7, 200] нет, т.к разница между закупками даже +- не одинаковая
        for item in diff_final:
            ideal_rec = ''
            us_id = item[0]
            if (max(item[1]) - min(item[1]))<=(sum(item[1])/len(item[1])):
                if not((len([int(i) for i in set(item[1])])==1 and int(item[1])==0)):
                    ideal_rec = diff_final

            if ideal_rec != '':
                avg = (sum(item[1])/len(item[1]))
                mass_returns.append([int(us_id), int(avg-item[1][-1])])

        answers = []
        for i in mass_returns:
            answers.append([return_name(str(i[0])), i[1]])
        
        return answers



#эта штука читает csv с cteшками и вместо id выдает красивый name товара
# (чтобы заказчик понимал что к чему)
def return_name(mId):
    with open("cte.csv", encoding='utf-8') as r_file:
        file_reader = csv.reader(r_file, delimiter=";")
    

        for row in file_reader:
            if ''.join([i for i in row[0]]) == mId:
                return row[1]



#второй модуль подбирает \возможные\ рекомендации
#например если я покупаю сначала ложку, вилку и кастрюлю
#а в следующий раз вилку, кастрюлю и сковородку
#то когда я куплю вилку с кастрюлей, мне порекомендуют купить
#либо ложку, либо сковородку :)
def module2(inn):
    
    name = 'jsons/'+str(inn)+'.json'

    with open(name) as jsondata:
        mass_returns = []
        data = json.loads(jsondata.read())
        mass_STE = []
        contracts = data["contracts"]

        #тут мы снова читаем json
        for i in range(len(contracts)):
            STE = json.loads(data["contracts"][i]["ste"])
            if change_json(str(STE), i) != []:
                #ste, date, inn
                mass_STE.append(change_json(str(STE), i))

        similars = []
        

        #а здесь ищем схожие заказы. ind_compared > 740000 проверяет
        #чтобы схожесть заказов была более 74%. 
        for zakaz in mass_STE:
            zakaz_index = zakaz[0][3]

            mass_similar = []

            mass_compared = mass_STE
            mass_compared.remove(zakaz)

            for el in mass_compared:
                ind_compared = compare_orders(zakaz, el)
                if ind_compared > 640000:
                    mass_similar.append(el[0][3])
                
            if mass_similar != []:
                mass_similar.append(zakaz_index)
                similars.append(mass_similar)

        fin_similars = []
        for i in similars:
            if len(i) > 2:
                fin_similars.append(sorted(i))
            
        #print(fin_similars)


        #тут мы смотрим время publishing заказа, чтобы снова
        #выявить последовательность
        for index in fin_similars:
            ideal_rec = []
        
            #index = [31, 44, 25]
            times = []
            rec_ste = contracts[index[random.randint(0, 2)]]['ste']
            for i in index:
                t = contracts[i]["publish_time"][:10].split('-')
                t = datetime.datetime(int(t[0]), int(t[1]), int(t[2]))
                times.append(t)

            times.append(datetime.datetime.now())

    
            times = sorted(times)
            last_time = times[-1]
        
            differences = []

            for i in range(len(times)-1):
                k = abs((times[i+1] - times[i]).total_seconds())/3600/24
                differences.append(k)

            differences_final = []
        
            for i in differences:
                differences_final.append(i)

            print(differences_final)
            
            #смотрим подходит ли последовательность вообще
            if (max(differences_final) - sum(differences_final)/len(differences_final))<=(sum(differences_final)/len(differences_final)):
                if not((len([int(i) for i in set(differences_final)])==1 and int(differences_final[0])==0)):
                    ideal_rec = differences_final

            

            if len(ideal_rec)!=0:
                avg = int(sum(ideal_rec)/len(ideal_rec))
                m = []
                j = json.loads(rec_ste)
                for i in j:
                    m.append(i["Id"])
                mass_returns = ([(str(m)[1:][::-1][1:][::-1]), abs(avg-int(ideal_rec[-1]))])

        #и наконец выводим рекомендацию
        names = []
        if len(mass_returns)==0:
            return " "
        for i in mass_returns[0].split(','):
            el = i.replace(' ', '')
            names.append(return_name(el))
        return [names, mass_returns[1]]

def compare_arrays(m1, m2, id1, id2):
    all_items = []
    for i in m1:
        if i not in all_items:
            all_items.append(i)

    for i in m2:
        if i not in all_items:
            all_items.append(i)

    m = len(all_items)/(len(m1)+len(m2))
    if m < 0.5:
        return id2


def module3(inn):
    with open('info.json', 'r', encoding='utf-8') as f:
        templ = json.load(f)
        items = templ['unique_ste_id']
        customers = templ['unique_customers']
    with open('inn_items.json', 'r', encoding='utf-8') as f:
        templ = json.load(f)
        inn_items = templ
    #print(items)
    #print(customers)

    mass = inn_items[str(inn)]
    arr = []

    for i in inn_items:
        inn_compare = i
        mass_compare = inn_items[i]
        a = compare_arrays(mass, mass_compare, inn, inn_compare)
        if a != None:
            arr.append(a)


    if len(arr)==0:
        print('no recommendations')
    else:
        rec = []
        for mInn in arr:
            mass1 = inn_items[str(inn)] #здесь должны быть items с инн = inn
            mass2 = inn_items[str(mInn)] #здесь должны быть items с инн = mInn
            uniq_1 = set(mass1)
            uniq_2 = set(mass2)
            try:
                st = random.choice(list(uniq_2.difference(uniq_1)))


                rec.append(return_name(str(st)))
            except IndexError:
                continue

        return rec
 
    
    
