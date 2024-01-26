from collections import defaultdict
import datetime
from pprint import pformat, pprint
import regex as re
import sys
import time
from xml.sax.saxutils import unescape

from moss_dump_analyzer import read_en_article_text
from moss_entity_check import skip_article_strings
from wikitext_util import get_main_body_wikitext

# Run time: 1h40m per 100,000 articles (before performance improvements)

transform_dict = {}
with open("/var/local/moss/bulk-wikipedia/Typos", "r") as regex_file:

    for line in regex_file:
        if "Typo" not in line:
            continue
        line = unescape(line)
        line = line.replace("</span>", "")
        line = re.sub("<span.*?>", "", line)

        if "disabled" in line:
            continue
        if "find=" not in line:
            continue
        attribute = re.search('find="(.*?)" replace="(.*?)"', line, re.MULTILINE)
        if attribute:
            if attribute[1] == "Regex code to detect the error":
                continue
            replacement = re.sub(r"\$([0-9])", r"\\\1", attribute[2])
            transform_dict[attribute[1]] = replacement

regexes = list(transform_dict.keys())

regex_frequencies = {

    # N=5000
    '(?<=\\b(?:[aA]ccid|[cC]li|[dD]isobedi|[eE]xcell|[iI]ngredi|[lL]eni|[oO]bedi|[sS]uperintend|[tT]ranscend|[vV]iol))an(c[ey]|t[a-z]*)\\b(?<!Violant[aei])': 1,  # noqa
    '(?<=\\s+(?:a(?:re|s)|As|be(?:c(?:ame|om(?:e|ing))|en|ing)|is|not|to\\s+be|w(?:as|ere))(?:\\s+(?:al(?:l|so)|now))?\\s+)\\bapart\\s+of\\b': 1,  # noqa
    '(?=b(?:il|li))(?<=\\b(?:[A-Z][a-z]*|[a-z]+))b(?:il|li)(?:li?)?t(ies|y)\\b': 1,  # noqa
    "\\b(1\\d\\d0|20\\d0)['’´ˈ׳᾿‘′Ꞌꞌ`]s(?<=\\b(?:[aA]n?|[tT]he)\\s{1,9}(?:earl(?:ier|y)|later?|mid(?:dle)?)?[–‑−—―\\s]{0,9}(?:1\\d|20)\\d0['’´ˈ׳᾿‘′Ꞌꞌ`]s)": 1,  # noqa
    '\\b(?:br(?:it?|ri)?t(ains?|i(?:cisms?|sh(?:ers?|isms?|ly|ness)?)|ney|ons?|pop|tany))\\b': 1,  # noqa
    '\\b([aA])(?:thorith?|ut(?:h(?:orith|rorith?)|orith?))([a-z]+)\\b(?<!Autorit(?:eit|ratto))': 1,  # noqa
    '\\b([bB])illard(s)?\\b(?<!\\b(?:[A-Z][a-z]+ (?:[A-Z]\\. )?Billard|de Billard))': 1,  # noqa
    '\\b([cC]o[ck][ae][–‑−—―\\s]*[cC]ola|[cC]oca-cola)\\b': 1,  # noqa
    '\\b([cC]on|[oO]c|[rR]e(?:oc)?)cur(?:[ae]|ra)n(ces?|t(?:ly)?)\\b': 1,  # noqa
    '\\b([dD])e[-–‑−—―]?facto\\b': 1,  # noqa
    '\\b([dD]is|[eE]x|[iI]n(?:dis|ex|sus)|[sS]us)penc(a(?:bl[ey]|r(?:ies|y)|tions?)|e(?:[ds]?|rs?)|ful|i(?:ng|ve(?:ly|ness)?))\\b': 1,  # noqa
    '\\b([eE])stimated\\s+at\\s+(?:a(?:bout|pprox(?:imately|\\.)|round)|roughly)\\b': 1,  # noqa
    '\\b([hH](?:a(?:pp|st)|eav))ily-(?=[a-z]+\\b)(?![a-z]+-)': 1,  # noqa
    '\\b([hwHW]|[sS][hw])e[;’´ˈ׳᾿‘′Ꞌꞌ`]([ds]|ll)\\b': 1,  # noqa
    '\\b([oO])c(?:curr?a|ur(?:[ea]|r(?:[ae]|r+e)))n(ces?|t)\\b': 1,  # noqa
    '\\b([pP])ublicly-(?=[a-z]+ed\\b)': 1,  # noqa
    '\\b([sS])tone[–‑−—―\\s]mason(s)?\\b': 1,  # noqa
    '\\b([tT])r(?:ipti|ypt[iy])ch(s)?\\b(?!\\.\\w)': 1,  # noqa
    '\\b([tT])wel(?:f|th)(s)?\\b': 1,  # noqa
    '\\bMombassa\\b': 1,  # noqa
    '\\bProfessor(?<=\\b(?:[aA]|[fF]ormer|[tT]enure(?:d|-[tT]rack)|[vV]isiting)\\s+\\w+)(?=(?:[,;\\.\\)]|\\s+(?:at\\s|in\\s|o[fn]\\s)))': 1,  # noqa
    "\\bWisden\\s+Cricketer(?:[';’´ˈ׳᾿‘′Ꞌꞌ`]s\\s+Alm[ae]nack?|s(?:\\s+Almanack?|['’´ˈ׳᾿‘′Ꞌꞌ`]\\s+Almanack?|'\\s+Alm[ae]nac))\\b": 1,  # noqa
    '\\b[aA]rai?b(an?s?|ia?n?s?|ns?|s?)\\b(?<!Arab(?:ia(?:ns?)?|s?))': 1,  # noqa
    '\\b[bB]lu\\s?[rR]ay\\b': 1,  # noqa
    '\\b[bB]ritt+(anni[ac]|ish)\\b': 1,  # noqa
    '\\b[cC](?:ovid[-–‑−—―\\s]?|OVID[–‑−—―\\s])19\\b': 1,  # noqa
    '\\b[gG]hanian(s)?\\b': 1,  # noqa
    '\\b[gG]ithub\\b(?!\\.io)': 1,  # noqa
    '\\b[oO]tt?om[ae]n\\s+empire\\b': 1,  # noqa
    '\\b[yY]ukon\\s+[tT]erritory\\b': 1,  # noqa
    '\\baustr(al|ones)?ia(ns?|s?)\\b': 1,  # noqa
    '\\bbaham+(an?s?|ians?)\\b': 1,  # noqa
    '\\bbenin(ians?)?\\b': 1,  # noqa
    '\\bbrazill?(ians?)?\\b': 1,  # noqa
    '\\bbur(kina|m(?:a|ese)|urundi(?:ans?)?)\\b': 1,  # noqa
    '\\bcol([ou])mbia(ns?)?\\b': 1,  # noqa
    '\\bgre(cian|e(?:ce|ks?))\\b': 1,  # noqa
    '\\bhind(is?|u(?:s(?:tan(?:is?)?)?)?|uism)\\b': 1,  # noqa
    '\\bhungar(ians?|y)\\b': 1,  # noqa
    '\\blong\\s+standing\\b(?<=\\b(?:[aA]|[tT]he)\\s+long\\s+standing)(?!\\s+(?:in\\b|o(?:f\\b|vation\\b)))': 1,  # noqa
    '\\bmal+ay(a(?:l(?:am|i)|ns?|s?)|s?|sian?s?)\\b': 1,  # noqa
    '\\bpurpose\\s+built(?=\\s+(?:arenas?|buildings?|c(?:ampus|lubhouse|om(?:munity|plex))|depot|f(?:ac(?:ilit(?:ies|y)|tor(?:ies|y))|o(?:otball|r))|g(?:a(?:llery|rage)|round)|location|m(?:osques?|useum)|new|offices?|premises|road|s(?:chool|et|ite|t(?:a(?:dium|ge)|ore|rip|udios?))|t(?:heatre|raining)|unit)\\b)|purpose(?<=(?:,|\\b(?:[aA]|first|its|new|[tT]he))\\s+\\w+)\\s+built\\b': 1,  # noqa
    '\\btagalog\\b': 1,  # noqa
    '\\btake\\s+off\\b(?<=\\b(a(?:fter|t)|before|during|its|on)\\s+take\\s+off)': 1,  # noqa
    '\\s?,\\s?\\s?,\\s?': 1,  # noqa
    '([\\d\\.]+(?:[–‑−—―\\s]|&nbsp;)?)[gG](?:Bit(?:[p\\/]se?c?|s[p\\/]se?c?)|b(?:it(?:[p\\/]se?c?|s[p\\/]se?c?)|[p\\/]se?c?|s[p\\/]se?c?))\\b': 2,  # noqa
    '(\\d(?:[–‑−—―\\s]|&nbsp;)?[µmkMGT])w\\b': 2,  # noqa
    '\\b([bB]as(?:e|ket)|[cC]annon|[fF]oo[st]|[hH]and|[kK]ick|[pP](?:addle|ickle)|[sS](?:now|pit|tick)|[vV]olley)[–‑−—―\\s]+ball(s)?\\b': 2,  # noqa
    '\\b([bB]etween)\\s+(\\d+[\\d,\\.]*\\d)[-–‑−—―](\\d+[\\d,\\.]*\\d)\\b(?!\\s+and\\b)(?!\\s+to\\b)(?!-)': 2,  # noqa
    '\\b([bB]irth|[fF]ire)[–‑−—―\\s]place(s)?\\b': 2,  # noqa
    '\\b([bB]r|[ltLT]|[sS]l)ightly-(?=[a-z]+\\b)(?![a-z]+-)': 2,  # noqa
    "\\b([cC])harg(?:[eè]\\s+d['’´ˈ׳᾿‘′Ꞌꞌ`]|é\\s+(?:D['’´ˈ׳᾿‘′Ꞌꞌ`]|d['’´ˈ׳᾿‘′Ꞌꞌ`]))([aA])ffaires\\b": 2,  # noqa
    '\\b([rR])ecently-(?=[a-z]+ed\\b)(?![a-z]+-)': 2,  # noqa
    '\\b([sS])imilarly-(?=[a-z]+\\b)(?![a-z]+-)': 2,  # noqa
    "\\b([tT])(?:ehy|hey|yhe)(?:ll|[';’´ˈ׳᾿‘′Ꞌꞌ`]l+)\\b": 2,  # noqa
    '\\b(an?\\s+\\d\\d?(?:[nr]d|st|th))\\s+century\\b': 2,  # noqa
    "\\b(are|[cC](?:a|ould)|[dD](?:id|o(?:es)?)|[hH]a(?:[ds]|ve)|[sS]hould|[wW](?:as|ere|o(?:uld)?))(?:[';’´ˈ׳᾿‘′Ꞌꞌ`]n|n[;’´ˈ׳᾿‘′Ꞌꞌ`])t\\b": 2,  # noqa
    "\\b(could|should|they|w(?:h(?:at|o)|ould)|you)['’´ˈ׳᾿‘′Ꞌꞌ`]ve\\b": 2,  # noqa
    '\\b(modern|present)[–‑−—―\\s]+day\\b(?=\\s)(?<=\\b(?:[aA]|[bB]y|[iI](?:n|ts)|[nN]ear|of|[tT]heir|with)\\s+(?:modern|present)\\s+day)': 2,  # noqa
    '\\bAcademy\\b(?<=\\b(?:[aA]n?|[iI]ts|new|of|same|[tT]h(?:e|is)|\\w+,)\\s+\\w+)(?!(?:\\s+(?:for|o[fn])(?:\\s+the)?)?\\s+[\\dA-Z])(?<![\\w,]\\s+An\\s+\\w+|Triple\\s+A\\s+\\w+)': 2,  # noqa
    '\\bE(d(?:itorial|ucation)|ngineering|xecutive)(?<=(?:\\(|(?:[,;]|[\\s\\(](?:[a-z]+|A[ns]|Current|Former|Its|The))\\s+)\\w+)\\s+[dD]irector(s)?(?=\\s+[a-z\\(]|[,;:\\.\\)])(?<!\\b[A-Z][a-z]+\\s+of\\s+\\w+\\s+\\w+)': 2,  # noqa
    '\\bP[hH]\\.(?<=[\\s\\(]P[hH]\\.)\\s*D\\.?(?<!Ph\\.D\\.)(?=[\\s,\\)])': 2,  # noqa
    '\\b[eE]ncycl(?:op(?:ae|e?)|pa?e)dia\\s+[bB]rit+an+ic*a+\\b': 2,  # noqa
    '\\b[fF]ed[–‑−—―\\s]?[eE]x\\b': 2,  # noqa
    '\\bai?sia(ns?|s?|tic)\\b': 2,  # noqa
    '\\barmenia(ns?)?\\b': 2,  # noqa
    "\\bniger(i[ae]n?s?|ois|\\b(?!''))(?!\\s*seed)\\b": 2,  # noqa
    '\\b(?:and\\s+)?([eE])(?:tc\\b(?<!/etc)([^\\.\\w])|ct\\b\\.*)': 3,  # noqa
    '\\b(?:you[–‑−—―\\s]?[tT]|You(?:[-–‑−—―][tT]|t|\\s+[tT]))ube(rs?)?\\b(?<!</?youtube)': 3,  # noqa
    '\\b(a(?:[ms]?|nd?|re)|b(?:e(?:come)?|y)|could|d(?:id|o)|f(?:or|rom)|go|h(?:a(?:s|ve)|e|im|ow)|i[fst]s?|m(?:ade|e|ore)|no|o(?:[fr]|ther)|sh(?:e|ould)|t(?:h(?:e(?:ir|[mny]?|se)|[iu]s)|o)|w(?:as|ere|h(?:at|e(?:n|re)|i(?:ch|le)|om?|y)ith|ould)|is\\s+a)\\s{1,5}\\1\\b(?!-)': 3,  # noqa
    "\\bD(epartment(?:['’´ˈ׳᾿‘′Ꞌꞌ`]s)?)(?<=(?:\\bThe|\\s[a-z]+)\\s+[\\w'’]+)(?=\\s+[a-z]+\\s+[a-z\\d]|[,;\\.])(?!\\s+of\\s)": 3,  # noqa
    '\\bUS(?:\\s+(?:D\\$?|\\$)|D\\$?|\\$)(?<=(?:\\b[a-z]+\\s+|[\\(,]\\s*)US[\\s\\$D]+)(?:\\s+(?:&nbsp;\\s*)?|&nbsp;\\s*)?\\$?(?<!US\\$)(?=\\d)': 3,  # noqa
    '\\bU\\.S(?=[\\s,])(?<=\\sU\\.S)': 3,  # noqa
    "\\bV(ice)\\b(?<=\\s+(?:a(?:cting|ppointed|s?)|be(?:en|c(?:ame|om(?:e|ing)))?|Democratic|elected|for(?:mer)?|h(?:er|i[ms])|i(?:ncumbent|s|ts)|n(?:amed|ew)|Republican|s(?:erving|itting)|t(?:heir|o)|U\\.?S\\.?|was|\\w+'s)\\s+\\w+)(?<![A-Z][a-z]+\\s+for\\s+\\w+)([-\\s]+)[pP](residen(?:cy|t(?:ial|sial)?))(?=(?:[,\\.;\\)]|\\s+[a-z]+))(?!\\s+of\\s)": 3,  # noqa
    '\\b[aA]merc?ic?a(n(?:[as]?|ism))?\\b(?<!America[nasim]*)(?<![A-Z](?:[a-z]+|\\.)\\s+\\(?americana)': 3,  # noqa
    "\\b[aA]pril\\s+[fF]ools['’´ˈ׳᾿‘′Ꞌꞌ`]?\\s+[dD]ay\\b": 3,  # noqa
    '\\b[mM]et+al+ica\\b': 3,  # noqa
    '\\bafghani(s(?:tan)?)?\\b': 3,  # noqa
    '\\bend\\s+result\\b': 3,  # noqa
    '\\b(?:eng?|En)l(and|ish(?:m[ae]n|wom[ae]n)?)': 4,  # noqa
    '\\b([iI]t?)[;’´ˈ׳᾿‘′Ꞌꞌ`]([dms]|ll)\\b': 4,  # noqa
    '\\b([nN])ewly-(?=(?:[a-z]+ed\\b|(?:a(?:rriving|vailable)|b(?:o(?:rn|ught)|uilt)|d(?:eveloping|rawn|ug)|e(?:ligible|merging)|forming|independent|made|popular|r(?:e(?:b(?:orn|uilt)|drawn)|ich)|s(?:hot|ingle)|w(?:ealthy|on|ritten))\\b))(?!formed|wed)': 4,  # noqa
    '\\b(\\d+)(?<=(?:\\s|\\()\\d+)[-—](\\d+)(?=\\s+(?:a(?:cademic|dvantage|gainst|t|way)|c(?:areer|omeback)|d(?:eadlock|ef(?:eat|icit)|raw)|edge|final|game|home|in|(?:halftime\\s+)?lead|(?:road\\s+)?loss|ma(?:jority|rgin|rk)|o(?:n|ver(?:all|time)?)|(?:(?:conference|playoff|regular(?:\\-|\\s+)season)\\s+)?record|r(?:esult|out|un)|sc(?:hool\\s+year|ore(?:line)?)|((?:regular|undefeated)\\s+)?seasons?|s(?:eries|h(?:ootout|utout)|plit|t(?:alemate|art)|weep)|t(?:erm|ie|o|riumph)|upset|v(?:ictory|ote)|(?:road\\s+)?win|with)\\b)(?<!\\b(?:A(?:tco|TCO)|Columbia|Dot|Epic|ISO|[Ll]aws?|RCA|[sS]er(?:ial|\\.)(?:\\s+[nN]o\\.)?|s/[nN]:?)\\s+\\d+[-—]\\d+)(?<!\\b7\\d7-\\d+)(?!(?<=1-2)\\s+result)': 4,  # noqa
    "\\b(he|she|they|wh(?:at|o)|you)['’´ˈ׳᾿‘′Ꞌꞌ`]ll\\b": 4,  # noqa
    "\\bApostle(?:['’;´ˈ׳᾿‘′Ꞌꞌ`]s['’´ˈ׳᾿‘′Ꞌꞌ`]?|s['’´ˈ׳᾿‘′Ꞌꞌ`]?)\\s+Creed\\b": 4,  # noqa
    "\\bChair(m[ae]n|persons?|wom[ae]n)?\\b(?<=(?:(?:\\bAs|The|\\s[a-z]+|[-–;,])\\s+|\\()\\w+)(?=(?:\\s+of\\s+the(?:\\s+[aA]dvisory)?\\s+[bB]oard\\b|\\s+(?:a(?:fter|nd|t)|b(?:etween|y)|during|f(?:or|rom)|i[ns]|on|since|to|until|w(?:as|ith))\\s|[,;\\.\\)])|\\s+[a-z]+[,;\\.\\)]|\\s+[io]n\\s|\\s+of\\s+the\\s+[a-z]|(?:\\s+[a-z]+){3,}|['’´]s\\s+[a-z])": 4,  # noqa
    '\\bE(merit(?:us|[ai]))(?<=(?:[;,]|\\s[a-z]+)\\s+\\w+)(?<!Augusta\\s+Emerita)(?!\\s+(?:Augusta|Park))\\b': 4,  # noqa
    "\\bVice\\b(?<=(?:\\b(?:[a-z\\d]+|Its|The|\\w+['’´ˈ׳᾿‘′Ꞌꞌ`]s)\\s+|,\\s+|\\()\\w+)-[pP]resident(s)?\\b(?=(?:[,;\\.\\)]|\\s+[a-z\\(]))": 4,  # noqa
    "\\bwon['’´ˈ׳᾿‘′Ꞌꞌ`]t\\b": 4,  # noqa
    '\\b(?:the\\s+)?(A(?:pril|ugust)|December|February|J(?:anuary|u(?:ly|ne))|Ma(?:rch|y)|November|October|September)\\s+of\\s+([12]\\d{3})\\b': 5,  # noqa
    '\\b([ck]?m|mi)²': 5,  # noqa
    '\\b([gG])reat\\s+(?=(?:great[-–‑−—―\\s]+){0,5}grand(?:aunts?|child(?:ren)?|daughters?|fathers?|kids?|mothers?|n(?:ephews?|i(?:blings?|eces?))|parents?|sons?|uncles?)\\b)': 5,  # noqa
    '\\b([tT])rad(?:e|ing)[–‑−—―\\s]block?\\b': 5,  # noqa
    '\\bUniversity\\b(?<=\\b(?:[aA]n?|[iI]ts|new|of|same|[tT]h(?:e|is)|\\w+,)\\s+\\w+)(?!(?:\\s+(?:at|for|o[fn])(?:\\s+the)?)?\\s+[\\dA-ZŁ])(?<![\\w,]\\s+A\\s+\\w+)': 5,  # noqa
    '\\b[mM]arxis([mt])-[lL]eninis([mt])\\b': 5,  # noqa
    "\\b(?<=[\\s\\(]|\\A)([aA])(?<=a|(?:[\\.\\n]\\s\\s?\\s?|\\A)A)\\s\\s?((?:[aA](?!\\b|2\\b|[aA]A?[aTA]?|b(?:ogado|rirse)|c(?:a(?:demiei|o)|ceptat?a?|estei|ordo|quis)|ddaswyd|ED|FN|f(?:ace|ecta)|j(?:outé|uns)|l(?:ba\\b|calde|do\\b|guien\\b|ma)|LL|m(?:basadei|érica)|MD|[nN](?:\\b|amnese|[dD]\\b|daluc|G|ihila|tiga|ului)|OA|p(?:a(?:gar\\b|recer\\b)|ostar\\b|robat\\b)|quest|r(?:der\\b|enys\\b|matei\\b|quitectura|te(?:\\b|lor\\b))|R[S\\$]|s(?:\\b|souvi)|t(?:\\b|ahualpa\\b|enuar|hair|lântida|riz|teint)|U[DS\\$\\£]|us(?:iàs|triei\\b)|v(?:ançar|enida|ut\\b)|WG|ZN)|[eE](?!\\b|cologia|di(?:ção|l\\b|tora\\b)|gipto|GP|l(?:a\\b|itei\\b|las\\b)|m(?:a\\b|b(?:ajadora|oîté)|igracja|pezar\\b)|n(?:core\\sdu|ergia|f(?:lamm[eé]|rentar)|ga(?:gé|ñar)|loquecer|se[nñ]ar|tend(?:erse|u)\\b|tra(?:da|[iî]n[eé]|r\\b)|tre(?:na(?:dor|r))?|voyé)|qui(?:librista|p[ao])|RN|s(?:as?\\b|c(?:a[dl]a|ola|u(?:char|ela|ltura|ridão))|fera|p(?:a(?:ldas|[nñń])|erança))|st(?:a(?:\\b|ciones|dos|r\\b)|é|e(?:\\b|ban)|o(?:\\b|s\\b)|ra(?:da|t[eé][gx]ia)|r(?:é[il]a|e(?:[il]a|llar)|uc?tura)|udia[nr])|TB\\b|t(?:é|e(?:rna)?)?\\b|[uU](?:[A-Za-z]{2}|\\sde\\b)|u\\b|U[IR]|v(?:acuar|r(?:eilor|op))|w[abei]|x(?:ist[ée](?:ncia)?|p(?:ansão|eri[eê]ncia|osição|ressão))|xtranj)|h(?:aut[besu]|eir|o(?:rs\\sd|ur(?:\\b|[gs]|ly)))|[iI](?!\\b|a(?:ij|[șş]i)|DR\\b|greja|[iI][iI]?[iI]?|l(?:\\sraen\\b|egal|ha\\b)|LS|m(?:age[nm]\\b|igração|magini\\b)|n(?:\\b|ceput|dia[’']?s\\b|d(?:icação|ro\\b|úst)|és|f(?:luência|ormační)|glat|icios|nei\\b|quisição|s(?:t(?:ancias|itucí)|ulté)|t(?:e(?:gra(?:nte|rse)|ligência|r(?:preta|ven)[cç][aã]o)|imidade|ra\\b)|v(?:asão|e(?:nté|stit)))|NR\\b|QD\\b|R(?:£|R\\b)|s(?:\\b|chia\\b|la\\b|te\\b)|SK|ts?\\b|u(?:bit(?:\\b|-o\\b)|d(?:ex\\b|ice\\b)|re\\b)|[vx]\\b|V(?:th|\\b)|XC?\\b|[\\b\\d])|M(?:D\\b|VP\\b)|[oO](?!\\b|ax|b(?:a\\b|čan|chodní|ra|tenu|ţi|yv)|c(?:cidente|h(?:o|rany)|upat)|d(?:\\b|e[cč]et\\b)|este|f(?:\\b|erecer)|ggi|hniv|ito\\b|kol[íi]e?\\b|l(?:ot\\b|še\\b|vidarte)|mnisciê|MR\\b|nda\\b|[nN](?:\\s|[cçiIC][eaE]|[eE](?!g(?:\\b|a\\b|es|in)|i(?:da|[lr])|rous))|O\\b|opa|p(?:éra|erador\\b)|ra?\\b|[rR](?:\\b|a(?:[şsș]ului|z\\b)|chestr\\b|d(?:em|inii)|fu\\b|i(?:\\b|lla))|S-9\\b|s(?:asuna|curas|o(?:bnosti|na))|t(?:r[ao]\\b|tobre)|u(?:\\b|a[bcdglt]|ed|i|tro)|v(?:elha|iedo))|u(?!\\b|[A-Z\\dcček\\:\\.\\-]|a(?:dim|h\\b|in\\b)|b[aiou]|d(?:ev\\b|raw\\b)|fo|g(?:a(?:li|nd)|x\\b)|i(?:le\\b|n|ro|tat\\b)|jam|l(?:ak|u)|m(?:a\\b|\\b|ění\\b|r(?:ia|l))|n(?:(?:\\s|a(?:ni|ry|s\\b|\\b|te\\b))|d\\b|e(?:\\b|i\\b|sco)|o[rs]?\\b|s\\b|uib?)|ni(?!d(?:[eol]|io)|gn|ll|m(?:ag|[bim]|p[aeloru])|n(?:au|[cd]|eb|[fghjk]|i[nt]|oc|[tnvsq])|r(?:ad|[kr]|on))|omo|p(?:azilas?|risin\\b)|r[aeiolsuy]|s[aeiou]|s(?:b(?:net)?|d)\\b|s\\$|s(?:hape|t(?:ream|ed(?:es)?\\b))|t(?:[aeiou]|r(?:anga|ic))|[vž]|yu\\b|zs\\b))[^\\|\\[\\]\\<\\⌊\\>\\{\\}\\s]{0,29})(?<=\\b(?:[\\S\\s]){1,49}(?<!\\b(?:[aA](?:baten|c(?:ceso|o(?:mpañando|sa)|t)|cusa|d(?:herits|i[oó]s|misión|vanced)|eroporto|gus|menazan|[nñN][oO]|n(?:\\b|dalucía|fibio|s\\b)|prendiendo|şa|spirante|t(?:acó|ención)|u(?:menta|r|sf(?:\\.|ührung)|torov)|xudar|y(?:údame|ud(?:ar|dó)))|[bB](?:a(?:rokiem|ttery)|enefician|ílé|usca(?:ndo)?)|[cČC](?:a(?:bellera|lle|mino|ntan?\\b|r(?:retera|tas?))|a(?:sar|tegory\\:?)|e(?:n(?:sura|trală)|rcano)?|h(?:ama|lorophyll|romogranin?)|iclista|íny|lass|o\\.|om(?:ienzan|p(?:any|o(?:sition|und)|r(?:ó|ometido))|unicações)?|o(?:n(?:certo|firma|oció|trat[aoó]|vocatoria)|sta)|u(?:arto|m)|yclosporine)|[dD](?:[áàâăåeêèé]|a(?:lla)?|e(?:dicada|[nst]|nuncian|recho|seó|tienen|s(?:apareceu|p(?:edida|iden))|voción)|[iîìíòôóuùûú]|i(?:gas|le|recto|vision)|o(?:jmy|uble)|urante)|[eéEÉ](?:\\b|cusa|insatzgruppe|jecutan?|l(?:e|le)|mpecé|n(?:frenta(?:rá)?|señ(?:ame|[óo])|t(?:onces|re(?:\\b|gó|vista)))?|s(:quivel|t)?|t|x(?:itos|tradita(?:do)?))|[fF](?:a(?:cilitar|z)|e(?:menina|rmato)|i(?:ammanti|chó)|ormula|rente|u(?:[ií]|sil|tbol))|[gG](?:alega|enerală|lorie|olpe|r(?:ade|oup)|uerra)|[hH](?:istorických|o(?:mena(?:gem|je|tge)|usle))|[iI](?:\\b|l\\b|n(?:formații|na|te(?:gran|r(?:preta|vista)))|n(?:trodu(?:cción|zione)|vita(?:ción)?)|storie|terum)|[jJ](?:r|un(?:g|ior|to))|[kK](?:lavír|r(?:ál|tek)|u(?:ltúry|řátko))|[lL](?:abe|e\\b|ékaři|ewis|i(?:gada|pid|st)|íderes|iniers|le(?:ga(?:n?|r[aá]?)|va(?:n|sen))|u(?:i|xe))|[mM](?:a(?:nu|s|tar)|hic\\b|\\.I|[íi]nima\\b|iedo|o(?:del|n(?:te|umento)|ro[șs]anu)|o(?:u(?:lin|nd)|vid[ao])|u(?:lt|sgos))|[nN](?:bsp|ei|iegan|ônibus|o(?:mbrar|tícia|us))|[oO](?:kina\\}\\}|cchio|lza|maggio|noare|riente|sob\\b|t(?:ázky|ec\\b)|u\\b)|[pP](?:a(?:r[at]|s(?:ado|sou?))|e(?:ntru|r(?:ò|petua)|se)|i(?:etro|ù)|lan|o(?:int|nte)|r(?:o|ólogo|e(?:ludio|senta))|r[ůu]myslu|ublicat|\\.)|[qQ](?:\\sand|u(?:ando|[ei]))|[rR](?:apó|e(?:c(?:ibe|ordando|usa)|ferencias|gião|i|torno)|isale|o(?:i|mână|zšířené))|şi\\b|[sS](?:a(?:be|lve\\b|tisface)|e(?:ason|cuestran|ine)|[eé]r(?:á|ie|vir)|i(?:c\\s?(?:\\|)?|de|ngle)|o(?:b(?:re)?|ciální|u)|p(?:ortivă|rijin)|t(?:avební|yky)|u(?:b(?:ida|unit|(?:-)unit)|ma|p(?:le|plemento)|rt|stituye)|[\\.é])|[tT](?:arda|áxi|he|o(?:da|or(?:no|turan))|r(?:azendo|en|i(?:buto|ple))|ype)|[uU](?:hlie|n[ade])|[vV](?:a(?:da|[is]?|mos?|riant|yas)|e(?:che|n(?:ce[rn]?|d[aeo]|g[ao]|t[ae]))|e(?:ta|z)|ě(?:du?|rný)|i(?:agem|llena|ol(?:on?cello|u))|i(?:tamin|va(?:ce)?)|ojsko|ol(?:a(?:mos|r)|ta|v(?:amos|er(?:[aáé]|emos|te)?)|v(?:í|i(:?endo)?))|oy|uel(?:[aeu]\\b|t[ao]\\b|v[aeo]s?\\b))|[wW]h[aā]nau|[yY]\\b|[zZŽ](?:eit|ivoty))\\W?\\s?\\s?[aA]\\s?\\s?\\2))": 6,  # noqa
    '\\bCollege\\b(?<=\\b(?:[aA]n?|[iI]ts|new|of|same|[tT]h(?:e|is)|\\w+,)\\s+\\w+)(?!(?:\\s+(?:de|for|o[fn])(?:\\s+the)?)?\\s+[\\dA-Z])(?<![\\w,]\\s+A\\s+\\w+)': 6,  # noqa
    '\\bProvince(?<=(?:[;,]|\\s[a-z]+)\\s+\\w+)\\s+of\\b(?!\\s+Canada)': 6,  # noqa
    "\\bmid\\b(?<=\\b[tT]he\\s+\\w+)[\\s–]+(20\\d0|1[4-9]\\d0)['’;´ˈ׳᾿‘′Ꞌꞌ`]?s\\b": 6,  # noqa
    '\\b[hH]ans?\\s+[cC]hristian\\s+[aA]nders[eio]n\\b': 7,  # noqa
    "\\b[pP]alme?\\s+[dD]['’´ˈ׳᾿‘′Ꞌꞌ`][oO]r\\b": 7,  # noqa
    '\\b[pP]rince\\s+[eE]dward\\s+[iI]sland(er?s?|rs?|s?)\\b': 7,  # noqa
    '\\bet(?:\\.\\s*al\\b\\.?|\\s+al\\b(?!\\.))': 7,  # noqa
    '\\s+,(?<=[A-Za-z\\d\\)]\\s+,)\\s?': 7,  # noqa
    'ically-(?=[a-z]+\\b)(?![a-z]+-)': 7,  # noqa
    "\\b(?:C(?:ote\\s+[dD]['’´ˈ׳᾿‘′Ꞌꞌ`][iI]|ôte\\s+(?:D['’´ˈ׳᾿‘′Ꞌꞌ`][iI]|[dD](?:['’´ˈ׳᾿‘′Ꞌꞌ`][iI]|['’´ˈ׳᾿‘′Ꞌꞌ`]i)))|c[oô]te\\s+d['’´ˈ׳᾿‘′Ꞌꞌ`][iI])voire\\b": 8,  # noqa
    '\\b[sS][ãa]o\\s+[tT]om[éeè]\\s+(?:[aA]nd|&)\\s+[pP]r[íi]ncipe\\b': 8,  # noqa
    "\\bcan['’´ˈ׳᾿‘′Ꞌꞌ`]t\\b": 8,  # noqa
    "\\b([tT])hey[';’´ˈ׳᾿‘′Ꞌꞌ`]?([rv])e?\\b": 10,  # noqa
    "\\b(they|w(?:e|h(?:at|o))|you)['’´ˈ׳᾿‘′Ꞌꞌ`]re\\b": 10,  # noqa
    '\\b([fF]rom)(?<![cC]ompilation\\s+from)\\s+(\\d+[\\d,\\.]*\\d)[-–‑−—―](\\d+[\\d,\\.]*\\d)\\b(?!\\s+til\\b)(?!\\s+to\\b)(?!\\s+until\\b)(?!-)': 11,  # noqa
    '\\bPresident(s)?\\b(?<=\\b(?:[cC]o|[vV]ice)-\\w+)': 11,  # noqa
    "\\b([yY])ou[';’´ˈ׳᾿‘′Ꞌꞌ`]?(d|ll|[rv]e)\\b(?<!\\bYoud)": 13,  # noqa
    "\\bC(athedral|ent(?:er|re)|hapel|ity|lub|o(?:llege|m(?:mi(?:ssion|ttee)|pany)|n(?:sulate|vention)|rporation|un(?:cil|ty)))(?<=\\b(?:[iI]ts|[tT]h(?:e|is))\\s+\\w+)(?=(?:[,\\;\\.\\)\\:]|['’´ˈ׳᾿‘′Ꞌꞌ`]s\\s|\\s+[\\(–]|\\s+(?:a(?:cquired|fter|lso|n(?:d\\s+[a-z]+\\s+[a-z]+|nounced)?|re|s?)|b(?:e(?:fore|gan)|ut|y)|c(?:an|o(?:nducts|uld)|urrently)|during|established|f(?:or|rom)|h(?:a[ds]|osts)|is?|launched|ma(?:de|intains)|now|o(?:ffers|n\\s+[a-z\\d]+|perates|r)|receive[ds]|s(?:hould|upports)|t(?:he|o)|until|w(?:as|ere|hile|i(?:ll|th)|o(?:rks|uld)))\\b))(?!\\s+(?:for|o[fn])(?:\\s(?:an?\\b|the\\b))?\\s+[A-Z])": 14,  # noqa
    "\\b([tT])ha(?:t['’;´ˈ׳᾿‘′Ꞌꞌ`]?s|st)\\b": 15,  # noqa
    '\\b[eE]ncyclo?p(?:ae?|[eæ]?)dia\\s+Brit(?:a(?:n(?:ic*|n+i(?:cc)?)|n+ic+)|t+a(?:n(?:ic*|n+i(?:cc)?)))a+\\b': 16,  # noqa
    "\\b(Accordingly|Consequently|Even\\s+so|F(?:or\\s+example|urthermore)|In(?:deed|\\s+other\\s+words)|M(?:eanwhile(?!\\s+Gardens)|oreover)|N(?:ever|one)theless|On\\s+the\\s+other\\s+hand|Therefore|Subsequently(?!\\s+(?:enacted|featured|re(?:built|named)|t(?:old|ransferred))))(?!\\s+\\|)?(?=\\s+[\\p{L}´ˈ׳᾿’′Ꞌꞌ`'\\[\\|\\]]+\\b)": 20,  # noqa
    '…': 22,  # noqa
    '\\b(\\d+)(?<=\\s\\d+)(?<!number[\\s\\d]+)[-—](\\d+)[-—](\\d+)(?=[,\\.;\\n\\)])(?<!\\b(?:(?:1[7-9]|20)\\d{2}-\\d{2}-\\d{2}|9-1-1|\\d{3}-\\d{3}-\\d{4}|\\d{5}-\\d{5}-\\d{1,4}))': 25,  # noqa
    '\\b(A(?:pril|ugust)|December|February|J(?:anuary|u(?:ly|ne))|Ma(?:rch|y)|November|October|September)(?<=\\b(?:[aA]fter|and|[bB](?:e(?:fore|tween)|orn|y)|[dD]ied|[fF]rom|[oO]n|to|[uU]ntil|\\w+,)\\s+\\w+)\\s+([1-3]?\\d),\\s+([12]\\d\\d\\d)(?=\\s+\\w)': 30,  # noqa
    '\\b[nN]ova\\s+[sS]cotia(n)?\\b': 33,  # noqa
    '\\b(\\d+)(?<=\\s\\d+)[-—](\\d+)(?=[,\\.;\\n\\)])(?<!\\b(?:ANSI(?:/VITA)?|A(?:cc\\.\\s+[Nn]o\\.|STM\\s+[A-Z]+|tco|TCO)|Boeing|C(?:GCG|olumbia)|D(?:ash|ot)|Epic|FIPS|I(?:EC|NCITS|RAS|S[BS]N:?|SO(?:/IEC)?)|[Ll]aws?|LCCC?N|[mM](?:GC|odel)|N(?:ACA|[oO]\\.?:?)|[nN](?:GC|umber:?)|#:?|P(?:art|K|N\\s*G|ublication)|RCA[;,]?|[rR]unway|S(?:ection|[ah]|/[nN]:?)|[sS]er(?:ial|\\.)(?:\\s+[nN]o\\.)?|s/[nN]:?|VITA|Widow)\\s+\\d+[-—]\\d+)(?<!\\b(?:\\d(?:[-—][02-9]\\d|\\d[-—][02-9]\\d\\d)|\\1[-—]\\1\\b|7\\d7-\\d+|\\d{5}[-—]\\d{4}))': 51,  # noqa
    "(?<=\\w)[;’´ˈ׳᾿‘′Ꞌꞌ`]s\\b(?<!'\\w[;’´ˈ׳᾿‘′Ꞌꞌ`]s|&[#\\w]{1,99};s)": 73,  # noqa
    "\\b(are|could|d(?:id|o(?:es)?)|ha(?:[ds]|ve)|is|m(?:ight|ust)|should|w(?:as|ere|ould))n['’´ˈ׳᾿‘′Ꞌꞌ`]t\\b": 107,  # noqa
}

