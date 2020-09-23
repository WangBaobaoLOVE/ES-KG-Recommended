from django.shortcuts import render, redirect
from django.http import HttpResponse

# jieba -> import
import jieba
import numpy as np
import re
from collections import Counter   #引入Counter
from elasticsearch import Elasticsearch
es = Elasticsearch(['localhost:9200'])
import pandas as pd
schoolRange = pd.read_excel('static/files/schoolRange.xlsx')
import math
global_acount_sorted = []

######################
# the functions defined by myself
#######################

def splitWords(text):
    words_splited = jieba.cut_for_search(text)
    words_string = ','.join(words_splited)
    words_list = words_string.split(',')
    print(words_list)
    return words_list

def wordsClassifiter(text):
    edu_dic = ['专业', '大学', '高校', '毕业', '深造', '本科', '硕士', '博士', '学生', '研究生', '学院', '学', '大']
    work_dic = ['工作', '就业']
    project_dic = ['项目']
    dics = [edu_dic, work_dic, project_dic]
    symbol = '，|。|：|；|？|“|”|！|、|‘|’'

    text = re.split(symbol, text)
    text.reverse()
    print(text)

    before = -1
    edu_work_project = [[],[],[]]
    for words in text:
        if words:
            for dic_num in range(len(dics)):
                status = 0
                for word in dics[dic_num]:
                    if word in words:
                        edu_work_project[dic_num].append(words)
                        before = dic_num
                        status = 1
                        break

                if status:
                    break
            if status == 0 and before >= 0:
                edu_work_project[before].append(words)

    return edu_work_project

def wordClassifiter(words):
    edu_work_project_words = [[], [], []]
    for words_num in range(len(edu_work_project_words)):
        print(words_num)
        for word in words[words_num]:
            if not word:
                break
            print(word)
            edu_work_project_words[words_num] += splitWords(word)

    print(edu_work_project_words)
    return edu_work_project_words

def edu_select(word):
    if not word:
        return []

    edu_ids = []
    filed_names = ["school_name","discipline_name"]
    for each_word in word:
        if len(each_word)<2:
            continue
        for filed_name in filed_names:
            if len(each_word) < 4 and filed_name == "school_name":
                continue
            results_edu = es.search(
                index='eke_education',
                body={
                    "query": {
                        "match":{
                            filed_name: each_word,
                        }
                        # 还需要添加一个学历本科，硕士和博士的筛选
                    },
                    "size": 100
                },
                filter_path=["hits.hits._id"]
            )

            for result_edu in results_edu['hits']['hits']:
                edu_ids.append(result_edu['_id'])
    return list(set(edu_ids))

def work_select(word):
    work_ids = []

    if not word:
        return []

    for each_word in word:
        results_work = es.search(
            index='eke_work',
            body={
                "query": {
                    "multi_match":{
                        "query": each_word,
                        "fields":["responsibilities","achievement","corporation_name","industry_name","architecture_name","position_name"]
                    }
                    # 还需要添加years的筛选
                }
            },
            filter_path=["hits.hits._id"]
        )


        for result_work in results_work['hits']['hits']:
            work_ids.append(result_work['_id'])

    return list(set(work_ids))

def project_select(word):
    project_ids = []

    if not word:
        return []

    for each_word in word:
        results_project = es.search(
            index='eke_project',
            body={
                "query": {
                    "multi_match":{
                        "query": each_word,
                        "fields":["name","describe","responsibilities"]
                    }
                    # 还需要添加years的筛选
                }
            },
            filter_path=["hits.hits._id"]
        )


        for result_project in results_project['hits']['hits']:
            project_ids.append(result_project['_id'])

    return list(set(project_ids))

def acount_select(word):
    acount_ids_all = []
    filed_names = ['education', 'work', 'project']
    for each_filed in range(len(filed_names)):
        for each_word in word[each_filed]:
            results_acount = es.search(
                index='eke_acount',
                body = {
                    "query": {
                        "match":{
                            filed_names[each_filed]: each_word
                        }
                    }
                },
                filter_path=["hits.hits._id"]
            )
            for result_acount in results_acount['hits']['hits']:
                acount_ids_all.append(result_acount['_id'])

    # acount_ids = dict(Counter(acount_ids_all))
    return acount_ids_all

def select(word):
    edu_work_project_ids = [[], [], []]

    edu_work_project_ids[0] += edu_select(word[0])
    edu_work_project_ids[1] += work_select(word[1])
    edu_work_project_ids[2] += project_select(word[2])

    acount_ids = acount_select(edu_work_project_ids)

    return acount_ids

