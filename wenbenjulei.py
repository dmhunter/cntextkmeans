#-*- coding: UTF-8 -*-
import sys
import os
import urllib
import urllib2
import json 
import lxml
import xmllib
import chardet
import bs4
from bs4 import BeautifulSoup
import shutil
reload(sys)
sys.setdefaultencoding('utf-8')
import jieba
import math
import time
import random
import numpy as np
def getjsonlist(n):
#利用第三方api提供商聚合数据的免费微信热门精选API，抓取1000篇文章的相关信息（包括文章URL等信息），以json列表格式返回数据
	apikey='6e9066524df3ab1977f850637f1f8b5f'
	apiurl='http://v.juhe.cn/weixin/query'
	header={'apikey':apikey}
	doclinksjson=[]
	for i in range(1,n+1):
		urlparam={'pno':i,'ps':100,'key':apikey,'dtype':'json'}
		geturl=apiurl+'?'+urllib.urlencode(urlparam)
		weixinrequest=urllib2.Request(geturl)
		weixinwenzhang=urllib2.urlopen(weixinrequest).read()
		doclinksjson.append(json.loads(weixinwenzhang))
	return doclinksjson
def writejsoninfo(jsonfilelist):
#将获取到的json文件中的文章标题，公众号，文章链接保存到文件。
	wxdoc=open('微信精选文章.txt','w')
	content=''
	for k in range(0,len(jsonfilelist)):
		for i in jsonfilelist[k]['result']['list']:
			content+='文章标题:'+i['title']+'\n'+'公众号:'+i['source']+'\n'+'文章链接:'+i['url']+'\n'
	wxdoc.write(content)
	wxdoc.close()
	print "精选文章，公众号，文章链接已保存!"
def getwxtxt(jsonfilelist):
#根据json返回的文件中的url获取微信中的文章，并将文章中的文本内容抓取下来，保存到本地。
	if os.path.exists(r'微信精选文章/'):	
		shutil.rmtree(r'微信精选文章/')
		os.mkdir(r'微信精选文章/')	
	else:
		os.mkdir(r'微信精选文章/')
	for i in range(0,len(jsonfilelist)):
		for k in jsonfilelist[i]['result']['list']:
			url=k['url']
			wxrequ=urllib2.Request(url)
			wxresp=urllib2.urlopen(wxrequ).read()
			wxbs=BeautifulSoup(wxresp)
			if wxbs.find('div',class_='rich_media_content'):			
				wxcontent=wxbs.find('div',class_='rich_media_content').get_text()
			else:		
				continue		
			if len(wxcontent)<200:	
				continue
			else:
								
				wxfile=open(r'微信精选文章/'+wxbs.title.get_text().replace(r'/','&')+'.txt','w')  #有的文章标题中有/这样的字符，与文件名规范冲突，需要转换一下
				wxfile.write(wxcontent)
				wxfile.close()
	print "精选文章的文本信息写入成功！"
	return os.listdir(r'微信精选文章/')

def docfenci(doclist):
#将文档列表中的文档分词，去除其中的停用词
	stopwords=open('stopwords.txt','r').read() #读取中文停用词大全，分词后的列表中将将停用词删除，避免占用过多内存	
	quanbufenci=[]
	txtfileid=dict()
	a=0
	textidfenci=dict()
	for txtfile in doclist:   #os.listdir(doclist):
		txtfileid.update({a:txtfile})
		txt=open(r'微信精选文章/'+txtfile,'r').read()
		fencilist=jieba.cut(txt,cut_all=True)
		fenciperlist=[]
		for fenci in fencilist:
			if fenci in stopwords or fenci=='\n':
				continue					
			else:
				fenciperlist.append(fenci)
#		print u'%s' % fenciperlist
		textidfenci.update({a:fenciperlist})
		quanbufenci+=fenciperlist
		a+=1
	fencidictlist=list(set(quanbufenci))
	txtfileid=sorted(txtfileid.iteritems(),reverse=False)
	return textidfenci,fencidictlist,txtfileid #返回所有文章的分词结果以及分词的集合
def wordfreq(textidfenci,fencidictlist):
#统计所有文章的所有词频
#所有文档的分词的集合，剔除了重复项
	fencisetlist=[]
	basedata=[[0 for col in range(len(fencidictlist))] for row in range(len(textidfenci))]
	m=0
#	fencilistf=open('分词列表.txt','w')
	for i in fencidictlist:
#		fencisetlist.append(i)
#		fencilistf.write(i)
		j=0
		for k in textidfenci: #这样的遍历，k表示字典的键，很容易弄错,要注意
			basedata[j][m]=textidfenci[k].count(i)
			j+=1
		m+=1
	print '文档词频统计已完成！'
#	print basedata
	return basedata  #返回以分词为列，文档为行的二维数组，数组值表示对应文档对应分词出现次数