regexes = sorted(regexes, key=lambda r: (len(r), r))

please_load = "all"

if please_load == "high_freq_only":
    regex_list = []
    for regex_string in regexes:
        if regex_string in regex_frequencies.keys():
            regex_list.append(regex_string)
    regex_list = sorted(regex_list, key=lambda r: regex_frequencies[r])
    regex_dict = {r: re.compile(r) for r in regex_list}
elif please_load == "low_freq_only":
    regex_list = []
    for regex_string in regexes:
        if regex_string not in regex_frequencies.keys():
            regex_list.append(regex_string)
    regex_dict = {r: re.compile(r) for r in regex_list}
elif please_load == "all":
    regex_dict = {r: re.compile(r) for r in regexes}
else:
    print(f"Unknown please_load {please_load}")
    exit(1)

print(f"Loaded {len(regex_dict.keys())} regular expressions")

# regex_dict = {r: re.compile(r) for r in regexes}
# print(f"Loaded {len(regexes)} regular expressions")


def skip_article(article_text):
    """
    # Weeded out upstream by xml_to_csv.py
    if article_text.startswith("#REDIRECT") or article_text.startswith("#redirect"):
        return True
    """

    for skip_string in skip_article_strings:
        if skip_string in article_text:
            return True

    return False


attr_suppressor = re.compile('<(ref|span) .*?>')
general_suppressor_patterns = [
    r"https?://[^ \n\|&]+",
    r"[0-9a-zA-Z\-\.]+\.(com|edu|org|gov)",
    r"<!--.*?-->",
    r"{{not a typo.*?}}",
]
general_suppressor_regexes = [re.compile(p, flags=re.S) for p in general_suppressor_patterns]