def score_edu(edu_ids):
    for edu_index in [0, -1]:
        edu_search = es.search(
                index='eke_education',
                body = {
                    "query": {
                        "match": {
                            "_id": edu_ids[edu_index]
                        }
                    }
                },
                filter_path=["hits.hits._source"]
            )
        if edu_index == 0:
            edu = edu_search['hits']['hits'][0]['_source']['school_name']
        else:
            d = edu_search['hits']['hits'][0]['_source']['sort_id']
            if d > 3:
                d = 3
    print(edu)
    # print(d)

    edu_range = schoolRange[schoolRange['学校名称'] == edu]
    if not edu_range.shape[0]:
        s = 60
        m = 1
    else:
        s = edu_range['综合得分'].iloc[0]
        m = edu_range['星级排名'].iloc[0]

    E = (d * d) * (s / 10) * m / 9
    print('d = {}; m = {}; s = {}; E = {}.'.format(d,m,s,E))
    return E

def score_work(work_ids):
    scale_list = []
    for work_index in range(len(work_ids)):
        work = es.search(
                index='eke_work',
                body = {
                    "query": {
                        "match": {
                            "_id": work_ids[work_index]
                        }
                    }
                },
                filter_path=["hits.hits._source"]
            )
        work = work['hits']['hits'][0]['_source']
        # print(work)

        symbol = '，|。|：|；|？|“|”|！|、|‘|’|-|人'
        # print(re.split(symbol, work['scale']))
        if not work['scale']:
            scale_list.append(10)
        else:
            for each_scale in re.split(symbol, work['scale']):
                try:
                    if isinstance(int(each_scale), int):
                        scale_list.append(int(each_scale))
                except:
                    pass
                # print(each_scale)

        if work_index == 0:
            if not work['end_time']:
                y_end = work['start_time'].split('年')[0]
            else:
                y_end = work['end_time'].split('年')[0]
            # print(y_end)

            if len(work_ids) == 1:
                y_start = work['start_time'].split('年')[0]
        elif work_index == len(work_ids)-1:
            y_start = work['start_time'].split('年')[0]

    # print('this is work')
    # print(scale_list)
    c = max(scale_list)
    if c < 10:
        c = 10   # print(c)
    # print(y_end)
    # print(y_start)
    if not y_end or not y_start:
        y = 1
    else:
        y = int(y_end) - int(y_start) if int(y_end) > int(y_start) else int(y_start) - int(y_end)
    y_ = y/len(work_ids)
    W = 10*math.log10(y+1)*y_*(math.log10(c))*(math.log10(c))/16
    print('c={};y={};y_={};W={}'.format(c,y,y_,W))
    return W

