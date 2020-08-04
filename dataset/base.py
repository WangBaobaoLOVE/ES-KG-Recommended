import jsonlines
import json
import os

# Note: 1.jsonl is the dataset supported by HuiYuan;(we have rename the filename)
# HuiYuan don't allow us to spread the dataset,
# So we not push the dataset in the github repository.
# Butwill push one sample of dataset in the github repository.

def getOneSampleFromDataset(inputFilePath = '1.jsonl', outputFilePath = './oneSample.json', index=1):
    """
    Get one sample from dataset to intro the structure

    :param inputFilePath:
    :param outputFilePath: path of dataset file
    :param index: the index of one sample that you want to get, it is [1, getSize()]

    :return: one sample data of dataset file in index, return -1 while index is error.
    """
    size = getSize(inputFilePath)
    if index <= 0 or index > size:
        print('The value of index is error. It is in [1, {}]'.format(size))
        return -1

    with jsonlines.open(inputFilePath) as reader:
        for i in range(index):
            oneSample = reader.read()
        with open(outputFilePath, 'w') as outputFile:
            json.dump(oneSample, outputFile)
        return oneSample

def getSize(inputFilePath = '1.jsonl'):
    '''
    Get thenumber/size of resume in file
    :param inputFilePath: the file
    :return: the number/size
    '''
    with jsonlines.open(inputFilePath) as reader:
        size = 0
        for obj in reader:
            size += 1
        return size

def sliptData2Acount_Work_Education_Project(fileDir = './data/'):
    '''
    slipt original file -> acount, work, education, project,
    in order to import them to elasticsearch.

    :param fileDir: the dir of files after slipting

    :output: save four json files[eke_acount.json,eke_work.json,eke_education.json,eke_project.json] in fileDir.
    '''

    folder = os.path.exists(fileDir)
    if not folder:  # 判断是否存在文件夹如果不存在则创建为文件夹
        os.makedirs(fileDir)

    with jsonlines.open('1.jsonl') as reader:
        for obj in reader:
            eke_acount_id = {"index": {"_id": obj["id"]}}
            eke_work_ids = []
            eke_education_ids = []
            eke_project_ids = []

            for work_id in obj["work"]:
                eke_work_ids.append(work_id)
                # print(work_id)
                # print(obj["work"][work_id])
                eke_work_id = {"index": {"_id": work_id}}
                with open(fileDir+"eke_work.json", "a") as f:
                    json.dump(eke_work_id, f)
                    f.write('\n')
                    json.dump(obj["work"][work_id], f)
                    f.write('\n')
            # print(eke_work_ids)

            for education_id in obj["education"]:
                eke_education_ids.append(education_id)
                # print(education_id)
                # print(obj["education"][education_id])
                eke_education_id = {"index": {"_id": education_id}}
                with open(fileDir + "eke_education.json", "a") as f:
                    json.dump(eke_education_id, f)
                    f.write('\n')
                    json.dump(obj["education"][education_id], f)
                    f.write('\n')
            # print(eke_education_ids)

            for project_id in obj["project"]:
                eke_project_ids.append(project_id)
                # print(project_id)
                # print(obj["project"][project_id])
                eke_project_id = {"index": {"_id": project_id}}
                with open(fileDir+"eke_project.json", "a") as f:
                    json.dump(eke_project_id, f)
                    f.write('\n')
                    json.dump(obj["project"][project_id], f)
                    f.write('\n')
            # print(eke_project_ids)

            eke_acount_value = {"work": eke_work_ids, "education": eke_education_ids, "project": eke_project_ids}
            with open(fileDir + "eke_acount.json", "a") as f:
                json.dump(eke_acount_id, f)
                f.write('\n')
                json.dump(eke_acount_value, f)
                f.write('\n')

def importElasticsearch(fileDir='./data/', fileName='eke_work.json'):
    '''

    :param fileDir:
    :param fileName:
    :return:
    '''
    if not os.path.exists(fileDir + fileName):
        print('no file {} in path {}'.format(fileName, fileDir))

    fileNames = ['eke_work.json', 'eke_project.json']
    if fileName in fileNames:
        with jsonlines.open('1.jsonl') as reader:
            for obj in reader:
                for work_id in obj["work"]:
                    eke_work_id = {"index":{"_id": work_id}}
                    with open(fileName, "w") as f:
                        json.dump(eke_work_id, f)
                        f.write('\n')
                        json.dump(obj["work"][work_id], f)
                        f.write('\n')
                # os.system("curl -H \"Content-Type: application/json\" -XPOST \"localhost:9200/{}/_bulk?pretty&refresh\" --data-binary \"@{}\" ".format(fileName.strip('.json'),fileName))

    path = os.getcwd()
    os.chdir(fileDir)
    # os.system("curl -H \"Content-Type: application/json\" -XPOST \"localhost:9200/{}/_bulk?pretty&refresh\" --data-binary \"@{}\" ".format(fileName.strip('.json'),fileName))
    os.chdir(path)

if __name__== '__main__':
    pass

    # pringetOneSampleFromDataset('1.jsonl'))
    # print('历份数见:{}'.format(getSize()))
    # sliptData2Acount_Work_Education_Project()
    #
    # print('acount数:{}'.format(getSize(inputFilePath='./data/eke_acount.json')/2)) # because two column mean a data, so result /2.
    # print('work数:{}'.format(getSize(inputFilePath='./data/eke_work.json')/2))
    # print('education数:{}'.format(getSize(inputFilePath='./data/eke_education.json')/2))
    # print('project数:{}'.format(getSize(inputFilePath='./data/eke_project.json')/2))
    #
    fileNames = ['eke_acount.json', 'eke_education.json','eke_work.json', 'eke_project.json']
    for file in fileNames:
        importElasticsearch(fileName=file)