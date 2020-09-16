# ES-KG-Recommended（大数据下简历的搜索和排序）

## 仓库建立初衷

主要是因为参加第二届“慧源共享”全国高校开放数据创新研究大赛，然后这里就是我们团队存放代码和相关文件的地方了。

至于为什么选择e成科技简历脱敏调查数据集来做目前这个大数据下简历的搜索和排序，主要是因为团队成员同样将面临找工作的问题，希望能够对我们有所启发；另一个就是其他数据集很多是来自图书馆的数据，这个个人感觉只能得到统计学上的结果。虽然可能是因为主办单位有许多高校图书馆。
Elasticsearch
大家在浏览仓库代码或文件的时候可能会产生一些文件不存在等的疑问，这主要是因为比赛数据不能公开，望大家见谅。

## 代码环境
### 硬件环境
主要是我们团队成员的个人笔记本（PC），配置就不在这里列了，相信大家目前PC的基本配置都是可以支撑程序运行的。
### 软件环境

1. 操作系统：ubuntu18.04，所以我们不保证在其他操作环境下能够正常运行；
2. 相关软件：
    1. Elasticsearch:主要承担简历数据的存储和搜索；
    2. Kibana：可以辅助对Elasticsearch进行操作；
    3. Pycharm：主要编写python脚本程序，实现对Elasticsearch的自动化操作；
    4. Anaconda:主要是为python提供第三方库；
    5. jupyter notebook：可以交互式编程，主要负责测试工作。

### 软件环境的安装配置

这里暂时就不赘述了，主要用的都是主流系统、软件和开源软件。后期有空在详细写下安装配置过程。

1. ubuntu18.04：这个系统镜像如果从官网下载的话，速度真心还不慢。可以点击[here](http://jxz2dz.natappfree.cc/static/files/ubuntu-18.04.4-desktop-amd64.iso)帮我测试下是否能从我自己搭建的网站下载。至于系统安装就不详细介绍了，百度一下啥都有，主要区别在于不同品牌的电脑进入BISO的操作略微有些不同。
2. Elasticsearch：这是开源软件，有自己的官网。人家的教程比我的详细，只要安装成功就可以了。点击在[here](http://jxz2dz.natappfree.cc/static/files/)下载。
3. kibana：同Elasticsearch。点击在[here](http://jxz2dz.natappfree.cc/static/files/kibana-7.8.0-amd64.deb)下载。
4. Pycharm：ubuntu的应用商店就有，点击安装就可以了。点击在[here](http://jxz2dz.natappfree.cc/static/files/pycharm-community-2020.1.2.tar.gz)下载。
5. Anaconda：这个网上教程很多，点击在[here](http://jxz2dz.natappfree.cc/static/files/Anaconda3-2020.02-Linux-x86_64.sh)下载。
6. jupyter notebook: 这个安装了Anaconda也就有了。

## First：认识数据

这里主要是熟悉，了解，探索一下简历数据是怎样，各字段都代表什么含义，如何着手进行研究等等。参考[exploreData.ipynb](./dataset/exploreData.ipynb)

### 一个简历样本数据

![简历结构](./images/structure.png)

具体的简历数据样本和样本数据中各字段含义可到[exploreData.ipynb](./dataset/exploreData.ipynb)查看。可以看出一份简历主要有4部分构成：

1. id： 表示了简历的所属人；
2. 教育经历：主要包括受教育时间，受教育高校，学习专业；
3. 工作经历：工作过的公司，时间，规模，职位等；
4. 项目经历：参与的项目，负责内容，时间等。

### 外引数据——schoolRange.xlsx

在该数据表中主要存储了中国高校排名，参考[2019-2020中国大学排名800强完整榜单（校友会最新版）](https://www.dxsbb.com/news/5463.html)，内部的缺失数据已经人工补齐。主要用于在为搜索到的简历排序时，为教育经历提供参考依据。

## 