def cosine_similarity(sentence1: str, sentence2: str) -> float:
    """
    # https://blog.csdn.net/weixin{'121434534': 15.801196489097885, '26327177': 50.55390409445972, '135053140': 7.748811970041714, '118596235': 18.13094694220987, '114071609': 21.27343100704666, '37014643': 22.07291221253464, '90151109': 34.66959551876757, '132488020': 17.714202382303164, '118984034': 21.2537074446553, '85602734': 28.455025373837024, '121473296': 11.717576779938565, '133659820': 17.269689626269134, '112092201': 24.813906505991554, '129773846': 15.241994624139071, '5228481': 16.45200886861863, '120143391': 14.184431586565314, '124754632': 7.491386562602215, '46544708': 25.094186355638772, '122790404': 27.866338525905768, '118831865': 8.924601813133899, '133090722 22.48094947379913, '127234752': 21.290222165352983, '127024522': 22.230472239155272, '16784103': 35.62669135259276, '123883574': 12.280110113271897, '116565443': 8.188414216899162, '125414292': 27.73462022654379, '118824909': 8.648497673713326, '7641745': 17.65174196816221, '134594186': 18.9777977594527, '51646655': 23.807812379268356, '92810011': 22.931041743555042, '126259744': 29.272641287313725, '119055352': 59.9873030950221, '124885306': 14.665919895935549, '129078544': 20.62274562612221, '112842059': 50.083479519952014, '109211196': 24.77889165308978, '116081379': 38.57180685499044, '13653994': 35.22327369316456, '121740156': 24.02566915472974, '92570286': 22.7314021931305, '136195468': 13.468312074954603, '51398622': 32.55624866268633, '20206455': 21.060438300242375, '132671680': 7.519608124695713, '15096146': 32.13851836474585, '135784026': 18.054993282542554, '15435479': 43.98889791224, '27507450': 15.807959644391437, '126536398': 17.636968332824615, '53420503': 22.074464809793398, '131938328': 13.415786282514642, '130374534': 12.33407817341507, '90440092': 24.27286113173468, '24794721': 13.327394204782866, '97168483': 41.8104231240808, '105794467': 47.77392444031108, '113672389': 18.59654323025785, '80802202': 17.494642872796657, '105142529': 21.349677793350423, '7425048': 24.465321616878708, '62880362': 24.386084607963088, '12126430': 38.83457923513964, '131015286': 9.459321061669591, '11292624': 16.532864093919073, '128399916': 29.152450877961982, '89731440': 52.36621645874135, '12344197': 40.47014344708637, '119661893': 8.978199898826228, '136037960': 7.491386562602215, '31391669': 16.722565298133397, '120897898': 42.62359669713415, '46418959': 25.513062613931424, '127413260': 21.216198164776486, '98433448': 37.67374348045941, '130145910': 22.39425373757915, '107742068': 24.77034792835972, '108761217': 13.323232684600782, '89909666': 9.5057258633496, '131105072': 15.181131130594487, '19989585': 21.52717034059238, '128740358': 17.778494703157364, '107371512': 44.11631839028236, '97014850': 11.061206556415547, '119654393': 34.48503938838043, '14712344': 26.864982157037765, '129161560': 14.197877163966862, '126586504': 9.38358777030354, '118605390': 23.832485359825988, '27151510': 15.873076006884899, '134745710': 19.710631694809088, '119514047': 14.325796183431484, '32246209': 20.427619805336604, '9383020': 31.48399541949921, '128624712': 8.587392871834828, '92675275': 7.491386562602215, '92758127': 41.83951268319831, '118867471': 13.327394204782866, '134534616': 13.917424093061976, '45191029': 47.401470321400794, '14862180': 31.33953626049505, '57325001': 22.94161864168627, '112068898': 11.8070370151985, '92921812': 12.833200675164317, '133391070': 19.17528010406445, '135427734': 10.276700443425185, '105887957': 32.244081647680936, '131219644': 18.8057906929832, '4112081': 54.787473994410064, '88619884': 60.39210848071639, '62755101': 19.458219214604508, '136534134': 18.734115208058995, '79552677': 17.090675451491105, '114230339': 41.0252001115908, '17952051': 9.091622784605573, '92577556': 41.79422412977354, '135957890': 13.362583705823821, '121753494': 22.612860870083523, '140077968': 28.775848983533997, '126827804': 27.796703277480155, '39552111': 25.975913753451103, '119575543': 9.770848510903322, '116912183': 30.02962168917749, '136070518': 20.54044710720378, '27319729': 26.426035689757878, '133625060': 14.042681112801889, '18082359': 9.194456938370145, '28926741': 33.92810591879609, '136449552': 17.540513843686263, '134596214': 27.676686128518316, '102138545': 17.791657090138944, '130552186': 15.022255953566798, '121802448': 14.08980375664122, '95100589': 21.429247715710595, '128807166': 12.603656150254531, '105967790': 12.825948999387942, '116501831': 37.25373730395783, '77930727': 8.724061479043712, '134236868': 20.047731764090198, '92625532': 33.36373849401056, '25073875': 36.48739083799917, '15156937': 39.40879309918197, '110417200': 30.302593516965032, '101850493': 23.243003127088297, '137012356': 18.156848020549802, '113282903': 22.382275117717146, '69960595': 28.085293512119755, '108755580': 36.73773750705026, '134870982': 7.491386562602215, '123906898': 15.330731206038019, '107641249': 12.33398985691138, '122981962': 21.989112889126154, '126419354': 26.12499964608872, '87606889': 53.85728987780307, '52868856': 56.01535237918256, '132567336': 15.353125982100678, '101765373': 22.049197167003847, '20400061': 26.50848954986469, '52275752': 25.23576690194895, '27213338': 14.211804996290748, '8204599': 23.27612819829973, '123552504': 25.069851348920484, '119927325': 10.09721822804016, '36774132': 16.525636365728626, '15867933': 32.248528162297006, '38432612': 27.00011732713716, '62869860': 47.05207098385506, '70497364': 21.171227657183927, '16402162': 8.449842445104888, '108939722': 31.342296904421097, '46152606': 9.293697444755944, '60975873': 37.63139860045099, '51801591': 9.001801833795167, '104455096': 21.99989005523272, '102483409': 9.267075366223855, '10207924': 33.209746837005746, '109867826': 36.9505313376549, '41515696': 18.860651786616305, '28169832': 22.816292434527433, '15724533': 17.97002980289662, '135127644': 36.10485087607588, '118840555': 37.31677866625738, '19510210': 31.208859313683572, '120029968': 8.630045307724194, '12675025': 19.18005215280108, '100253158': 21.415322568122722, '118748116': 9.624719895935549, '140156477': 18.237048640040094, '117784207': 26.188164549865476, '128493840': 8.079734983843283, '97330171': 22.891946345321134, '140249525': 10.582768460716105, '136086876': 43.060510113271896, '23761776': 17.019515170902665, '118960912': 7.670307033122088, '7418429': 43.05803365482086, '24303493': 23.68751872972101, '29329838': 41.88812468251075, '135354122': 19.18666574452918, '101635509': 8.46612906368622, '79638734': 11.266029009579196, '127320486': 55.861184008718794, '36043029': 28.947889204269856, '79267045': 20.996336577608712, '112008302': 38.0306470464229, '48596524': 27.720121880871204, '128468872': 23.297378741899962, '117362131': 19.840845560926155, '88313872': 32.348151588805806, '103616203': 32.89793166024153, '96770302': 37.95169796965182, '107582544': 18.942296675874115, '118200739': 13.467051319075187, '123470838': 7.491386562602215, '77908198': 22.462461228651772, '128868418': 19.72222272455042, '33608905': 15.285888519246628, '106996052': 24.644839633725006, '134687734': 20.412190618720096, '18660362': 19.1657375523048, '86048922': 8.422615591590784, '112119065': 29.374082017357257, '22130466': 18.646785412864148, '30172815': 32.06618342665436, '116818227': 16.960236078790288, '122083494': 7.491386562602215, '25759407': 14.632129796170483, '109408817': 30.955219275529217, '117204127': 14.140986562602215, '107185040': 15.647163334350772, '38534728': 24.857409729892805, '128559510': 12.23755666411044, '14582188': 27.076123496024966, '105217261': 22.98885094820539, '118192647': 17.573961613582455, '8905901': 22.384825087052135, '11563621': 17.44333310643683, '15802788': 52.489733139495605, '118944757': 21.15688891603691, '115156875': 13.695957333570599, '132487658': 40.30617740196243, '113421634': 16.694140797900324, '40692499': 13.597210078766896, '118185502': 9.014843275518846, '30482635': 15.789662906669383, '116528517': 38.787015977285904, '48090692': 21.88755044091362, '115796247': 23.3149866045852, '92579238': 14.660225883616235, '13534500': 13.006240806090334, '6157688': 39.85012959353477, '59426812': 7.670307033122088, '25675895': 30.135228005565295, '138339988': 17.11155354349711, '38776320': 30.46399450553642, '17382192': 22.130669257376837, '120038771': 13.24709357717323, '79446663': 11.617303386382993, '21028681': 19.538641535774207, '9041089': 36.28862926333943, '5168546': 36.00100372912116, '91111519': 12.345247795787028, '80547839': 18.09722387615285, '118835712': 39.834387440610904, '59584364': 11.677178674360551, '75559039': 32.24182816503456, '22650265': 31.322738458160853, '140372350': 17.182524226432445, '94457137': 18.966597721180054, '82726330': 14.292941988877207, '133717898': 30.82399121517556, '14211415': 26.651647783972642, '10608478': 32.306221686165934, '89187342': 12.517576779938564, '111050214': 16.357952324513104, '29599635': 10.212029818795264, '134977464': 24.322893988869073, '42153029': 8.351026719442173, '117187444': 19.524791469068788, '13475522': 33.597965598336486, '50971447': 40.75113515043337, '55855541': 30.36465197953474, '133968368': 14.607507064333284, '17858518': 19.98983480231835, '128127690': 16.898652131395625, '117121268': 27.752477672497132, '99332990': 43.05928300525301, '121536936': 7.491386562602215, '14411057': 27.45177414575124, '17190720': 10.523767387548991, '121167110': 41.53898540536307, '126469548': 7.491386562602215, '128643574': 20.028888548117923, '128206152': 12.286005476409025, '132443964': 11.721629908943605, '123332500': 23.009590914096158, '118701918': 7.491386562602215, '14858616': 41.19040498826109, '129848050': 26.05985091002258, '126217960': 10.07214590945308, '40501821': 31.995821828429463, '92765304': 35.32559402299785, '115459709': 26.274474683644776, '133362488': 38.64281008629642, '140376674': 10.773261268111547, '102131840': 38.37108593849118, '131524776': 33.79184738155098, '127725038': 24.49229082080279, '118374705': 21.69061727493299, '128528904': 25.313420640863022, '128659668': 48.246210854117216, '124322828': 7.6730181442331995, '74120482': 18.052632208091683, '139859482': 7.5591183116266105, '130536114': 44.299486120431965, '128486642': 34.55483307760987, '40233169': 19.745877898029743, '117056310': 7.808298327607561, '123350370': 8.056719895935549, '15643476': 17.951106124287506, '112515269': 20.671496356735798, '136253096': 25.860617005206542, '44866741': 22.39928010406445, '103630994': 22.10345821829827, '119614083': 22.015368113704405, '131172404': 10.939892127910868, '45619653': 18.947829654189494, '44213061': 15.560287056774435, '133035400': 30.37219064342328, '136068422': 10.861699456189896, '26552691': 31.13522389268426, '30034271': 33.78612949140949, '118699430': 20.56706780897747, '7650210': 14.49088773117686, '123626662': 24.97324627010238, '136790110': 28.979594043549227, '111489386': 24.336503327721346, '102647999': 17.679373958658918, '10623263': 10.947122670914107, '115320820': 27.129886258401882, '122509654': 7.547829686789211, '106058120': 46.01733242969641, '16814099': 22.873008305670417, '100183445': 41.83431989593555, '45245011': 9.293735244291407, '98171810': 24.849775686164367, '120207162': 7.547829686789211, '50229006': 8.215140869677803, '11877445': 19.109278359256713, '83265600': 47.47158878775782, '52337951': 32.596127882045494, '34697223': 23.652546578656036, '44607251': 32.85622990353807, '130447526': 10.953414160231697, '69925158': 11.919282297787362, '121353930': 53.11729013049283, '101584767': 7.491386562602215, '118414358': 25.8225206781271, '120001574': 12.241804283190579, '132993772': 8.981376230099029, '86532572': 30.4888868446649, '112370722': 9.537848064187981, '127094238': 10.186659621845582, '21601672': 23.954159122779913, '17335863': 15.161158983484711, '130616714': 26.18002805364878, '71986246': 11.682867395959002, '118408493': 29.7416102448393, '139791438': 18.254656413707355, '131067764': 37.905593568514234, '136054112': 10.013248418665595, '114102635': 26.689107546307646, '12975528': 32.60797378570295, '117869955': 14.776638471613653, '78582661': 46.23545953886088, '121725522': 16.69778246925875, '118239741': 20.41061119975651, '130882546': 22.919746824993187, '13702336': 20.835905002682225, '135831440': 8.534558828347103, '16448991': 22.806867433708526, '14712187': 23.784899970183282, '119689041': 43.0699173006364, '140306502': 27.94321661803438, '119762884': 31.799570157620465, '125031920': 9.643454984466391, '10161829': 9.617328115905382, '107344136': 29.52474941928115, '129956590': 17.977010355146206, '118197783': 10.136909252423827, '9253091': 27.06115566398561, '121856338': 43.04724399830386, '11056112': 29.541057395466776, '95368663': 37.61323276231808, '126476244': 12.649536785719922, '130061356': 11.745798342032062, '47650875': 23.869908064912437, '39209242': 36.6293994161989, '130926848': 11.881595730352887, '124112462': 29.731523910532104, '48681724': 17.9437757336732, '111086132': 21.94371395730739, '112234430': 7.580846797862152, '118706564': 10.547556586969254, '87981575': 9.619060910344238, '102016576': 18.700263258390255, '132525822': 9.136534700539142, '74273187': 29.33918428354843, '68757173': 31.166035819615622, '93615988': 10.603292952149241, '120065399': 38.24802365796749, '7605828': 20.322623704250837, '124361218': 11.85870104343801, '136048770': 24.056273606338713, '91715607': 29.67048646183501, '118617783': 20.000271142134512, '15546441': 27.156404766253615, '87263821': 57.61222343218486, '11232006': 19.397768693108343, '54873454': 19.428429568656448, '119460116': 11.923364886975321, '51697663': 34.83078770609772, '20249790': 22.41967745141307, '11329305': 24.022779741976997, '85216870': 16.29688233987334, '118548519': 30.152754094410604, '123487976': 9.773708653215278, '108080084': 22.086794990585982, '132602338': 11.203071981287943, '128782342': 20.202222020883323, '115852854': 10.906227046274315, '128394716': 14.924362169486367, '19077555': 11.835849332697915, '81090365': 9.172242945194345, '6266457': 24.24767711875443, '115278973': 23.30456833264294, '15703889': 27.310508290698436, '85993461': 49.31596838067685, '139609634': 12.166033605603392, '5483421': 40.75113515043337, '112287635': 9.228855879120026, '118858503': 32.29948481003974, '45941006': 17.216076143292106, '95704437': 13.719577332725493, '23660213': 32.67473073322652, '89159794': 17.86401314126543, '131389194': 11.000656523578046, '107228134': 47.239341432474106, '117943361': 31.671707237965663, '115517186': 41.57264391883038, '105388630': 26.161827628252286, '119040335': 25.70159872515021, '122805196': 9.821794039838114, '111150865': 26.75152008625888, '83650465': 12.545798342032063, '109024492': 19.53494947983758, '118442361': 17.841946770731116, '99021829': 7.491386562602215, '121981506': 23.19498918514872, '106429101': 20.71020158727033, '122935264': 7.660715935163204, '108321486': 13.13355454952633, '12950179': 18.547047507487182, '129517242': 14.45497125141325, '85520945': 20.647015832885984, '14483019': 51.03057514545931, '12338658': 18.44359505324599, '111806091': 19.826856532970353, '4639841': 40.838439330087816, '136094340': 25.100003777518353, '30679550': 40.08294577828616, '107322219': 7.604272810976208, '140002336': 9.333264223248488, '126655154': 13.008555834484323, '80675163': 19.453886277863077, '7515539': 49.11620103265893, '114453004': 14.666286434936898, '22157368': 23.416583970861826, '136496398': 11.849336212789149, '111070586': 8.90187601746996, '131933452': 23.303194912191152, '6598083': 17.795086912041107, '70169042': 23.253971787176443, '31115119': 44.42205014965819, '20269819': 26.20880670641989, '122312372': 7.491386562602215, '135928062': 9.374204857750513, '81914732': 26.630343718540026, '126888038': 24.454734046789525, '128465410': 44.40221700967094, '98120070': 19.042610841570777, '114559213': 13.901872810976208, '86074069': 23.153024752794625, '8648572': 30.55836503462224, '13877079': 18.858810500634892, '112864519': 9.033157461363375, '140257385': 20.197747405211054, '119824995': 20.60661278516878, '127704832': 26.35637110331789, '132877370': 42.85560211416744, '118273047': 28.740730335574245, '11223099': 44.480575809716086, '106067365': 34.72198577716653, '33293106': 27.820688987674732, '118200210': 20.645298822881976, '139905462': 18.11873619002892, '91148113': 16.46882287823373, '134555254': 32.95723506046436, '124395094': 8.889444535635661, '56817319': 25.926991238252278, '17299953': 15.367732596902183, '38878114': 17.776154297367622, '124353150': 21.940826354473312, '124575180': 7.865236244950765, '52278886': 13.185412657131135, '11419654': 31.09778636189334, '136445492': 8.01561406585423, '127917180': 9.67309971666726, '51364289': 40.53026069660473, '13287100': 33.988987619808874, '41107136': 11.670991180298978, '75117734': 27.59461113699453, '124361452': 11.85870104343801, '39755153': 27.780865836371206, '41500163': 20.531243591456654, '82261127': 10.32147976747158, '116851371': 25.235593308472325, '81963741': 25.78775206807839, '8992626': 15.132214392594653, '83865638': 46.15377325369114, '135928424': 8.291386562602215, '135485118': 10.005667149684884, '7890216': 53.19798973490522, '38171827': 11.294245159166973, '20198095': 15.562753321342715, '136074522': 27.770305308041973, '27208402': 15.776514415735384, '115470422': 7.536116680232183, '102653012': 22.47015041447086, '128922776': 14.012971108687942, '113062062': 9.427233105751998, '126223934': 12.994698034658226, '130309762': 11.808475889904532, '107057665': 7.62590709491305, '25734782': 17.400032635531996, '124432834': 24.15036546349122, '126911008': 8.556821938501178, '14182893': 18.902871992028363, '78518879': 14.189568858393876, '127403640': 9.003557814341399, '90187389': 30.344359844541298, '80153499': 7.66612906368622, '124623200': 15.430408940021888, '119802220': 9.535919932048143, '10838027': 29.111149521967473, '10376225': 33.33027715036366, '116460454': 67.89294116004932, '36745222': 14.241386562602216, '108689789': 27.29456952019443, '23959379': 20.39528071317342, '127100036': 12.895955650983286, '121070544': 30.412065796788184, '117030118': 16.18068828775953, '40415409': 14.633876019316688, '102145407': 9.579037865293671, '115763568': 20.738809308377803, '19428522': 22.82748938779473, '117933504': 7.808298327607561, '119683793': 11.896497250458438, '116330837': 11.896497250458438, '21989013': 31.244358173630552, '19030795': 15.101180428425026, '140225197': 27.83749587441275, '134618332': 14.74338809991179, '114016556': 18.764379948629454, '119811585': 23.79410311378453, '112351803': 31.991812886174078, '119119269': 7.539156609505357, '111259099': 26.42261807008132, '12942084': 36.12239008593989, '28820051': 14.838788968293805, '134478252': 18.09722387615285, '78652750': 44.598256754078285, '19903423': 21.18185461143863, '119747794': 16.345826440443382, '91863132': 7.510200937331214, '10994883': 25.714305192836164, '124993582': 14.377752718627747, '123002526': 10.182384007597575, '17017512': 16.33382014040316, '52371498': 38.17427583388489, '99348539': 25.510305090427337, '119372881': 9.475440222562648, '132856022': 17.041946770731116, '70622427': 16.467274002160785, '118045139': 11.820631007046659, '133042192': 20.94607705187336, '118236047': 27.324245290006395, '90315572': 36.71404603782564, '136063788': 27.65757453186697, '135298422': 14.767692414693808, '118736877': 7.660715935163204, '127426254': 15.933652073754082, '115992038': 32.331743760833454, '59494732': 41.3411063487013, '31464684': 15.105704673611113, '42523068': 15.319397547095344, '14193301': 9.738818713896524, '112703776': 17.02141830093988, '92765555': 52.07475094465735, '140272158': 28.163466962269922, '57809791': 8.207068444681708, '27981968': 9.454515194317803, '122080946': 9.221664559586706, '115676451': 13.203240325233757, '116818684': 19.34022697085655, '139773222': 11.8070370151985, '136006484': 15.206383856326614, '97663253': 11.382142814520433, '103026206': 22.856711023261596, '133917270': 49.014470503106125, '56433902': 8.572046239833638, '82125879': 14.91605737096972, '119402356': 22.89306989087068, '23902801': 18.0585307586751, '50597312': 8.404272810976208, '107276765': 25.22156637674067, '24762022': 29.713983658747484, '55274525': 7.259827917873562, '38657708': 24.576877529665968, '13283074': 37.46368387614706, '92711697': 27.488129465728736, '98873962': 30.70597677195747, '122116228': 17.61544150315951, '117927044': 16.23406690519454, '124347990': 30.643961937684097, '128848840': 12.02108535993504, '21871302': 19.857333294018943, '97376723': 18.36215004219938, '85214013': 10.53157646693019, '121516446': 9.443997847273886, '131892004': 15.106597109069515, '99197539': 19.48466319146495, '118671741': 30.27863054173806, '129466996': 17.07274611060239, '109200022': 17.395303350257414, '91854387': 20.24541020016242, '133689430': 13.697269865893865, '26804068': 41.30098135313146, '80495114': 29.399461963841212, '117097616': 10.586479921014668, '35561499': 15.345237410538179, '18341551': 12.825784378713253, '86008205': 36.71404603782564, '128844542': 9.476316284805499, '109580987': 45.043873616014466, '39551404': 26.843723548267143, '135051438': 7.777659315434012, '129466478': 21.227578227938725, '57425134': 14.325505337961262, '90358841': 29.116179419792, '65889949': 18.048904128221757, '118678481': 33.107459281677315, '132824708': 16.16701560428837, '139902706': 31.286158807598945, '131775736': 36.155119473999164, '108959439': 38.172626727870664, '92086345': 29.738577532180965, '16826028': 9.436087288999314, '120030232': 14.933701757061069, '21032819': 31.810595866158256, '119194158': 21.219896854662487, '20830748': 29.37935607558891, '94807271': 27.87751989593555, '20893790': 26.900554772811304, '93133456': 22.123051763918106, '123400154': 10.634399299919359, '113272944': 22.60239479601427, '134809322': 16.300861488691172, '108968876': 27.19467433778564, '89385325': 31.5565797203653, '23541622': 17.92906355152607, '136594132': 34.81769040875926, '80991977': 23.485904114778208, '127204648': 10.331228725083086, '17079717': 11.573261268111548, '97610120': 8.107724020822964, '90044520': 7.856144961219548, '128930306': 18.917704739023023, '125269268': 28.24098381317646, '116884565': 27.236161263700424, '103658239': 21.725150185101405, '85147036': 21.416003150628953, '121450568': 21.127446623612546, '10452041': 18.47053443178281, '103833510': 17.53977234548159, '125800580': 22.87619159908533, '116626573': 31.166831698847663, '118634150': 18.046036787786754, '13061626': 22.895593494346205, '136828732': 12.630463028312557, '131057420': 21.40655463976511, '92262880': 33.952205526575035, '140009144': 8.886268899672089, '121493570': 17.91216899295334, '139946898': 11.519920470655423, '28605674': 26.000895883484596, '140393970': 19.935865401754626, '109659169': 50.984636469670875, '8276170': 18.017945390949325, '139822410': 19.88480473589114, '113930036': 32.32112413798346, '109994502': 34.08267352651295, '23631777': 28.253770015967092, '116025180': 34.34043744693525, '115781457': 30.001332620536964, '124921218': 21.278797815690922, '117219991': 12.432169850636075, '110797195': 8.380479647861694, '122311212': 11.88617590166896, '134305684': 15.639434162906, '130527358': 7.826051909011434, '120596320': 34.48417120214174, '110266211': 9.178886562602216, '114263353': 21.701741755013643, '97768092': 19.557355256737193, '117065638': 40.90386955453229, '29239128': 30.99952721806561, '7076811': 37.107258515379776, '123556812': 17.815730389924806, '123425124': 8.224172174233738, '124110196': 7.491386562602215, '123589744': 10.590591827316716, '127235786': 34.35231256795085, '140141694': 15.74518631021149, '25250350': 9.77403952970452, '76074686': 9.706898223698316, '92305428': 11.774019904125561, '21715700': 31.933030437570395, '134683322': 9.796741331457849, '139791518': 15.56178159255732, '128034574': 24.39822110292166}
_40400177/article/details/89409619
    compute normalized COSINE similarity.
    :param sentence1: English sentence.
    :param sentence2: English sentence.
    :return: normalized similarity of two input sentences.
    """
    seg1 = ','.join(jieba.cut_for_search(sentence1))
    seg2 = ','.join(jieba.cut_for_search(sentence2))

    word_list = list(set([word for word in seg1 + seg2]))
    word_count_vec_1 = []
    word_count_vec_2 = []
    for word in word_list:
        word_count_vec_1.append(seg1.count(word))
        word_count_vec_2.append(seg2.count(word))

    vec_1 = np.array(word_count_vec_1)
    vec_2 = np.array(word_count_vec_2)

    num = vec_1.dot(vec_2.T)
    denom = np.linalg.norm(vec_1) * np.linalg.norm(vec_2)
    if denom == 0:
        return 0.80
    cos = num / denom
    # print('num = {}; denom = {}.'.format(num, denom))
    sim = 0.5 + 0.5 * cos

    return sim

