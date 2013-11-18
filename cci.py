import copy
import os
import re
import xml.etree.ElementTree as ET
import pdb

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
		tree = ET.parse(file)
		articleNode = tree.find("object[@kind='Article']")
		if(articleNode is None):
			return None
		ccitextNode = articleNode.find("content/data/cci:ccitext", namespaces=ns)
		article['fly'] = getText(ccitextNode.find("*[@displayname='fly']"))
		article['headline'] = getText(ccitextNode.find("*[@displayname='head']"))
		article['location'] = getText(ccitextNode.find("*[@displayname='rubric']/*[@displayname='dateline']"))
		if(article['location'] is None):
			article['rubric'] = getText(ccitextNode.find("*[@displayname='rubric']/cci:p", namespaces=ns))
		else:
			article['rubric'] = ccitextNode.find("*[@displayname='rubric']/*[@displayname='dateline']", namespaces=ns).tail.strip()
		article['content'] = getContent(ccitextNode.find("cci:body", namespaces=ns))
		article['correction'] = getContent(ccitextNode.find("*[@displayname='correction']", namespaces=ns))
		pageNode = articleNode.find("parents/*[@kind='Page']")
		if(pageNode is not None):
			sectionPage = getText(pageNode.find("*/*[@name='PageNameCont']"))
			sectionParts = re.split("(\d+)", sectionPage)
			article['section'] = {
				'name': sectionParts[0],
				'page': sectionParts[1]
			}
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
	ret = """
<!DOCTYPE nitf PUBLIC "http://www.nitf.org/dtds/nitf-x020-strict.dtd" "nitf-x020-strict.dtd">
<nitf>
	<head>
		<title>{headline}</title>
		<docdata>
			<date.issue norm="20130824" />
		</docdata>
		<pubdata date.publication="20130824" edition.area="UKPB" edition.name="ECN" name="The Economist Newspaper" position.section="BRITAIN" position.sequence="BR2" volume="408" number="8850" issue="1" />
		<revision-history function="editor" name="" />
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
			<p>MIRANDA warnings, as fans of American cop shows know, begin by informing thugs that they have “the right to remain silent”—quoting a Supreme Court ruling in 1966 in favour of Ernesto Miranda, who had not been told this. In Britain, the same name is becoming a rallying point against different legal excesses.</p>
			<p>
				On August 18th the Terrorism Act 2000 was used to detain David Miranda, a Brazilian who was carrying materials for the
				<em class="Italic">Guardian</em>
				newspaper between two journalists: Laura Poitras, a documentary film-maker in Berlin, and Glenn Greenwald, a resident of Rio de Janeiro and
				<em class="Italic">Guardian</em>
				reporter who has written stories based on leaks by Edward Snowden, a former contractor for America’s National Security Agency. Mr Miranda was questioned for nine hours at Heathrow airport, the maximum allowed under the act. His laptop, a hard drive and even his digital watch were confiscated.
			</p>
			<p>It initially appeared as if Mr Miranda had been targeted because he is Mr Greenwald’s partner. Yet the detention seems to have been for what he may have been carrying, not who he is. Theresa May, the home secretary, justified it by pointing to the danger that classified material could fall into the wrong hands. If the police believe somebody might have “highly sensitive stolen information” they can act, she explained. She was informed in advance of the detention, as were Downing Street and the White House. She claimed it was not within a minister’s power to intervene in a police matter. “Long may that continue,” she said.</p>
			<p>Yet it is surely within her remit to question the detention of Mr Miranda, and in particular its legal grounds: why, otherwise, were she and other officials notified in advance?</p>
			<p>The Terrorism Act 2000 was aimed at Irish republican terrorism. One section gives police exceptional powers to question travellers at British borders for up to nine hours—without suspicion and without a lawyer. Refusal to answer is itself a crime. (Mr Miranda was forced to divulge encryption passwords.) Police may seize property, though it must be returned. The only constraint is that the purpose should be to ascertain if the person “is or has been concerned in the commission, preparation or instigation of acts of terrorism”.</p>
			<hl2 class="subhead" style="subhead">Mightier than the pen</hl2>
			<p>
				This looks preposterous in Mr Miranda’s case, if the term terrorism is to have meaning. The editor of the
				<em class="Italic">Guardian</em>
				, Alan Rusbridger, decried the incident as “conflating terrorism and journalism”.
			</p>
			<p>The authorities are certainly more assertive these days. Mr Rusbridger disclosed that, a month ago, officials from Britain’s spy agency, GCHQ, oversaw the smashing up of computers that contained copies of the leaked documents in the newspaper’s basement—even though other copies existed in Brazil and New York, whence much of the reporting was emanating. Even the White House press secretary opined that America would not resort to that.</p>
			<p>The police defended their use of the act as “legally and procedurally sound”. Yet David Anderson QC, who oversees compliance with the act, points out that it is unusual. During the questioning, the police said Mr Miranda would be in for a full nine hours. Mr Anderson is looking into whether the police applied the act correctly or if they abused their authority.</p>
			<p>A move to reform the anti-terrorism law, including a reduction of the maximum time of detention to six hours, is already underway—supported by Mrs May—and is set to be debated in Parliament this autumn. Lord Falconer, who helped introduce the legislation and later became Lord Chancellor under Tony Blair, says that the act “does not apply, either on its terms or in its spirit, to Mr Miranda”. Perhaps one day British police officers will get their own Miranda rules.</p>
		</body.content>
		<body.end />
	</body>
</nitf>
		""".format(**article)
	print(ret)

#path = "C:\\Users\\jamestsao\\Desktop\\OnlineExport"
#path = "C:\\Users\\jamestsao\\Desktop\\CCI_20300824"
path = "C:\\Users\\jamestsao\\Desktop\\OnlineExport (new)"
#path = "C:\\Users\\jamestsao\\Desktop\\OnlineExport (new)\\Economist_ECN_APSI_1_BR2_Surburban London.ART.2_GLA3RFGH.1"

for root, subFolders, files in os.walk(path):
	processedOne = False
	for file in files:
		if(len(subFolders) > 0):
			continue
		elif(os.path.splitext(file)[1].upper() != '.XML'):
			continue
		else:
			print(os.path.join(root, file))
			article = process(os.path.join(root, file))
			toXml(article)
			# print(article)
			processedOne = True
			break
	if(processedOne):
		break