def tfidf(basedata):
#根据TF-IDF算法提取特征词汇
	worddocs=[]
	for i in range(len(basedata[0])):
		persumifs=0
		for j in range(len(basedata)):
			persumifs+=basedata[j][i]
		worddocs.append(persumifs)
	idfs=[]
	for i in range(len(worddocs)):
		idfs.append(math.log(float(len(basedata))/(worddocs[i]+1)))
	for i in range(len(basedata)):
		b=sum(basedata[i])
		for j in range(len(basedata[0])):
			basedata[i][j]*=float(idfs[j])/(b+1)
	return basedata
def topwords(idfswordlist,n=10):
#返回一个列表中前10大元素以及其角标,如果前10大元素中有小于０的元素，则列表可不用达到10个元素
	topfeaturedict=dict()
	for i in range(n):
		feature=max(idfswordlist)
		if feature>0:
			index=idfswordlist.index(feature)
			topfeaturedict.update({feature:index})
			idfswordlist[index]=-100
		else:
			break
	topfeaturedict=sorted(topfeaturedict.iteritems(),reverse=True)
	return topfeaturedict   #返回{特征值１：该特征值在原始文档向量中的角标，特征值２：特征值在原始文档向量中的角标，...｝按特征值降序排列之后的元组列表[(最大特征值，最大特征值的角标)，(第二大特征值，该特征值的角标),(..)...]

	
def showfeaturewords(topfeaturedict,fencidictlist):
#根据提取的前10大tfidf特征值找到特征词
	topfeaturewords=[]
	for j in topfeaturedict:
		topfeaturewords.append((fencidictlist[j[1]],j[0]))
	return topfeaturewords
#返回一个文档的前１０大特征词与特征值对应的列表[(特征值最大的特征词,特征值),(特征值第二大的特征词,特征值),(..)...]

def savetopfeaturewords(basedata,fencidictlist,docstopwords=topwords,docsfeaturewords=showfeaturewords):
#找到各个文档与对应的前10大特征词,并保存
	docstopfeaturewords=[]
	for i in range(len(basedata)):
#		print '第',i+1,'篇文章的特征词是：',docsfeaturewords(docstopwords(basedata[i]),fencidictlist),'\n'
		docstopfeaturewords.append(docsfeaturewords(docstopwords(basedata[i]),fencidictlist))
	return docstopfeaturewords
#返回所有文档的前１０大特征词与特征值对应的列表汇总，数据结构为[[(特征词１,特征词１的特征值),(特征词２,特征词２的特征值),(..)...],[第二篇文档的前１０大特征词与特征值对应字典],[..]...],按文档顺序排列

def featurewords(docstopfeaturewords):
#返回所有文档的前１０大特征词列表汇总，数据结构为[[文档１的前１０大特征词],[文档２的前１０大特征词],[..]...],其中各文档的特征词列表按照对应特征值降序的顺序对应排列
	featurewordslist=[]
	for i in docstopfeaturewords:
		featurewords=[]		
		for j in i:
			featurewords.append(j[0])
		featurewordslist.append(featurewords)
	return featurewordslist


def docfeature(docstopfeaturewords,basedata,featurewordslist):
#将得到的各个文档的特征词形成集合，组成文档id－特征词的二维表格，表格的值即为各文档对应的特征词的tfidf值。
	featuresum=[]
	for i in range(len(docstopfeaturewords)):
		for j in range(len(docstopfeaturewords[i])):
			featuresum.append(docstopfeaturewords[i][j][0])
	featuresumset=set(featuresum)
	featuresumsetlist=list(featuresumset)
#	print featuresumsetlist
	docfeaturetable=[[0 for col in range(len(featuresumset))] for row in range(len(basedata))]
	for i in range(len(basedata)):
		for j in range(len(featuresumsetlist)):
			if featuresumsetlist[j] in featurewordslist[i]:
				docfeaturetable[i][j]=docstopfeaturewords[i][featurewordslist[i].index(featuresumsetlist[j])][1]     
	return docfeaturetable

def distance(alist,blist):
#计算两个向量间的距离
	listdistance=[pow((float(alist[i])-blist[i]),2) for i in range(len(alist))]	
	docdistance=math.sqrt(sum(listdistance))	
	return docdistance

def nearmean(docfeaturetable,docidlist,xiangliangdistance=distance):
#寻找一组文档向量中最接近均值的向量,docfeaturetable是文档id-特征词二维表格，doclist是文档id列表，k是每个向量的维数
	docmean=[]
	for i in range(len(docfeaturetable[0])):
		docsum=0
		for j in range(len(docidlist)):
			docsum+=docfeaturetable[docidlist[j]][i]
		docmean.append(float(docsum)/len(docidlist))  #得到均值向量
	docdistances=[]
	for i in docidlist:
		docdistances.append(xiangliangdistance(docfeaturetable[i],docmean))
	return docidlist[docdistances.index(min(docdistances))]


