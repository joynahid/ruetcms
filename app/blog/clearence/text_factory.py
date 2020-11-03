import re

HTML_ESC = [
    ('<','&lt;'),
    ('>','&gt;'),
    ('/','&#47;'),
    ('\\','&#92;'),
    ('& ','&#38;'),
]

BOLD = (
    '<b>','</b>'
)

HEAD = (
    '<h3>','</h3>'
)

LINK = (
    '<a target="__blank" href="','</a>'
)

CODE = (
    '<div class="code"><code>','</code></div>'
)

class textFactory:
    def __init__(self, string):
        self.data = string.strip()
        self.markdown = {}

    def escape(self):
        for i in HTML_ESC:
            self.data = self.data.replace(i[0],i[1])

        return self.data

    def isTitle(self, str):
        ok = True

        return ok

    def tokenize(self):
        boldTexts = re.finditer(r'(\*{2}[\w\W]+?\*{2})', self.data, flags = re.I|re.M)

        for e in boldTexts:
            rng = e.span()
            self.markdown[rng[0]] = 'b',rng

        headTexts = re.finditer(r'(^##.+?\n*$)', self.data, flags = re.I|re.M)

        for e in headTexts:
            rng = e.span()
            self.markdown[rng[0]] = 'h',rng

        linkTexts = re.finditer(r'((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)', self.data, flags = re.I|re.M)

        for e in linkTexts:
            rng = e.span()
            self.markdown[rng[0]] = 'l',rng
        
        codeBlock = linkTexts = re.finditer(r'(\`\`\`[\s\S]+?\`\`\`)', self.data, flags = re.I|re.M)

        for e in codeBlock:
            rng = e.span()
            self.markdown[rng[0]] = 'c',rng

    def makeBold(self):
        boldText = ''
        n = len(self.data)
        i = 0
        while i<n:
            whatToDo = -1 if i not in self.markdown else self.markdown[i]

            if whatToDo == -1: boldText+=self.data[i]

            elif whatToDo[0] == 'b':
                boldText+= BOLD[0] + self.data[whatToDo[1][0]+2:whatToDo[1][1]-2] + BOLD[1]
                i = whatToDo[1][1]-1

            if whatToDo !=-1: print(whatToDo)
            i+=1

        self.data = boldText

        print('Bold ', self.data)

    def serveHtml(self):
        htmlData = ''

        self.escape()
        self.tokenize()
        self.makeBold()

        n = len(self.data)
        i = 0
        while i<n:
            whatToDo = -1 if i not in self.markdown else self.markdown[i]

            if whatToDo == -1: htmlData+=self.data[i]

            elif whatToDo[0] == 'h':
                htmlData+= HEAD[0] + self.data[whatToDo[1][0]+2:whatToDo[1][1]].strip().strip('\n') + HEAD[1]
                i = whatToDo[1][1]-1

            elif whatToDo[0] == 'l':
                htmlData+= LINK[0] + self.data[whatToDo[1][0]:whatToDo[1][1]] + '">' + self.data[whatToDo[1][0]:whatToDo[1][1]] + LINK[1]
                i = whatToDo[1][1]-1

            elif whatToDo[0] == 'c':
                htmlData+= CODE[0] + self.data[whatToDo[1][0]+3:whatToDo[1][1]-3].strip('\n') + CODE[1]
                i = whatToDo[1][1]-1

            if whatToDo !=-1: print(whatToDo)
            i+=1

        htmlData = re.sub(r'(</h3>\n*)', '</h3>', htmlData, flags = re.I|re.M).replace('\n','<br/>')

        return htmlData