def score_project(project_ids):
    n_sum = []
    for project_id in project_ids:
        project = es.search(
                index='eke_project',
                body = {
                    "query": {
                        "match": {
                            "_id": project_id
                        }
                    }
                },
                filter_path= ["hits.hits._source"]
            )
        project = project['hits']['hits'][0]['_source']

        # print(project['describe'])
        # print(project['responsibilities'])
        sim = cosine_similarity(project['describe'], project['responsibilities'])
        n_sum.append(sim)
        # print(n_sum)

    n = len(project_ids) if len(project_ids) <= 9 else 9
    n_ = 10*sum(n_sum)/len(n_sum)
    P = 10*math.log10(n+1)*n_
    print('n = {}; n_ = {}; P = {}.'.format(n, n_, P))
    return P

def score(acount_id):
    a = 0.4
    b = 0.3
    c = 0.3
    # print(acount_id)
    acount = es.search(
                index='eke_acount',
                body = {
                    "query": {
                        "match": {
                            "_id": acount_id
                        }
                    }
                },
                filter_path=["hits.hits._source"]
            )
    acount = acount['hits']['hits'][0]['_source']

    edu_ids = acount["education"]
    work_ids = acount["work"]
    project_ids = acount["project"]

    E = score_edu(edu_ids)
    W = score_work(work_ids)
    P = score_project(project_ids)
    Score = a * E + b * W + c * P
    print('Score = {}'.format(Score))
    return Score