def compare(lastcluster,presentcluster):
#每次聚类结果为[[],[],[],[]...],需判断相邻两次聚类结果是否一致
	lastlist=[]
	presentlist=[]	
	if len(lastcluster)!=len(presentcluster):
		return False
	else:	
		for i in range(len(lastcluster)):
			lastlist.append(set(lastcluster[i]))
			presentlist.append(set(presentcluster[i]))
		a=0	
		for i in lastlist:
			for j in presentlist:
				if i==j:
					a+=1
					break
				else:
					continue
		if a==len(lastcluster):
			return True
		else:
			return False


def krandom(k,docnumber):
#在０～文档总数之间随机生成ｋ个互不相同的随机整数
	krandomlist=[]
	for i in range(k):
		a=int(round(random.random()*docnumber))
		while a in krandomlist:
			a=int(round(random.random()*docnumber))
		krandomlist.append(a)
	return krandomlist

def tablekmeans(docfeaturetable,k,docdistances=distance,nearmeanfun=nearmean,comparecluster=compare,krandoms=krandom):
#根据得到的文档－特征词二维表格，运用Kmeans算法进行分类
#随机选择k个文档作为初始聚类中心
	krandom=krandoms(k,len(docfeaturetable))
	initclusters=list()
	for i in range(len(krandom)):
		initclusters.append([krandom[i]])
	for i in range(len(docfeaturetable)):
		if i not in krandom:
			distances=[]
			for j in krandom:
				distances.append(docdistances(docfeaturetable[i],docfeaturetable[j]))
			initclusters[distances.index(min(distances))].append(i)

 #整理成｛聚类中心文档１:set(文档×××,文档×××,...),聚类中心文档２:set(文档×××，文档×××,...)...｝
	lastcluster=initclusters
	presentcluster=list()
	clusterresult=initclusters
	while comparecluster(lastcluster,clusterresult)!=True:
		newcenterlist=[]		
		for i in lastcluster:
			newcenterlist.append(nearmeanfun(docfeaturetable,i))
#		print '-----',newcenterlist
		lastcluster=clusterresult
		presentcluster=list()
		for i in range(len(newcenterlist)):
			presentcluster.append([newcenterlist[i]])
		for i in range(len(docfeaturetable)):
			if i not in newcenterlist:
				newdistances=[]
				for j in newcenterlist:
					newdistances.append(docdistances(docfeaturetable[i],docfeaturetable[j]))
				presentcluster[newdistances.index(min(newdistances))].append(i)
		clusterresult=presentcluster
	return clusterresult

def listsum(alist,blist):
#对两个相同长度的列表进行分别求和，形成新列表，例如[1,2,3]+[0,1,2]得到[1,3,5]
	result=[]
	if len(alist)!=len(blist):
		print "列表长度不一致，不能相加！"
		return False
	else:
		for i in range(len(alist)):
			result.append(alist[i]+blist[i])
		return result		

def clusterwords(clusterresult,basedata,fencidictlist,topwordsfun=topwords,listsumfun=listsum):
#根据聚类结果，给出各类最具代表性的特征词
	clusterfeaturewords=[]
	clustertfidfsumlist=[[0 for i in range(len(basedata[0]))] for j in range(len(clusterresult))]
	for i in range(len(clusterresult)):	
		for j in clusterresult[i]:
			clustertfidfsumlist[i]=listsumfun(clustertfidfsumlist[i],basedata[j])
	features=[]
	for i in range(len(clustertfidfsumlist)):	
		features.append(topwordsfun(clustertfidfsumlist[i]))
	for i in range(len(features)):
		perfeaturewords=[]		
		for j in range(len(features[i])):
			perfeaturewords.append(fencidictlist[features[i][j][1]])
		clusterfeaturewords.append(perfeaturewords)
	return 	clusterfeaturewords		


def main():
#主函数体
	start=time.clock()
	#json=getjsonlist(10)
	#writejsoninfo(json)
	#f=getwxtxt(json)  #ip被微信封杀，这里至对之前抓取的一部分（接近400篇）文档进行聚类分析,因此前面这几行程序就注释掉，不运行
	b=docfenci(os.listdir(r'微信精选文章/'))
	basedata=tfidf(wordfreq(b[0],b[1]))
	c=savetopfeaturewords(basedata,b[1])
	d=docfeature(c,basedata,featurewords(c))
	e=tablekmeans(d,10)
	print e
	print "========================================================\n"
	features=clusterwords(e,basedata,b[1])
	for i in features:
		for j in i:
			print j	,
		print '\n******************************************************\n'
	end=time.clock()
	print '运行时间:',end-start,'秒'
	print 'CurrentTime:',
	print time.strftime('%Y-%m-%d %I:%M:%S', time.localtime())

if __name__=="__main__":
	main()