# Reduce false positives at the expense of missing some things
aggressive_suppressor_patterns = [
    r'<ref( .*?>|>).*?</ref>',
    r'<ref .*?/>',
    r"<gallery[^>]*>.*?</gallery>",  # Must happen before table removal due to possibility of "|-"
    r"<code[^>]*>.*?</code>",
    r"<syntaxhighlight[^>]*>.*?</syntaxhighlight>",
    r"<math[^>]*>.*?</math>",
    r"<score[^>]*>.*?</score>",
    r'{\|.*?\|}',
    r'{{[Ii]nfobox([^}]+{{.*?}})+.*?}}',
    r'{{[Ii]nfobox.*?}}',
    r'\[\[(File|Image):.*\]\]',
    r'{{[Ll]ang.*?}}',
    r'{{IPA.*?}}',
]
aggressive_suppressor_regexes = [re.compile(p, flags=re.S) for p in aggressive_suppressor_patterns]


def clean_article(article_text, aggressive=False):
    article_text = attr_suppressor.sub(r"<\1>", article_text)
    for suppress_re in general_suppressor_regexes:
        article_text = suppress_re.sub("✂", article_text)
    if aggressive:
        article_text = get_main_body_wikitext(article_text)
        for suppress_re in aggressive_suppressor_regexes:
            article_text = suppress_re.sub("✂", article_text)
    return article_text


