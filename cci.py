import copy
import os
import re
from lxml import etree
from xml.dom.minidom import parseString
import time
from time import strftime

ns = {
	"cci": "urn:schemas-ccieurope.com",
	"ccit": "http://www.ccieurope.com/xmlns/ccimltables",
	"ccix": "http://www.ccieurope.com/xmlns/ccimlextensions"
}

tagMap = {
	"italic": "italics",
	"capitals": "caps"
}

def process(file):
	try:
		article = {}
		tree = etree.parse(file)

		articleNode = tree.find("object[@kind='Article']")
		if(articleNode is None):
			return None

		importFileName = getText(articleNode.find("attributes/*[@name='Name']"))

		ccitextNode = articleNode.find("content/data/cci:ccitext", namespaces=ns)
		article['fly'] = getText(ccitextNode.find("*[@displayname='fly']"))
		article['headline'] = getText(ccitextNode.find("*[@displayname='head']"))
		article['location'] = getText(ccitextNode.find("*[@displayname='rubric']/*/*[@displayname='dateline']"))
		if(article['location'] is None):
			article['rubric'] = getText(ccitextNode.find("*[@displayname='rubric']/cci:p", namespaces=ns))
		else:
			ccitextTags = ccitextNode.findall("*[@displayname='rubric']/cci:p", namespaces=ns)
			article['rubric'] = getText(ccitextTags[-1])

		article['content'] = getContent(ccitextNode.find("cci:body", namespaces=ns))
		article['correction'] = getContent(ccitextNode.find("*[@displayname='correction']", namespaces=ns))

		# duKeyName and duKeyVersion
		textNode = articleNode.find("children/*[@kind='Text']")
		if(textNode is not None):
			article['duKeyName'] = getText(textNode.find("*/*[@name='Name']"))
			article['duKeyVersion'] = getText(textNode.find("*/*[@name='Version']"))

		pageNode = articleNode.find("parents/*[@kind='Page']")
		if(pageNode is not None):
			sectionPage = getText(pageNode.find("*/*[@name='PageNameCont']"))
			sectionParts = re.split("(\d+)", sectionPage)
			# pubDate
			pubDateSimple = getText(pageNode.find("*/*[@name='PubDateCont']"))
			pubDate = strftime("%Y%m%d", time.strptime(pubDateSimple, "%d-%m-%Y"))

			article['section'] = {
				'positionSequence': sectionPage,
				'name': sectionParts[0],
				'page': sectionParts[1],
				'pubDate': pubDate,
				'editionArea': getText(pageNode.find("*/*[@name='ZoneCont']")),
				'editionName': getText(pageNode.find("*/*[@name='ProductNameCont']"))
			}

			if(importFileName is not None):
				importFileName = os.path.splitext(importFileName)[0]
				importFileName = importFileName.replace(" ", "_")
				article['fileName'] = importFileName+'_'+pubDateSimple+'.art'

		# Media/images.
		photoNodes = articleNode.findall("children/*[@kind='Photo']")
		if(photoNodes is not None):
			article['images'] = []
			for photoNode in photoNodes:
				imageName = getText(photoNode.find("*/*[@name='Name']"))
				article['images'].append({'name': imageName})
		return article
	except Exception as e:
		print("ERROR: {}".format(e))
		return None


def getText(root):
	if(root is None):
		return None
	ret = ""
	for node in root.iter():
		if(node.text is None):
			continue;
		tag = extractTag(node)
		if(tag in tagMap):
			ret += "<{0}>{1}</{0}>".format(tagMap[tag], node.text)
			if(node.tail is not None):
				ret += node.tail.rstrip()
		else:
			ret += node.text.strip()
	return ret

def getContent(root):
	if(root is None):
		return None
	ret = []
	for node in root.findall("./"):
		tag = extractTag(node)
		if(tag == "p"):
			ret.append({
				'type': 'paragraph',
				'content': ''.join(getText(node))
				})
		elif(tag == "subhead"):
			ret.append({
				'type': 'subhead',
				'content': ''.join(getText(node))
				})
		else:
			continue
	return ret

def extractTag(node):
	return re.sub("{.*}","",node.tag)

def NoneToEmptyStr(d):
	for k in d:
		if d[k] is None:
			d[k] = ''
		elif type(d[k]) == dict:
			NoneToEmptyStr(d[k])
		elif type(d[k]) == list:
			for i in d[k]:
				NoneToEmptyStr(i)
	return d

def toXml(article):
	article = NoneToEmptyStr(copy.deepcopy(article))
	output = """
<!DOCTYPE nitf PUBLIC "http://www.nitf.org/dtds/nitf-x020-strict.dtd" "nitf-x020-strict.dtd">
<nitf>
	<head>
		<title>{headline}</title>
		<meta name="PagesEU" content="44"/>
		<meta name="PagesAP" content="47"/>
		<meta name="PagesUK" content="52"/>
		<meta name="PagesUS" content="44"/>
		<docdata>
			<doc-id id-string="5A426P3"/>
			<du-key generation="{duKeyVersion}" key="{duKeyName}"/>
			<urgency ed-urg="0"/>
			<date.issue norm="{section[pubDate]}"/>
		</docdata>
		<pubdata date.publication="{section[pubDate]}" edition.area="{section[editionArea]}" edition.name="{section[editionName]}" name="The Economist Newspaper" position.section="{section[name]}" position.sequence="{section[positionSequence]}" volume="409" number="8859" issue="1"/>
		<revision-history function="editor" name=""/>
	</head>
	<body>
		<body.head>
			<hedline>
				<hl1>{headline}</hl1>
				<hl2 class="fly">{fly}</hl2>
			</hedline>
			<dateline>
				<location>{location}</location>
			</dateline>
			<abstract>
				<hl2 />
			</abstract>
		</body.head>
		<body.content>
			<media media-type="image">
				<media-reference mime-type="image/jpeg" name="20130824_BRP004" data-location="20130824_BRP004.jpg" source="20130824_BRP004.jpg" width="159" height="280" />
				<media-caption>Someone will be there to meet you</media-caption>
				<media-producer />
			</media>
			<p class="rubric">{rubric}</p>
			<p>{content}</p>
		</body.content>
		<body.end />
	</body>
</nitf>
		""".format(**article)
	# print output

	# Save to .art file.
	# TODO : need to replace with fast library, for now using minidom
	# because its quite easy to write however it can be very slow.
	doc = parseString(output)

	with open(article['fileName'], "w") as f:
		f.write( doc.toxml('ISO-8859-1') )

path = os.path.join(os.path.dirname(__file__), 'import-xml')

for root, subFolders, files in os.walk(path):
	processedOne = False
	counter = 0
	for file in files:
		if(len(subFolders) > 0):
			continue
		elif(os.path.splitext(file)[1].upper() != '.XML'):
			continue
		else:
			print(os.path.join(root, file))
			article = process(os.path.join(root, file))
			toXml(article)
			counter += 1
			# If you like to process just one file, uncomment these lines.
			# processedOne = True
			# break
	# if(processedOne):
		# break
	print counter, 'files have been processed.'