def sort(acount_selected):
    acount_sorted = {}
    print('this is sort!')

    for each_acount in acount_selected:
        acount_sorted[each_acount] = score(each_acount)

    # https://www.cnblogs.com/linyawen/archive/2012/03/15/2398292.html
    acount_sorted = sorted(acount_sorted.items(), key=lambda d: d[1], reverse=1)
    # print(acount_sorted)
    return acount_sorted

##########################
# Create your views here.
#
###########################

def search(request):
    if request.method == 'POST':
        text = request.POST.get('text')
        if not text:
            return render(request, 'SR/search.html',{'status': '输入为空，请重新输入'})

        # 分句
        words = wordsClassifiter(text)
        # print(words)

        effect = 0
        for word in words:
            if word:
                effect = 1
                break
        if not effect:
            return render(request, 'SR/search.html',{'status': '输入无效，请输入有效的语句'})

        # 分词
        word = wordClassifiter(words)

        effect = 0
        for word_ in word:
            if word_:
                effect = 1
                break
        if not effect:
            return render(request, 'SR/search.html',{'status': '输入无效，请输入有效的语句'})

        # select
        acount_ids = select(word)
        # print(acount_ids)

        # sort
        global_acount_sorted.append(sort(acount_ids))

        return redirect('results')
    return render(request, 'SR/search.html')

def results(request):
    print(global_acount_sorted[0])
    return render(request, 'SR/results.html', {'acount_sorted': global_acount_sorted[0]})

def profile(request):
    return render(request, 'SR/profile.html')