def regex_callback(article_title, article_text):
    if skip_article(article_text):
        return
    article_text = clean_article(article_text, aggressive=True)

    for (regex_string, regex_compiled) in regex_dict.items():
        result = regex_compiled.search(article_text)
        if result:
            print(article_title)
            # For performance reasons, stop after the first detected problem
            return


checked = 0
skipped = 0
regex_runtimes = defaultdict(int)
regex_hits = defaultdict(int)
debug_contents = False
print_stats = False  # Probably need to set parallel=False


def show_replacement(result, regex_string, regex_compiled, article_text):
    replacement = transform_dict[regex_string]
    snippet_start = max(result.start() - 10, 0)
    snippet_end = min(result.end() + 10, len(article_text))
    snippet = article_text[snippet_start:snippet_end]
    changed_to = regex_compiled.sub(replacement, snippet)
    if snippet == changed_to:
        return None
    else:
        snippet = snippet.replace("\n", "\\n")
        changed_to = changed_to.replace("\n", "\\n")
        return (f'"{snippet}" -> "{changed_to}"')


def calibration_callback(article_title, article_text):
    global checked
    global skipped

    if skip_article(article_text):
        skipped += 1
        return
    article_text = clean_article(article_text, aggressive=True)

    checked += 1
    article_matched = False
    for (regex_string, regex_compiled) in regex_dict.items():
        if print_stats:
            start_time = time.time()
            result = regex_compiled.search(article_text)
            elapsed = time.time() - start_time
            regex_runtimes[regex_string] += elapsed

        if result:
            replacement_str = show_replacement(result, regex_string, regex_compiled, article_text)
            if replacement_str:
                article_matched = True
                if print_stats:
                    regex_hits[regex_string] += 1
                print(f"{article_title}\t{pformat(result[0])}\t{replacement_str}\t{regex_string}")

    if article_matched and debug_contents:
        print(">>>>>>>>>>>>>>>>>>>>")
        print(article_text)
        print("<<<<<<<<<<<<<<<<<<<<")

    if print_stats:
        if checked % 1000 == 0:
            print(f"{checked} articles checked so far", file=sys.stderr)
            print(f"{skipped} articles skipped so far", file=sys.stderr)
        if checked % 1000 == 0:
            runtimes_sorted = sorted(regex_runtimes.items(), key=lambda pair: (pair[1], pair[0]))
            pprint(runtimes_sorted)

            hits_sorted = sorted(regex_hits.items(), key=lambda pair: (pair[1], pair[0]))
            for (r, hits) in hits_sorted:
                print(f"    {pformat(r)}: {hits},  # noqa", file=sys.stderr)
            # pprint(hits_sorted)


print(f"{datetime.datetime.now().isoformat()} ")
# read_en_article_text(regex_callback, parallel=True)
read_en_article_text(calibration_callback, parallel=True)
print(f"{datetime.datetime.now().isoformat()} ")
